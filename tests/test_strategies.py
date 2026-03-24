"""
Tests for ConversionStrategy interfaces and their integration
with JavaCodeGenerator and OopTransformer.
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.conversion_strategies import (
    ConversionStrategyRegistry, DefaultFileIoStrategy,
    JdbcSqlStrategy, JpaSqlStrategy, DefaultCicsStrategy,
    VsamToDatabaseStrategy, get_default_registry,
)
from src.java_generator import JavaCodeGenerator
from src.oop_transformer import OopTransformer, TransformOptions
from src.cobol_parser import CobolParser
from tests.conftest import sample_path


class TestDefaultFileIoStrategy:
    """Test DefaultFileIoStrategy."""

    @pytest.fixture
    def strategy(self):
        return DefaultFileIoStrategy()

    def test_generate_imports(self, strategy):
        imports = strategy.generate_imports()
        assert "java.io.*" in imports
        assert "java.nio.file.*" in imports

    def test_generate_open(self, strategy):
        lines = strategy.generate_open("fileHandler", "INPUT", "    ")
        assert len(lines) == 1
        assert 'fileHandler.open("INPUT")' in lines[0]

    def test_generate_close(self, strategy):
        lines = strategy.generate_close("fileHandler", "    ")
        assert len(lines) == 1
        assert "fileHandler.close()" in lines[0]

    def test_generate_read(self, strategy):
        lines = strategy.generate_read("fileHandler", "record", "    ")
        assert len(lines) == 1
        assert "fileHandler.readRecord()" in lines[0]

    def test_generate_write(self, strategy):
        lines = strategy.generate_write("fileHandler", "data", "    ")
        assert len(lines) == 1
        assert "fileHandler.writeRecord(data)" in lines[0]

    def test_generate_handler_class_body(self, strategy):
        lines = strategy.generate_handler_class_body("TestHandler", "TEST-FILE", "SEQUENTIAL", "    ")
        body = "\n".join(lines)
        assert "public void open(String mode)" in body
        assert "public void close()" in body
        assert "public String readRecord()" in body
        assert "public void writeRecord(String record)" in body
        assert "public String getFileStatus()" in body


class TestJdbcSqlStrategy:
    """Test JdbcSqlStrategy."""

    @pytest.fixture
    def strategy(self):
        return JdbcSqlStrategy()

    def test_generate_imports(self, strategy):
        imports = strategy.generate_imports()
        assert "java.sql.Connection" in imports
        assert "java.sql.PreparedStatement" in imports
        assert "java.sql.ResultSet" in imports

    def test_generate_fields(self, strategy):
        lines = strategy.generate_fields("    ")
        body = "\n".join(lines)
        assert "Connection connection" in body
        assert "sqlCode" in body

    def test_generate_select(self, strategy):
        lines = strategy.generate_select(
            "SELECT * FROM EMPLOYEES WHERE ID = :emp-id",
            ["emp-id"], ["emp-name"], "    "
        )
        body = "\n".join(lines)
        assert "prepareStatement" in body
        assert "executeQuery" in body

    def test_generate_insert(self, strategy):
        lines = strategy.generate_insert_update_delete(
            "INSERT INTO EMPLOYEES VALUES (:emp-id, :emp-name)",
            ["emp-id", "emp-name"], "    "
        )
        body = "\n".join(lines)
        assert "prepareStatement" in body
        assert "executeUpdate" in body

    def test_generate_cursor_lifecycle(self, strategy):
        # DECLARE
        declare = strategy.generate_cursor_declare("EMP-CUR", "SELECT * FROM EMP", "    ")
        assert any("empCurSql" in l for l in declare)

        # OPEN
        open_lines = strategy.generate_cursor_open("EMP-CUR", [], "    ")
        assert any("prepareStatement" in l for l in open_lines)

        # FETCH
        fetch = strategy.generate_cursor_fetch("EMP-CUR", ["emp-name", "emp-id"], "    ")
        assert any("empCurRs.next()" in l for l in fetch)

        # CLOSE
        close = strategy.generate_cursor_close("EMP-CUR", "    ")
        assert any("empCurRs.close()" in l for l in close)

    def test_generate_commit(self, strategy):
        lines = strategy.generate_commit("    ")
        assert any("connection.commit()" in l for l in lines)

    def test_generate_rollback(self, strategy):
        lines = strategy.generate_rollback("    ")
        assert any("connection.rollback()" in l for l in lines)


class TestJpaSqlStrategy:
    """Test JPA/Hibernate strategy."""

    @pytest.fixture
    def strategy(self):
        return JpaSqlStrategy()

    def test_generate_imports(self, strategy):
        imports = strategy.generate_imports()
        assert "javax.persistence.EntityManager" in imports

    def test_generate_fields(self, strategy):
        lines = strategy.generate_fields("    ")
        body = "\n".join(lines)
        assert "EntityManager" in body

    def test_generate_select_uses_native_query(self, strategy):
        lines = strategy.generate_select(
            "SELECT * FROM EMPLOYEES", [], ["emp-name"], "    "
        )
        body = "\n".join(lines)
        assert "createNativeQuery" in body

    def test_generate_commit_uses_em(self, strategy):
        lines = strategy.generate_commit("    ")
        assert any("em.getTransaction().commit()" in l for l in lines)


class TestVsamToDatabaseStrategy:
    """Test VSAM-to-DB strategy."""

    @pytest.fixture
    def strategy(self):
        return VsamToDatabaseStrategy()

    def test_generate_imports(self, strategy):
        imports = strategy.generate_imports()
        assert "java.sql.Connection" in imports

    def test_generate_handler_fields(self, strategy):
        fields = strategy.generate_handler_fields("CUST-FILE", "INDEXED")
        body = "\n".join(fields)
        assert "TABLE_NAME" in body
        assert "Connection" in body

    def test_generate_open_sets_mode(self, strategy):
        lines = strategy.generate_open("handler", "INPUT", "    ")
        assert any("setMode" in l for l in lines)

    def test_generate_read_by_key(self, strategy):
        lines = strategy.generate_read("handler", "record", "    ")
        assert any("readByKey" in l for l in lines)


class TestDefaultCicsStrategy:
    """Test DefaultCicsStrategy."""

    @pytest.fixture
    def strategy(self):
        return DefaultCicsStrategy()

    def test_terminal_io_send(self, strategy):
        lines = strategy.generate_terminal_io(
            "SEND", {"MAPSET": "MSET1", "MAP": "MAP1", "FROM": "WS-DATA"}, "    "
        )
        body = "\n".join(lines)
        assert "cicsTerminal.sendMap" in body

    def test_file_io_read(self, strategy):
        lines = strategy.generate_file_io(
            "READ", {"DATASET": "CUSTFILE", "INTO": "WS-REC", "RIDFLD": "WS-KEY"}, "    "
        )
        body = "\n".join(lines)
        assert "cicsFile.read" in body

    def test_program_control_link(self, strategy):
        lines = strategy.generate_program_control(
            "LINK", {"PROGRAM": "SUBPGM", "COMMAREA": "WS-COMM"}, "    "
        )
        body = "\n".join(lines)
        assert 'cicsProgram.link("SUBPGM"' in body


class TestRegistryIntegration:
    """Test strategy registry integration with generator/transformer."""

    def test_default_registry_exists(self):
        registry = get_default_registry()
        assert isinstance(registry.file_io, DefaultFileIoStrategy)
        assert isinstance(registry.sql, JdbcSqlStrategy)
        assert isinstance(registry.cics, DefaultCicsStrategy)

    def test_swap_sql_strategy(self):
        registry = ConversionStrategyRegistry()
        assert isinstance(registry.sql, JdbcSqlStrategy)
        registry.sql = JpaSqlStrategy()
        assert isinstance(registry.sql, JpaSqlStrategy)

    def test_swap_file_io_strategy(self):
        registry = ConversionStrategyRegistry()
        registry.file_io = VsamToDatabaseStrategy()
        assert isinstance(registry.file_io, VsamToDatabaseStrategy)

    def test_generator_uses_strategy(self):
        """Generator should produce different output based on strategy."""
        options = TransformOptions()
        # Default (JDBC)
        gen_jdbc = JavaCodeGenerator(options)
        assert isinstance(gen_jdbc.strategies.sql, JdbcSqlStrategy)

        # Custom (JPA)
        registry = ConversionStrategyRegistry()
        registry.sql = JpaSqlStrategy()
        gen_jpa = JavaCodeGenerator(options, strategy_registry=registry)
        assert isinstance(gen_jpa.strategies.sql, JpaSqlStrategy)

    def test_transformer_uses_strategy(self):
        """Transformer should accept custom strategy registry."""
        registry = ConversionStrategyRegistry()
        registry.file_io = VsamToDatabaseStrategy()
        transformer = OopTransformer(strategy_registry=registry)
        assert isinstance(transformer.strategies.file_io, VsamToDatabaseStrategy)

    def test_full_pipeline_with_default_strategy(self):
        """Full pipeline should work with default strategies."""
        parser = CobolParser(encoding="utf-8")
        transformer = OopTransformer()
        generator = JavaCodeGenerator()

        program = parser.parse_file(sample_path("hello.cbl"))
        project = transformer.transform(program)
        assert project.main_class is not None

        code = generator.generate_class(project.main_class)
        assert len(code) > 0

    def test_full_pipeline_with_jpa_strategy(self):
        """Full pipeline should work with JPA strategy."""
        registry = ConversionStrategyRegistry()
        registry.sql = JpaSqlStrategy()

        parser = CobolParser(encoding="utf-8")
        transformer = OopTransformer(strategy_registry=registry)
        generator = JavaCodeGenerator(strategy_registry=registry)

        program = parser.parse_file(sample_path("hello.cbl"))
        project = transformer.transform(program)
        assert project.main_class is not None


class TestExecSqlViaStrategy:
    """Test EXEC SQL generation via strategy."""

    @pytest.fixture
    def parser(self):
        return CobolParser(encoding="utf-8", use_lark=True)

    def test_exec_sql_uses_jdbc_by_default(self, parser):
        source = """\
       IDENTIFICATION DIVISION.
       PROGRAM-ID. SQLTEST.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 WS-A PIC X.
       PROCEDURE DIVISION.
       MAIN-PARA.
           EXEC SQL SELECT * FROM TABLE END-EXEC.
           STOP RUN.
"""
        program = parser.parse_string(source)
        assert program.has_exec_sql is True

        generator = JavaCodeGenerator()
        transformer = OopTransformer()
        project = transformer.transform(program)
        code = generator.generate_class(project.main_class)
        assert "java.sql" in code or "Connection" in code
