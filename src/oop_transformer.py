"""
OOP Transformer
COBOLの手続き型構造をJavaのオブジェクト指向パターンに変換する
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
from .cobol_parser import (
    CobolProgram, DataItem, Paragraph, Section, Statement,
    StatementType, FileDefinition, to_pascal_case, to_camel_case
)


@dataclass
class JavaField:
    name: str
    java_type: str
    initial_value: Optional[str] = None
    is_array: bool = False
    array_size: int = 0
    access: str = "private"
    comment: str = ""
    is_constant: bool = False
    original_cobol_name: str = ""
    original_picture: str = ""


@dataclass
class JavaMethod:
    name: str
    return_type: str = "void"
    parameters: List[tuple] = field(default_factory=list)
    body_statements: List[Statement] = field(default_factory=list)
    access: str = "public"
    comment: str = ""
    original_paragraph: str = ""
    is_main_entry: bool = False


@dataclass
class JavaClass:
    name: str
    package_name: str = ""
    imports: Set[str] = field(default_factory=set)
    fields: List[JavaField] = field(default_factory=list)
    methods: List[JavaMethod] = field(default_factory=list)
    inner_classes: List['JavaClass'] = field(default_factory=list)
    implements: List[str] = field(default_factory=list)
    extends: str = ""
    is_data_class: bool = False
    comment: str = ""
    is_enum: bool = False
    enum_values: List[str] = field(default_factory=list)


@dataclass
class JavaProject:
    main_class: Optional[JavaClass] = None
    data_classes: List[JavaClass] = field(default_factory=list)
    service_classes: List[JavaClass] = field(default_factory=list)
    enum_classes: List[JavaClass] = field(default_factory=list)
    file_handler_classes: List[JavaClass] = field(default_factory=list)


@dataclass
class TransformOptions:
    package_name: str = "com.migrated"
    generate_getters_setters: bool = True
    use_big_decimal: bool = True
    generate_javadoc: bool = True
    generate_toString: bool = True
    extract_data_classes: bool = True
    extract_enums: bool = True
    extract_file_handlers: bool = True
    group_related_paragraphs: bool = True
    vendor_type: str = "standard"  # Vendor dialect (standard, ibm, fujitsu, etc.)


class OopTransformer:
    def __init__(self, options: TransformOptions = None):
        self.options = options or TransformOptions()

    def transform(self, program: CobolProgram) -> JavaProject:
        project = JavaProject()

        # Step 1: Extract data classes from group-level items
        if self.options.extract_data_classes:
            project.data_classes = self._extract_data_classes(program)

        # Step 2: Extract enums from 88-level items
        if self.options.extract_enums:
            project.enum_classes = self._extract_enums(program)

        # Step 3: Extract file handler classes
        if self.options.extract_file_handlers:
            project.file_handler_classes = self._extract_file_handlers(program)

        # Step 4: Build main class
        project.main_class = self._build_main_class(program, project)

        # Step 5: Group related paragraphs into service classes
        if self.options.group_related_paragraphs:
            services = self._extract_service_classes(program, project)
            project.service_classes.extend(services)

        return project

    def _extract_data_classes(self, program: CobolProgram) -> List[JavaClass]:
        classes = []

        for item in program.working_storage + program.local_storage:
            if item.level == 1 and item.is_group and not item.is_filler:
                cls = self._data_item_to_class(item)
                if cls and len(cls.fields) > 0:
                    classes.append(cls)

        for item in program.linkage_section:
            if item.level == 1 and item.is_group and not item.is_filler:
                cls = self._data_item_to_class(item)
                if cls and len(cls.fields) > 0:
                    cls.comment = f"Linkage section data class (originally from COBOL LINKAGE SECTION)"
                    classes.append(cls)

        return classes

    def _data_item_to_class(self, item: DataItem) -> Optional[JavaClass]:
        cls = JavaClass(
            name=item.to_class_name(),
            package_name=self.options.package_name + ".model",
            is_data_class=True,
            comment=f"Data class migrated from COBOL group item: {item.name}"
        )

        for child in item.children:
            if child.is_88_level:
                continue
            if child.is_filler:
                continue

            if child.is_group and len(child.children) > 0:
                # Nested group -> inner class or separate class
                inner = self._data_item_to_class(child)
                if inner:
                    cls.inner_classes.append(inner)
                    field = JavaField(
                        name=child.to_field_name(),
                        java_type=child.to_class_name(),
                        original_cobol_name=child.name,
                        is_array=child.occurs > 0,
                        array_size=child.occurs,
                    )
                    cls.fields.append(field)
            else:
                field = self._data_item_to_field(child)
                cls.fields.append(field)

        # Add required imports
        for f in cls.fields:
            if "BigDecimal" in f.java_type:
                cls.imports.add("java.math.BigDecimal")
            if f.is_array:
                cls.imports.add("java.util.List")
                cls.imports.add("java.util.ArrayList")

        return cls

    def _data_item_to_field(self, item: DataItem) -> JavaField:
        java_type = item.java_type
        if self.options.use_big_decimal and "double" in java_type:
            java_type = "java.math.BigDecimal"

        initial_value = None
        if item.value is not None:
            initial_value = self._convert_value(item.value, java_type)

        return JavaField(
            name=item.to_field_name(),
            java_type=java_type.replace("java.math.", "") if "BigDecimal" in java_type else java_type,
            initial_value=initial_value,
            is_array=item.occurs > 0,
            array_size=item.occurs,
            original_cobol_name=item.name,
            original_picture=item.picture,
        )

    def _convert_value(self, cobol_value: str, java_type: str) -> str:
        upper = cobol_value.upper().strip()

        if upper in ("SPACES", "SPACE"):
            return '""'
        if upper in ("ZEROS", "ZEROES", "ZERO"):
            if "BigDecimal" in java_type:
                return "BigDecimal.ZERO"
            if java_type in ("int", "long"):
                return "0"
            return '""'
        if upper == "HIGH-VALUES" or upper == "HIGH-VALUE":
            return "0xFF"
        if upper == "LOW-VALUES" or upper == "LOW-VALUE":
            return "0x00"

        # Numeric value
        if java_type in ("int", "long"):
            try:
                return str(int(cobol_value.replace("+", "").replace("-", "-")))
            except ValueError:
                return "0"
        if "BigDecimal" in java_type:
            return f'new BigDecimal("{cobol_value}")'
        if java_type == "String":
            return f'"{cobol_value}"'

        return f'"{cobol_value}"'

    def _extract_enums(self, program: CobolProgram) -> List[JavaClass]:
        enums = []

        def find_88_groups(items: List[DataItem]):
            for item in items:
                # Check if this item has multiple 88-level children -> enum candidate
                children_88 = [c for c in item.children if c.is_88_level]
                if len(children_88) >= 2:
                    enum_cls = JavaClass(
                        name=item.to_class_name() + "Type",
                        package_name=self.options.package_name + ".enums",
                        is_enum=True,
                        comment=f"Enum derived from COBOL 88-level conditions on: {item.name}",
                    )
                    for c88 in children_88:
                        enum_name = c88.name.upper().replace("-", "_")
                        enum_cls.enum_values.append(enum_name)
                    enums.append(enum_cls)

                if item.children:
                    find_88_groups(item.children)

        find_88_groups(program.working_storage)
        find_88_groups(program.local_storage)

        return enums

    def _extract_file_handlers(self, program: CobolProgram) -> List[JavaClass]:
        handlers = []

        for file_def in program.files:
            cls = JavaClass(
                name=to_pascal_case(file_def.select_name or file_def.fd_name or "File") + "Handler",
                package_name=self.options.package_name + ".io",
                comment=f"File handler for COBOL file: {file_def.select_name}",
            )
            cls.imports.add("java.io.*")
            cls.imports.add("java.nio.file.*")

            # Fields
            cls.fields.append(JavaField(
                name="filePath",
                java_type="String",
                access="private",
            ))
            cls.fields.append(JavaField(
                name="fileStatus",
                java_type="String",
                initial_value='"00"',
                access="private",
            ))

            if file_def.organization.upper() in ("SEQUENTIAL", "LINE SEQUENTIAL"):
                cls.imports.add("java.io.BufferedReader")
                cls.imports.add("java.io.BufferedWriter")
                cls.fields.append(JavaField(name="reader", java_type="BufferedReader", access="private"))
                cls.fields.append(JavaField(name="writer", java_type="BufferedWriter", access="private"))

            # Methods
            open_method = JavaMethod(
                name="open",
                return_type="void",
                parameters=[("String", "mode")],
                comment="Open the file (INPUT/OUTPUT/I-O/EXTEND)",
            )
            cls.methods.append(open_method)

            close_method = JavaMethod(
                name="close",
                return_type="void",
                comment="Close the file",
            )
            cls.methods.append(close_method)

            read_method = JavaMethod(
                name="readRecord",
                return_type="String",
                comment="Read a record from the file",
            )
            cls.methods.append(read_method)

            write_method = JavaMethod(
                name="writeRecord",
                parameters=[("String", "record")],
                return_type="void",
                comment="Write a record to the file",
            )
            cls.methods.append(write_method)

            cls.methods.append(JavaMethod(
                name="getFileStatus",
                return_type="String",
                comment="Get the file status code",
            ))

            handlers.append(cls)

        return handlers

    def _build_main_class(self, program: CobolProgram, project: JavaProject) -> JavaClass:
        class_name = to_pascal_case(program.program_id) if program.program_id else "MainProgram"

        main_class = JavaClass(
            name=class_name,
            package_name=self.options.package_name,
            comment=f"Main class migrated from COBOL program: {program.program_id}",
        )

        # Add fields for elementary data items (non-group 01/77 levels)
        extracted_class_names = {c.name for c in project.data_classes}

        for item in program.working_storage + program.local_storage:
            if item.is_filler:
                continue

            if item.is_group and item.to_class_name() in extracted_class_names:
                # Reference to extracted data class
                field = JavaField(
                    name=item.to_field_name(),
                    java_type=item.to_class_name(),
                    initial_value=f"new {item.to_class_name()}()",
                    original_cobol_name=item.name,
                )
                main_class.fields.append(field)
                main_class.imports.add(f"{self.options.package_name}.model.{item.to_class_name()}")
            elif not item.is_group:
                field = self._data_item_to_field(item)
                main_class.fields.append(field)
            else:
                # Group not extracted as separate class - add fields inline
                self._flatten_group_fields(item, main_class)

        # Add file handler references
        for handler_cls in project.file_handler_classes:
            field_name = handler_cls.name[0].lower() + handler_cls.name[1:]
            main_class.fields.append(JavaField(
                name=field_name,
                java_type=handler_cls.name,
                initial_value=f"new {handler_cls.name}()",
            ))
            main_class.imports.add(f"{self.options.package_name}.io.{handler_cls.name}")

        # Convert paragraphs to methods
        all_paragraphs = list(program.paragraphs)
        for section in program.sections:
            all_paragraphs.extend(section.paragraphs)

        for para in all_paragraphs:
            method = JavaMethod(
                name=to_camel_case(para.name),
                body_statements=para.statements,
                original_paragraph=para.name,
                comment=f"Migrated from COBOL paragraph: {para.name}",
            )

            # First paragraph is main entry point
            if para == all_paragraphs[0] if all_paragraphs else None:
                method.is_main_entry = True

            main_class.methods.append(method)

        # Standard imports
        if any("BigDecimal" in f.java_type for f in main_class.fields):
            main_class.imports.add("java.math.BigDecimal")
        if any(f.is_array for f in main_class.fields):
            main_class.imports.add("java.util.List")
            main_class.imports.add("java.util.ArrayList")

        main_class.imports.add("java.util.Scanner")

        # Vendor-specific imports based on EXEC blocks
        if program.has_exec_sql:
            main_class.imports.add("java.sql.Connection")
            main_class.imports.add("java.sql.DriverManager")
            main_class.imports.add("java.sql.PreparedStatement")
            main_class.imports.add("java.sql.ResultSet")
            main_class.imports.add("java.sql.SQLException")

        if program.has_exec_cics:
            main_class.imports.add("// TODO: Add CICS service interface imports")

        # Add SQL connection field if needed
        if program.has_exec_sql:
            main_class.fields.insert(0, JavaField(
                name="connection",
                java_type="Connection",
                access="private",
                comment="JDBC connection for embedded SQL",
                original_cobol_name="EXEC-SQL-CONNECTION",
            ))
            main_class.fields.insert(1, JavaField(
                name="sqlCode",
                java_type="int",
                initial_value="0",
                access="private",
                comment="SQLCODE return value",
                original_cobol_name="SQLCODE",
            ))

        return main_class

    def _flatten_group_fields(self, item: DataItem, cls: JavaClass):
        for child in item.children:
            if child.is_88_level or child.is_filler:
                continue
            if child.is_group:
                self._flatten_group_fields(child, cls)
            else:
                field = self._data_item_to_field(child)
                field.comment = f"From group: {item.name}"
                cls.fields.append(field)

    def _extract_service_classes(self, program: CobolProgram, project: JavaProject) -> List[JavaClass]:
        """Group related paragraphs by prefix into service classes."""
        services = []
        prefix_groups: Dict[str, List[Paragraph]] = {}

        all_paragraphs = list(program.paragraphs)
        for section in program.sections:
            all_paragraphs.extend(section.paragraphs)

        for para in all_paragraphs:
            name = para.name.upper()
            # Group by prefix (e.g., CALC-xxx, VALIDATE-xxx)
            parts = name.split("-")
            if len(parts) >= 2:
                prefix = parts[0]
                if prefix not in prefix_groups:
                    prefix_groups[prefix] = []
                prefix_groups[prefix].append(para)

        # Only create service classes for groups with 3+ related paragraphs
        for prefix, paragraphs in prefix_groups.items():
            if len(paragraphs) >= 3:
                cls = JavaClass(
                    name=to_pascal_case(prefix) + "Service",
                    package_name=self.options.package_name + ".service",
                    comment=f"Service class for related operations: {prefix}-*",
                )

                for para in paragraphs:
                    method = JavaMethod(
                        name=to_camel_case(para.name),
                        body_statements=para.statements,
                        original_paragraph=para.name,
                        comment=f"Migrated from: {para.name}",
                    )
                    cls.methods.append(method)

                services.append(cls)

        return services
