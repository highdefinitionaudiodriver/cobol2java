"""
Java Code Generator
変換されたOOP構造からJavaソースコードを生成する
"""
import os
import re
from typing import List, Optional
from .cobol_parser import (
    Statement, StatementType, to_pascal_case, to_camel_case
)
from .oop_transformer import (
    JavaProject, JavaClass, JavaField, JavaMethod, TransformOptions
)
from .vendor_extensions import (
    parse_exec_block, generate_exec_sql_java,
    generate_exec_cics_java, generate_exec_dli_java,
    generate_gnucobol_call_java
)


class JavaCodeGenerator:
    def __init__(self, options: TransformOptions = None):
        self.options = options or TransformOptions()
        self.indent = "    "

    def generate_project(self, project: JavaProject, output_dir: str):
        os.makedirs(output_dir, exist_ok=True)

        # Generate main class
        if project.main_class:
            self._write_class(project.main_class, output_dir)

        # Generate data classes
        for cls in project.data_classes:
            self._write_class(cls, output_dir)

        # Generate enum classes
        for cls in project.enum_classes:
            self._write_class(cls, output_dir)

        # Generate file handler classes
        for cls in project.file_handler_classes:
            self._write_class(cls, output_dir)

        # Generate service classes
        for cls in project.service_classes:
            self._write_class(cls, output_dir)

    def _write_class(self, cls: JavaClass, output_dir: str):
        # Create package directory structure
        pkg_path = cls.package_name.replace(".", os.sep) if cls.package_name else ""
        class_dir = os.path.join(output_dir, pkg_path)
        os.makedirs(class_dir, exist_ok=True)

        filepath = os.path.join(class_dir, f"{cls.name}.java")
        code = self.generate_class(cls)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(code)

        return filepath

    def generate_class(self, cls: JavaClass) -> str:
        lines = []

        # Package declaration
        if cls.package_name:
            lines.append(f"package {cls.package_name};")
            lines.append("")

        # Imports
        imports = sorted(cls.imports)
        if imports:
            for imp in imports:
                lines.append(f"import {imp};")
            lines.append("")

        # Class Javadoc
        if self.options.generate_javadoc and cls.comment:
            lines.append("/**")
            lines.append(f" * {cls.comment}")
            lines.append(" */")

        if cls.is_enum:
            lines.extend(self._generate_enum(cls))
        elif cls.is_data_class:
            lines.extend(self._generate_data_class(cls))
        else:
            lines.extend(self._generate_regular_class(cls))

        return "\n".join(lines)

    def _generate_enum(self, cls: JavaClass) -> List[str]:
        lines = []
        lines.append(f"public enum {cls.name} {{")

        for i, val in enumerate(cls.enum_values):
            separator = "," if i < len(cls.enum_values) - 1 else ";"
            lines.append(f"{self.indent}{val}{separator}")

        lines.append("}")
        return lines

    def _generate_data_class(self, cls: JavaClass) -> List[str]:
        lines = []

        # Class declaration
        extends = f" extends {cls.extends}" if cls.extends else ""
        implements = f" implements {', '.join(cls.implements)}" if cls.implements else ""
        lines.append(f"public class {cls.name}{extends}{implements} {{")
        lines.append("")

        # Inner classes first (nested data types)
        for inner in cls.inner_classes:
            inner_lines = self._generate_data_class(inner)
            for il in inner_lines:
                lines.append(f"{self.indent}{il}")
            lines.append("")

        # Fields
        for field in cls.fields:
            lines.extend(self._generate_field(field, 1))
        lines.append("")

        # Default constructor
        lines.append(f"{self.indent}public {cls.name}() {{")
        for field in cls.fields:
            init = self._get_field_initializer(field)
            if init:
                lines.append(f"{self.indent}{self.indent}this.{field.name} = {init};")
        lines.append(f"{self.indent}}}")
        lines.append("")

        # Getters and Setters
        if self.options.generate_getters_setters:
            for field in cls.fields:
                lines.extend(self._generate_getter(field, 1))
                lines.append("")
                lines.extend(self._generate_setter(field, 1))
                lines.append("")

        # toString()
        if self.options.generate_toString:
            lines.extend(self._generate_toString(cls, 1))
            lines.append("")

        lines.append("}")
        return lines

    def _generate_regular_class(self, cls: JavaClass) -> List[str]:
        lines = []

        extends = f" extends {cls.extends}" if cls.extends else ""
        implements = f" implements {', '.join(cls.implements)}" if cls.implements else ""
        lines.append(f"public class {cls.name}{extends}{implements} {{")
        lines.append("")

        # Fields
        for field in cls.fields:
            lines.extend(self._generate_field(field, 1))
        lines.append("")

        # Scanner for ACCEPT statements
        has_accept = any(
            self._has_statement_type(m.body_statements, StatementType.ACCEPT)
            for m in cls.methods
        )
        if has_accept:
            lines.append(f"{self.indent}private final Scanner scanner = new Scanner(System.in);")
            lines.append("")

        # Constructor
        lines.append(f"{self.indent}public {cls.name}() {{")
        for field in cls.fields:
            init = self._get_field_initializer(field)
            if init:
                lines.append(f"{self.indent}{self.indent}this.{field.name} = {init};")
        lines.append(f"{self.indent}}}")
        lines.append("")

        # Methods
        for method in cls.methods:
            lines.extend(self._generate_method(method, 1))
            lines.append("")

        # Main method
        main_entry = next((m for m in cls.methods if m.is_main_entry), None)
        if main_entry:
            lines.append(f"{self.indent}public static void main(String[] args) {{")
            lines.append(f"{self.indent}{self.indent}{cls.name} program = new {cls.name}();")
            lines.append(f"{self.indent}{self.indent}program.{main_entry.name}();")
            lines.append(f"{self.indent}}}")
            lines.append("")

        # File handler methods (if this class has file handlers)
        for method in cls.methods:
            if not method.body_statements:
                # Generate stub for file handler methods
                pass

        lines.append("}")
        return lines

    def _generate_field(self, field: JavaField, depth: int) -> List[str]:
        lines = []
        indent = self.indent * depth

        if self.options.generate_javadoc and field.comment:
            lines.append(f"{indent}/** {field.comment} */")

        if field.original_cobol_name:
            lines.append(f"{indent}// COBOL: {field.original_cobol_name}" +
                         (f" PIC {field.original_picture}" if field.original_picture else ""))

        type_str = field.java_type
        if field.is_array:
            type_str = f"List<{self._box_type(field.java_type)}>"

        modifier = "static final" if field.is_constant else ""
        access_mod = f"{field.access} {modifier}".strip() if modifier else field.access

        if field.initial_value and not field.is_array:
            lines.append(f"{indent}{access_mod} {type_str} {field.name} = {field.initial_value};")
        elif field.is_array:
            lines.append(f"{indent}{access_mod} {type_str} {field.name} = new ArrayList<>();")
        else:
            lines.append(f"{indent}{access_mod} {type_str} {field.name};")

        return lines

    def _generate_getter(self, field: JavaField, depth: int) -> List[str]:
        indent = self.indent * depth
        type_str = f"List<{self._box_type(field.java_type)}>" if field.is_array else field.java_type
        getter_name = f"get{field.name[0].upper()}{field.name[1:]}"

        return [
            f"{indent}public {type_str} {getter_name}() {{",
            f"{indent}{self.indent}return this.{field.name};",
            f"{indent}}}",
        ]

    def _generate_setter(self, field: JavaField, depth: int) -> List[str]:
        indent = self.indent * depth
        type_str = f"List<{self._box_type(field.java_type)}>" if field.is_array else field.java_type
        setter_name = f"set{field.name[0].upper()}{field.name[1:]}"

        return [
            f"{indent}public void {setter_name}({type_str} {field.name}) {{",
            f"{indent}{self.indent}this.{field.name} = {field.name};",
            f"{indent}}}",
        ]

    def _generate_toString(self, cls: JavaClass, depth: int) -> List[str]:
        indent = self.indent * depth
        lines = [
            f"{indent}@Override",
            f"{indent}public String toString() {{",
            f'{indent}{self.indent}return "{cls.name}{{" +',
        ]

        for i, field in enumerate(cls.fields):
            prefix = '"' if i == 0 else '", '
            if field.java_type == "String":
                lines.append(f"""{indent}{self.indent}{self.indent}{prefix}{field.name}='" + {field.name} + '\\'' +""")
            else:
                lines.append(f'{indent}{self.indent}{self.indent}{prefix}{field.name}=" + {field.name} +')

        lines.append(f"""{indent}{self.indent}{self.indent}"}}'";""")
        lines.append(f"{indent}}}")

        return lines

    def _generate_method(self, method: JavaMethod, depth: int) -> List[str]:
        lines = []
        indent = self.indent * depth

        # Javadoc
        if self.options.generate_javadoc and method.comment:
            lines.append(f"{indent}/**")
            lines.append(f"{indent} * {method.comment}")
            lines.append(f"{indent} */")

        # Method signature
        params = ", ".join(f"{t} {n}" for t, n in method.parameters)
        lines.append(f"{indent}{method.access} {method.return_type} {method.name}({params}) {{")

        # Method body
        if method.body_statements:
            body_lines = self._generate_statements(method.body_statements, depth + 1)
            lines.extend(body_lines)
        else:
            lines.append(f"{indent}{self.indent}// TODO: Implement method body")

        lines.append(f"{indent}}}")
        return lines

    def _generate_statements(self, statements: List[Statement], depth: int) -> List[str]:
        lines = []
        indent = self.indent * depth

        for stmt in statements:
            generated = self._generate_statement(stmt, depth)
            lines.extend(generated)

        return lines

    def _generate_statement(self, stmt: Statement, depth: int) -> List[str]:
        indent = self.indent * depth
        lines = []

        if stmt.type == StatementType.MOVE:
            lines.extend(self._gen_move(stmt, indent))
        elif stmt.type == StatementType.ADD:
            lines.extend(self._gen_add(stmt, indent))
        elif stmt.type == StatementType.SUBTRACT:
            lines.extend(self._gen_subtract(stmt, indent))
        elif stmt.type == StatementType.MULTIPLY:
            lines.extend(self._gen_multiply(stmt, indent))
        elif stmt.type == StatementType.DIVIDE:
            lines.extend(self._gen_divide(stmt, indent))
        elif stmt.type == StatementType.COMPUTE:
            lines.extend(self._gen_compute(stmt, indent))
        elif stmt.type == StatementType.IF:
            lines.extend(self._gen_if(stmt, depth))
        elif stmt.type == StatementType.EVALUATE:
            lines.extend(self._gen_evaluate(stmt, depth))
        elif stmt.type == StatementType.PERFORM:
            lines.extend(self._gen_perform(stmt, indent))
        elif stmt.type == StatementType.DISPLAY:
            lines.extend(self._gen_display(stmt, indent))
        elif stmt.type == StatementType.ACCEPT:
            lines.extend(self._gen_accept(stmt, indent))
        elif stmt.type == StatementType.CALL:
            lines.extend(self._gen_call(stmt, indent))
        elif stmt.type == StatementType.OPEN:
            lines.extend(self._gen_open(stmt, indent))
        elif stmt.type == StatementType.CLOSE:
            lines.extend(self._gen_close(stmt, indent))
        elif stmt.type == StatementType.READ:
            lines.extend(self._gen_read(stmt, indent))
        elif stmt.type == StatementType.WRITE:
            lines.extend(self._gen_write(stmt, indent))
        elif stmt.type == StatementType.INITIALIZE:
            lines.extend(self._gen_initialize(stmt, indent))
        elif stmt.type == StatementType.STRING:
            lines.extend(self._gen_string_stmt(stmt, indent))
        elif stmt.type == StatementType.SET:
            lines.extend(self._gen_set(stmt, indent))
        elif stmt.type == StatementType.STOP_RUN:
            lines.append(f"{indent}System.exit(0);")
        elif stmt.type == StatementType.GOBACK:
            lines.append(f"{indent}return;")
        elif stmt.type == StatementType.EXIT:
            lines.append(f"{indent}return;")
        elif stmt.type == StatementType.CONTINUE:
            lines.append(f"{indent}// CONTINUE")
        elif stmt.type == StatementType.GO_TO:
            target = self._extract_after(stmt.raw_text, "GO TO")
            lines.append(f"{indent}// GO TO {target} - requires manual refactoring")
            lines.append(f"{indent}{to_camel_case(target)}();")
        elif stmt.type in (StatementType.EXEC_SQL, StatementType.EXEC_CICS,
                           StatementType.EXEC_DLI, StatementType.EXEC_OTHER):
            lines.extend(self._gen_exec(stmt, indent))
        elif stmt.type == StatementType.XML_GENERATE:
            lines.extend(self._gen_xml_generate(stmt, indent))
        elif stmt.type == StatementType.XML_PARSE:
            lines.extend(self._gen_xml_parse(stmt, indent))
        elif stmt.type == StatementType.JSON_GENERATE:
            lines.extend(self._gen_json_generate(stmt, indent))
        elif stmt.type == StatementType.JSON_PARSE:
            lines.extend(self._gen_json_parse(stmt, indent))
        elif stmt.type == StatementType.INVOKE:
            lines.extend(self._gen_invoke(stmt, indent))
        elif stmt.type == StatementType.ENTER:
            lines.extend(self._gen_enter(stmt, indent))
        else:
            lines.append(f"{indent}// TODO: {stmt.raw_text}")

        return lines

    def _gen_move(self, stmt: Statement, indent: str) -> List[str]:
        text = stmt.raw_text
        match = re.match(r'MOVE\s+(.*?)\s+TO\s+(.*)', text, re.IGNORECASE)
        if not match:
            return [f"{indent}// TODO: {text}"]

        source = match.group(1).strip()
        targets = [t.strip() for t in match.group(2).split() if t.strip()]

        source_java = self._convert_operand(source)
        lines = []
        for target in targets:
            target_java = to_camel_case(target)
            lines.append(f"{indent}{target_java} = {source_java};")
        return lines

    def _gen_add(self, stmt: Statement, indent: str) -> List[str]:
        text = stmt.raw_text

        # ADD a TO b GIVING c
        giving_match = re.match(r'ADD\s+(.*?)\s+TO\s+(.*?)\s+GIVING\s+(.*)', text, re.IGNORECASE)
        if giving_match:
            a = self._convert_operand(giving_match.group(1).strip())
            b = self._convert_operand(giving_match.group(2).strip())
            c = to_camel_case(giving_match.group(3).strip())
            return [f"{indent}{c} = {b} + {a};"]

        # ADD a TO b
        to_match = re.match(r'ADD\s+(.*?)\s+TO\s+(.*)', text, re.IGNORECASE)
        if to_match:
            a = self._convert_operand(to_match.group(1).strip())
            targets = [t.strip() for t in to_match.group(2).split() if t.strip()]
            return [f"{indent}{to_camel_case(t)} += {a};" for t in targets]

        return [f"{indent}// TODO: {text}"]

    def _gen_subtract(self, stmt: Statement, indent: str) -> List[str]:
        text = stmt.raw_text

        giving_match = re.match(r'SUBTRACT\s+(.*?)\s+FROM\s+(.*?)\s+GIVING\s+(.*)', text, re.IGNORECASE)
        if giving_match:
            a = self._convert_operand(giving_match.group(1).strip())
            b = self._convert_operand(giving_match.group(2).strip())
            c = to_camel_case(giving_match.group(3).strip())
            return [f"{indent}{c} = {b} - {a};"]

        from_match = re.match(r'SUBTRACT\s+(.*?)\s+FROM\s+(.*)', text, re.IGNORECASE)
        if from_match:
            a = self._convert_operand(from_match.group(1).strip())
            targets = [t.strip() for t in from_match.group(2).split() if t.strip()]
            return [f"{indent}{to_camel_case(t)} -= {a};" for t in targets]

        return [f"{indent}// TODO: {text}"]

    def _gen_multiply(self, stmt: Statement, indent: str) -> List[str]:
        text = stmt.raw_text

        giving_match = re.match(r'MULTIPLY\s+(.*?)\s+BY\s+(.*?)\s+GIVING\s+(.*)', text, re.IGNORECASE)
        if giving_match:
            a = self._convert_operand(giving_match.group(1).strip())
            b = self._convert_operand(giving_match.group(2).strip())
            c = to_camel_case(giving_match.group(3).strip())
            return [f"{indent}{c} = {a} * {b};"]

        by_match = re.match(r'MULTIPLY\s+(.*?)\s+BY\s+(.*)', text, re.IGNORECASE)
        if by_match:
            a = self._convert_operand(by_match.group(1).strip())
            b = to_camel_case(by_match.group(2).strip())
            return [f"{indent}{b} *= {a};"]

        return [f"{indent}// TODO: {text}"]

    def _gen_divide(self, stmt: Statement, indent: str) -> List[str]:
        text = stmt.raw_text

        rem_match = re.match(
            r'DIVIDE\s+(.*?)\s+(?:BY|INTO)\s+(.*?)\s+GIVING\s+(.*?)\s+REMAINDER\s+(.*)',
            text, re.IGNORECASE
        )
        if rem_match:
            a = self._convert_operand(rem_match.group(1).strip())
            b = self._convert_operand(rem_match.group(2).strip())
            c = to_camel_case(rem_match.group(3).strip())
            d = to_camel_case(rem_match.group(4).strip())
            return [
                f"{indent}{c} = {a} / {b};",
                f"{indent}{d} = {a} % {b};"
            ]

        giving_match = re.match(r'DIVIDE\s+(.*?)\s+(?:BY|INTO)\s+(.*?)\s+GIVING\s+(.*)', text, re.IGNORECASE)
        if giving_match:
            a = self._convert_operand(giving_match.group(1).strip())
            b = self._convert_operand(giving_match.group(2).strip())
            c = to_camel_case(giving_match.group(3).strip())
            return [f"{indent}{c} = {a} / {b};"]

        into_match = re.match(r'DIVIDE\s+(.*?)\s+INTO\s+(.*)', text, re.IGNORECASE)
        if into_match:
            a = self._convert_operand(into_match.group(1).strip())
            b = to_camel_case(into_match.group(2).strip())
            return [f"{indent}{b} /= {a};"]

        return [f"{indent}// TODO: {text}"]

    def _gen_compute(self, stmt: Statement, indent: str) -> List[str]:
        text = stmt.raw_text
        match = re.match(r'COMPUTE\s+(\S+)\s*=\s*(.*)', text, re.IGNORECASE)
        if match:
            target = to_camel_case(match.group(1).strip())
            expr = self._convert_expression(match.group(2).strip())
            return [f"{indent}{target} = {expr};"]
        return [f"{indent}// TODO: {text}"]

    def _gen_if(self, stmt: Statement, depth: int) -> List[str]:
        indent = self.indent * depth
        lines = []

        # Extract condition from raw text
        text = stmt.raw_text
        cond_match = re.match(r'IF\s+(.*)', text, re.IGNORECASE)
        condition = self._convert_condition(cond_match.group(1).strip()) if cond_match else "true"

        lines.append(f"{indent}if ({condition}) {{")

        # Then block
        for child in stmt.children:
            lines.extend(self._generate_statement(child, depth + 1))

        # Else block
        if stmt.else_children:
            lines.append(f"{indent}}} else {{")
            for child in stmt.else_children:
                lines.extend(self._generate_statement(child, depth + 1))

        lines.append(f"{indent}}}")
        return lines

    def _gen_evaluate(self, stmt: Statement, depth: int) -> List[str]:
        indent = self.indent * depth
        lines = []

        # Extract subject
        text = stmt.raw_text
        subj_match = re.match(r'EVALUATE\s+(.*)', text, re.IGNORECASE)
        subject = subj_match.group(1).strip() if subj_match else ""

        if subject.upper() == "TRUE":
            # EVALUATE TRUE -> chain of if/else-if
            for i, (when_val, when_stmts) in enumerate(stmt.when_blocks):
                prefix = "if" if i == 0 else "} else if"
                condition = self._convert_condition(when_val)
                if when_val.upper() == "OTHER":
                    lines.append(f"{indent}}} else {{")
                else:
                    lines.append(f"{indent}{prefix} ({condition}) {{")
                for ws in when_stmts:
                    lines.extend(self._generate_statement(ws, depth + 1))
            lines.append(f"{indent}}}")
        else:
            # EVALUATE var -> switch
            subject_java = to_camel_case(subject)
            lines.append(f"{indent}switch ({subject_java}) {{")

            for when_val, when_stmts in stmt.when_blocks:
                if when_val.upper() == "OTHER":
                    lines.append(f"{indent}{self.indent}default:")
                else:
                    case_val = self._convert_operand(when_val)
                    lines.append(f"{indent}{self.indent}case {case_val}:")
                for ws in when_stmts:
                    lines.extend(self._generate_statement(ws, depth + 2))
                lines.append(f"{indent}{self.indent}{self.indent}break;")

            lines.append(f"{indent}}}")

        return lines

    def _gen_perform(self, stmt: Statement, indent: str) -> List[str]:
        text = stmt.raw_text

        # PERFORM ... VARYING
        varying_match = re.match(
            r'PERFORM\s+(\S+)\s+VARYING\s+(\S+)\s+FROM\s+(\S+)\s+BY\s+(\S+)\s+UNTIL\s+(.*)',
            text, re.IGNORECASE
        )
        if varying_match:
            target = to_camel_case(varying_match.group(1))
            var = to_camel_case(varying_match.group(2))
            from_val = self._convert_operand(varying_match.group(3))
            by_val = self._convert_operand(varying_match.group(4))
            until_cond = self._convert_condition(varying_match.group(5).strip())
            return [
                f"{indent}for ({var} = {from_val}; !({until_cond}); {var} += {by_val}) {{",
                f"{indent}{self.indent}{target}();",
                f"{indent}}}",
            ]

        # PERFORM ... UNTIL
        until_match = re.match(r'PERFORM\s+(\S+)\s+UNTIL\s+(.*)', text, re.IGNORECASE)
        if until_match:
            target = to_camel_case(until_match.group(1))
            condition = self._convert_condition(until_match.group(2).strip())
            return [
                f"{indent}while (!({condition})) {{",
                f"{indent}{self.indent}{target}();",
                f"{indent}}}",
            ]

        # PERFORM ... TIMES
        times_match = re.match(r'PERFORM\s+(\S+)\s+(\S+)\s+TIMES', text, re.IGNORECASE)
        if times_match:
            target = to_camel_case(times_match.group(1))
            count = self._convert_operand(times_match.group(2))
            return [
                f"{indent}for (int i = 0; i < {count}; i++) {{",
                f"{indent}{self.indent}{target}();",
                f"{indent}}}",
            ]

        # PERFORM ... THRU
        thru_match = re.match(r'PERFORM\s+(\S+)\s+THRU\s+(\S+)', text, re.IGNORECASE)
        if thru_match:
            start = to_camel_case(thru_match.group(1))
            end = to_camel_case(thru_match.group(2))
            return [
                f"{indent}// PERFORM {thru_match.group(1)} THRU {thru_match.group(2)}",
                f"{indent}{start}();",
                f"{indent}// ... through ...",
                f"{indent}{end}();",
            ]

        # Simple PERFORM
        simple_match = re.match(r'PERFORM\s+(\S+)', text, re.IGNORECASE)
        if simple_match:
            target = to_camel_case(simple_match.group(1))
            return [f"{indent}{target}();"]

        return [f"{indent}// TODO: {text}"]

    def _gen_display(self, stmt: Statement, indent: str) -> List[str]:
        text = stmt.raw_text
        match = re.match(r'DISPLAY\s+(.*)', text, re.IGNORECASE)
        if match:
            content = match.group(1).strip()
            parts = self._split_display_args(content)
            java_parts = []
            for part in parts:
                java_parts.append(self._convert_operand(part.strip()))
            expr = " + ".join(java_parts) if java_parts else '""'
            return [f"{indent}System.out.println({expr});"]
        return [f"{indent}// TODO: {text}"]

    def _gen_accept(self, stmt: Statement, indent: str) -> List[str]:
        text = stmt.raw_text
        match = re.match(r'ACCEPT\s+(\S+)', text, re.IGNORECASE)
        if match:
            target = to_camel_case(match.group(1))
            return [f"{indent}{target} = scanner.nextLine();"]
        return [f"{indent}// TODO: {text}"]

    def _gen_call(self, stmt: Statement, indent: str) -> List[str]:
        text = stmt.raw_text
        match = re.match(r'CALL\s+["\'](\S+)["\']\s*(USING\s+(.*))?', text, re.IGNORECASE)
        if match:
            program_name = match.group(1)
            using = match.group(3)
            param_names = []
            if using:
                param_names = [to_camel_case(p.strip()) for p in using.split()
                               if p.strip().upper() not in ("BY", "REFERENCE", "CONTENT", "VALUE")]

            # Check for GnuCOBOL CBL_* system routines
            gnucobol_result = generate_gnucobol_call_java(program_name, param_names, indent)
            if gnucobol_result:
                return gnucobol_result

            program = to_pascal_case(program_name)
            method_name = to_camel_case(program_name)
            params = ", ".join(param_names)
            return [
                f"{indent}// CALL to external program: {program_name}",
                f"{indent}{program} {method_name}Instance = new {program}();",
                f"{indent}{method_name}Instance.execute({params});",
            ]
        return [f"{indent}// TODO: {text}"]

    def _gen_open(self, stmt: Statement, indent: str) -> List[str]:
        text = stmt.raw_text
        match = re.match(r'OPEN\s+(INPUT|OUTPUT|I-O|EXTEND)\s+(.*)', text, re.IGNORECASE)
        if match:
            mode = match.group(1).upper()
            files = [f.strip() for f in match.group(2).split() if f.strip()]
            lines = []
            for f in files:
                handler = to_camel_case(f) + "Handler"
                lines.append(f'{indent}{handler}.open("{mode}");')
            return lines
        return [f"{indent}// TODO: {text}"]

    def _gen_close(self, stmt: Statement, indent: str) -> List[str]:
        text = stmt.raw_text
        match = re.match(r'CLOSE\s+(.*)', text, re.IGNORECASE)
        if match:
            files = [f.strip() for f in match.group(1).split() if f.strip()]
            return [f"{indent}{to_camel_case(f)}Handler.close();" for f in files]
        return [f"{indent}// TODO: {text}"]

    def _gen_read(self, stmt: Statement, indent: str) -> List[str]:
        text = stmt.raw_text
        match = re.match(r'READ\s+(\S+)', text, re.IGNORECASE)
        if match:
            file_name = match.group(1)
            handler = to_camel_case(file_name) + "Handler"
            record_var = to_camel_case(file_name) + "Record"

            lines = [f"{indent}String {record_var} = {handler}.readRecord();"]

            # Check for AT END
            at_end_match = re.search(r'AT\s+END\s+(.*?)(?:NOT\s+AT\s+END|$)', text, re.IGNORECASE)
            if at_end_match:
                lines = [
                    f"{indent}String {record_var} = {handler}.readRecord();",
                    f'{indent}if ("{record_var}" == null) {{',
                    f"{indent}{self.indent}// AT END processing",
                    f"{indent}}}",
                ]

            return lines
        return [f"{indent}// TODO: {text}"]

    def _gen_write(self, stmt: Statement, indent: str) -> List[str]:
        text = stmt.raw_text
        match = re.match(r'WRITE\s+(\S+)', text, re.IGNORECASE)
        if match:
            record = match.group(1)
            handler = to_camel_case(record) + "Handler"
            return [f"{indent}{handler}.writeRecord({to_camel_case(record)}.toString());"]
        return [f"{indent}// TODO: {text}"]

    def _gen_initialize(self, stmt: Statement, indent: str) -> List[str]:
        text = stmt.raw_text
        match = re.match(r'INITIALIZE\s+(.*)', text, re.IGNORECASE)
        if match:
            targets = [t.strip() for t in match.group(1).split() if t.strip() and t.upper() not in ("REPLACING",)]
            lines = []
            for target in targets:
                var = to_camel_case(target)
                lines.append(f"{indent}{var} = new {to_pascal_case(target)}(); // INITIALIZE")
            return lines
        return [f"{indent}// TODO: {text}"]

    def _gen_string_stmt(self, stmt: Statement, indent: str) -> List[str]:
        text = stmt.raw_text
        into_match = re.search(r'INTO\s+(\S+)', text, re.IGNORECASE)
        if into_match:
            target = to_camel_case(into_match.group(1))
            return [
                f"{indent}// STRING concatenation",
                f"{indent}StringBuilder sb = new StringBuilder();",
                f"{indent}// TODO: Add string parts from COBOL STRING statement",
                f"{indent}{target} = sb.toString();",
            ]
        return [f"{indent}// TODO: {text}"]

    def _gen_set(self, stmt: Statement, indent: str) -> List[str]:
        text = stmt.raw_text

        # SET flag TO TRUE/FALSE
        bool_match = re.match(r'SET\s+(\S+)\s+TO\s+(TRUE|FALSE)', text, re.IGNORECASE)
        if bool_match:
            var = to_camel_case(bool_match.group(1))
            val = bool_match.group(2).lower()
            return [f"{indent}{var} = {val};"]

        # SET var UP/DOWN BY n
        updown_match = re.match(r'SET\s+(\S+)\s+(UP|DOWN)\s+BY\s+(\S+)', text, re.IGNORECASE)
        if updown_match:
            var = to_camel_case(updown_match.group(1))
            direction = updown_match.group(2).upper()
            amount = self._convert_operand(updown_match.group(3))
            op = "+=" if direction == "UP" else "-="
            return [f"{indent}{var} {op} {amount};"]

        # SET var TO value
        to_match = re.match(r'SET\s+(\S+)\s+TO\s+(.*)', text, re.IGNORECASE)
        if to_match:
            var = to_camel_case(to_match.group(1))
            val = self._convert_operand(to_match.group(2).strip())
            return [f"{indent}{var} = {val};"]

        return [f"{indent}// TODO: {text}"]

    def _gen_xml_generate(self, stmt: Statement, indent: str) -> List[str]:
        """Generate Java code for IBM XML GENERATE."""
        text = stmt.raw_text
        # XML GENERATE xml-document FROM data-item COUNT IN xml-count
        from_match = re.search(r'XML\s+GENERATE\s+(\S+)\s+FROM\s+(\S+)', text, re.IGNORECASE)
        if from_match:
            target = to_camel_case(from_match.group(1))
            source = to_camel_case(from_match.group(2))
            count_match = re.search(r'COUNT\s+IN\s+(\S+)', text, re.IGNORECASE)
            count_var = to_camel_case(count_match.group(1)) if count_match else "xmlLength"
            return [
                f"{indent}// IBM XML GENERATE",
                f"{indent}javax.xml.bind.JAXBContext jaxbCtx = javax.xml.bind.JAXBContext.newInstance({source}.getClass());",
                f"{indent}javax.xml.bind.Marshaller marshaller = jaxbCtx.createMarshaller();",
                f"{indent}java.io.StringWriter sw = new java.io.StringWriter();",
                f"{indent}marshaller.marshal({source}, sw);",
                f"{indent}{target} = sw.toString();",
                f"{indent}int {count_var} = {target}.length();",
            ]
        return [f"{indent}// TODO: XML GENERATE - {text[:80]}"]

    def _gen_xml_parse(self, stmt: Statement, indent: str) -> List[str]:
        """Generate Java code for IBM XML PARSE."""
        text = stmt.raw_text
        doc_match = re.search(r'XML\s+PARSE\s+(\S+)', text, re.IGNORECASE)
        if doc_match:
            source = to_camel_case(doc_match.group(1))
            proc_match = re.search(r'PROCESSING\s+PROCEDURE\s+(\S+)', text, re.IGNORECASE)
            proc = to_camel_case(proc_match.group(1)) if proc_match else "processXml"
            return [
                f"{indent}// IBM XML PARSE",
                f"{indent}javax.xml.parsers.DocumentBuilder db = javax.xml.parsers.DocumentBuilderFactory.newInstance().newDocumentBuilder();",
                f"{indent}org.w3c.dom.Document xmlDoc = db.parse(new java.io.ByteArrayInputStream({source}.getBytes()));",
                f"{indent}{proc}(xmlDoc);",
            ]
        return [f"{indent}// TODO: XML PARSE - {text[:80]}"]

    def _gen_json_generate(self, stmt: Statement, indent: str) -> List[str]:
        """Generate Java code for IBM JSON GENERATE."""
        text = stmt.raw_text
        from_match = re.search(r'JSON\s+GENERATE\s+(\S+)\s+FROM\s+(\S+)', text, re.IGNORECASE)
        if from_match:
            target = to_camel_case(from_match.group(1))
            source = to_camel_case(from_match.group(2))
            return [
                f"{indent}// IBM JSON GENERATE",
                f"{indent}com.fasterxml.jackson.databind.ObjectMapper mapper = new com.fasterxml.jackson.databind.ObjectMapper();",
                f"{indent}{target} = mapper.writeValueAsString({source});",
            ]
        return [f"{indent}// TODO: JSON GENERATE - {text[:80]}"]

    def _gen_json_parse(self, stmt: Statement, indent: str) -> List[str]:
        """Generate Java code for IBM JSON PARSE."""
        text = stmt.raw_text
        parse_match = re.search(r'JSON\s+PARSE\s+(\S+)', text, re.IGNORECASE)
        if parse_match:
            source = to_camel_case(parse_match.group(1))
            into_match = re.search(r'INTO\s+(\S+)', text, re.IGNORECASE)
            target = to_camel_case(into_match.group(1)) if into_match else "jsonResult"
            return [
                f"{indent}// IBM JSON PARSE",
                f"{indent}com.fasterxml.jackson.databind.ObjectMapper mapper = new com.fasterxml.jackson.databind.ObjectMapper();",
                f"{indent}{target} = mapper.readValue({source}, {to_pascal_case(target)}.class);",
            ]
        return [f"{indent}// TODO: JSON PARSE - {text[:80]}"]

    def _gen_invoke(self, stmt: Statement, indent: str) -> List[str]:
        """Generate Java code for OO COBOL INVOKE (Hitachi/Micro Focus)."""
        text = stmt.raw_text
        # INVOKE object-name "method-name" USING arg1 arg2 RETURNING result
        match = re.match(
            r'INVOKE\s+(\S+)\s+["\'](\S+)["\']\s*(.*)',
            text, re.IGNORECASE
        )
        if match:
            obj = to_camel_case(match.group(1))
            method = to_camel_case(match.group(2))
            rest = match.group(3)
            # Extract parameters
            params = ""
            using_match = re.search(r'USING\s+(.*?)(?:RETURNING|$)', rest, re.IGNORECASE)
            if using_match:
                args = [to_camel_case(a.strip()) for a in using_match.group(1).split()
                        if a.strip().upper() not in ("BY", "REFERENCE", "CONTENT", "VALUE")]
                params = ", ".join(args)
            # Return value
            ret_match = re.search(r'RETURNING\s+(\S+)', rest, re.IGNORECASE)
            if ret_match:
                ret_var = to_camel_case(ret_match.group(1))
                return [f"{indent}{ret_var} = {obj}.{method}({params});"]
            return [f"{indent}{obj}.{method}({params});"]
        # INVOKE SELF / INVOKE SUPER
        self_match = re.match(r'INVOKE\s+(SELF|SUPER)\s+["\'](\S+)["\']', text, re.IGNORECASE)
        if self_match:
            target = "this" if self_match.group(1).upper() == "SELF" else "super"
            method = to_camel_case(self_match.group(2))
            return [f"{indent}{target}.{method}();"]
        return [f"{indent}// TODO: INVOKE - {text[:80]}"]

    def _gen_enter(self, stmt: Statement, indent: str) -> List[str]:
        """Generate Java code for HP/Tandem ENTER TAL or other ENTER statements."""
        text = stmt.raw_text
        return [
            f"{indent}// ENTER statement (vendor-specific mixed-language call)",
            f"{indent}// Original: {text[:100]}",
            f"{indent}// TODO: Convert inline TAL/assembler to Java native method call",
        ]

    def _gen_exec(self, stmt: Statement, indent: str) -> List[str]:
        """Generate Java code for EXEC SQL/CICS/DLI blocks using vendor_extensions."""
        raw = stmt.raw_text
        # Remove trailing period if present
        if raw.endswith("."):
            raw = raw[:-1].strip()
        block = parse_exec_block(raw)
        if not block:
            return [f"{indent}// TODO: EXEC block - {raw[:80]}"]

        if stmt.type == StatementType.EXEC_SQL:
            return generate_exec_sql_java(block, indent)
        elif stmt.type == StatementType.EXEC_CICS:
            return generate_exec_cics_java(block, indent)
        elif stmt.type == StatementType.EXEC_DLI:
            return generate_exec_dli_java(block, indent)
        else:
            return [
                f"{indent}// EXEC {block.exec_type} {block.command}",
                f"{indent}// TODO: Manual conversion required",
                f"{indent}// {raw[:100]}",
            ]

    # --- Helper methods ---

    def _convert_operand(self, cobol_operand: str) -> str:
        operand = cobol_operand.strip().rstrip(".")
        upper = operand.upper()

        # Special values
        if upper in ("SPACES", "SPACE"):
            return '""'
        if upper in ("ZEROS", "ZEROES", "ZERO"):
            return "0"
        if upper in ("HIGH-VALUES", "HIGH-VALUE"):
            return "0xFF"
        if upper in ("LOW-VALUES", "LOW-VALUE"):
            return "0x00"
        if upper == "TRUE":
            return "true"
        if upper == "FALSE":
            return "false"

        # String literal
        if (operand.startswith('"') and operand.endswith('"')) or \
           (operand.startswith("'") and operand.endswith("'")):
            return f'"{operand[1:-1]}"'

        # Numeric literal
        if re.match(r'^[+-]?\d+\.?\d*$', operand):
            return operand

        # COBOL variable name -> Java name
        if re.match(r'^[A-Za-z0-9-]+$', operand):
            return to_camel_case(operand)

        # Qualified name (e.g., FIELD OF RECORD)
        of_match = re.match(r'(\S+)\s+OF\s+(\S+)', operand, re.IGNORECASE)
        if of_match:
            field = to_camel_case(of_match.group(1))
            parent = to_camel_case(of_match.group(2))
            return f"{parent}.{field}"

        # Subscripted (e.g., ITEM(1))
        sub_match = re.match(r'(\S+)\s*\(\s*(\S+)\s*\)', operand)
        if sub_match:
            var = to_camel_case(sub_match.group(1))
            idx = self._convert_operand(sub_match.group(2))
            return f"{var}.get({idx} - 1)"

        return to_camel_case(operand)

    def _convert_condition(self, cobol_condition: str) -> str:
        cond = cobol_condition.strip().rstrip(".")

        # First, convert COBOL identifiers (words with hyphens) to camelCase
        # This must happen before operator replacement to avoid hyphen confusion
        def replace_cobol_id(m):
            name = m.group(0)
            upper = name.upper()
            # Preserve COBOL keywords that will be replaced later
            keywords = {"NOT", "AND", "OR", "IS", "EQUAL", "GREATER", "LESS", "THAN",
                        "NUMERIC", "ALPHABETIC", "SPACES", "ZEROS", "ZEROES"}
            if upper in keywords:
                return name
            return to_camel_case(name)

        cond = re.sub(r'[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+', replace_cobol_id, cond, flags=re.IGNORECASE)

        # NOT condition (but not "NOT EQUAL", "NOT AT END" etc.)
        # Handle standalone NOT at the beginning
        not_start = re.match(r'^NOT\s+(?!EQUAL|AT\s+END|ON)', cond, re.IGNORECASE)
        if not_start:
            inner = self._convert_condition(cond[not_start.end():])
            return f"!({inner})"

        # AND / OR
        cond = re.sub(r'\bAND\b', '&&', cond, flags=re.IGNORECASE)
        cond = re.sub(r'\bOR\b', '||', cond, flags=re.IGNORECASE)

        # Comparison operators (order matters - longer patterns first)
        cond = re.sub(r'\bIS\s+NOT\s+EQUAL\s+TO\b', '!=', cond, flags=re.IGNORECASE)
        cond = re.sub(r'\bIS\s+GREATER\s+THAN\s+OR\s+EQUAL\s+TO\b', '>=', cond, flags=re.IGNORECASE)
        cond = re.sub(r'\bIS\s+LESS\s+THAN\s+OR\s+EQUAL\s+TO\b', '<=', cond, flags=re.IGNORECASE)
        cond = re.sub(r'\bGREATER\s+THAN\s+OR\s+EQUAL\b', '>=', cond, flags=re.IGNORECASE)
        cond = re.sub(r'\bLESS\s+THAN\s+OR\s+EQUAL\b', '<=', cond, flags=re.IGNORECASE)
        cond = re.sub(r'\bIS\s+GREATER\s+THAN\b', '>', cond, flags=re.IGNORECASE)
        cond = re.sub(r'\bIS\s+LESS\s+THAN\b', '<', cond, flags=re.IGNORECASE)
        cond = re.sub(r'\bGREATER\s+THAN\b', '>', cond, flags=re.IGNORECASE)
        cond = re.sub(r'\bLESS\s+THAN\b', '<', cond, flags=re.IGNORECASE)
        cond = re.sub(r'\bNOT\s+EQUAL\s+TO\b', '!=', cond, flags=re.IGNORECASE)
        cond = re.sub(r'\bNOT\s+EQUAL\b', '!=', cond, flags=re.IGNORECASE)
        cond = re.sub(r'\bIS\s+EQUAL\s+TO\b', '==', cond, flags=re.IGNORECASE)
        cond = re.sub(r'\bEQUAL\s+TO\b', '==', cond, flags=re.IGNORECASE)
        cond = re.sub(r'\bEQUAL\b', '==', cond, flags=re.IGNORECASE)
        cond = re.sub(r'\bIS\s+NOT\b', '!=', cond, flags=re.IGNORECASE)

        # NUMERIC / ALPHABETIC checks
        cond = re.sub(r'(\S+)\s+IS\s+NUMERIC', r'\1 != null', cond, flags=re.IGNORECASE)
        cond = re.sub(r'(\S+)\s+IS\s+ALPHABETIC', r'\1 != null', cond, flags=re.IGNORECASE)

        # Convert special values
        cond = re.sub(r'\bSPACES?\b', '""', cond, flags=re.IGNORECASE)
        cond = re.sub(r'\bZERO(?:S|ES)?\b', '0', cond, flags=re.IGNORECASE)

        # Convert any remaining standalone COBOL-style uppercase words
        def replace_remaining(m):
            word = m.group(0)
            if word in ("&&", "||", "==", "!=", ">=", "<=", ">", "<", "true", "false", "null", "!"):
                return word
            if re.match(r'^[+-]?\d+\.?\d*$', word):
                return word
            if word.startswith('"') or word.startswith("'"):
                return word
            # Single COBOL word without hyphens (e.g., STATUS, EOF)
            if re.match(r'^[A-Z][A-Z0-9]+$', word):
                return to_camel_case(word)
            return word

        cond = re.sub(r'[A-Z][A-Z0-9]{2,}', replace_remaining, cond)

        return cond

    def _convert_expression(self, cobol_expr: str) -> str:
        expr = cobol_expr.strip().rstrip(".")

        # Replace COBOL operators
        expr = re.sub(r'\*\*', 'Math.pow(', expr)

        # First convert COBOL variable names (identifiers with hyphens) to camelCase
        # This must happen before splitting by operators
        def replace_cobol_id(m):
            name = m.group(0)
            # Skip numeric literals
            if re.match(r'^[+-]?\d+\.?\d*$', name):
                return name
            return to_camel_case(name)

        expr = re.sub(r'[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+', replace_cobol_id, expr, flags=re.IGNORECASE)

        return expr

    def _split_display_args(self, text: str) -> List[str]:
        parts = []
        current = ""
        in_quote = False
        quote_char = ""

        for ch in text:
            if ch in ('"', "'") and not in_quote:
                in_quote = True
                quote_char = ch
                current += ch
            elif ch == quote_char and in_quote:
                in_quote = False
                current += ch
                parts.append(current.strip())
                current = ""
            elif in_quote:
                current += ch
            elif ch == " " and not in_quote:
                if current.strip():
                    parts.append(current.strip())
                current = ""
            else:
                current += ch

        if current.strip():
            parts.append(current.strip())

        return parts

    def _extract_after(self, text: str, keyword: str) -> str:
        match = re.search(keyword + r'\s+(.*)', text, re.IGNORECASE)
        return match.group(1).strip() if match else ""

    def _box_type(self, java_type: str) -> str:
        box_map = {
            "int": "Integer",
            "long": "Long",
            "double": "Double",
            "float": "Float",
            "boolean": "Boolean",
            "char": "Character",
        }
        return box_map.get(java_type, java_type)

    def _get_field_initializer(self, field: JavaField) -> Optional[str]:
        if field.initial_value:
            return field.initial_value
        if field.is_array:
            return "new ArrayList<>()"
        # Default initialization
        defaults = {
            "int": "0",
            "long": "0L",
            "double": "0.0",
            "float": "0.0f",
            "boolean": "false",
            "String": '""',
            "BigDecimal": "BigDecimal.ZERO",
        }
        return defaults.get(field.java_type)

    def _has_statement_type(self, stmts: List[Statement], stmt_type: StatementType) -> bool:
        for s in stmts:
            if s.type == stmt_type:
                return True
            if self._has_statement_type(s.children, stmt_type):
                return True
            if self._has_statement_type(s.else_children, stmt_type):
                return True
        return False
