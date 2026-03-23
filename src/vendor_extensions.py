"""
Vendor-Specific COBOL Extensions Module
世界各メーカー独自のCOBOL方言を処理する

対応メーカー:
  - IBM       : Enterprise COBOL / z/OS COBOL (EXEC CICS, EXEC SQL, EXEC DLI, COMP-5)
  - Fujitsu   : NetCOBOL (SCREEN SECTION, PIC N, FORMAT)
  - NEC       : ACOS-4 COBOL (ACOS固有ファイル, 独自ACCEPT/DISPLAY)
  - Hitachi   : VOS3/COBOL2002 (OO拡張, 独自PIC句)
  - MicroFocus: Visual COBOL (OO COBOL, .NET/JVM, Embedded SQL)
  - Unisys    : MCP/ClearPath COBOL (独自IO, SCREEN)
  - Bull/Atos : GCOS COBOL (GCOS固有拡張)
  - HP/Tandem : NonStop COBOL (GUARDIAN, TAL連携)
  - GnuCOBOL  : OpenCOBOL / GnuCOBOL (OSS拡張)
  - standard  : COBOL-85 / COBOL-2002 / COBOL-2014 標準準拠
"""
import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum


class VendorType(Enum):
    STANDARD = "standard"
    IBM = "ibm"
    FUJITSU = "fujitsu"
    NEC = "nec"
    HITACHI = "hitachi"
    MICRO_FOCUS = "microfocus"
    UNISYS = "unisys"
    BULL_ATOS = "bull"
    HP_TANDEM = "hp"
    GNU_COBOL = "gnucobol"
    AUTO_DETECT = "auto"


VENDOR_DISPLAY_NAMES = {
    VendorType.STANDARD: "COBOL Standard (COBOL-85/2002/2014)",
    VendorType.IBM: "IBM Enterprise COBOL (z/OS, AS/400)",
    VendorType.FUJITSU: "Fujitsu NetCOBOL (PRIMERGY/PRIMEQUEST)",
    VendorType.NEC: "NEC ACOS COBOL (ACOS-4/ACOS-2)",
    VendorType.HITACHI: "Hitachi VOS3 COBOL / COBOL2002",
    VendorType.MICRO_FOCUS: "Micro Focus Visual COBOL",
    VendorType.UNISYS: "Unisys MCP/ClearPath COBOL",
    VendorType.BULL_ATOS: "Bull/Atos GCOS COBOL",
    VendorType.HP_TANDEM: "HP NonStop COBOL (Tandem)",
    VendorType.GNU_COBOL: "GnuCOBOL (OpenCOBOL)",
    VendorType.AUTO_DETECT: "Auto Detect",
}


# ======================================================================
#  Embedded block definitions (EXEC ... END-EXEC)
# ======================================================================
@dataclass
class ExecBlock:
    """Represents an EXEC ... END-EXEC block."""
    exec_type: str  # CICS, SQL, DLI, HTML, etc.
    command: str     # The command verb (e.g. SEND, RECEIVE, SELECT)
    raw_text: str
    parameters: Dict[str, str] = field(default_factory=dict)


# ======================================================================
#  Vendor-specific data type extensions
# ======================================================================
VENDOR_PIC_TYPES: Dict[VendorType, Dict[str, str]] = {
    VendorType.IBM: {
        # COMP-5: native binary (same as platform int)
        "COMP-5": "int",
        # POINTER / FUNCTION-POINTER / PROCEDURE-POINTER
        "POINTER": "long",
        "FUNCTION-POINTER": "long",
        "PROCEDURE-POINTER": "long",
        # DISPLAY-1 (DBCS)
        "DISPLAY-1": "String",
        # NATIONAL (Unicode)
        "NATIONAL": "String",
        # XML-TEXT / XML-NTEXT
        "XML-TEXT": "String",
        "XML-NTEXT": "String",
    },
    VendorType.FUJITSU: {
        # PIC N (Japanese DBCS / National characters)
        "NATIONAL": "String",
        # NC (National Character)
        "NC": "String",
        # COMP-5
        "COMP-5": "int",
        # COMP-X (unsigned native binary)
        "COMP-X": "int",
    },
    VendorType.NEC: {
        "COMP-5": "int",
        "NATIONAL": "String",
        # NEC-specific KANJI type
        "KANJI": "String",
    },
    VendorType.HITACHI: {
        "COMP-5": "int",
        "NATIONAL": "String",
        # Hitachi-specific object reference
        "OBJECT-REFERENCE": "Object",
    },
    VendorType.MICRO_FOCUS: {
        "COMP-5": "int",
        "COMP-X": "int",
        "POINTER": "long",
        "NATIONAL": "String",
        # MF-specific binary types
        "BINARY-CHAR": "byte",
        "BINARY-SHORT": "short",
        "BINARY-LONG": "int",
        "BINARY-DOUBLE": "long",
        # Float types
        "FLOAT-SHORT": "float",
        "FLOAT-LONG": "double",
        "FLOAT-EXTENDED": "double",
    },
    VendorType.UNISYS: {
        "COMP-5": "int",
        "NATIONAL": "String",
    },
    VendorType.HP_TANDEM: {
        "COMP-5": "int",
        "NATIVE-2": "short",
        "NATIVE-4": "int",
        "NATIVE-8": "long",
    },
    VendorType.GNU_COBOL: {
        "COMP-5": "int",
        "COMP-X": "int",
        "POINTER": "long",
        "BINARY-C-LONG": "long",
        "FLOAT-SHORT": "float",
        "FLOAT-LONG": "double",
    },
}

# PIC N → String mapping (Japanese/Chinese double-byte)
PIC_N_VENDORS = {VendorType.FUJITSU, VendorType.NEC, VendorType.HITACHI, VendorType.IBM}


# ======================================================================
#  EXEC block parsers
# ======================================================================
def parse_exec_block(text: str) -> Optional[ExecBlock]:
    """Parse an EXEC ... END-EXEC block into structured data."""
    match = re.match(
        r'EXEC\s+(\w+)\s+(.*?)\s*END-EXEC',
        text, re.IGNORECASE | re.DOTALL
    )
    if not match:
        return None

    exec_type = match.group(1).upper()
    body = match.group(2).strip()

    if exec_type == "SQL":
        return _parse_exec_sql(body, text)
    elif exec_type == "CICS":
        return _parse_exec_cics(body, text)
    elif exec_type == "DLI":
        return _parse_exec_dli(body, text)
    else:
        return ExecBlock(exec_type=exec_type, command=body.split()[0] if body else "",
                         raw_text=text, parameters={"body": body})


def _parse_exec_sql(body: str, raw: str) -> ExecBlock:
    """Parse EXEC SQL block."""
    parts = body.strip().split()
    command = parts[0].upper() if parts else "UNKNOWN"

    params = {"sql": body}

    # Detect SQL type
    if command in ("SELECT", "INSERT", "UPDATE", "DELETE", "MERGE"):
        params["type"] = "DML"
    elif command in ("CREATE", "ALTER", "DROP", "TRUNCATE"):
        params["type"] = "DDL"
    elif command in ("DECLARE", "OPEN", "CLOSE", "FETCH"):
        params["type"] = "CURSOR"
    elif command == "INCLUDE":
        params["type"] = "INCLUDE"
        if len(parts) > 1:
            params["copybook"] = parts[1]
    elif command == "BEGIN":
        params["type"] = "TRANSACTION"
    elif command in ("COMMIT", "ROLLBACK"):
        params["type"] = "TRANSACTION"
    elif command == "WHENEVER":
        params["type"] = "ERROR_HANDLING"
    else:
        params["type"] = "OTHER"

    # Extract host variables (:variable-name)
    host_vars = re.findall(r':([A-Za-z0-9-]+)', body)
    if host_vars:
        params["host_variables"] = ",".join(host_vars)

    return ExecBlock(exec_type="SQL", command=command, raw_text=raw, parameters=params)


def _parse_exec_cics(body: str, raw: str) -> ExecBlock:
    """Parse EXEC CICS block (IBM specific)."""
    parts = body.strip().split()
    command = parts[0].upper() if parts else "UNKNOWN"

    params = {"cics_body": body}

    # Parse CICS parameters (KEY(VALUE) format)
    for m in re.finditer(r'(\w+)\s*\(([^)]*)\)', body):
        params[m.group(1).upper()] = m.group(2).strip()

    # Classify CICS command
    if command in ("SEND", "RECEIVE"):
        params["type"] = "TERMINAL_IO"
    elif command in ("READ", "WRITE", "REWRITE", "DELETE", "STARTBR", "READNEXT", "READPREV", "ENDBR", "UNLOCK"):
        params["type"] = "FILE_IO"
    elif command in ("LINK", "XCTL", "RETURN", "LOAD", "RELEASE"):
        params["type"] = "PROGRAM_CONTROL"
    elif command in ("GETMAIN", "FREEMAIN"):
        params["type"] = "STORAGE"
    elif command in ("SYNCPOINT", "ABEND"):
        params["type"] = "TRANSACTION"
    elif command in ("START", "CANCEL", "RETRIEVE"):
        params["type"] = "INTERVAL_CONTROL"
    elif command in ("ASKTIME", "FORMATTIME"):
        params["type"] = "TIME"
    elif command in ("ENQ", "DEQ"):
        params["type"] = "QUEUE"
    elif command in ("WRITEQ", "READQ", "DELETEQ"):
        params["type"] = "TEMP_STORAGE"
    elif command == "HANDLE":
        # Detect HANDLE subtype (CONDITION, AID, ABEND)
        handle_sub = parts[1].upper() if len(parts) > 1 else ""
        if handle_sub == "CONDITION":
            params["type"] = "HANDLE_CONDITION"
        elif handle_sub == "AID":
            params["type"] = "HANDLE_AID"
        elif handle_sub == "ABEND":
            params["type"] = "HANDLE_ABEND"
        else:
            params["type"] = "ERROR_HANDLING"
    elif command == "IGNORE":
        params["type"] = "ERROR_HANDLING"
    elif command == "ASSIGN":
        params["type"] = "ASSIGN"
    elif command == "INQUIRE":
        params["type"] = "INQUIRE"
    elif command == "ADDRESS":
        params["type"] = "ADDRESS"
    elif command == "SET":
        params["type"] = "CICS_SET"
    else:
        params["type"] = "OTHER"

    return ExecBlock(exec_type="CICS", command=command, raw_text=raw, parameters=params)


def _parse_exec_dli(body: str, raw: str) -> ExecBlock:
    """Parse EXEC DLI block (IBM IMS)."""
    parts = body.strip().split()
    command = parts[0].upper() if parts else "UNKNOWN"
    params = {"dli_body": body, "type": "IMS"}

    for m in re.finditer(r'(\w+)\s*\(([^)]*)\)', body):
        params[m.group(1).upper()] = m.group(2).strip()

    return ExecBlock(exec_type="DLI", command=command, raw_text=raw, parameters=params)


# ======================================================================
#  Java code generation for vendor-specific constructs
# ======================================================================
def generate_exec_sql_java(block: ExecBlock, indent: str) -> List[str]:
    """Generate Java code for EXEC SQL."""
    lines = []
    sql_type = block.parameters.get("type", "OTHER")
    sql = block.parameters.get("sql", "")
    host_vars = block.parameters.get("host_variables", "").split(",")
    host_vars = [v.strip() for v in host_vars if v.strip()]

    def _camel(name):
        parts = name.lower().replace("_", "-").split("-")
        return parts[0] + "".join(p.capitalize() for p in parts[1:]) if parts else name

    lines.append(f"{indent}// EXEC SQL: {block.command}")

    if sql_type == "CURSOR" and block.command == "DECLARE":
        cursor_match = re.search(r'DECLARE\s+(\S+)\s+CURSOR\s+FOR\s+(.*)', sql, re.IGNORECASE | re.DOTALL)
        if cursor_match:
            cursor_name = _camel(cursor_match.group(1))
            select_sql = cursor_match.group(2).strip().rstrip(".")
            lines.append(f'{indent}String {cursor_name}Sql = "{select_sql}";')
        return lines

    if sql_type == "CURSOR" and block.command == "OPEN":
        cursor_match = re.search(r'OPEN\s+(\S+)', sql, re.IGNORECASE)
        if cursor_match:
            name = _camel(cursor_match.group(1))
            lines.append(f"{indent}PreparedStatement {name}Stmt = connection.prepareStatement({name}Sql);")
            for i, hv in enumerate(host_vars, 1):
                lines.append(f"{indent}{name}Stmt.setObject({i}, {_camel(hv)});")
            lines.append(f"{indent}ResultSet {name}Rs = {name}Stmt.executeQuery();")
        return lines

    if sql_type == "CURSOR" and block.command == "FETCH":
        cursor_match = re.search(r'FETCH\s+(\S+)\s+INTO\s+(.*)', sql, re.IGNORECASE | re.DOTALL)
        if cursor_match:
            name = _camel(cursor_match.group(1))
            into_vars = [_camel(v.strip().lstrip(":")) for v in cursor_match.group(2).split(",")]
            lines.append(f"{indent}if ({name}Rs.next()) {{")
            for i, var in enumerate(into_vars, 1):
                lines.append(f"{indent}    {var} = {name}Rs.getObject({i});")
            lines.append(f"{indent}}} else {{")
            lines.append(f"{indent}    sqlCode = 100; // NOT FOUND")
            lines.append(f"{indent}}}")
        return lines

    if sql_type == "CURSOR" and block.command == "CLOSE":
        cursor_match = re.search(r'CLOSE\s+(\S+)', sql, re.IGNORECASE)
        if cursor_match:
            name = _camel(cursor_match.group(1))
            lines.append(f"{indent}{name}Rs.close();")
            lines.append(f"{indent}{name}Stmt.close();")
        return lines

    if block.command == "SELECT":
        # SELECT ... INTO :var1, :var2 FROM ...
        into_match = re.search(r'SELECT\s+(.*?)\s+INTO\s+(.*?)\s+FROM\s+(.*)', sql, re.IGNORECASE | re.DOTALL)
        if into_match:
            select_cols = into_match.group(1).strip()
            into_vars = [_camel(v.strip().lstrip(":")) for v in into_match.group(2).split(",")]
            from_clause = into_match.group(3).strip().rstrip(".")

            clean_sql = f"SELECT {select_cols} FROM {from_clause}"
            clean_sql = re.sub(r':([A-Za-z0-9-]+)', '?', clean_sql)

            lines.append(f'{indent}PreparedStatement pstmt = connection.prepareStatement("{clean_sql}");')
            for i, hv in enumerate(host_vars, 1):
                if hv not in [v.lower().replace("-", "") for v in into_match.group(2).replace(":", "").split(",")]:
                    lines.append(f"{indent}pstmt.setObject({i}, {_camel(hv)});")
            lines.append(f"{indent}ResultSet rs = pstmt.executeQuery();")
            lines.append(f"{indent}if (rs.next()) {{")
            for i, var in enumerate(into_vars, 1):
                lines.append(f"{indent}    {var} = rs.getObject({i});")
            lines.append(f"{indent}}}")
            lines.append(f"{indent}rs.close();")
            lines.append(f"{indent}pstmt.close();")
        return lines

    if block.command in ("INSERT", "UPDATE", "DELETE"):
        clean_sql = re.sub(r':([A-Za-z0-9-]+)', '?', sql).rstrip(".")
        lines.append(f'{indent}PreparedStatement pstmt = connection.prepareStatement("{clean_sql}");')
        for i, hv in enumerate(host_vars, 1):
            lines.append(f"{indent}pstmt.setObject({i}, {_camel(hv)});")
        lines.append(f"{indent}int affectedRows = pstmt.executeUpdate();")
        lines.append(f"{indent}pstmt.close();")
        return lines

    if block.command in ("COMMIT", "ROLLBACK"):
        lines.append(f"{indent}connection.{block.command.lower()}();")
        return lines

    if sql_type == "INCLUDE":
        copybook = block.parameters.get("copybook", "SQLCA")
        lines.append(f"{indent}// SQL INCLUDE {copybook}")
        if copybook.upper() == "SQLCA":
            lines.append(f"{indent}int sqlCode = 0;")
            lines.append(f"{indent}String sqlState = \"00000\";")
        return lines

    if sql_type == "ERROR_HANDLING":
        lines.append(f"{indent}// SQL WHENEVER - handled by try/catch")
        return lines

    # Fallback
    lines.append(f'{indent}// TODO: Translate SQL: {sql[:80]}...')
    return lines


def generate_exec_cics_java(block: ExecBlock, indent: str) -> List[str]:
    """Generate Java code for EXEC CICS."""
    lines = []
    cmd = block.command
    params = block.parameters
    cics_type = params.get("type", "OTHER")

    lines.append(f"{indent}// EXEC CICS {cmd}")

    if cics_type == "TERMINAL_IO":
        if cmd == "SEND":
            mapset = params.get("MAPSET", "mapset")
            map_name = params.get("MAP", "map")
            from_var = params.get("FROM", "data")
            lines.append(f'{indent}cicsTerminal.sendMap("{mapset}", "{map_name}", {_to_camel(from_var)});')
        elif cmd == "RECEIVE":
            map_name = params.get("MAP", "map")
            into_var = params.get("INTO", "data")
            lines.append(f'{indent}{_to_camel(into_var)} = cicsTerminal.receiveMap("{map_name}");')

    elif cics_type == "FILE_IO":
        dataset = params.get("DATASET", params.get("FILE", "file"))
        if cmd == "READ":
            into_var = params.get("INTO", "record")
            ridfld = params.get("RIDFLD", "key")
            lines.append(f'{indent}{_to_camel(into_var)} = cicsFile.read("{dataset}", {_to_camel(ridfld)});')
        elif cmd == "WRITE":
            from_var = params.get("FROM", "record")
            ridfld = params.get("RIDFLD", "key")
            lines.append(f'{indent}cicsFile.write("{dataset}", {_to_camel(ridfld)}, {_to_camel(from_var)});')
        elif cmd == "REWRITE":
            from_var = params.get("FROM", "record")
            lines.append(f'{indent}cicsFile.rewrite("{dataset}", {_to_camel(from_var)});')
        elif cmd == "DELETE":
            ridfld = params.get("RIDFLD", "key")
            lines.append(f'{indent}cicsFile.delete("{dataset}", {_to_camel(ridfld)});')
        elif cmd == "STARTBR":
            ridfld = params.get("RIDFLD", "key")
            lines.append(f'{indent}cicsFile.startBrowse("{dataset}", {_to_camel(ridfld)});')
        elif cmd in ("READNEXT", "READPREV"):
            into_var = params.get("INTO", "record")
            method = "readNext" if cmd == "READNEXT" else "readPrev"
            lines.append(f'{indent}{_to_camel(into_var)} = cicsFile.{method}("{dataset}");')
        elif cmd == "ENDBR":
            lines.append(f'{indent}cicsFile.endBrowse("{dataset}");')

    elif cics_type == "PROGRAM_CONTROL":
        if cmd == "LINK":
            program = params.get("PROGRAM", "subprogram")
            commarea = params.get("COMMAREA", "")
            if commarea:
                lines.append(f'{indent}cicsProgram.link("{program}", {_to_camel(commarea)});')
            else:
                lines.append(f'{indent}cicsProgram.link("{program}");')
        elif cmd == "XCTL":
            program = params.get("PROGRAM", "nextprogram")
            lines.append(f'{indent}cicsProgram.transferControl("{program}");')
            lines.append(f'{indent}return;')
        elif cmd == "RETURN":
            transid = params.get("TRANSID", "")
            if transid:
                lines.append(f'{indent}cicsProgram.returnToTransaction("{transid}");')
            else:
                lines.append(f'{indent}return;')

    elif cics_type == "TEMP_STORAGE":
        queue = params.get("QUEUE", params.get("TD", "queue"))
        if cmd == "WRITEQ":
            from_var = params.get("FROM", "data")
            lines.append(f'{indent}cicsTempStorage.writeQueue("{queue}", {_to_camel(from_var)});')
        elif cmd == "READQ":
            into_var = params.get("INTO", "data")
            lines.append(f'{indent}{_to_camel(into_var)} = cicsTempStorage.readQueue("{queue}");')
        elif cmd == "DELETEQ":
            lines.append(f'{indent}cicsTempStorage.deleteQueue("{queue}");')

    elif cics_type == "TRANSACTION":
        if cmd == "SYNCPOINT":
            lines.append(f'{indent}cicsTransaction.syncpoint();')
        elif cmd == "ABEND":
            abcode = params.get("ABCODE", "XXXX")
            lines.append(f'{indent}throw new CicsAbendException("{abcode}");')

    elif cics_type == "TIME":
        if cmd == "ASKTIME":
            abstime = params.get("ABSTIME", "absTime")
            lines.append(f'{indent}long {_to_camel(abstime)} = System.currentTimeMillis();')
        elif cmd == "FORMATTIME":
            abstime = params.get("ABSTIME", "absTime")
            lines.append(f'{indent}String formattedTime = new java.text.SimpleDateFormat("yyyy-MM-dd HH:mm:ss").format(new java.util.Date({_to_camel(abstime)}));')

    elif cics_type == "HANDLE_CONDITION":
        # EXEC CICS HANDLE CONDITION ERROR(label) NOTFND(label) ...
        lines.append(f"{indent}// CICS HANDLE CONDITION - exception handler registration")
        for key, val in params.items():
            if key not in ("type", "cics_body") and val:
                handler = _to_camel(val)
                lines.append(f'{indent}cicsExceptionHandler.register("{key}", () -> {handler}());')

    elif cics_type == "HANDLE_AID":
        # EXEC CICS HANDLE AID PF1(label) PF3(label) ENTER(label) CLEAR(label) ...
        lines.append(f"{indent}// CICS HANDLE AID - attention key handler registration")
        for key, val in params.items():
            if key not in ("type", "cics_body") and val:
                handler = _to_camel(val)
                lines.append(f'{indent}cicsAidHandler.register("{key}", () -> {handler}());')

    elif cics_type == "HANDLE_ABEND":
        # EXEC CICS HANDLE ABEND PROGRAM(name) or LABEL(name)
        program = params.get("PROGRAM", "")
        label = params.get("LABEL", "")
        if program:
            lines.append(f'{indent}cicsAbendHandler.setProgram("{program}");')
        elif label:
            lines.append(f'{indent}cicsAbendHandler.setLabel(() -> {_to_camel(label)}());')
        else:
            lines.append(f"{indent}cicsAbendHandler.reset();")

    elif cics_type == "STORAGE":
        if cmd == "GETMAIN":
            set_var = params.get("SET", "ptr")
            length = params.get("LENGTH", params.get("FLENGTH", "256"))
            lines.append(f"{indent}byte[] {_to_camel(set_var)} = new byte[{length}];")
        elif cmd == "FREEMAIN":
            data_var = params.get("DATA", params.get("DATAPOINTER", "ptr"))
            lines.append(f"{indent}{_to_camel(data_var)} = null; // FREEMAIN")

    elif cics_type == "INTERVAL_CONTROL":
        if cmd == "START":
            transid = params.get("TRANSID", "txn")
            lines.append(f'{indent}cicsIntervalControl.startTransaction("{transid}");')
        elif cmd == "CANCEL":
            reqid = params.get("REQID", "req")
            lines.append(f'{indent}cicsIntervalControl.cancel("{reqid}");')
        elif cmd == "RETRIEVE":
            into_var = params.get("INTO", "data")
            lines.append(f'{indent}{_to_camel(into_var)} = cicsIntervalControl.retrieve();')

    elif cics_type == "QUEUE":
        queue = params.get("QUEUE", params.get("RESOURCE", "queue"))
        if cmd == "ENQ":
            lines.append(f'{indent}cicsQueue.enqueue("{queue}");')
        elif cmd == "DEQ":
            lines.append(f'{indent}cicsQueue.dequeue("{queue}");')

    elif cics_type == "ASSIGN":
        # EXEC CICS ASSIGN SYSID(var) USERID(var) ...
        lines.append(f"{indent}// CICS ASSIGN - system value retrieval")
        for key, val in params.items():
            if key not in ("type", "cics_body") and val:
                lines.append(f'{indent}{_to_camel(val)} = cicsSystem.getAssignValue("{key}");')

    elif cics_type == "INQUIRE":
        # EXEC CICS INQUIRE FILE(name) STATUS(var) ...
        lines.append(f"{indent}// CICS INQUIRE - resource status inquiry")
        resource_name = params.get("FILE", params.get("PROGRAM", params.get("TRANSACTION", "resource")))
        for key, val in params.items():
            if key not in ("type", "cics_body", "FILE", "PROGRAM", "TRANSACTION") and val:
                lines.append(f'{indent}{_to_camel(val)} = cicsSystem.inquire("{resource_name}", "{key}");')

    elif cics_type == "ADDRESS":
        # EXEC CICS ADDRESS CSA(ptr) CWA(ptr) TWA(ptr) ...
        lines.append(f"{indent}// CICS ADDRESS - address retrieval")
        for key, val in params.items():
            if key not in ("type", "cics_body") and val:
                lines.append(f'{indent}{_to_camel(val)} = cicsSystem.getAddress("{key}");')

    elif cics_type == "CICS_SET":
        # EXEC CICS SET FILE(name) ENABLED/DISABLED ...
        lines.append(f"{indent}// CICS SET - resource modification")
        resource = params.get("FILE", params.get("PROGRAM", params.get("TRANSACTION", "resource")))
        lines.append(f'{indent}cicsSystem.setResource("{resource}", params);')

    elif cics_type == "ERROR_HANDLING":
        # EXEC CICS IGNORE CONDITION ...
        lines.append(f"{indent}// CICS error handling - {cmd}")
        lines.append(f"{indent}// Handled by try/catch in Java")

    else:
        lines.append(f"{indent}// TODO: CICS {cmd} - manual conversion required")
        lines.append(f"{indent}// {block.raw_text[:100]}")

    return lines


def generate_exec_dli_java(block: ExecBlock, indent: str) -> List[str]:
    """Generate Java code for EXEC DLI (IMS)."""
    lines = [
        f"{indent}// EXEC DLI {block.command} (IMS Database)",
        f"{indent}// TODO: Convert IMS DL/I call to JPA/Hibernate",
        f"{indent}// Original: {block.raw_text[:100]}",
    ]
    return lines


def _to_camel(cobol_name: str) -> str:
    name = cobol_name.strip().strip("'\"")
    if not name or not re.match(r'^[A-Za-z]', name):
        return name
    parts = name.lower().replace("_", "-").split("-")
    return parts[0] + "".join(p.capitalize() for p in parts[1:]) if parts else name


# ======================================================================
#  Vendor-specific PIC N handling (Japanese/CJK double-byte)
# ======================================================================
def is_pic_n(picture: str, vendor: VendorType) -> bool:
    """Check if PIC clause uses N (National/DBCS) type."""
    if vendor not in PIC_N_VENDORS and vendor != VendorType.STANDARD:
        return False
    pic = picture.upper().replace(" ", "")
    return bool(re.match(r'^N+$', re.sub(r'N\((\d+)\)', lambda m: 'N' * int(m.group(1)), pic)))


# ======================================================================
#  Fujitsu NetCOBOL: SCREEN SECTION handling
# ======================================================================
@dataclass
class ScreenField:
    level: int
    name: str
    line: int = 0
    col: int = 0
    pic: str = ""
    value: str = ""
    from_field: str = ""
    to_field: str = ""
    attribute: str = ""  # HIGHLIGHT, REVERSE-VIDEO, UNDERLINE, etc.


def parse_screen_section_item(line: str) -> Optional[ScreenField]:
    """Parse a SCREEN SECTION data item."""
    match = re.match(r'(\d{1,2})\s+(\S+)(.*)', line)
    if not match:
        return None

    field = ScreenField(level=int(match.group(1)), name=match.group(2).rstrip("."))
    rest = match.group(3)

    line_match = re.search(r'LINE\s+(?:NUMBER\s+IS\s+)?(\d+)', rest, re.IGNORECASE)
    if line_match:
        field.line = int(line_match.group(1))

    col_match = re.search(r'COL(?:UMN)?\s+(?:NUMBER\s+IS\s+)?(\d+)', rest, re.IGNORECASE)
    if col_match:
        field.col = int(col_match.group(1))

    pic_match = re.search(r'PIC(?:TURE)?\s+(?:IS\s+)?(\S+)', rest, re.IGNORECASE)
    if pic_match:
        field.pic = pic_match.group(1).rstrip(".")

    val_match = re.search(r'VALUE\s+(?:IS\s+)?(.*?)(?:\s+LINE|\s+COL|\s+PIC|\s+FROM|\s+TO|$)', rest, re.IGNORECASE)
    if val_match:
        field.value = val_match.group(1).strip().strip("'\"").rstrip(".")

    from_match = re.search(r'FROM\s+(\S+)', rest, re.IGNORECASE)
    if from_match:
        field.from_field = from_match.group(1).rstrip(".")

    to_match = re.search(r'TO\s+(\S+)', rest, re.IGNORECASE)
    if to_match:
        field.to_field = to_match.group(1).rstrip(".")

    for attr in ["HIGHLIGHT", "REVERSE-VIDEO", "UNDERLINE", "BLINK", "BLANK WHEN ZERO"]:
        if attr in rest.upper():
            field.attribute = attr
            break

    return field


def generate_screen_section_java(fields: List[ScreenField], class_name: str, indent: str) -> List[str]:
    """Generate a Java console UI class from SCREEN SECTION."""
    lines = [
        f"{indent}/**",
        f"{indent} * Screen UI class generated from COBOL SCREEN SECTION",
        f"{indent} */",
        f"{indent}public class {class_name}Screen {{",
        f"{indent}    private final java.util.Scanner scanner = new java.util.Scanner(System.in);",
        f"",
    ]

    # Display method
    lines.append(f"{indent}    public void display() {{")
    for f in fields:
        if f.value:
            lines.append(f'{indent}        System.out.println("{f.value}");')
        elif f.from_field:
            lines.append(f'{indent}        System.out.println({_to_camel(f.from_field)});')
    lines.append(f"{indent}    }}")
    lines.append(f"")

    # Accept method
    input_fields = [f for f in fields if f.to_field]
    if input_fields:
        lines.append(f"{indent}    public void accept() {{")
        for f in input_fields:
            label = f.name.replace("-", " ").title()
            lines.append(f'{indent}        System.out.print("{label}: ");')
            lines.append(f'{indent}        {_to_camel(f.to_field)} = scanner.nextLine();')
        lines.append(f"{indent}    }}")

    lines.append(f"{indent}}}")
    return lines


# ======================================================================
#  Auto-detection of vendor from source code
# ======================================================================
def detect_vendor(source_lines: List[str]) -> VendorType:
    """Analyze COBOL source to detect vendor dialect."""
    text = "\n".join(source_lines).upper()

    scores: Dict[VendorType, int] = {v: 0 for v in VendorType if v != VendorType.AUTO_DETECT}

    # IBM signatures
    if "EXEC CICS" in text:
        scores[VendorType.IBM] += 10
    if "EXEC SQL" in text:
        scores[VendorType.IBM] += 3
        scores[VendorType.MICRO_FOCUS] += 2
    if "EXEC DLI" in text:
        scores[VendorType.IBM] += 10
    if "DISPLAY-1" in text or "XML GENERATE" in text or "JSON GENERATE" in text:
        scores[VendorType.IBM] += 5
    if "XML PARSE" in text or "JSON PARSE" in text:
        scores[VendorType.IBM] += 5
    if "CHANNEL" in text and "CONTAINER" in text:
        scores[VendorType.IBM] += 5
    if "FUNCTION CURRENT-DATE" in text:
        scores[VendorType.IBM] += 1
    if "SERVICE SECTION" in text:
        scores[VendorType.IBM] += 3
    if "SQLCA" in text:
        scores[VendorType.IBM] += 2
    if "EIBCALEN" in text or "EIBTRNID" in text or "DFHCOMMAREA" in text:
        scores[VendorType.IBM] += 8
    if "CICS" in text and "HANDLE" in text:
        scores[VendorType.IBM] += 5

    # Fujitsu signatures
    if "SCREEN SECTION" in text:
        scores[VendorType.FUJITSU] += 5
        scores[VendorType.GNU_COBOL] += 3
        scores[VendorType.MICRO_FOCUS] += 2
    if re.search(r'PIC\s+N\(', text) or re.search(r'PIC\s+N+\b', text):
        scores[VendorType.FUJITSU] += 4
        scores[VendorType.NEC] += 3
        scores[VendorType.HITACHI] += 3
    if "FORMAT" in text and "PRINTING MODE" in text:
        scores[VendorType.FUJITSU] += 5
    if "CALL-CONVENTION" in text:
        scores[VendorType.FUJITSU] += 3
    if "PRINTER-CONTROL" in text or "FORMS-OVERLAY" in text:
        scores[VendorType.FUJITSU] += 5
    if "SYMBOLIC-TERMINAL" in text:
        scores[VendorType.FUJITSU] += 4

    # NEC signatures
    if "ACOS" in text:
        scores[VendorType.NEC] += 8
    if "DISPLAY-ALL" in text or "ACCEPT-ALL" in text:
        scores[VendorType.NEC] += 6
    if "AIM " in text and ("STORE" in text or "FETCH" in text):
        scores[VendorType.NEC] += 7
    if "READ-ALL" in text or "WRITE-ALL" in text:
        scores[VendorType.NEC] += 5

    # Hitachi signatures
    if "CLASS-ID" in text and "METHOD-ID" in text:
        scores[VendorType.HITACHI] += 4
        scores[VendorType.MICRO_FOCUS] += 3
    if "OBJECT-REFERENCE" in text:
        scores[VendorType.HITACHI] += 5
    if "INVOKE " in text and "SELF" in text:
        scores[VendorType.HITACHI] += 3
        scores[VendorType.MICRO_FOCUS] += 3
    if "VOS3" in text or "COBOL2002" in text:
        scores[VendorType.HITACHI] += 8

    # Micro Focus signatures
    if "CLASS-ID" in text:
        scores[VendorType.MICRO_FOCUS] += 3
    if "$SET" in text:
        scores[VendorType.MICRO_FOCUS] += 5
    if ">>DEFINE" in text:
        scores[VendorType.MICRO_FOCUS] += 3
        scores[VendorType.GNU_COBOL] += 3
    if "COMP-X" in text:
        scores[VendorType.MICRO_FOCUS] += 3
        scores[VendorType.GNU_COBOL] += 2
    if "BINARY-LONG" in text or "BINARY-SHORT" in text:
        scores[VendorType.MICRO_FOCUS] += 4
    if "FLOAT-SHORT" in text or "FLOAT-LONG" in text:
        scores[VendorType.MICRO_FOCUS] += 3
        scores[VendorType.GNU_COBOL] += 2
    if "ILUSING" in text or "ILSMARTLINKAGE" in text:
        scores[VendorType.MICRO_FOCUS] += 8

    # GnuCOBOL signatures
    if ">>SOURCE" in text:
        scores[VendorType.GNU_COBOL] += 5
    if "BINARY-C-LONG" in text:
        scores[VendorType.GNU_COBOL] += 5
    if re.search(r'CALL\s+["\']CBL_', text):
        scores[VendorType.GNU_COBOL] += 8
    if re.search(r'CALL\s+["\']CBL_OC_', text) or re.search(r'CALL\s+["\']CBL_GC_', text):
        scores[VendorType.GNU_COBOL] += 10
    if ">>TURN" in text or ">>LISTING" in text:
        scores[VendorType.GNU_COBOL] += 4

    # HP/Tandem signatures
    if "GUARDIAN" in text or "ENSCRIBE" in text:
        scores[VendorType.HP_TANDEM] += 8
    if "NATIVE-2" in text or "NATIVE-4" in text:
        scores[VendorType.HP_TANDEM] += 5
    if "ENTER TAL" in text or "ENTER COBOL" in text:
        scores[VendorType.HP_TANDEM] += 10
    if "NONSTOP" in text or "TANDEM" in text:
        scores[VendorType.HP_TANDEM] += 5
    if "PATHWAY" in text or "SERVERCLASS" in text:
        scores[VendorType.HP_TANDEM] += 6

    # Unisys signatures
    if "ALGOL" in text or "WFL" in text:
        scores[VendorType.UNISYS] += 5
    if "DMSII" in text:
        scores[VendorType.UNISYS] += 8
    if re.search(r'\bGIVE\b', text) and re.search(r'\bPORT\b', text):
        scores[VendorType.UNISYS] += 6
    if "MCP" in text and "CLEARPATH" in text:
        scores[VendorType.UNISYS] += 8
    if "CHANGE ATTRIBUTE" in text:
        scores[VendorType.UNISYS] += 5

    # Bull/Atos
    if "GCOS" in text:
        scores[VendorType.BULL_ATOS] += 8
    if "TP8" in text or "TDS " in text:
        scores[VendorType.BULL_ATOS] += 7
    if "IDSII" in text:
        scores[VendorType.BULL_ATOS] += 8

    # Find best match
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return VendorType.STANDARD

    return best


# ======================================================================
#  Vendor-specific extra imports for generated Java
# ======================================================================
# ======================================================================
#  GnuCOBOL CBL_* system routine mapping
# ======================================================================
GNUCOBOL_CBL_ROUTINES: Dict[str, Dict[str, str]] = {
    # File operations
    "CBL_OPEN_FILE": {"java": "new java.io.FileInputStream({0})", "desc": "Open file"},
    "CBL_CREATE_FILE": {"java": "new java.io.FileOutputStream({0})", "desc": "Create file"},
    "CBL_READ_FILE": {"java": "{0}.read({1}, 0, {2})", "desc": "Read from file"},
    "CBL_WRITE_FILE": {"java": "{0}.write({1}, 0, {2})", "desc": "Write to file"},
    "CBL_CLOSE_FILE": {"java": "{0}.close()", "desc": "Close file"},
    "CBL_DELETE_FILE": {"java": "new java.io.File({0}).delete()", "desc": "Delete file"},
    "CBL_RENAME_FILE": {"java": "new java.io.File({0}).renameTo(new java.io.File({1}))", "desc": "Rename file"},
    "CBL_CHECK_FILE_EXIST": {"java": "new java.io.File({0}).exists()", "desc": "Check file exists"},
    "CBL_COPY_FILE": {"java": "java.nio.file.Files.copy(java.nio.file.Path.of({0}), java.nio.file.Path.of({1}))", "desc": "Copy file"},
    # String operations
    "CBL_TOUPPER": {"java": "{0}.toUpperCase()", "desc": "Convert to uppercase"},
    "CBL_TOLOWER": {"java": "{0}.toLowerCase()", "desc": "Convert to lowercase"},
    # Environment
    "CBL_GET_CSR_POS": {"java": "/* cursor position */ 0", "desc": "Get cursor position"},
    "CBL_SET_CSR_POS": {"java": "/* set cursor position */", "desc": "Set cursor position"},
    "CBL_READ_KBD_CHAR": {"java": "System.in.read()", "desc": "Read keyboard char"},
    # System
    "CBL_OC_NANOSLEEP": {"java": "Thread.sleep({0})", "desc": "Sleep nanoseconds"},
    "CBL_GC_NANOSLEEP": {"java": "Thread.sleep({0})", "desc": "Sleep nanoseconds"},
    "SYSTEM": {"java": "Runtime.getRuntime().exec({0})", "desc": "Execute system command"},
    # Byte operations
    "CBL_AND": {"java": "({0} & {1})", "desc": "Bitwise AND"},
    "CBL_OR": {"java": "({0} | {1})", "desc": "Bitwise OR"},
    "CBL_XOR": {"java": "({0} ^ {1})", "desc": "Bitwise XOR"},
    "CBL_NOT": {"java": "(~{0})", "desc": "Bitwise NOT"},
    "CBL_EQ": {"java": "~({0} ^ {1})", "desc": "Bitwise equivalence"},
}


def generate_gnucobol_call_java(program_name: str, args: List[str], indent: str) -> Optional[List[str]]:
    """Generate Java code for GnuCOBOL CBL_* system routine calls."""
    upper_name = program_name.upper()
    routine = GNUCOBOL_CBL_ROUTINES.get(upper_name)
    if not routine:
        return None

    lines = [f"{indent}// GnuCOBOL system routine: {upper_name} ({routine['desc']})"]
    java_template = routine["java"]

    # Substitute arguments
    java_code = java_template
    for i, arg in enumerate(args):
        java_code = java_code.replace(f"{{{i}}}", arg)

    lines.append(f"{indent}{java_code};")
    return lines


# ======================================================================
#  Unisys MCP COBOL extensions
# ======================================================================
def classify_unisys_statement(text: str) -> Optional[str]:
    """Classify Unisys MCP-specific COBOL statements."""
    upper = text.upper().strip()
    if upper.startswith("GIVE"):
        return "GIVE"
    elif upper.startswith("RECEIVE"):
        return "RECEIVE"
    elif upper.startswith("PORT"):
        return "PORT"
    elif upper.startswith("CHANGE") and "ATTRIBUTE" in upper:
        return "CHANGE_ATTRIBUTE"
    elif "DMSII" in upper:
        return "DMSII"
    return None


def generate_unisys_java(stmt_type: str, raw_text: str, indent: str) -> List[str]:
    """Generate Java code for Unisys MCP-specific statements."""
    lines = [f"{indent}// Unisys MCP: {stmt_type}"]
    if stmt_type == "GIVE":
        lines.append(f"{indent}// GIVE - transfer control to another program")
        lines.append(f"{indent}// TODO: Convert to inter-process communication")
    elif stmt_type == "RECEIVE":
        lines.append(f"{indent}// RECEIVE - receive message from port")
        lines.append(f"{indent}// TODO: Convert to message queue consumer")
    elif stmt_type == "PORT":
        lines.append(f"{indent}// PORT - port-based communication")
        lines.append(f"{indent}// TODO: Convert to socket/MQ communication")
    elif stmt_type == "CHANGE_ATTRIBUTE":
        lines.append(f"{indent}// CHANGE ATTRIBUTE - modify file attributes")
        lines.append(f"{indent}// TODO: Convert to Java NIO file attribute change")
    elif stmt_type == "DMSII":
        lines.append(f"{indent}// DMSII database operation")
        lines.append(f"{indent}// TODO: Convert to JPA/Hibernate database call")
    lines.append(f"{indent}// Original: {raw_text[:100]}")
    return lines


# ======================================================================
#  Fujitsu NetCOBOL: FORMAT clause / CALL-CONVENTION
# ======================================================================
def is_fujitsu_format_clause(text: str) -> bool:
    """Check if text contains Fujitsu-specific FORMAT clause."""
    upper = text.upper()
    return "FORMAT" in upper and ("PRINTING MODE" in upper or "FREE" in upper or "FIXED" in upper)


def generate_fujitsu_format_java(text: str, indent: str) -> List[str]:
    """Generate Java for Fujitsu FORMAT printing."""
    return [
        f"{indent}// Fujitsu NetCOBOL FORMAT clause",
        f"{indent}// TODO: Convert to Java print formatting (PrintWriter/PrintStream)",
        f"{indent}// Original: {text[:100]}",
    ]


# ======================================================================
#  NEC ACOS-specific extensions
# ======================================================================
def is_nec_acos_extension(text: str) -> bool:
    """Check for NEC ACOS-specific COBOL extensions."""
    upper = text.upper()
    return any(kw in upper for kw in [
        "ACOS", "DISPLAY-ALL", "ACCEPT-ALL",
        "WRITE-ALL", "READ-ALL", "AIM"
    ])


def generate_nec_acos_java(text: str, indent: str) -> List[str]:
    """Generate Java for NEC ACOS-specific statements."""
    upper = text.upper()
    lines = [f"{indent}// NEC ACOS-specific extension"]
    if "DISPLAY-ALL" in upper or "ACCEPT-ALL" in upper:
        lines.append(f"{indent}// Full-screen terminal I/O")
        lines.append(f"{indent}// TODO: Convert to console/web UI interaction")
    elif "AIM" in upper:
        lines.append(f"{indent}// AIM (Advanced Information Manager) database access")
        lines.append(f"{indent}// TODO: Convert to JPA/Hibernate or JDBC call")
    else:
        lines.append(f"{indent}// TODO: Convert NEC-specific extension to Java")
    lines.append(f"{indent}// Original: {text[:100]}")
    return lines


# ======================================================================
#  Bull/Atos GCOS-specific extensions
# ======================================================================
def is_bull_gcos_extension(text: str) -> bool:
    """Check for Bull/Atos GCOS-specific COBOL extensions."""
    upper = text.upper()
    return any(kw in upper for kw in [
        "GCOS", "TP8", "TDS",
        "STORE", "FETCH", "MODIFY",  # IDSII database verbs
    ])


def generate_bull_gcos_java(text: str, indent: str) -> List[str]:
    """Generate Java for Bull/Atos GCOS-specific statements."""
    upper = text.upper()
    lines = [f"{indent}// Bull/Atos GCOS-specific extension"]
    if any(kw in upper for kw in ["STORE", "FETCH", "MODIFY"]):
        lines.append(f"{indent}// IDSII database operation")
        lines.append(f"{indent}// TODO: Convert to JPA/Hibernate or JDBC call")
    elif "TP8" in upper or "TDS" in upper:
        lines.append(f"{indent}// TP8/TDS transaction processing")
        lines.append(f"{indent}// TODO: Convert to Java transaction management")
    else:
        lines.append(f"{indent}// TODO: Convert GCOS-specific extension to Java")
    lines.append(f"{indent}// Original: {text[:100]}")
    return lines


def get_vendor_imports(vendor: VendorType, has_sql: bool, has_cics: bool) -> List[str]:
    """Get required Java imports based on vendor features."""
    imports = []
    if has_sql:
        imports.extend([
            "java.sql.Connection",
            "java.sql.DriverManager",
            "java.sql.PreparedStatement",
            "java.sql.ResultSet",
            "java.sql.SQLException",
        ])
    if has_cics:
        imports.append("// TODO: Add CICS service interface imports")

    return imports
