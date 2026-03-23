"""
Tests for the structured PROCEDURE DIVISION parser.
Tests StatementClassifier, BlockParser, and ProcedureDivisionParser.
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.cobol_parser import CobolParser, StatementType
from src.lark_procedure_parser import (
    StatementClassifier, BlockParser, ProcedureDivisionParser,
)
from tests.conftest import sample_path


@pytest.fixture
def classifier():
    return StatementClassifier()


@pytest.fixture
def block_parser(classifier):
    return BlockParser(classifier)


@pytest.fixture
def lark_parser():
    return CobolParser(encoding="utf-8", use_lark=True)


@pytest.fixture
def legacy_parser():
    return CobolParser(encoding="utf-8", use_lark=False)


class TestStatementClassifier:
    """Tests for declarative verb registry classification."""

    def test_move(self, classifier):
        stmt = classifier.classify('MOVE "HELLO" TO WS-NAME')
        assert stmt.type == StatementType.MOVE

    def test_add(self, classifier):
        stmt = classifier.classify('ADD 1 TO WS-COUNT')
        assert stmt.type == StatementType.ADD

    def test_subtract(self, classifier):
        stmt = classifier.classify('SUBTRACT WS-A FROM WS-B')
        assert stmt.type == StatementType.SUBTRACT

    def test_multiply(self, classifier):
        stmt = classifier.classify('MULTIPLY WS-A BY WS-B GIVING WS-C')
        assert stmt.type == StatementType.MULTIPLY

    def test_divide(self, classifier):
        stmt = classifier.classify('DIVIDE WS-A INTO WS-B')
        assert stmt.type == StatementType.DIVIDE

    def test_compute(self, classifier):
        stmt = classifier.classify('COMPUTE WS-RESULT = WS-A * WS-B')
        assert stmt.type == StatementType.COMPUTE

    def test_if(self, classifier):
        stmt = classifier.classify('IF WS-A > 10')
        assert stmt.type == StatementType.IF

    def test_evaluate(self, classifier):
        stmt = classifier.classify('EVALUATE TRUE')
        assert stmt.type == StatementType.EVALUATE

    def test_perform(self, classifier):
        stmt = classifier.classify('PERFORM 100-INIT')
        assert stmt.type == StatementType.PERFORM

    def test_display(self, classifier):
        stmt = classifier.classify('DISPLAY "HELLO"')
        assert stmt.type == StatementType.DISPLAY

    def test_accept(self, classifier):
        stmt = classifier.classify('ACCEPT WS-INPUT')
        assert stmt.type == StatementType.ACCEPT

    def test_call(self, classifier):
        stmt = classifier.classify('CALL "SUBPROG" USING WS-PARAM')
        assert stmt.type == StatementType.CALL

    def test_set(self, classifier):
        stmt = classifier.classify('SET WS-FLAG TO TRUE')
        assert stmt.type == StatementType.SET

    def test_initialize(self, classifier):
        stmt = classifier.classify('INITIALIZE WS-RECORD')
        assert stmt.type == StatementType.INITIALIZE

    def test_exit(self, classifier):
        stmt = classifier.classify('EXIT')
        assert stmt.type == StatementType.EXIT

    def test_goback(self, classifier):
        stmt = classifier.classify('GOBACK')
        assert stmt.type == StatementType.GOBACK

    # Compound verbs
    def test_stop_run(self, classifier):
        stmt = classifier.classify('STOP RUN')
        assert stmt.type == StatementType.STOP_RUN

    def test_go_to(self, classifier):
        stmt = classifier.classify('GO TO PARA-EXIT')
        assert stmt.type == StatementType.GO_TO

    def test_xml_generate(self, classifier):
        stmt = classifier.classify('XML GENERATE WS-XML FROM WS-DATA')
        assert stmt.type == StatementType.XML_GENERATE

    def test_xml_parse(self, classifier):
        stmt = classifier.classify('XML PARSE WS-XML')
        assert stmt.type == StatementType.XML_PARSE

    def test_json_generate(self, classifier):
        stmt = classifier.classify('JSON GENERATE WS-JSON FROM WS-DATA')
        assert stmt.type == StatementType.JSON_GENERATE

    def test_json_parse(self, classifier):
        stmt = classifier.classify('JSON PARSE WS-JSON')
        assert stmt.type == StatementType.JSON_PARSE

    # EXEC blocks
    def test_exec_sql(self, classifier):
        stmt = classifier.classify('EXEC SQL SELECT * FROM TABLE END-EXEC')
        assert stmt.type == StatementType.EXEC_SQL

    def test_exec_cics(self, classifier):
        stmt = classifier.classify('EXEC CICS SEND MAP("MAP1") END-EXEC')
        assert stmt.type == StatementType.EXEC_CICS

    def test_exec_dli(self, classifier):
        stmt = classifier.classify('EXEC DLI GU USING PCB(1) END-EXEC')
        assert stmt.type == StatementType.EXEC_DLI

    def test_exec_other(self, classifier):
        stmt = classifier.classify('EXEC UNKNOWN SOMETHING END-EXEC')
        assert stmt.type == StatementType.EXEC_OTHER

    # Vendor-specific
    def test_invoke(self, classifier):
        stmt = classifier.classify('INVOKE OBJ-REF "methodName"')
        assert stmt.type == StatementType.INVOKE

    def test_enter(self, classifier):
        stmt = classifier.classify('ENTER TAL "procname"')
        assert stmt.type == StatementType.ENTER

    # Block terminators should return None
    def test_end_if_returns_none(self, classifier):
        assert classifier.classify('END-IF') is None

    def test_end_evaluate_returns_none(self, classifier):
        assert classifier.classify('END-EVALUATE') is None

    def test_else_returns_none(self, classifier):
        assert classifier.classify('ELSE') is None

    def test_when_returns_none(self, classifier):
        assert classifier.classify('WHEN OTHER') is None

    def test_empty_returns_none(self, classifier):
        assert classifier.classify('') is None

    def test_unknown_verb(self, classifier):
        stmt = classifier.classify('SOMETHING-UNKNOWN')
        assert stmt.type == StatementType.UNKNOWN

    # Token preservation
    def test_tokens_preserved(self, classifier):
        stmt = classifier.classify('MOVE "HELLO" TO WS-NAME')
        assert stmt.tokens == ['MOVE', '"HELLO"', 'TO', 'WS-NAME']

    def test_raw_text_preserved(self, classifier):
        stmt = classifier.classify('PERFORM 100-INIT UNTIL WS-EOF.')
        assert "PERFORM 100-INIT UNTIL WS-EOF" in stmt.raw_text


class TestBlockParser:
    """Tests for unified block parsing."""

    def test_simple_if_block(self, classifier, block_parser):
        stmts = [
            'IF WS-A > 10',
            'DISPLAY "BIG"',
            'END-IF',
        ]
        stmt = classifier.classify(stmts[0])
        idx = block_parser.parse_block(stmts, 0, stmt)
        assert idx == 3
        assert len(stmt.children) == 1
        assert stmt.children[0].type == StatementType.DISPLAY

    def test_if_else_block(self, classifier, block_parser):
        stmts = [
            'IF WS-A > 10',
            'DISPLAY "BIG"',
            'ELSE',
            'DISPLAY "SMALL"',
            'END-IF',
        ]
        stmt = classifier.classify(stmts[0])
        idx = block_parser.parse_block(stmts, 0, stmt)
        assert idx == 5
        assert len(stmt.children) == 1
        assert len(stmt.else_children) == 1

    def test_nested_if_block(self, classifier, block_parser):
        stmts = [
            'IF WS-A > 10',
            'IF WS-B > 5',
            'DISPLAY "DEEP"',
            'END-IF',
            'END-IF',
        ]
        stmt = classifier.classify(stmts[0])
        idx = block_parser.parse_block(stmts, 0, stmt)
        assert idx == 5
        assert len(stmt.children) == 1
        inner_if = stmt.children[0]
        assert inner_if.type == StatementType.IF
        assert len(inner_if.children) == 1

    def test_evaluate_block(self, classifier, block_parser):
        stmts = [
            'EVALUATE TRUE',
            'WHEN WS-A >= 90',
            'MOVE "A" TO WS-GRADE',
            'WHEN WS-A >= 80',
            'MOVE "B" TO WS-GRADE',
            'WHEN OTHER',
            'MOVE "C" TO WS-GRADE',
            'END-EVALUATE',
        ]
        stmt = classifier.classify(stmts[0])
        idx = block_parser.parse_block(stmts, 0, stmt)
        assert idx == 8
        assert len(stmt.when_blocks) == 3
        assert stmt.when_blocks[0][0] == "WS-A >= 90"
        assert stmt.when_blocks[2][0] == "OTHER"

    def test_if_inside_evaluate(self, classifier, block_parser):
        stmts = [
            'EVALUATE TRUE',
            'WHEN WS-A >= 90',
            'IF WS-B > 0',
            'DISPLAY "OK"',
            'END-IF',
            'WHEN OTHER',
            'DISPLAY "DEFAULT"',
            'END-EVALUATE',
        ]
        stmt = classifier.classify(stmts[0])
        idx = block_parser.parse_block(stmts, 0, stmt)
        assert idx == 8
        assert len(stmt.when_blocks) == 2
        # First WHEN block should contain an IF statement
        when1_stmts = stmt.when_blocks[0][1]
        assert len(when1_stmts) == 1
        assert when1_stmts[0].type == StatementType.IF


class TestProcedureParserParity:
    """Compare structured parser vs legacy parser outputs."""

    def _compare_paragraphs(self, lark_paras, legacy_paras, context=""):
        assert len(lark_paras) == len(legacy_paras), \
            f"{context} Paragraph count: lark={len(lark_paras)}, legacy={len(legacy_paras)}"
        for l, r in zip(lark_paras, legacy_paras):
            assert l.name == r.name, f"{context} Para name mismatch: {l.name} vs {r.name}"
            assert len(l.statements) == len(r.statements), \
                f"{context} {l.name} stmt count: lark={len(l.statements)}, legacy={len(r.statements)}"

    def test_parity_control_flow(self, lark_parser, legacy_parser):
        lark_prog = lark_parser.parse_file(sample_path("control_flow.cbl"))
        legacy_prog = legacy_parser.parse_file(sample_path("control_flow.cbl"))
        self._compare_paragraphs(lark_prog.paragraphs, legacy_prog.paragraphs,
                                "control_flow")

    def test_parity_hello(self, lark_parser, legacy_parser):
        lark_prog = lark_parser.parse_file(sample_path("hello.cbl"))
        legacy_prog = legacy_parser.parse_file(sample_path("hello.cbl"))
        self._compare_paragraphs(lark_prog.paragraphs, legacy_prog.paragraphs,
                                "hello")

    def test_parity_copy_test(self, lark_parser, legacy_parser):
        lark_prog = lark_parser.parse_file(sample_path("copy_test.cbl"))
        legacy_prog = legacy_parser.parse_file(sample_path("copy_test.cbl"))
        self._compare_paragraphs(lark_prog.paragraphs, legacy_prog.paragraphs,
                                "copy_test")

    def test_parity_comp3(self, lark_parser, legacy_parser):
        lark_prog = lark_parser.parse_file(sample_path("comp3_pointer.cbl"))
        legacy_prog = legacy_parser.parse_file(sample_path("comp3_pointer.cbl"))
        self._compare_paragraphs(lark_prog.paragraphs, legacy_prog.paragraphs,
                                "comp3_pointer")

    def test_parity_nested_if_structure(self, lark_parser, legacy_parser):
        """Verify nested IF children match between parsers."""
        lark_prog = lark_parser.parse_file(sample_path("control_flow.cbl"))
        legacy_prog = legacy_parser.parse_file(sample_path("control_flow.cbl"))

        # Find 500-VALIDATE in both
        lark_validate = None
        legacy_validate = None
        for p in lark_prog.paragraphs:
            if p.name == "500-VALIDATE":
                lark_validate = p
        for p in legacy_prog.paragraphs:
            if p.name == "500-VALIDATE":
                legacy_validate = p

        assert lark_validate is not None
        assert legacy_validate is not None

        # Compare statement types
        lark_types = [s.type for s in lark_validate.statements]
        legacy_types = [s.type for s in legacy_validate.statements]
        assert lark_types == legacy_types

        # Compare EVALUATE when_blocks count
        lark_eval = [s for s in lark_validate.statements
                     if s.type == StatementType.EVALUATE][0]
        legacy_eval = [s for s in legacy_validate.statements
                       if s.type == StatementType.EVALUATE][0]
        assert len(lark_eval.when_blocks) == len(legacy_eval.when_blocks)

    def test_parity_exec_flags(self, lark_parser, legacy_parser):
        """EXEC SQL/CICS/DLI flags should match."""
        source = """\
       IDENTIFICATION DIVISION.
       PROGRAM-ID. EXECTEST.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 WS-A PIC X.
       PROCEDURE DIVISION.
       MAIN-PARA.
           EXEC SQL SELECT * FROM TABLE END-EXEC.
           EXEC CICS SEND MAP("MAP1") END-EXEC.
           STOP RUN.
"""
        lark_prog = lark_parser.parse_string(source)
        legacy_prog = legacy_parser.parse_string(source)
        assert lark_prog.has_exec_sql == legacy_prog.has_exec_sql
        assert lark_prog.has_exec_cics == legacy_prog.has_exec_cics

    def test_parity_called_programs(self, lark_parser, legacy_parser):
        source = """\
       IDENTIFICATION DIVISION.
       PROGRAM-ID. CALLTEST.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 WS-A PIC X.
       PROCEDURE DIVISION.
       MAIN-PARA.
           CALL "SUBPROG1" USING WS-A.
           CALL "SUBPROG2" USING WS-A.
           STOP RUN.
"""
        lark_prog = lark_parser.parse_string(source)
        legacy_prog = legacy_parser.parse_string(source)
        assert sorted(lark_prog.called_programs) == sorted(legacy_prog.called_programs)


class TestProcedureParserFallback:
    """Test legacy fallback when use_lark=False."""

    def test_legacy_still_works(self, legacy_parser):
        program = legacy_parser.parse_file(sample_path("control_flow.cbl"))
        assert program.program_id == "CTRLFLOW"
        assert len(program.paragraphs) >= 7

    def test_legacy_nested_if(self, legacy_parser):
        program = legacy_parser.parse_file(sample_path("control_flow.cbl"))
        validate = None
        for p in program.paragraphs:
            if p.name == "500-VALIDATE":
                validate = p
                break
        assert validate is not None
        eval_stmts = [s for s in validate.statements
                      if s.type == StatementType.EVALUATE]
        assert len(eval_stmts) >= 1
