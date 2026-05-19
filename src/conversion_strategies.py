"""
Conversion Strategy Interfaces (Extension Points)

COBOL→Java変換エンジンの拡張ポイントを定義する。
ファイルI/O、EXEC SQL、EXEC CICSの変換ロジックを
Strategyパターンで差し替え可能にする。

使い方:
  1. 各Strategyインターフェースを継承して具体クラスを作成
  2. ConversionStrategyRegistry に登録
  3. JavaCodeGenerator / OopTransformer がレジストリ経由で呼び出す

拡張例:
  - JdbcSqlStrategy: EXEC SQL → JDBC PreparedStatement (デフォルト)
  - JpaSqlStrategy: EXEC SQL → JPA/Hibernate Entity操作
  - VsamToDbStrategy: VSAM KSDS/RRDS → Spring JdbcTemplate
  - VsamToFileStrategy: VSAM → java.nio flat file (デフォルト)
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Type


# ============================================================
# File I/O Strategy
# ============================================================

class FileIoStrategy(ABC):
    """COBOL file I/O (OPEN/CLOSE/READ/WRITE) → Java 変換戦略."""

    @abstractmethod
    def generate_imports(self) -> Set[str]:
        """生成するJavaコードに必要なimport文を返す."""

    @abstractmethod
    def generate_handler_fields(self, file_name: str, organization: str) -> List[str]:
        """ファイルハンドラクラスのフィールド定義を返す."""

    @abstractmethod
    def generate_open(self, handler_var: str, mode: str, indent: str) -> List[str]:
        """OPEN文のJavaコードを返す."""

    @abstractmethod
    def generate_close(self, handler_var: str, indent: str) -> List[str]:
        """CLOSE文のJavaコードを返す."""

    @abstractmethod
    def generate_read(self, handler_var: str, record_var: str, indent: str) -> List[str]:
        """READ文のJavaコードを返す."""

    @abstractmethod
    def generate_write(self, handler_var: str, record_expr: str, indent: str) -> List[str]:
        """WRITE文のJavaコードを返す."""

    @abstractmethod
    def generate_handler_class_body(
        self, class_name: str, file_name: str,
        organization: str, indent: str
    ) -> List[str]:
        """ファイルハンドラクラスのメソッド本体を生成."""


class SqlConversionStrategy(ABC):
    """EXEC SQL → Java 変換戦略."""

    @abstractmethod
    def generate_imports(self) -> Set[str]:
        """必要なJava import文を返す."""

    @abstractmethod
    def generate_fields(self, indent: str) -> List[str]:
        """メインクラスに追加するフィールド定義を返す."""

    @abstractmethod
    def generate_select(
        self, sql: str, host_vars: List[str],
        into_vars: List[str], indent: str
    ) -> List[str]:
        """SELECT文のJavaコードを返す."""

    @abstractmethod
    def generate_insert_update_delete(
        self, sql: str, host_vars: List[str], indent: str
    ) -> List[str]:
        """INSERT/UPDATE/DELETE文のJavaコードを返す."""

    @abstractmethod
    def generate_cursor_declare(
        self, cursor_name: str, select_sql: str, indent: str
    ) -> List[str]:
        """DECLARE CURSOR文のJavaコードを返す."""

    @abstractmethod
    def generate_cursor_open(
        self, cursor_name: str, host_vars: List[str], indent: str
    ) -> List[str]:
        """OPEN CURSOR文のJavaコードを返す."""

    @abstractmethod
    def generate_cursor_fetch(
        self, cursor_name: str, into_vars: List[str], indent: str
    ) -> List[str]:
        """FETCH文のJavaコードを返す."""

    @abstractmethod
    def generate_cursor_close(
        self, cursor_name: str, indent: str
    ) -> List[str]:
        """CLOSE CURSOR文のJavaコードを返す."""

    @abstractmethod
    def generate_commit(self, indent: str) -> List[str]:
        """COMMIT文のJavaコードを返す."""

    @abstractmethod
    def generate_rollback(self, indent: str) -> List[str]:
        """ROLLBACK文のJavaコードを返す."""


class CicsConversionStrategy(ABC):
    """EXEC CICS → Java 変換戦略."""

    @abstractmethod
    def generate_imports(self) -> Set[str]:
        """必要なJava import文を返す."""

    @abstractmethod
    def generate_fields(self, indent: str) -> List[str]:
        """メインクラスに追加するフィールド定義を返す."""

    @abstractmethod
    def generate_terminal_io(
        self, command: str, params: Dict[str, str], indent: str
    ) -> List[str]:
        """SEND/RECEIVE MAP文のJavaコードを返す."""

    @abstractmethod
    def generate_file_io(
        self, command: str, params: Dict[str, str], indent: str
    ) -> List[str]:
        """CICS FILE I/O (READ/WRITE/REWRITE/DELETE/BROWSE) のJavaコードを返す."""

    @abstractmethod
    def generate_program_control(
        self, command: str, params: Dict[str, str], indent: str
    ) -> List[str]:
        """LINK/XCTL/RETURN文のJavaコードを返す."""

    @abstractmethod
    def generate_temp_storage(
        self, command: str, params: Dict[str, str], indent: str
    ) -> List[str]:
        """WRITEQ/READQ/DELETEQ文のJavaコードを返す."""


# ============================================================
# Default Implementations
# ============================================================

def _camel(name: str) -> str:
    """COBOL名をcamelCaseに変換."""
    import re
    name = name.strip().strip("'\"")
    if not name or not re.match(r'^[A-Za-z]', name):
        return name
    parts = name.lower().replace("_", "-").split("-")
    return parts[0] + "".join(p.capitalize() for p in parts[1:]) if parts else name


class DefaultFileIoStrategy(FileIoStrategy):
    """デフォルト: java.io/nio を使ったフラットファイルI/O."""

    def generate_imports(self) -> Set[str]:
        return {"java.io.*", "java.nio.file.*"}

    def generate_handler_fields(self, file_name: str, organization: str) -> List[str]:
        lines = [
            "private String filePath;",
            'private String fileStatus = "00";',
        ]
        if organization.upper() in ("SEQUENTIAL", "LINE SEQUENTIAL", ""):
            lines.append("private BufferedReader reader;")
            lines.append("private BufferedWriter writer;")
        return lines

    def generate_open(self, handler_var: str, mode: str, indent: str) -> List[str]:
        return [f'{indent}{handler_var}.open("{mode}");']

    def generate_close(self, handler_var: str, indent: str) -> List[str]:
        return [f"{indent}{handler_var}.close();"]

    def generate_read(self, handler_var: str, record_var: str, indent: str) -> List[str]:
        return [f"{indent}String {record_var} = {handler_var}.readRecord();"]

    def generate_write(self, handler_var: str, record_expr: str, indent: str) -> List[str]:
        return [f"{indent}{handler_var}.writeRecord({record_expr});"]

    def generate_handler_class_body(
        self, class_name: str, file_name: str,
        organization: str, indent: str
    ) -> List[str]:
        lines = []
        i2 = indent * 2
        # open()
        lines.append(f"{indent}public void open(String mode) throws IOException {{")
        lines.append(f'{i2}switch (mode) {{')
        lines.append(f'{i2}    case "INPUT":')
        lines.append(f'{i2}        reader = new BufferedReader(new FileReader(filePath));')
        lines.append(f'{i2}        break;')
        lines.append(f'{i2}    case "OUTPUT":')
        lines.append(f'{i2}        writer = new BufferedWriter(new FileWriter(filePath));')
        lines.append(f'{i2}        break;')
        lines.append(f'{i2}    case "I-O":')
        lines.append(f'{i2}        reader = new BufferedReader(new FileReader(filePath));')
        lines.append(f'{i2}        writer = new BufferedWriter(new FileWriter(filePath, true));')
        lines.append(f'{i2}        break;')
        lines.append(f'{i2}    case "EXTEND":')
        lines.append(f'{i2}        writer = new BufferedWriter(new FileWriter(filePath, true));')
        lines.append(f'{i2}        break;')
        lines.append(f'{i2}}}')
        lines.append(f'{i2}fileStatus = "00";')
        lines.append(f"{indent}}}")
        lines.append("")
        # close()
        lines.append(f"{indent}public void close() throws IOException {{")
        lines.append(f"{i2}if (reader != null) reader.close();")
        lines.append(f"{i2}if (writer != null) writer.close();")
        lines.append(f'{i2}fileStatus = "00";')
        lines.append(f"{indent}}}")
        lines.append("")
        # readRecord()
        lines.append(f"{indent}public String readRecord() throws IOException {{")
        lines.append(f"{i2}String line = reader.readLine();")
        lines.append(f'{i2}fileStatus = (line == null) ? "10" : "00";')
        lines.append(f"{i2}return line;")
        lines.append(f"{indent}}}")
        lines.append("")
        # writeRecord()
        lines.append(f"{indent}public void writeRecord(String record) throws IOException {{")
        lines.append(f"{i2}writer.write(record);")
        lines.append(f"{i2}writer.newLine();")
        lines.append(f'{i2}fileStatus = "00";')
        lines.append(f"{indent}}}")
        lines.append("")
        # getFileStatus()
        lines.append(f"{indent}public String getFileStatus() {{")
        lines.append(f"{i2}return fileStatus;")
        lines.append(f"{indent}}}")
        return lines


class JdbcSqlStrategy(SqlConversionStrategy):
    """デフォルト: JDBC PreparedStatementを使ったSQL変換."""

    def generate_imports(self) -> Set[str]:
        return {
            "java.sql.Connection",
            "java.sql.DriverManager",
            "java.sql.PreparedStatement",
            "java.sql.ResultSet",
            "java.sql.SQLException",
        }

    def generate_fields(self, indent: str) -> List[str]:
        return [
            f"{indent}/** JDBC connection for embedded SQL */",
            f"{indent}private Connection connection;",
            f"{indent}private int sqlCode = 0;",
        ]

    def generate_select(
        self, sql: str, host_vars: List[str],
        into_vars: List[str], indent: str
    ) -> List[str]:
        import re
        clean_sql = re.sub(r':([A-Za-z0-9-]+)', '?', sql).rstrip(".")
        lines = [
            f'{indent}PreparedStatement pstmt = connection.prepareStatement("{clean_sql}");',
        ]
        bind_vars = [hv for hv in host_vars if _camel(hv) not in [_camel(v) for v in into_vars]]
        for i, hv in enumerate(bind_vars, 1):
            lines.append(f"{indent}pstmt.setObject({i}, {_camel(hv)});")
        lines.append(f"{indent}ResultSet rs = pstmt.executeQuery();")
        lines.append(f"{indent}if (rs.next()) {{")
        for i, var in enumerate(into_vars, 1):
            lines.append(f"{indent}    {_camel(var)} = rs.getObject({i});")
        lines.append(f"{indent}}}")
        lines.append(f"{indent}rs.close();")
        lines.append(f"{indent}pstmt.close();")
        return lines

    def generate_insert_update_delete(
        self, sql: str, host_vars: List[str], indent: str
    ) -> List[str]:
        import re
        clean_sql = re.sub(r':([A-Za-z0-9-]+)', '?', sql).rstrip(".")
        lines = [
            f'{indent}PreparedStatement pstmt = connection.prepareStatement("{clean_sql}");',
        ]
        for i, hv in enumerate(host_vars, 1):
            lines.append(f"{indent}pstmt.setObject({i}, {_camel(hv)});")
        lines.append(f"{indent}int affectedRows = pstmt.executeUpdate();")
        lines.append(f"{indent}pstmt.close();")
        return lines

    def generate_cursor_declare(
        self, cursor_name: str, select_sql: str, indent: str
    ) -> List[str]:
        name = _camel(cursor_name)
        return [f'{indent}String {name}Sql = "{select_sql}";']

    def generate_cursor_open(
        self, cursor_name: str, host_vars: List[str], indent: str
    ) -> List[str]:
        name = _camel(cursor_name)
        lines = [
            f"{indent}PreparedStatement {name}Stmt = connection.prepareStatement({name}Sql);",
        ]
        for i, hv in enumerate(host_vars, 1):
            lines.append(f"{indent}{name}Stmt.setObject({i}, {_camel(hv)});")
        lines.append(f"{indent}ResultSet {name}Rs = {name}Stmt.executeQuery();")
        return lines

    def generate_cursor_fetch(
        self, cursor_name: str, into_vars: List[str], indent: str
    ) -> List[str]:
        name = _camel(cursor_name)
        lines = [f"{indent}if ({name}Rs.next()) {{"]
        for i, var in enumerate(into_vars, 1):
            lines.append(f"{indent}    {_camel(var)} = {name}Rs.getObject({i});")
        lines.append(f"{indent}}} else {{")
        lines.append(f"{indent}    sqlCode = 100; // NOT FOUND")
        lines.append(f"{indent}}}")
        return lines

    def generate_cursor_close(
        self, cursor_name: str, indent: str
    ) -> List[str]:
        name = _camel(cursor_name)
        return [
            f"{indent}{name}Rs.close();",
            f"{indent}{name}Stmt.close();",
        ]

    def generate_commit(self, indent: str) -> List[str]:
        return [f"{indent}connection.commit();"]

    def generate_rollback(self, indent: str) -> List[str]:
        return [f"{indent}connection.rollback();"]


class DefaultCicsStrategy(CicsConversionStrategy):
    """デフォルト: 抽象CICSインターフェースへのマッピング."""

    def generate_imports(self) -> Set[str]:
        return {"// TODO: Add CICS service interface imports"}

    def generate_fields(self, indent: str) -> List[str]:
        return [
            f"{indent}// CICS service interfaces - implement with your middleware adapter",
            f"{indent}// private CicsTerminal cicsTerminal;",
            f"{indent}// private CicsFile cicsFile;",
            f"{indent}// private CicsProgram cicsProgram;",
            f"{indent}// private CicsTempStorage cicsTempStorage;",
        ]

    def generate_terminal_io(
        self, command: str, params: Dict[str, str], indent: str
    ) -> List[str]:
        lines = [f"{indent}// EXEC CICS {command}"]
        if command == "SEND":
            mapset = params.get("MAPSET", "mapset")
            map_name = params.get("MAP", "map")
            from_var = params.get("FROM", "data")
            lines.append(
                f'{indent}cicsTerminal.sendMap("{mapset}", "{map_name}", {_camel(from_var)});'
            )
        elif command == "RECEIVE":
            map_name = params.get("MAP", "map")
            into_var = params.get("INTO", "data")
            lines.append(
                f'{indent}{_camel(into_var)} = cicsTerminal.receiveMap("{map_name}");'
            )
        return lines

    def generate_file_io(
        self, command: str, params: Dict[str, str], indent: str
    ) -> List[str]:
        lines = [f"{indent}// EXEC CICS {command}"]
        dataset = params.get("DATASET", params.get("FILE", "file"))
        if command == "READ":
            into_var = params.get("INTO", "record")
            ridfld = params.get("RIDFLD", "key")
            lines.append(
                f'{indent}{_camel(into_var)} = cicsFile.read("{dataset}", {_camel(ridfld)});'
            )
        elif command == "WRITE":
            from_var = params.get("FROM", "record")
            ridfld = params.get("RIDFLD", "key")
            lines.append(
                f'{indent}cicsFile.write("{dataset}", {_camel(ridfld)}, {_camel(from_var)});'
            )
        elif command == "REWRITE":
            from_var = params.get("FROM", "record")
            lines.append(
                f'{indent}cicsFile.rewrite("{dataset}", {_camel(from_var)});'
            )
        elif command == "DELETE":
            ridfld = params.get("RIDFLD", "key")
            lines.append(
                f'{indent}cicsFile.delete("{dataset}", {_camel(ridfld)});'
            )
        elif command == "STARTBR":
            ridfld = params.get("RIDFLD", "key")
            lines.append(
                f'{indent}cicsFile.startBrowse("{dataset}", {_camel(ridfld)});'
            )
        elif command in ("READNEXT", "READPREV"):
            into_var = params.get("INTO", "record")
            method = "readNext" if command == "READNEXT" else "readPrev"
            lines.append(
                f'{indent}{_camel(into_var)} = cicsFile.{method}("{dataset}");'
            )
        elif command == "ENDBR":
            lines.append(f'{indent}cicsFile.endBrowse("{dataset}");')
        return lines

    def generate_program_control(
        self, command: str, params: Dict[str, str], indent: str
    ) -> List[str]:
        lines = [f"{indent}// EXEC CICS {command}"]
        if command == "LINK":
            program = params.get("PROGRAM", "subprogram")
            commarea = params.get("COMMAREA", "")
            if commarea:
                lines.append(
                    f'{indent}cicsProgram.link("{program}", {_camel(commarea)});'
                )
            else:
                lines.append(f'{indent}cicsProgram.link("{program}");')
        elif command == "XCTL":
            program = params.get("PROGRAM", "nextprogram")
            lines.append(f'{indent}cicsProgram.transferControl("{program}");')
            lines.append(f"{indent}return;")
        elif command == "RETURN":
            transid = params.get("TRANSID", "")
            if transid:
                lines.append(
                    f'{indent}cicsProgram.returnToTransaction("{transid}");'
                )
            else:
                lines.append(f"{indent}return;")
        return lines

    def generate_temp_storage(
        self, command: str, params: Dict[str, str], indent: str
    ) -> List[str]:
        lines = [f"{indent}// EXEC CICS {command}"]
        queue = params.get("QUEUE", params.get("TD", "queue"))
        if command == "WRITEQ":
            from_var = params.get("FROM", "data")
            lines.append(
                f'{indent}cicsTempStorage.writeQueue("{queue}", {_camel(from_var)});'
            )
        elif command == "READQ":
            into_var = params.get("INTO", "data")
            lines.append(
                f'{indent}{_camel(into_var)} = cicsTempStorage.readQueue("{queue}");'
            )
        elif command == "DELETEQ":
            lines.append(f'{indent}cicsTempStorage.deleteQueue("{queue}");')
        return lines


# ============================================================
# VSAM-to-Database Strategy (拡張例)
# ============================================================

class VsamToDatabaseStrategy(FileIoStrategy):
    """VSAM (KSDS/RRDS/ESDS) → JDBC/Spring JdbcTemplate マッピング.

    VSAM KSDS → テーブル (主キー=RECORD KEY)
    VSAM RRDS → テーブル (主キー=RELATIVE KEY, auto-increment)
    VSAM ESDS → テーブル (追記型, sequence付き)
    """

    def generate_imports(self) -> Set[str]:
        return {
            "java.sql.Connection",
            "java.sql.PreparedStatement",
            "java.sql.ResultSet",
            "java.sql.SQLException",
        }

    def generate_handler_fields(self, file_name: str, organization: str) -> List[str]:
        table = _camel(file_name).upper()
        return [
            f'private static final String TABLE_NAME = "{table}";',
            "private Connection connection;",
            'private String fileStatus = "00";',
            "private ResultSet browseResultSet;",
        ]

    def generate_open(self, handler_var: str, mode: str, indent: str) -> List[str]:
        return [
            f'{indent}// VSAM OPEN {mode} → DB connection already active',
            f'{indent}{handler_var}.setMode("{mode}");',
        ]

    def generate_close(self, handler_var: str, indent: str) -> List[str]:
        return [
            f"{indent}// VSAM CLOSE → commit pending changes",
            f"{indent}{handler_var}.commitAndClose();",
        ]

    def generate_read(self, handler_var: str, record_var: str, indent: str) -> List[str]:
        return [
            f"{indent}// VSAM READ → SELECT by primary key",
            f"{indent}String {record_var} = {handler_var}.readByKey(key);",
        ]

    def generate_write(self, handler_var: str, record_expr: str, indent: str) -> List[str]:
        return [
            f"{indent}// VSAM WRITE → INSERT INTO table",
            f"{indent}{handler_var}.insertRecord({record_expr});",
        ]

    def generate_handler_class_body(
        self, class_name: str, file_name: str,
        organization: str, indent: str
    ) -> List[str]:
        i2 = indent * 2
        lines = []
        lines.append(f"{indent}private String mode;")
        lines.append("")
        lines.append(f"{indent}public void setMode(String mode) {{")
        lines.append(f"{i2}this.mode = mode;")
        lines.append(f"{indent}}}")
        lines.append("")
        lines.append(f"{indent}public String readByKey(String key) throws SQLException {{")
        lines.append(f'{i2}PreparedStatement ps = connection.prepareStatement(')
        lines.append(f'{i2}    "SELECT * FROM " + TABLE_NAME + " WHERE RECORD_KEY = ?");')
        lines.append(f"{i2}ps.setString(1, key);")
        lines.append(f"{i2}ResultSet rs = ps.executeQuery();")
        lines.append(f"{i2}if (rs.next()) {{")
        lines.append(f'{i2}    fileStatus = "00";')
        lines.append(f"{i2}    return rs.getString(1);")
        lines.append(f"{i2}}} else {{")
        lines.append(f'{i2}    fileStatus = "23"; // RECORD NOT FOUND')
        lines.append(f"{i2}    return null;")
        lines.append(f"{i2}}}")
        lines.append(f"{indent}}}")
        lines.append("")
        lines.append(f"{indent}public void insertRecord(String record) throws SQLException {{")
        lines.append(f'{i2}PreparedStatement ps = connection.prepareStatement(')
        lines.append(f'{i2}    "INSERT INTO " + TABLE_NAME + " (RECORD_DATA) VALUES (?)");')
        lines.append(f"{i2}ps.setString(1, record);")
        lines.append(f"{i2}ps.executeUpdate();")
        lines.append(f'{i2}fileStatus = "00";')
        lines.append(f"{indent}}}")
        lines.append("")
        lines.append(f"{indent}public void commitAndClose() throws SQLException {{")
        lines.append(f"{i2}if (browseResultSet != null) browseResultSet.close();")
        lines.append(f"{i2}connection.commit();")
        lines.append(f'{i2}fileStatus = "00";')
        lines.append(f"{indent}}}")
        lines.append("")
        lines.append(f"{indent}public String getFileStatus() {{")
        lines.append(f"{i2}return fileStatus;")
        lines.append(f"{indent}}}")
        return lines


# ============================================================
# JPA/Hibernate SQL Strategy (拡張例)
# ============================================================

class JpaSqlStrategy(SqlConversionStrategy):
    """EXEC SQL → JPA/Hibernate EntityManager 変換.

    JDBCではなくEntityManager経由でORM操作を行う。
    """

    def generate_imports(self) -> Set[str]:
        return {
            "javax.persistence.EntityManager",
            "javax.persistence.EntityManagerFactory",
            "javax.persistence.Persistence",
            "javax.persistence.Query",
            "javax.persistence.TypedQuery",
        }

    def generate_fields(self, indent: str) -> List[str]:
        return [
            f"{indent}private EntityManagerFactory emf = Persistence.createEntityManagerFactory(\"migrated-pu\");",
            f"{indent}private EntityManager em = emf.createEntityManager();",
            f"{indent}private int sqlCode = 0;",
        ]

    def generate_select(
        self, sql: str, host_vars: List[str],
        into_vars: List[str], indent: str
    ) -> List[str]:
        import re
        # Convert to JPQL-style
        jpql = re.sub(r':([A-Za-z0-9-]+)', lambda m: ':' + _camel(m.group(1)), sql)
        lines = [
            f'{indent}Query query = em.createNativeQuery("{jpql}");',
        ]
        for hv in host_vars:
            if _camel(hv) not in [_camel(v) for v in into_vars]:
                lines.append(f'{indent}query.setParameter("{_camel(hv)}", {_camel(hv)});')
        lines.append(f"{indent}Object[] result = (Object[]) query.getSingleResult();")
        for i, var in enumerate(into_vars):
            lines.append(f"{indent}{_camel(var)} = result[{i}];")
        return lines

    def generate_insert_update_delete(
        self, sql: str, host_vars: List[str], indent: str
    ) -> List[str]:
        import re
        jpql = re.sub(r':([A-Za-z0-9-]+)', lambda m: ':' + _camel(m.group(1)), sql)
        lines = [
            f"{indent}em.getTransaction().begin();",
            f'{indent}Query query = em.createNativeQuery("{jpql}");',
        ]
        for hv in host_vars:
            lines.append(f'{indent}query.setParameter("{_camel(hv)}", {_camel(hv)});')
        lines.append(f"{indent}int affectedRows = query.executeUpdate();")
        lines.append(f"{indent}em.getTransaction().commit();")
        return lines

    def generate_cursor_declare(
        self, cursor_name: str, select_sql: str, indent: str
    ) -> List[str]:
        name = _camel(cursor_name)
        return [f'{indent}String {name}Jpql = "{select_sql}";']

    def generate_cursor_open(
        self, cursor_name: str, host_vars: List[str], indent: str
    ) -> List[str]:
        name = _camel(cursor_name)
        lines = [
            f"{indent}Query {name}Query = em.createNativeQuery({name}Jpql);",
        ]
        for hv in host_vars:
            lines.append(f'{indent}{name}Query.setParameter("{_camel(hv)}", {_camel(hv)});')
        lines.append(f"{indent}java.util.List {name}Results = {name}Query.getResultList();")
        lines.append(f"{indent}java.util.Iterator {name}Iter = {name}Results.iterator();")
        return lines

    def generate_cursor_fetch(
        self, cursor_name: str, into_vars: List[str], indent: str
    ) -> List[str]:
        name = _camel(cursor_name)
        lines = [f"{indent}if ({name}Iter.hasNext()) {{"]
        lines.append(f"{indent}    Object[] row = (Object[]) {name}Iter.next();")
        for i, var in enumerate(into_vars):
            lines.append(f"{indent}    {_camel(var)} = row[{i}];")
        lines.append(f"{indent}}} else {{")
        lines.append(f"{indent}    sqlCode = 100; // NOT FOUND")
        lines.append(f"{indent}}}")
        return lines

    def generate_cursor_close(
        self, cursor_name: str, indent: str
    ) -> List[str]:
        name = _camel(cursor_name)
        return [f"{indent}{name}Results = null; // Cursor closed"]

    def generate_commit(self, indent: str) -> List[str]:
        return [f"{indent}em.getTransaction().commit();"]

    def generate_rollback(self, indent: str) -> List[str]:
        return [f"{indent}em.getTransaction().rollback();"]


# ============================================================
# Strategy Registry
# ============================================================

class ConversionStrategyRegistry:
    """変換戦略のレジストリ。デフォルト戦略を提供し、差し替え可能。"""

    def __init__(self):
        self._file_io: FileIoStrategy = DefaultFileIoStrategy()
        self._sql: SqlConversionStrategy = JdbcSqlStrategy()
        self._cics: CicsConversionStrategy = DefaultCicsStrategy()

    @property
    def file_io(self) -> FileIoStrategy:
        return self._file_io

    @file_io.setter
    def file_io(self, strategy: FileIoStrategy):
        self._file_io = strategy

    @property
    def sql(self) -> SqlConversionStrategy:
        return self._sql

    @sql.setter
    def sql(self, strategy: SqlConversionStrategy):
        self._sql = strategy

    @property
    def cics(self) -> CicsConversionStrategy:
        return self._cics

    @cics.setter
    def cics(self, strategy: CicsConversionStrategy):
        self._cics = strategy


# Global default registry
_default_registry = ConversionStrategyRegistry()


def get_default_registry() -> ConversionStrategyRegistry:
    """デフォルトのレジストリを返す."""
    return _default_registry
