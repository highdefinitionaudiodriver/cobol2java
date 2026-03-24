"""
Tests for nested PERFORM, GO TO, and complex control flow conversion.
"""
import os
import pytest
from src.cobol_parser import CobolParser, StatementType
from src.oop_transformer import OopTransformer
from src.java_generator import JavaCodeGenerator
from tests.conftest import sample_path


class TestPerformParsing:
    """Tests for PERFORM statement parsing."""

    def test_simple_perform_detected(self, parser):
        source = """\
       IDENTIFICATION DIVISION.
       PROGRAM-ID. PERFTEST.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 WS-A PIC 9.
       PROCEDURE DIVISION.
       MAIN-PARA.
           PERFORM SUB-PARA.
           STOP RUN.
       SUB-PARA.
           MOVE 1 TO WS-A.
"""
        program = parser.parse_string(source)
        main_stmts = program.paragraphs[0].statements
        perform_stmts = [s for s in main_stmts if s.type == StatementType.PERFORM]
        assert len(perform_stmts) >= 1

    def test_perform_until_detected(self, parser):
        program = parser.parse_file(sample_path("control_flow.cbl"))
        main_para = None
        for p in program.paragraphs:
            if "MAIN" in p.name.upper():
                main_para = p
                break
        assert main_para is not None

        perform_stmts = [s for s in main_para.statements if s.type == StatementType.PERFORM]
        assert len(perform_stmts) >= 2

        # Check that PERFORM UNTIL has the UNTIL keyword in raw text
        until_stmts = [s for s in perform_stmts if "UNTIL" in s.raw_text.upper()]
        assert len(until_stmts) >= 1

    def test_perform_varying_detected(self, parser):
        program = parser.parse_file(sample_path("control_flow.cbl"))
        process_para = None
        for p in program.paragraphs:
            if p.name == "200-PROCESS":
                process_para = p
                break
        assert process_para is not None

        perform_stmts = [s for s in process_para.statements if s.type == StatementType.PERFORM]
        varying_stmts = [s for s in perform_stmts if "VARYING" in s.raw_text.upper()]
        assert len(varying_stmts) >= 1

    def test_nested_perform_calls(self, parser):
        """Paragraphs called by PERFORM should themselves contain statements."""
        program = parser.parse_file(sample_path("control_flow.cbl"))

        # 300-INNER-LOOP calls 400-CALCULATE and 500-VALIDATE
        inner_loop = None
        for p in program.paragraphs:
            if p.name == "300-INNER-LOOP":
                inner_loop = p
                break
        assert inner_loop is not None

        perform_stmts = [s for s in inner_loop.statements if s.type == StatementType.PERFORM]
        assert len(perform_stmts) >= 2

        perform_targets = [s.raw_text for s in perform_stmts]
        assert any("400-CALCULATE" in t for t in perform_targets)
        assert any("500-VALIDATE" in t for t in perform_targets)


class TestGoToParsing:
    """Tests for GO TO statement parsing."""

    def test_goto_detected(self, parser):
        program = parser.parse_file(sample_path("control_flow.cbl"))
        inner_loop = None
        for p in program.paragraphs:
            if p.name == "300-INNER-LOOP":
                inner_loop = p
                break
        assert inner_loop is not None

        # GO TO should be inside an IF block
        if_stmts = [s for s in inner_loop.statements if s.type == StatementType.IF]
        assert len(if_stmts) >= 1

        # Look for GO TO in IF children
        goto_found = False
        for if_stmt in if_stmts:
            for child in if_stmt.children:
                if child.type == StatementType.GO_TO:
                    goto_found = True
                    assert "300-INNER-LOOP-EXIT" in child.raw_text
        assert goto_found, "GO TO not found in IF block"

    def test_goto_inline(self, parser):
        source = """\
       IDENTIFICATION DIVISION.
       PROGRAM-ID. GOTOTEST.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 WS-X PIC 9.
       PROCEDURE DIVISION.
       PARA-A.
           MOVE 1 TO WS-X.
           GO TO PARA-B.
       PARA-B.
           DISPLAY WS-X.
           STOP RUN.
"""
        program = parser.parse_string(source)
        para_a = program.paragraphs[0]
        goto_stmts = [s for s in para_a.statements if s.type == StatementType.GO_TO]
        assert len(goto_stmts) == 1
        assert "PARA-B" in goto_stmts[0].raw_text

    def test_exit_paragraph(self, parser):
        program = parser.parse_file(sample_path("control_flow.cbl"))
        exit_para = None
        for p in program.paragraphs:
            if p.name == "300-INNER-LOOP-EXIT":
                exit_para = p
                break
        assert exit_para is not None
        exit_stmts = [s for s in exit_para.statements if s.type == StatementType.EXIT]
        assert len(exit_stmts) >= 1


class TestNestedIfEvaluate:
    """Tests for nested IF and EVALUATE structures."""

    def test_nested_if_in_validate(self, parser):
        program = parser.parse_file(sample_path("control_flow.cbl"))
        validate = None
        for p in program.paragraphs:
            if p.name == "500-VALIDATE":
                validate = p
                break
        assert validate is not None

        # Should have EVALUATE and nested IF statements
        evaluate_stmts = [s for s in validate.statements if s.type == StatementType.EVALUATE]
        assert len(evaluate_stmts) >= 1

        # EVALUATE should have WHEN blocks
        eval_stmt = evaluate_stmts[0]
        assert len(eval_stmt.when_blocks) >= 4

    def test_if_with_nested_if(self, parser):
        program = parser.parse_file(sample_path("control_flow.cbl"))
        validate = None
        for p in program.paragraphs:
            if p.name == "500-VALIDATE":
                validate = p
                break
        assert validate is not None

        # Find the outer IF statement (WS-GRADE = "A")
        if_stmts = [s for s in validate.statements if s.type == StatementType.IF]
        assert len(if_stmts) >= 1

        outer_if = if_stmts[0]
        # The outer IF should have children (inner IF for WS-OUTER-CTR > 3)
        assert len(outer_if.children) >= 1
        # The ELSE branch should also have an inner IF
        assert len(outer_if.else_children) >= 1

    def test_if_else_structure(self, parser):
        program = parser.parse_file(sample_path("control_flow.cbl"))
        calc_para = None
        for p in program.paragraphs:
            if p.name == "400-CALCULATE":
                calc_para = p
                break
        assert calc_para is not None

        if_stmts = [s for s in calc_para.statements if s.type == StatementType.IF]
        assert len(if_stmts) >= 1
        # IF should have both then and else branches
        assert len(if_stmts[0].children) >= 1
        assert len(if_stmts[0].else_children) >= 1


class TestControlFlowTransformation:
    """Integration tests: transform control flow COBOL to Java."""

    def test_transform_produces_methods(self, parser, transformer):
        program = parser.parse_file(sample_path("control_flow.cbl"))
        project = transformer.transform(program)

        assert project.main_class is not None
        method_names = [m.name for m in project.main_class.methods]

        assert "mainControl" in method_names or "000MainControl" in method_names or \
               any("main" in n.lower() for n in method_names)

    def test_all_paragraphs_become_methods(self, parser, transformer):
        program = parser.parse_file(sample_path("control_flow.cbl"))
        project = transformer.transform(program)

        method_names = [m.name for m in project.main_class.methods]
        # Each paragraph should produce a method
        assert len(method_names) >= 7  # 000-MAIN, 100, 200, 300, 300-EXIT, 400, 500, 900

    def test_generate_control_flow_java(self, parser, transformer, generator, output_dir):
        program = parser.parse_file(sample_path("control_flow.cbl"))
        project = transformer.transform(program)
        generator.generate_project(project, output_dir)

        # Verify Java files are generated
        java_files = []
        for root, dirs, files in os.walk(output_dir):
            for f in files:
                if f.endswith(".java"):
                    java_files.append(os.path.join(root, f))
        assert len(java_files) > 0

    def test_enum_from_88_flags(self, parser, transformer):
        program = parser.parse_file(sample_path("control_flow.cbl"))
        project = transformer.transform(program)

        # WS-EOF-FLAG has 2 x 88-levels, WS-ERROR-FLAG has 2 x 88-levels
        enum_names = [e.name for e in project.enum_classes]
        assert len(enum_names) >= 2

    def test_data_class_extraction(self, parser, transformer):
        program = parser.parse_file(sample_path("control_flow.cbl"))
        project = transformer.transform(program)

        # WS-COUNTERS and WS-FLAGS should be extracted as data classes
        class_names = [dc.name for dc in project.data_classes]
        assert any("Counter" in name or "Counters" in name for name in class_names), \
            f"Expected data class with 'Counter', got: {class_names}"
        assert any("Flag" in name or "Flags" in name for name in class_names), \
            f"Expected data class with 'Flag', got: {class_names}"


class TestComplexInlineControlFlow:
    """Tests for complex inline control flow patterns."""

    def test_evaluate_true_pattern(self, parser):
        source = """\
       IDENTIFICATION DIVISION.
       PROGRAM-ID. EVALTEST.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 WS-SCORE PIC 9(3).
       01 WS-GRADE PIC X.
       PROCEDURE DIVISION.
       MAIN-PARA.
           EVALUATE TRUE
               WHEN WS-SCORE >= 90
                   MOVE "A" TO WS-GRADE
               WHEN WS-SCORE >= 80
                   MOVE "B" TO WS-GRADE
               WHEN OTHER
                   MOVE "C" TO WS-GRADE
           END-EVALUATE.
           STOP RUN.
"""
        program = parser.parse_string(source)
        main_stmts = program.paragraphs[0].statements
        eval_stmts = [s for s in main_stmts if s.type == StatementType.EVALUATE]
        assert len(eval_stmts) == 1
        assert len(eval_stmts[0].when_blocks) == 3

    def test_deeply_nested_if(self, parser):
        source = """\
       IDENTIFICATION DIVISION.
       PROGRAM-ID. DEEPIF.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 WS-A PIC 9.
       01 WS-B PIC 9.
       01 WS-C PIC 9.
       PROCEDURE DIVISION.
       MAIN-PARA.
           IF WS-A = 1
               IF WS-B = 2
                   IF WS-C = 3
                       DISPLAY "DEEP"
                   END-IF
               END-IF
           END-IF.
           STOP RUN.
"""
        program = parser.parse_string(source)
        main_stmts = program.paragraphs[0].statements
        if_stmts = [s for s in main_stmts if s.type == StatementType.IF]
        assert len(if_stmts) == 1

        outer = if_stmts[0]
        assert len(outer.children) >= 1
        # First child should be nested IF
        inner_ifs = [c for c in outer.children if c.type == StatementType.IF]
        assert len(inner_ifs) >= 1

        # Second level nesting
        level2 = inner_ifs[0]
        level2_ifs = [c for c in level2.children if c.type == StatementType.IF]
        assert len(level2_ifs) >= 1

    def test_perform_thru(self, parser):
        source = """\
       IDENTIFICATION DIVISION.
       PROGRAM-ID. THRUTEST.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 WS-X PIC 9.
       PROCEDURE DIVISION.
       MAIN-PARA.
           PERFORM STEP-A THRU STEP-C.
           STOP RUN.
       STEP-A.
           MOVE 1 TO WS-X.
       STEP-B.
           MOVE 2 TO WS-X.
       STEP-C.
           MOVE 3 TO WS-X.
"""
        program = parser.parse_string(source)
        main_stmts = program.paragraphs[0].statements
        perform_stmts = [s for s in main_stmts if s.type == StatementType.PERFORM]
        assert len(perform_stmts) >= 1
        assert "THRU" in perform_stmts[0].raw_text.upper() or \
               "THROUGH" in perform_stmts[0].raw_text.upper()
