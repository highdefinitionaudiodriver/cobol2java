"""
Tests for COPY statement handling.
"""
import pytest
from src.cobol_parser import CobolParser
from src.oop_transformer import OopTransformer
from tests.conftest import sample_path


class TestCopyStatementParsing:
    """Tests for COPY clause detection and recording."""

    def test_copy_members_detected_in_file(self, parser):
        program = parser.parse_file(sample_path("copy_test.cbl"))
        assert program.program_id == "COPYTEST"
        # COPY FILECTRL in ENVIRONMENT DIVISION
        assert "FILECTRL" in program.copy_members

    def test_copy_wscopybook_detected(self, parser):
        program = parser.parse_file(sample_path("copy_test.cbl"))
        assert "WSCOPYBOOK" in program.copy_members

    def test_copy_sqlca_detected(self, parser):
        program = parser.parse_file(sample_path("copy_test.cbl"))
        assert "SQLCA" in program.copy_members

    def test_copy_count(self, parser):
        program = parser.parse_file(sample_path("copy_test.cbl"))
        assert len(program.copy_members) >= 3

    def test_data_items_after_copy_parsed(self, parser):
        """Data items defined after COPY statements should still be parsed."""
        program = parser.parse_file(sample_path("copy_test.cbl"))
        ws_record = None
        for item in program.working_storage:
            if item.name == "WS-RECORD":
                ws_record = item
                break
        assert ws_record is not None
        assert len(ws_record.children) >= 3

    def test_88_levels_after_copy(self, parser):
        """88-level items in data following COPY should be parsed."""
        program = parser.parse_file(sample_path("copy_test.cbl"))
        ws_record = None
        for item in program.working_storage:
            if item.name == "WS-RECORD":
                ws_record = item
                break
        assert ws_record is not None

        status_field = None
        for child in ws_record.children:
            if child.name == "WS-STATUS":
                status_field = child
                break
        assert status_field is not None

        # Should have 88-level children
        children_88 = [c for c in status_field.children if c.is_88_level]
        assert len(children_88) >= 3

    def test_copy_in_procedure_skipped(self, parser):
        """COPY in PROCEDURE DIVISION should be skipped without error."""
        source = """\
       IDENTIFICATION DIVISION.
       PROGRAM-ID. PROCTEST.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 WS-VAR PIC X(10).
       PROCEDURE DIVISION.
       MAIN-PARA.
           COPY PROCLIB.
           DISPLAY WS-VAR.
           STOP RUN.
"""
        program = parser.parse_string(source)
        assert program.program_id == "PROCTEST"
        # Should parse without raising exceptions
        assert len(program.paragraphs) >= 1

    def test_enum_extraction_from_88_after_copy(self, parser, transformer):
        """88-level items should still produce enums even with COPY in the file."""
        program = parser.parse_file(sample_path("copy_test.cbl"))
        project = transformer.transform(program)

        # WS-STATUS has 3 x 88-levels => should create an enum
        enum_names = [e.name for e in project.enum_classes]
        assert any("Status" in name for name in enum_names), \
            f"Expected enum with 'Status' in name, got: {enum_names}"


class TestCopyInlineString:
    """Tests for COPY handling using inline string parsing."""

    def test_multiple_copy_in_working_storage(self, parser):
        source = """\
       IDENTIFICATION DIVISION.
       PROGRAM-ID. MULTICOPY.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       COPY COPYBOOK1.
       01 WS-FIELD1 PIC X(10).
       COPY COPYBOOK2.
       01 WS-FIELD2 PIC 9(5).
       COPY COPYBOOK3.
       PROCEDURE DIVISION.
       MAIN-PARA.
           DISPLAY WS-FIELD1.
           STOP RUN.
"""
        program = parser.parse_string(source)
        # Data items after COPY should be parsed
        field_names = [item.name for item in program.working_storage]
        assert "WS-FIELD1" in field_names
        assert "WS-FIELD2" in field_names

    def test_copy_does_not_break_paragraphs(self, parser):
        source = """\
       IDENTIFICATION DIVISION.
       PROGRAM-ID. COPYPARA.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       COPY WSBOOK.
       01 WS-A PIC X(5).
       PROCEDURE DIVISION.
       FIRST-PARA.
           MOVE "HELLO" TO WS-A.
       SECOND-PARA.
           DISPLAY WS-A.
           STOP RUN.
"""
        program = parser.parse_string(source)
        para_names = [p.name for p in program.paragraphs]
        assert "FIRST-PARA" in para_names
        assert "SECOND-PARA" in para_names
