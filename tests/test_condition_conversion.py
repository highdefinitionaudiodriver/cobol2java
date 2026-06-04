"""Tests for COBOL condition -> Java condition conversion.

These guard against regressions in symbolic relational operator handling
(`=`, `NOT =`, `NOT >`, `NOT <`) and the comment-placeholder import bug,
which previously produced non-compilable Java such as `if (sqlcode not = 0)`
and `import // TODO ...;`.
"""
import pytest

from src.java_generator import JavaCodeGenerator
from src.oop_transformer import JavaClass, TransformOptions


@pytest.fixture
def gen():
    return JavaCodeGenerator(TransformOptions())


class TestSymbolicRelationalOperators:
    def test_bare_equals_becomes_double_equals(self, gen):
        assert gen._convert_condition("WS-COUNT = 5") == "wsCount == 5"

    def test_not_equals_symbolic(self, gen):
        assert gen._convert_condition("SQLCODE NOT = 0") == "sqlcode != 0"

    def test_not_greater_becomes_le(self, gen):
        assert gen._convert_condition("WS-A NOT > WS-B") == "wsA <= wsB"

    def test_not_less_becomes_ge(self, gen):
        assert gen._convert_condition("WS-A NOT < 10") == "wsA >= 10"

    def test_existing_ge_is_preserved(self, gen):
        assert gen._convert_condition("WS-A >= WS-B") == "wsA >= wsB"

    def test_word_form_not_equal_still_works(self, gen):
        assert gen._convert_condition("WS-A NOT EQUAL TO 0") == "wsA != 0"

    def test_leading_not_negates_whole_condition(self, gen):
        assert gen._convert_condition("NOT WS-FLAG = 1") == "!(wsFlag == 1)"

    def test_compound_condition(self, gen):
        assert (
            gen._convert_condition("WS-A <= 5 AND WS-B = 3")
            == "wsA <= 5 && wsB == 3"
        )


class TestImportCommentPlaceholder:
    def test_comment_import_is_not_wrapped(self, gen):
        cls = JavaClass(name="Foo", package_name="com.example")
        cls.imports = {"// TODO: Add CICS service interface imports"}
        out = gen.generate_class(cls)
        assert "// TODO: Add CICS service interface imports" in out
        assert "import // TODO" not in out

    def test_normal_import_still_wrapped(self, gen):
        cls = JavaClass(name="Foo", package_name="com.example")
        cls.imports = {"java.math.BigDecimal"}
        out = gen.generate_class(cls)
        assert "import java.math.BigDecimal;" in out
