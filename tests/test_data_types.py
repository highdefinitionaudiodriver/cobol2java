"""
Tests for COMP-3 (packed decimal), POINTER, and COBOL-specific data types.
"""
import pytest
from src.cobol_parser import CobolParser, pic_to_java_type
from src.oop_transformer import OopTransformer, TransformOptions
from tests.conftest import sample_path


class TestPicToJavaType:
    """Unit tests for pic_to_java_type mapping."""

    # --- COMP-3 / PACKED-DECIMAL ---

    def test_comp3_integer_maps_to_bigdecimal(self):
        result = pic_to_java_type("S9(7)", "COMP-3")
        assert result == "java.math.BigDecimal"

    def test_comp3_decimal_maps_to_bigdecimal(self):
        result = pic_to_java_type("S9(7)V99", "COMP-3")
        assert result == "java.math.BigDecimal"

    def test_comp3_unsigned_maps_to_bigdecimal(self):
        result = pic_to_java_type("9(5)", "COMP-3")
        assert result == "java.math.BigDecimal"

    def test_packed_decimal_maps_to_bigdecimal(self):
        result = pic_to_java_type("S9(9)V99", "PACKED-DECIMAL")
        assert result == "java.math.BigDecimal"

    def test_comp3_large_precision(self):
        result = pic_to_java_type("S9(18)V9(4)", "COMP-3")
        assert result == "java.math.BigDecimal"

    # --- COMP / BINARY ---

    def test_comp_small_maps_to_int(self):
        result = pic_to_java_type("S9(4)", "BINARY")
        assert result == "int"

    def test_comp_large_maps_to_long(self):
        result = pic_to_java_type("S9(18)", "COMP")
        assert result == "long"

    def test_comp_no_pic_maps_to_int(self):
        result = pic_to_java_type("", "COMP")
        assert result == "int"

    # --- COMP-1 / COMP-2 ---

    def test_comp1_maps_to_float(self):
        result = pic_to_java_type("", "COMP-1")
        assert result == "float"

    def test_comp2_maps_to_double(self):
        result = pic_to_java_type("", "COMP-2")
        assert result == "double"

    # --- COMP-5 / vendor-specific binary ---

    def test_comp5_maps_to_int(self):
        result = pic_to_java_type("", "COMP-5")
        assert result == "int"

    def test_binary_long_maps_to_int(self):
        result = pic_to_java_type("", "BINARY-LONG")
        assert result == "int"

    def test_binary_short_maps_to_short(self):
        result = pic_to_java_type("", "BINARY-SHORT")
        assert result == "short"

    def test_binary_double_maps_to_long(self):
        result = pic_to_java_type("", "BINARY-DOUBLE")
        assert result == "long"

    def test_binary_char_maps_to_byte(self):
        result = pic_to_java_type("", "BINARY-CHAR")
        assert result == "byte"

    # --- POINTER types ---

    def test_pointer_maps_to_long(self):
        result = pic_to_java_type("", "POINTER")
        assert result == "long"

    def test_function_pointer_maps_to_long(self):
        result = pic_to_java_type("", "FUNCTION-POINTER")
        assert result == "long"

    def test_procedure_pointer_maps_to_long(self):
        result = pic_to_java_type("", "PROCEDURE-POINTER")
        assert result == "long"

    # --- OBJECT REFERENCE ---

    def test_object_reference_maps_to_object(self):
        result = pic_to_java_type("", "OBJECT-REFERENCE")
        assert result == "Object"

    # --- FLOAT types ---

    def test_float_short_maps_to_float(self):
        result = pic_to_java_type("", "FLOAT-SHORT")
        assert result == "float"

    def test_float_long_maps_to_double(self):
        result = pic_to_java_type("", "FLOAT-LONG")
        assert result == "double"

    # --- NATIONAL / DBCS ---

    def test_pic_n_maps_to_string(self):
        result = pic_to_java_type("N(10)", "")
        assert result == "String"

    def test_display1_maps_to_string(self):
        result = pic_to_java_type("", "DISPLAY-1")
        assert result == "String"

    def test_national_maps_to_string(self):
        result = pic_to_java_type("", "NATIONAL")
        assert result == "String"

    # --- Standard PIC types ---

    def test_pic_x_maps_to_string(self):
        result = pic_to_java_type("X(30)", "")
        assert result == "String"

    def test_pic_9_small_maps_to_int(self):
        result = pic_to_java_type("9(5)", "")
        assert result == "int"

    def test_pic_9_large_maps_to_long(self):
        result = pic_to_java_type("9(15)", "")
        assert result == "long"

    def test_pic_9v9_maps_to_bigdecimal(self):
        result = pic_to_java_type("9(5)V99", "")
        assert result == "java.math.BigDecimal"

    def test_pic_s9_maps_to_int(self):
        result = pic_to_java_type("S9(4)", "")
        assert result == "int"


class TestDataTypeParsing:
    """Integration tests: parse COBOL with special data types and verify."""

    def test_parse_comp3_pointer_file(self, parser):
        program = parser.parse_file(sample_path("comp3_pointer.cbl"))
        assert program.program_id == "DATATYPES"

    def test_comp3_fields_detected(self, parser):
        program = parser.parse_file(sample_path("comp3_pointer.cbl"))
        packed_group = None
        for item in program.working_storage:
            if item.name == "WS-PACKED-FIELDS":
                packed_group = item
                break
        assert packed_group is not None
        assert len(packed_group.children) >= 4

        amount = packed_group.children[0]
        assert amount.name == "WS-AMOUNT"
        assert "COMP-3" in amount.usage.upper()
        assert amount.java_type == "java.math.BigDecimal"

    def test_pointer_fields_detected(self, parser):
        program = parser.parse_file(sample_path("comp3_pointer.cbl"))
        ptr_group = None
        for item in program.working_storage:
            if item.name == "WS-POINTER-FIELDS":
                ptr_group = item
                break
        assert ptr_group is not None

        ptr_addr = ptr_group.children[0]
        assert ptr_addr.name == "WS-PTR-ADDR"
        assert ptr_addr.java_type == "long"

    def test_comp1_comp2_fields(self, parser):
        program = parser.parse_file(sample_path("comp3_pointer.cbl"))
        binary_group = None
        for item in program.working_storage:
            if item.name == "WS-BINARY-FIELDS":
                binary_group = item
                break
        assert binary_group is not None

        # Find COMP-1 and COMP-2 fields
        field_types = {child.name: child.java_type for child in binary_group.children}
        assert field_types.get("WS-FLOAT-SHORT") == "float"
        assert field_types.get("WS-FLOAT-LONG") == "double"

    def test_standalone_comp3_level77(self, parser):
        program = parser.parse_file(sample_path("comp3_pointer.cbl"))
        standalone = None
        for item in program.working_storage:
            if item.name == "WS-STANDALONE":
                standalone = item
                break
        assert standalone is not None
        assert standalone.level == 77
        assert standalone.java_type == "java.math.BigDecimal"

    def test_transform_comp3_to_bigdecimal_fields(self, parser, transformer):
        program = parser.parse_file(sample_path("comp3_pointer.cbl"))
        project = transformer.transform(program)

        assert project.main_class is not None
        # Data classes should include WS-PACKED-FIELDS group
        packed_class = None
        for dc in project.data_classes:
            if "Packed" in dc.name:
                packed_class = dc
                break
        assert packed_class is not None
        # All COMP-3 fields should be BigDecimal
        for f in packed_class.fields:
            assert f.java_type == "BigDecimal", f"Expected BigDecimal for {f.name}, got {f.java_type}"

    def test_transform_pointer_to_long_fields(self, parser, transformer):
        program = parser.parse_file(sample_path("comp3_pointer.cbl"))
        project = transformer.transform(program)

        ptr_class = None
        for dc in project.data_classes:
            if "Pointer" in dc.name:
                ptr_class = dc
                break
        assert ptr_class is not None
        for f in ptr_class.fields:
            assert f.java_type in ("long", "Object"), f"Unexpected type {f.java_type} for {f.name}"

    def test_generate_java_output(self, parser, transformer, generator, output_dir):
        program = parser.parse_file(sample_path("comp3_pointer.cbl"))
        project = transformer.transform(program)
        generator.generate_project(project, output_dir)

        # Verify at least one .java file was generated
        java_files = []
        for root, dirs, files in __import__("os").walk(output_dir):
            for f in files:
                if f.endswith(".java"):
                    java_files.append(__import__("os").path.join(root, f))
        assert len(java_files) > 0, "No Java files generated"

        # Check that BigDecimal import appears in at least one file
        found_bigdecimal = False
        for jf in java_files:
            with open(jf, "r") as fh:
                content = fh.read()
                if "BigDecimal" in content:
                    found_bigdecimal = True
                    break
        assert found_bigdecimal, "BigDecimal not found in generated Java files"
