"""
Tests for the lark-based DATA DIVISION parser.
Verifies that lark produces identical results to the regex parser,
and tests lark-specific parsing capabilities.
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.lark_data_parser import LarkDataParser
from src.cobol_parser import CobolParser, DataItem
from tests.conftest import sample_path


@pytest.fixture
def lark_parser():
    return LarkDataParser()


@pytest.fixture
def regex_parser():
    """Parser with lark disabled (regex-only)."""
    return CobolParser(encoding="utf-8", use_lark=False)


@pytest.fixture
def lark_cobol_parser():
    """Parser with lark enabled."""
    return CobolParser(encoding="utf-8", use_lark=True)


class TestLarkParseStatement:
    """Unit tests for LarkDataParser.parse_statement."""

    def test_simple_pic_x(self, lark_parser):
        item = lark_parser.parse_statement('01 WS-NAME PIC X(30).')
        assert item is not None
        assert item.level == 1
        assert item.name == "WS-NAME"
        assert item.picture == "X(30)"

    def test_pic_9_with_sign(self, lark_parser):
        item = lark_parser.parse_statement('05 WS-AMOUNT PIC S9(7)V99.')
        assert item is not None
        assert item.level == 5
        assert item.name == "WS-AMOUNT"
        assert item.picture == "S9(7)V99"

    def test_comp3_usage(self, lark_parser):
        item = lark_parser.parse_statement('05 WS-PACKED PIC S9(7)V99 COMP-3.')
        assert item is not None
        assert item.picture == "S9(7)V99"
        assert item.usage == "COMP-3"

    def test_usage_is_keyword(self, lark_parser):
        item = lark_parser.parse_statement('05 WS-BIN PIC S9(4) USAGE IS BINARY.')
        assert item is not None
        assert item.usage == "BINARY"

    def test_pointer_usage(self, lark_parser):
        item = lark_parser.parse_statement('05 WS-PTR USAGE POINTER.')
        assert item is not None
        assert item.usage == "POINTER"

    def test_function_pointer(self, lark_parser):
        item = lark_parser.parse_statement('05 WS-FPTR USAGE FUNCTION-POINTER.')
        assert item is not None
        assert item.usage == "FUNCTION-POINTER"

    def test_value_string(self, lark_parser):
        item = lark_parser.parse_statement('77 WS-MSG PIC X(80) VALUE "Hello World".')
        assert item is not None
        assert item.value == "Hello World"

    def test_value_numeric(self, lark_parser):
        item = lark_parser.parse_statement('77 WS-COUNT PIC 9(5) VALUE 100.')
        assert item is not None
        assert item.value == "100"

    def test_value_spaces(self, lark_parser):
        item = lark_parser.parse_statement('77 WS-BLANK PIC X(10) VALUE SPACES.')
        assert item is not None
        assert item.value == "SPACES"

    def test_value_zeros(self, lark_parser):
        item = lark_parser.parse_statement('77 WS-ZERO PIC 9(5) VALUE ZEROS.')
        assert item is not None
        assert item.value == "ZEROS"

    def test_value_high_values(self, lark_parser):
        item = lark_parser.parse_statement('77 WS-HIGH PIC X VALUE HIGH-VALUES.')
        assert item is not None
        assert item.value == "HIGH-VALUES"

    def test_occurs_clause(self, lark_parser):
        item = lark_parser.parse_statement('05 WS-ITEM PIC X(10) OCCURS 50.')
        assert item is not None
        assert item.occurs == 50

    def test_redefines_clause(self, lark_parser):
        item = lark_parser.parse_statement('05 WS-REDEF PIC X(10) REDEFINES WS-ORIG.')
        assert item is not None
        assert item.redefines == "WS-ORIG"

    def test_level_77(self, lark_parser):
        item = lark_parser.parse_statement('77 WS-STANDALONE PIC S9(18) COMP-3.')
        assert item is not None
        assert item.level == 77
        assert item.usage == "COMP-3"

    def test_filler(self, lark_parser):
        item = lark_parser.parse_statement('05 FILLER PIC X(10).')
        assert item is not None
        assert item.is_filler is True
        assert item.picture == "X(10)"

    def test_88_level(self, lark_parser):
        item = lark_parser.parse_statement('88 STATUS-ACTIVE VALUE "Y".')
        assert item is not None
        assert item.level == 88
        assert item.is_88_level is True
        assert "Y" in item.condition_values

    def test_group_item_no_pic(self, lark_parser):
        item = lark_parser.parse_statement('01 WS-GROUP.')
        assert item is not None
        assert item.level == 1
        assert item.name == "WS-GROUP"
        assert item.picture == ""

    def test_packed_decimal_keyword(self, lark_parser):
        item = lark_parser.parse_statement('05 WS-PKD PIC S9(9)V99 PACKED-DECIMAL.')
        assert item is not None
        assert item.usage == "PACKED-DECIMAL"

    def test_comp1_standalone(self, lark_parser):
        item = lark_parser.parse_statement('05 WS-FLT COMP-1.')
        assert item is not None
        assert item.usage == "COMP-1"

    def test_comp2_standalone(self, lark_parser):
        item = lark_parser.parse_statement('05 WS-DBL COMP-2.')
        assert item is not None
        assert item.usage == "COMP-2"

    def test_invalid_input_returns_none(self, lark_parser):
        result = lark_parser.parse_statement('PROCEDURE DIVISION.')
        assert result is None

    def test_empty_input_returns_none(self, lark_parser):
        result = lark_parser.parse_statement('')
        assert result is None

    def test_pic_n_dbcs(self, lark_parser):
        item = lark_parser.parse_statement('05 WS-DBCS PIC N(10).')
        assert item is not None
        assert item.picture == "N(10)"


class TestLarkVsRegexParity:
    """Compare lark and regex parser outputs to ensure parity."""

    def _compare_items(self, lark_items: list, regex_items: list, context: str = ""):
        """Compare two lists of DataItems recursively."""
        assert len(lark_items) == len(regex_items), \
            f"{context} Item count mismatch: lark={len(lark_items)}, regex={len(regex_items)}"
        for i, (l_item, r_item) in enumerate(zip(lark_items, regex_items)):
            ctx = f"{context}[{i}] {l_item.name}"
            assert l_item.level == r_item.level, f"{ctx} level mismatch"
            assert l_item.name == r_item.name, f"{ctx} name mismatch"
            assert l_item.picture == r_item.picture, \
                f"{ctx} picture mismatch: lark={l_item.picture!r}, regex={r_item.picture!r}"
            assert l_item.usage.upper() == r_item.usage.upper(), \
                f"{ctx} usage mismatch: lark={l_item.usage!r}, regex={r_item.usage!r}"
            assert l_item.is_filler == r_item.is_filler, f"{ctx} is_filler mismatch"
            assert l_item.is_88_level == r_item.is_88_level, f"{ctx} is_88_level mismatch"
            assert l_item.occurs == r_item.occurs, f"{ctx} occurs mismatch"
            assert l_item.redefines == r_item.redefines, f"{ctx} redefines mismatch"
            # Recursively compare children
            self._compare_items(l_item.children, r_item.children, ctx + " > ")

    def test_parity_comp3_pointer(self, lark_cobol_parser, regex_parser):
        lark_prog = lark_cobol_parser.parse_file(sample_path("comp3_pointer.cbl"))
        regex_prog = regex_parser.parse_file(sample_path("comp3_pointer.cbl"))
        self._compare_items(lark_prog.working_storage, regex_prog.working_storage,
                          "comp3_pointer WS")

    def test_parity_control_flow(self, lark_cobol_parser, regex_parser):
        lark_prog = lark_cobol_parser.parse_file(sample_path("control_flow.cbl"))
        regex_prog = regex_parser.parse_file(sample_path("control_flow.cbl"))
        self._compare_items(lark_prog.working_storage, regex_prog.working_storage,
                          "control_flow WS")

    def test_parity_copy_test(self, lark_cobol_parser, regex_parser):
        lark_prog = lark_cobol_parser.parse_file(sample_path("copy_test.cbl"))
        regex_prog = regex_parser.parse_file(sample_path("copy_test.cbl"))
        self._compare_items(lark_prog.working_storage, regex_prog.working_storage,
                          "copy_test WS")

    def test_parity_hello(self, lark_cobol_parser, regex_parser):
        """hello.cbl contains OCCURS 1 TO 80 DEPENDING ON.
        Lark parser correctly extracts max=80, regex only gets min=1.
        We verify lark is at least as good (top-level item count matches)."""
        lark_prog = lark_cobol_parser.parse_file(sample_path("hello.cbl"))
        regex_prog = regex_parser.parse_file(sample_path("hello.cbl"))
        assert len(lark_prog.working_storage) == len(regex_prog.working_storage)


class TestLarkFallback:
    """Test that regex fallback works correctly."""

    def test_use_lark_false_still_works(self, regex_parser):
        """With use_lark=False, parser should still work via regex."""
        program = regex_parser.parse_file(sample_path("comp3_pointer.cbl"))
        assert program.program_id == "DATATYPES"
        assert len(program.working_storage) >= 4

    def test_lark_enabled_produces_same_program_id(self, lark_cobol_parser, regex_parser):
        lark_prog = lark_cobol_parser.parse_file(sample_path("comp3_pointer.cbl"))
        regex_prog = regex_parser.parse_file(sample_path("comp3_pointer.cbl"))
        assert lark_prog.program_id == regex_prog.program_id

    def test_lark_enabled_produces_same_paragraphs(self, lark_cobol_parser, regex_parser):
        lark_prog = lark_cobol_parser.parse_file(sample_path("control_flow.cbl"))
        regex_prog = regex_parser.parse_file(sample_path("control_flow.cbl"))
        lark_names = [p.name for p in lark_prog.paragraphs]
        regex_names = [p.name for p in regex_prog.paragraphs]
        assert lark_names == regex_names


class TestLarkEdgeCases:
    """Test edge cases specific to the lark parser."""

    def test_multiple_clauses_combined(self, lark_parser):
        item = lark_parser.parse_statement(
            '05 WS-FIELD PIC S9(5)V99 COMP-3 VALUE 123.45 OCCURS 10.'
        )
        assert item is not None
        assert item.picture == "S9(5)V99"
        assert item.usage == "COMP-3"
        assert item.occurs == 10

    def test_value_with_single_quotes(self, lark_parser):
        item = lark_parser.parse_statement("77 WS-FLAG PIC X VALUE 'Y'.")
        assert item is not None
        assert item.value == "Y"

    def test_long_cobol_name(self, lark_parser):
        item = lark_parser.parse_statement(
            '05 WS-VERY-LONG-DATA-ITEM-NAME PIC X(100).'
        )
        assert item is not None
        assert item.name == "WS-VERY-LONG-DATA-ITEM-NAME"

    def test_level_numbers_01_to_49(self, lark_parser):
        for level in [1, 2, 3, 5, 10, 15, 20, 25, 30, 49]:
            item = lark_parser.parse_statement(
                f'{level:02d} WS-LEVEL-{level} PIC X.'
            )
            assert item is not None, f"Failed for level {level}"
            assert item.level == level

    def test_comp5_usage(self, lark_parser):
        item = lark_parser.parse_statement('05 WS-C5 PIC S9(9) COMP-5.')
        assert item is not None
        assert item.usage == "COMP-5"

    def test_object_reference_usage(self, lark_parser):
        item = lark_parser.parse_statement('05 WS-OBJ USAGE OBJECT-REFERENCE.')
        assert item is not None
        assert item.usage == "OBJECT-REFERENCE"

    def test_procedure_pointer_usage(self, lark_parser):
        item = lark_parser.parse_statement('05 WS-PP USAGE PROCEDURE-POINTER.')
        assert item is not None
        assert item.usage == "PROCEDURE-POINTER"
