"""
COBOL Source Code Parser
COBOLソースファイルを解析し、構造化データに変換する
"""
import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from enum import Enum


class StatementType(Enum):
    MOVE = "MOVE"
    ADD = "ADD"
    SUBTRACT = "SUBTRACT"
    MULTIPLY = "MULTIPLY"
    DIVIDE = "DIVIDE"
    COMPUTE = "COMPUTE"
    IF = "IF"
    ELSE = "ELSE"
    END_IF = "END-IF"
    EVALUATE = "EVALUATE"
    WHEN = "WHEN"
    END_EVALUATE = "END-EVALUATE"
    PERFORM = "PERFORM"
    DISPLAY = "DISPLAY"
    ACCEPT = "ACCEPT"
    READ = "READ"
    WRITE = "WRITE"
    OPEN = "OPEN"
    CLOSE = "CLOSE"
    STOP_RUN = "STOP RUN"
    GOBACK = "GOBACK"
    CALL = "CALL"
    STRING = "STRING"
    UNSTRING = "UNSTRING"
    INSPECT = "INSPECT"
    INITIALIZE = "INITIALIZE"
    SET = "SET"
    EXIT = "EXIT"
    CONTINUE = "CONTINUE"
    GO_TO = "GO TO"
    EXEC_SQL = "EXEC SQL"
    EXEC_CICS = "EXEC CICS"
    EXEC_DLI = "EXEC DLI"
    EXEC_OTHER = "EXEC OTHER"
    XML_GENERATE = "XML GENERATE"
    XML_PARSE = "XML PARSE"
    JSON_GENERATE = "JSON GENERATE"
    JSON_PARSE = "JSON PARSE"
    INVOKE = "INVOKE"
    ENTER = "ENTER"
    UNKNOWN = "UNKNOWN"


COBOL_VERBS = {
    "ACCEPT", "ADD", "CALL", "CLOSE", "COMPUTE", "CONTINUE",
    "DELETE", "DISPLAY", "DIVIDE", "ENTER", "EVALUATE", "EXEC", "EXIT",
    "GO", "GOBACK", "IF", "INITIALIZE", "INSPECT", "INVOKE",
    "JSON", "MERGE", "MOVE", "MULTIPLY", "OPEN", "PERFORM",
    "READ", "RELEASE", "RETURN", "REWRITE", "SEARCH",
    "SET", "SORT", "START", "STOP", "STRING",
    "SUBTRACT", "UNSTRING", "WRITE", "XML",
}

BLOCK_TERMINATORS = {
    "END-IF", "END-EVALUATE", "END-PERFORM", "END-READ",
    "END-WRITE", "END-CALL", "END-COMPUTE", "END-DELETE",
    "END-MULTIPLY", "END-RETURN", "END-REWRITE", "END-SEARCH",
    "END-START", "END-STRING", "END-SUBTRACT", "END-UNSTRING",
}


@dataclass
class DataItem:
    level: int
    name: str
    picture: str = ""
    usage: str = ""
    value: Optional[str] = None
    occurs: int = 0
    occurs_depending: str = ""
    redefines: str = ""
    is_filler: bool = False
    children: List['DataItem'] = field(default_factory=list)
    is_88_level: bool = False
    condition_values: List[str] = field(default_factory=list)

    @property
    def is_group(self) -> bool:
        return len(self.children) > 0 and not self.picture

    @property
    def java_type(self) -> str:
        if self.is_88_level:
            return "boolean"
        if self.is_group:
            return self.to_class_name()
        return pic_to_java_type(self.picture, self.usage)

    def to_class_name(self) -> str:
        return to_pascal_case(self.name)

    def to_field_name(self) -> str:
        return to_camel_case(self.name)


@dataclass
class Statement:
    type: StatementType
    raw_text: str
    tokens: List[str] = field(default_factory=list)
    children: List['Statement'] = field(default_factory=list)
    else_children: List['Statement'] = field(default_factory=list)
    when_blocks: List[tuple] = field(default_factory=list)


@dataclass
class Paragraph:
    name: str
    statements: List[Statement] = field(default_factory=list)


@dataclass
class Section:
    name: str
    paragraphs: List[Paragraph] = field(default_factory=list)


@dataclass
class FileDefinition:
    select_name: str = ""
    assign_to: str = ""
    organization: str = "SEQUENTIAL"
    access_mode: str = "SEQUENTIAL"
    file_status: str = ""
    fd_name: str = ""
    record_name: str = ""
    data_items: List[DataItem] = field(default_factory=list)


@dataclass
class CobolProgram:
    program_id: str = ""
    author: str = ""
    date_written: str = ""
    source_file: str = ""
    files: List[FileDefinition] = field(default_factory=list)
    working_storage: List[DataItem] = field(default_factory=list)
    local_storage: List[DataItem] = field(default_factory=list)
    linkage_section: List[DataItem] = field(default_factory=list)
    screen_section: List['DataItem'] = field(default_factory=list)
    sections: List[Section] = field(default_factory=list)
    paragraphs: List[Paragraph] = field(default_factory=list)
    copy_members: List[str] = field(default_factory=list)
    called_programs: List[str] = field(default_factory=list)
    vendor_type: str = "standard"      # detected or specified vendor
    has_exec_sql: bool = False
    has_exec_cics: bool = False
    has_exec_dli: bool = False
    exec_data_blocks: List[str] = field(default_factory=list)  # EXEC blocks found in DATA DIVISION
    has_class_id: bool = False         # OO COBOL (Hitachi/Micro Focus)
    class_id: str = ""


def to_pascal_case(cobol_name: str) -> str:
    parts = cobol_name.lower().replace("_", "-").split("-")
    return "".join(p.capitalize() for p in parts if p)


def to_camel_case(cobol_name: str) -> str:
    pascal = to_pascal_case(cobol_name)
    if not pascal:
        return pascal
    return pascal[0].lower() + pascal[1:]


def pic_to_java_type(picture: str, usage: str = "", vendor: str = "standard") -> str:
    if not picture:
        usage_upper = usage.upper()
        # Check specific COMP variants before generic COMP/BINARY
        if usage_upper == "COMP-1":
            return "float"
        if usage_upper == "COMP-2":
            return "double"
        if usage_upper in ("COMP-5", "COMP-X", "BINARY-LONG"):
            return "int"
        if usage_upper in ("BINARY-SHORT",):
            return "short"
        if usage_upper in ("BINARY-DOUBLE",):
            return "long"
        if usage_upper in ("BINARY-CHAR",):
            return "byte"
        if usage_upper in ("FLOAT-SHORT",):
            return "float"
        if usage_upper in ("FLOAT-LONG", "FLOAT-EXTENDED"):
            return "double"
        if usage_upper in ("POINTER", "FUNCTION-POINTER", "PROCEDURE-POINTER"):
            return "long"
        if usage_upper in ("OBJECT-REFERENCE",):
            return "Object"
        if usage_upper in ("NATIONAL", "DISPLAY-1"):
            return "String"
        if usage_upper in ("NATIVE-2",):
            return "short"
        # Generic COMP/BINARY fallback
        if "COMP" in usage_upper or "BINARY" in usage_upper:
            return "int"
        if usage_upper in ("NATIVE-4",):
            return "int"
        if usage_upper in ("NATIVE-8", "BINARY-C-LONG"):
            return "long"
        return "String"

    pic = picture.upper().replace(" ", "")
    expanded = re.sub(r'(\w)\((\d+)\)', lambda m: m.group(1) * int(m.group(2)), pic)

    # PIC N / PIC N(xx) → String (Japanese/CJK DBCS - Fujitsu, NEC, Hitachi, IBM)
    if re.match(r'^N+$', expanded):
        return "String"

    has_sign = expanded.startswith("S") or expanded.startswith("-") or expanded.startswith("+")
    if has_sign:
        expanded = expanded.lstrip("S+-")

    has_decimal = "V" in expanded or "." in expanded

    if re.match(r'^[9Z0]+$', expanded.replace("V", "").replace(".", "")):
        if has_decimal or "COMP-3" in usage or "PACKED" in usage:
            return "java.math.BigDecimal"
        digit_count = len(expanded.replace("V", "").replace(".", ""))
        if digit_count <= 9:
            return "int"
        elif digit_count <= 18:
            return "long"
        else:
            return "java.math.BigDecimal"

    if re.match(r'^[XA]+$', expanded):
        return "String"

    return "String"


def _first_word(text: str) -> str:
    """Get the first word of a string, uppercased."""
    parts = text.strip().split()
    return parts[0].upper() if parts else ""


def _is_verb_start(text: str) -> bool:
    """Check if text starts with a COBOL verb or block terminator."""
    word = _first_word(text)
    return word in COBOL_VERBS or word in BLOCK_TERMINATORS or word == "ELSE" or word == "WHEN"


class CobolParser:
    def __init__(self, encoding: str = "utf-8", use_lark: bool = True):
        self.encoding = encoding
        self.use_lark = use_lark
        self._lark_parser = None
        self._procedure_parser = None
        self._division_router = None
        self._preprocessor = None
        if use_lark:
            try:
                from .lark_data_parser import LarkDataParser
                self._lark_parser = LarkDataParser()
            except ImportError:
                self._lark_parser = None
            try:
                from .lark_procedure_parser import ProcedureDivisionParser
                self._procedure_parser = ProcedureDivisionParser()
            except ImportError:
                self._procedure_parser = None
            try:
                from .division_parser import DivisionRouter, CobolPreprocessor
                self._division_router = DivisionRouter(self)
                self._preprocessor = CobolPreprocessor()
            except ImportError:
                self._division_router = None
                self._preprocessor = None

    def parse_file(self, filepath: str) -> CobolProgram:
        with open(filepath, "r", encoding=self.encoding, errors="replace") as f:
            raw_lines = f.readlines()

        lines = self._preprocess_dispatch(raw_lines)
        program = CobolProgram(source_file=filepath)
        self._parse_program_dispatch(lines, program)
        return program

    def parse_string(self, source: str) -> CobolProgram:
        raw_lines = source.splitlines(keepends=True)
        lines = self._preprocess_dispatch(raw_lines)
        program = CobolProgram()
        self._parse_program_dispatch(lines, program)
        return program

    def _preprocess_dispatch(self, raw_lines: List[str]) -> List[str]:
        """Use structured preprocessor if available, else legacy."""
        if self._preprocessor is not None:
            return self._preprocessor.process(raw_lines)
        return self._preprocess(raw_lines)

    def _parse_program_dispatch(self, lines: List[str], program: CobolProgram):
        """Use structured division router if available, else legacy."""
        if self._division_router is not None:
            self._division_router.parse(lines, program)
        else:
            self._parse_program(lines, program)

    def _preprocess(self, raw_lines: List[str]) -> List[str]:
        """Clean raw source lines: handle fixed/free format, remove comments, handle continuations."""
        processed = []
        for line in raw_lines:
            line = line.rstrip("\n\r")

            # Handle fixed-format COBOL (columns 7-72)
            if len(line) >= 7:
                indicator = line[6] if len(line) > 6 else " "
                if indicator in ("*", "/", "D", "d"):
                    continue
                if indicator == "-":
                    if processed:
                        processed[-1] = processed[-1].rstrip() + " " + (line[7:72].strip() if len(line) > 7 else "")
                    continue
                content = line[6:72] if len(line) > 6 else ""
            else:
                content = line

            content = content.rstrip()
            if content.strip():
                processed.append(content.strip())

        # Fallback to free-format if fixed format yields poor results
        if not processed or all(len(l.strip()) < 3 for l in processed):
            processed = []
            for line in raw_lines:
                line = line.rstrip("\n\r").rstrip()
                if line.strip().startswith("*>"):
                    continue
                if line.strip():
                    processed.append(line.strip())

        return processed

    def _join_data_statements(self, lines: List[str], start: int) -> Tuple[List[str], int]:
        """Join lines into period-delimited statements for DATA DIVISION sections.
        Returns (statements, next_index). Skips EXEC...END-EXEC blocks."""
        statements = []
        current = ""
        idx = start
        in_exec = False
        exec_accumulator = ""

        while idx < len(lines):
            line = lines[idx]
            upper = line.upper().strip()

            # Stop at division/section boundaries
            if any(s in upper for s in [
                "WORKING-STORAGE SECTION", "LOCAL-STORAGE SECTION",
                "LINKAGE SECTION", "FILE SECTION", "SCREEN SECTION",
                "REPORT SECTION", "COMMUNICATION SECTION",
                "PROCEDURE DIVISION", "DATA DIVISION",
                "ENVIRONMENT DIVISION", "IDENTIFICATION DIVISION"
            ]):
                if current.strip():
                    statements.append(current.strip())
                return statements, idx

            if re.match(r'^FD\s+', upper):
                if current.strip():
                    statements.append(current.strip())
                return statements, idx

            # Handle EXEC...END-EXEC blocks in DATA DIVISION
            # (e.g., EXEC SQL INCLUDE SQLCA END-EXEC, EXEC SQL DECLARE CURSOR ...)
            if in_exec:
                exec_accumulator += " " + line.strip()
                if "END-EXEC" in upper:
                    in_exec = False
                    # Store as a special marker statement (prefixed with __EXEC__)
                    statements.append("__EXEC__" + exec_accumulator.strip())
                    exec_accumulator = ""
                idx += 1
                continue

            if upper.startswith("EXEC "):
                if current.strip():
                    statements.append(current.strip())
                    current = ""
                if "END-EXEC" in upper:
                    # Single-line EXEC block
                    statements.append("__EXEC__" + line.strip())
                else:
                    in_exec = True
                    exec_accumulator = line.strip()
                idx += 1
                continue

            # Handle COPY statements in DATA DIVISION
            copy_match = re.match(r'^COPY\s+(\S+)', upper)
            if copy_match:
                if current.strip():
                    statements.append(current.strip())
                    current = ""
                statements.append("__COPY__" + copy_match.group(1).rstrip("."))
                idx += 1
                continue

            if line.rstrip().endswith("."):
                current += " " + line
                statements.append(current.strip())
                current = ""
            else:
                current += " " + line

            idx += 1

        if current.strip():
            statements.append(current.strip())
        if exec_accumulator.strip():
            statements.append("__EXEC__" + exec_accumulator.strip())
        return statements, idx

    def _parse_program(self, lines: List[str], program: CobolProgram):
        self._current_program = program  # Allow data section parser to track EXEC blocks
        idx = 0
        current_division = ""

        while idx < len(lines):
            line = lines[idx]
            upper = line.upper()

            if "IDENTIFICATION DIVISION" in upper or "ID DIVISION" in upper:
                current_division = "IDENTIFICATION"
                idx += 1
                continue

            if "ENVIRONMENT DIVISION" in upper:
                current_division = "ENVIRONMENT"
                idx += 1
                continue

            if "DATA DIVISION" in upper:
                current_division = "DATA"
                idx += 1
                continue

            if "PROCEDURE DIVISION" in upper:
                idx += 1
                self._parse_procedure_division(lines, idx, program)
                return

            if current_division == "IDENTIFICATION":
                self._parse_identification(line, program)
            elif current_division == "ENVIRONMENT":
                idx = self._parse_environment(lines, idx, program)
                continue
            elif current_division == "DATA":
                if "WORKING-STORAGE SECTION" in upper:
                    idx += 1
                    idx = self._parse_data_section(lines, idx, program.working_storage)
                    continue
                elif "LOCAL-STORAGE SECTION" in upper:
                    idx += 1
                    idx = self._parse_data_section(lines, idx, program.local_storage)
                    continue
                elif "LINKAGE SECTION" in upper:
                    idx += 1
                    idx = self._parse_data_section(lines, idx, program.linkage_section)
                    continue
                elif "SCREEN SECTION" in upper:
                    idx += 1
                    idx = self._parse_data_section(lines, idx, program.screen_section)
                    continue
                elif "FILE SECTION" in upper:
                    idx += 1
                    idx = self._parse_file_section(lines, idx, program)
                    continue

            idx += 1

    def _parse_identification(self, line: str, program: CobolProgram):
        upper = line.upper()
        if "PROGRAM-ID" in upper:
            match = re.search(r'PROGRAM-ID\.\s*(\S+)', line, re.IGNORECASE)
            if match:
                program.program_id = match.group(1).rstrip(".")
        elif "CLASS-ID" in upper:
            match = re.search(r'CLASS-ID\.\s*(\S+)', line, re.IGNORECASE)
            if match:
                program.class_id = match.group(1).rstrip(".")
                program.has_class_id = True
                if not program.program_id:
                    program.program_id = program.class_id
        elif "AUTHOR" in upper:
            match = re.search(r'AUTHOR\.\s*(.*)', line, re.IGNORECASE)
            if match:
                program.author = match.group(1).rstrip(".")
        elif "DATE-WRITTEN" in upper:
            match = re.search(r'DATE-WRITTEN\.\s*(.*)', line, re.IGNORECASE)
            if match:
                program.date_written = match.group(1).rstrip(".")

    def _parse_environment(self, lines: List[str], idx: int, program: CobolProgram) -> int:
        while idx < len(lines):
            line = lines[idx]
            upper = line.upper()

            if any(d in upper for d in ["DATA DIVISION", "PROCEDURE DIVISION"]):
                return idx

            if upper.startswith("SELECT"):
                file_def = FileDefinition()
                select_text = line
                while not select_text.rstrip().endswith(".") and idx + 1 < len(lines):
                    idx += 1
                    select_text += " " + lines[idx]

                match = re.search(r'SELECT\s+(\S+)', select_text, re.IGNORECASE)
                if match:
                    file_def.select_name = match.group(1)

                assign_match = re.search(r'ASSIGN\s+TO\s+["\']?(\S+?)["\']?[\s.]', select_text, re.IGNORECASE)
                if assign_match:
                    file_def.assign_to = assign_match.group(1).rstrip(".")

                org_match = re.search(r'ORGANIZATION\s+IS\s+(\S+)', select_text, re.IGNORECASE)
                if org_match:
                    file_def.organization = org_match.group(1).rstrip(".")

                status_match = re.search(r'FILE\s+STATUS\s+(?:IS\s+)?(\S+)', select_text, re.IGNORECASE)
                if status_match:
                    file_def.file_status = status_match.group(1).rstrip(".")

                program.files.append(file_def)

            copy_match = re.search(r'COPY\s+(\S+)', upper)
            if copy_match:
                program.copy_members.append(copy_match.group(1).rstrip("."))

            idx += 1
        return idx

    def _parse_file_section(self, lines: List[str], idx: int, program: CobolProgram) -> int:
        while idx < len(lines):
            line = lines[idx]
            upper = line.upper()

            if any(s in upper for s in [
                "WORKING-STORAGE SECTION", "LOCAL-STORAGE SECTION",
                "LINKAGE SECTION", "PROCEDURE DIVISION",
            ]):
                return idx

            fd_match = re.match(r'FD\s+(\S+)', upper)
            if fd_match:
                fd_name = fd_match.group(1).rstrip(".")
                target_fd = None
                for f in program.files:
                    if f.select_name.upper() == fd_name.upper():
                        target_fd = f
                        break
                if not target_fd:
                    target_fd = FileDefinition(select_name=fd_name)
                    program.files.append(target_fd)
                target_fd.fd_name = fd_name
                idx += 1
                idx = self._parse_data_section(lines, idx, target_fd.data_items)
                continue

            idx += 1
        return idx

    def _parse_data_section(self, lines: List[str], idx: int, items: List[DataItem],
                             program: 'CobolProgram' = None) -> int:
        """Parse data items from raw lines. Handles multi-line data definitions.
        EXEC blocks in DATA DIVISION are collected into program.exec_data_blocks."""
        stmts, next_idx = self._join_data_statements(lines, idx)
        for stmt in stmts:
            if stmt.startswith("__EXEC__"):
                exec_text = stmt[8:]  # Remove __EXEC__ prefix
                # Track EXEC SQL flags
                upper_exec = exec_text.upper()
                if "EXEC SQL" in upper_exec:
                    if hasattr(self, '_current_program') and self._current_program:
                        self._current_program.has_exec_sql = True
                        self._current_program.exec_data_blocks.append(exec_text)
            elif stmt.startswith("__COPY__"):
                copy_name = stmt[8:]  # Remove __COPY__ prefix
                if hasattr(self, '_current_program') and self._current_program:
                    self._current_program.copy_members.append(copy_name)
            else:
                self._parse_data_statement_dispatch(stmt, items)
        return next_idx

    def _parse_data_statement_dispatch(self, stmt: str, items: List[DataItem]):
        """Try lark parser first, fall back to regex parser on failure."""
        if self._lark_parser is not None:
            item = self._lark_parser.parse_statement(stmt)
            if item is not None:
                self._place_data_item(item, items)
                return
        # Fallback to regex-based parser
        self._parse_data_statement(stmt, items)

    def _parse_data_statement(self, stmt: str, items: List[DataItem],
                               _stack: List[DataItem] = None):
        """Parse a single period-terminated data statement. May contain multiple items."""
        # A single period-terminated statement could contain one data item
        stmt = stmt.rstrip(".")

        data_match = re.match(r'(\d{1,2})\s+(\S+)(.*)', stmt)
        if not data_match:
            return

        level = int(data_match.group(1))
        name = data_match.group(2).rstrip(".")
        rest = data_match.group(3).rstrip(".")

        item = DataItem(level=level, name=name)

        if name.upper() == "FILLER":
            item.is_filler = True

        if level == 88:
            item.is_88_level = True
            val_match = re.search(r'VALUES?\s+(?:ARE\s+|IS\s+)?(.*)', rest, re.IGNORECASE)
            if val_match:
                vals = val_match.group(1).rstrip(".")
                item.condition_values = [v.strip().strip("'\"") for v in re.split(r'\s+', vals) if v.strip()]
            # Attach to last non-88 item
            if items:
                last = items[-1]
                while last.children and not last.children[-1].is_88_level:
                    last = last.children[-1]
                last.children.append(item)
            return

        # PIC clause
        pic_match = re.search(r'PIC(?:TURE)?\s+(?:IS\s+)?(\S+)', rest, re.IGNORECASE)
        if pic_match:
            item.picture = pic_match.group(1).rstrip(".")

        # USAGE clause
        usage_match = re.search(
            r'USAGE\s+(?:IS\s+)?(\S+)|\b(COMP(?:-[0-9])?|BINARY|PACKED-DECIMAL)\b',
            rest, re.IGNORECASE
        )
        if usage_match:
            item.usage = (usage_match.group(1) or usage_match.group(2) or "").rstrip(".")

        # VALUE clause
        val_match = re.search(r'VALUE\s+(?:IS\s+)?(.*?)(?:\s+PIC|\s+USAGE|\s+OCCURS|$)', rest, re.IGNORECASE)
        if val_match:
            val = val_match.group(1).strip().rstrip(".")
            if val:
                item.value = val.strip("'\"")

        # OCCURS clause
        occ_match = re.search(r'OCCURS\s+(\d+)', rest, re.IGNORECASE)
        if occ_match:
            item.occurs = int(occ_match.group(1))

        # REDEFINES clause
        redef_match = re.search(r'REDEFINES\s+(\S+)', rest, re.IGNORECASE)
        if redef_match:
            item.redefines = redef_match.group(1).rstrip(".")

        # Place in hierarchy using items list as flat storage + stack reconstruction
        self._place_data_item(item, items)

    def _place_data_item(self, item: DataItem, items: List[DataItem]):
        """Place a data item in the correct position in the hierarchy."""
        if item.level == 1 or item.level == 77:
            items.append(item)
            return

        # Find parent: walk backwards to find an item with a lower level
        parent = self._find_parent(items, item.level)
        if parent:
            parent.children.append(item)
        else:
            items.append(item)

    def _find_parent(self, items: List[DataItem], target_level: int) -> Optional[DataItem]:
        """Find the nearest item with level < target_level, searching depth-first from the end."""
        for item in reversed(items):
            result = self._find_parent_recursive(item, target_level)
            if result is not None:
                return result
        return None

    def _find_parent_recursive(self, item: DataItem, target_level: int) -> Optional[DataItem]:
        """Recursively find deepest item with level < target_level."""
        # Check children last-to-first
        for child in reversed(item.children):
            if child.is_88_level:
                continue
            result = self._find_parent_recursive(child, target_level)
            if result is not None:
                return result
        # This item is a valid parent if level < target
        if item.level < target_level:
            return item
        return None

    # ==================== PROCEDURE DIVISION ====================

    def _parse_procedure_division(self, lines: List[str], start_idx: int, program: CobolProgram):
        """Parse the PROCEDURE DIVISION by segmenting into logical statements."""
        # First, segment the raw lines into logical statements
        proc_statements = self._segment_procedure(lines, start_idx)

        # Use structured parser if available, otherwise fall back to legacy
        if self._procedure_parser is not None:
            self._procedure_parser.parse(proc_statements, program)
            return

        self._parse_procedure_division_legacy(proc_statements, program)

    def _parse_procedure_division_legacy(self, proc_statements: List[str], program: CobolProgram):
        """Legacy procedure division parser (regex-based fallback)."""
        current_paragraph = None
        current_section = None
        idx = 0

        while idx < len(proc_statements):
            stmt_text = proc_statements[idx]
            upper = stmt_text.upper().rstrip(".")

            # Section header: NAME SECTION.
            section_match = re.match(r'^([A-Z0-9][-A-Z0-9]*)\s+SECTION\s*\.?$', upper)
            if section_match:
                current_section = Section(name=section_match.group(1))
                program.sections.append(current_section)
                current_paragraph = None
                idx += 1
                continue

            # Paragraph header: NAME. (a name that's not a verb, by itself)
            para_match = re.match(r'^([A-Z0-9][-A-Z0-9]*)\s*\.?$', upper)
            if para_match and not _is_verb_start(upper.rstrip(".")):
                para_name = para_match.group(1)
                # Make sure it's not a block terminator
                if para_name not in BLOCK_TERMINATORS and para_name not in ("ELSE", "WHEN"):
                    current_paragraph = Paragraph(name=para_name)
                    if current_section:
                        current_section.paragraphs.append(current_paragraph)
                    else:
                        program.paragraphs.append(current_paragraph)
                    idx += 1
                    continue

            # Ensure we have a current paragraph
            if current_paragraph is None:
                current_paragraph = Paragraph(name="MAIN")
                if current_section:
                    current_section.paragraphs.append(current_paragraph)
                else:
                    program.paragraphs.append(current_paragraph)

            # Parse the statement and handle block structures
            stmt = self._classify_statement(stmt_text)
            if stmt:
                # Track EXEC block flags
                if stmt.type == StatementType.EXEC_SQL:
                    program.has_exec_sql = True
                elif stmt.type == StatementType.EXEC_CICS:
                    program.has_exec_cics = True
                elif stmt.type == StatementType.EXEC_DLI:
                    program.has_exec_dli = True

                if stmt.type == StatementType.CALL:
                    call_match = re.search(r'CALL\s+["\'](\S+)["\']', stmt_text, re.IGNORECASE)
                    if call_match:
                        program.called_programs.append(call_match.group(1))

                if stmt.type == StatementType.IF:
                    idx = self._parse_if_block(proc_statements, idx, stmt)
                    current_paragraph.statements.append(stmt)
                    continue
                elif stmt.type == StatementType.EVALUATE:
                    idx = self._parse_evaluate_block(proc_statements, idx, stmt)
                    current_paragraph.statements.append(stmt)
                    continue
                elif stmt.type == StatementType.READ:
                    idx = self._parse_read_block(proc_statements, idx, stmt)
                    current_paragraph.statements.append(stmt)
                    continue
                else:
                    current_paragraph.statements.append(stmt)

            idx += 1

    def _segment_procedure(self, lines: List[str], start_idx: int) -> List[str]:
        """Segment procedure division lines into logical statements.
        Each COBOL verb starts a new statement. Multi-line statements
        (where continuation lines don't start with a verb) are joined.
        EXEC...END-EXEC blocks are collected as single statements."""
        statements = []
        current = ""
        in_exec = False
        exec_accumulator = ""

        for idx in range(start_idx, len(lines)):
            line = lines[idx]
            upper = line.upper()

            # Stop at other divisions
            if any(d in upper for d in ["IDENTIFICATION DIVISION", "ENVIRONMENT DIVISION", "DATA DIVISION"]):
                break

            # Skip COPY
            if upper.strip().startswith("COPY "):
                continue

            stripped = line.strip()
            if not stripped:
                continue

            # --- EXEC...END-EXEC block handling ---
            if in_exec:
                exec_accumulator += " " + stripped
                if "END-EXEC" in stripped.upper():
                    in_exec = False
                    # Flush any pending statement before the EXEC
                    if current.strip():
                        statements.append(current.strip())
                        current = ""
                    statements.append(exec_accumulator.strip())
                    exec_accumulator = ""
                continue

            if stripped.upper().startswith("EXEC "):
                # Start of EXEC block
                if current.strip():
                    statements.append(current.strip())
                    current = ""
                if "END-EXEC" in stripped.upper():
                    # Single-line EXEC...END-EXEC
                    statements.append(stripped)
                else:
                    in_exec = True
                    exec_accumulator = stripped
                continue

            # Remove trailing period for analysis, but keep it in the text
            analysis = stripped.rstrip(".").strip()
            first_word = _first_word(analysis)

            # Check if this is a section header
            is_section = bool(re.match(r'^[A-Z0-9][-A-Z0-9]*\s+SECTION\s*\.?$', upper.strip()))

            # Check if this is a paragraph header (single name, possibly with period)
            is_para = bool(re.match(r'^[A-Z0-9][-A-Z0-9]*\s*\.\s*$', upper.strip()))

            # Check if this starts a new statement (verb, block terminator, ELSE, WHEN)
            starts_new = (
                first_word in COBOL_VERBS or
                first_word in BLOCK_TERMINATORS or
                first_word in ("ELSE", "WHEN", "NOT") or
                is_section or is_para
            )

            if starts_new:
                # Flush current accumulated statement
                if current.strip():
                    statements.append(current.strip())
                current = stripped
            else:
                # Continuation of current statement
                current += " " + stripped

            # If statement ends with period, flush
            if stripped.endswith("."):
                if current.strip():
                    statements.append(current.strip())
                current = ""

        if current.strip():
            statements.append(current.strip())
        if exec_accumulator.strip():
            statements.append(exec_accumulator.strip())

        return statements

    def _classify_statement(self, text: str) -> Optional[Statement]:
        """Classify a segmented statement text into a Statement object."""
        stripped = text.strip().rstrip(".")
        if not stripped:
            return None

        tokens = stripped.split()
        first = tokens[0].upper() if tokens else ""

        type_map = {
            "MOVE": StatementType.MOVE,
            "ADD": StatementType.ADD,
            "SUBTRACT": StatementType.SUBTRACT,
            "MULTIPLY": StatementType.MULTIPLY,
            "DIVIDE": StatementType.DIVIDE,
            "COMPUTE": StatementType.COMPUTE,
            "IF": StatementType.IF,
            "EVALUATE": StatementType.EVALUATE,
            "PERFORM": StatementType.PERFORM,
            "DISPLAY": StatementType.DISPLAY,
            "ACCEPT": StatementType.ACCEPT,
            "READ": StatementType.READ,
            "WRITE": StatementType.WRITE,
            "OPEN": StatementType.OPEN,
            "CLOSE": StatementType.CLOSE,
            "CALL": StatementType.CALL,
            "STRING": StatementType.STRING,
            "UNSTRING": StatementType.UNSTRING,
            "INSPECT": StatementType.INSPECT,
            "INITIALIZE": StatementType.INITIALIZE,
            "SET": StatementType.SET,
            "EXIT": StatementType.EXIT,
            "CONTINUE": StatementType.CONTINUE,
            "GOBACK": StatementType.GOBACK,
        }

        # EXEC ... END-EXEC blocks
        if first == "EXEC":
            exec_type = tokens[1].upper() if len(tokens) > 1 else "OTHER"
            if exec_type == "SQL":
                stmt_type = StatementType.EXEC_SQL
            elif exec_type == "CICS":
                stmt_type = StatementType.EXEC_CICS
            elif exec_type == "DLI":
                stmt_type = StatementType.EXEC_DLI
            else:
                stmt_type = StatementType.EXEC_OTHER
            return Statement(type=stmt_type, raw_text=stripped, tokens=tokens)

        # IBM XML/JSON verbs
        if first == "XML" and len(tokens) > 1:
            second = tokens[1].upper()
            if second == "GENERATE":
                return Statement(type=StatementType.XML_GENERATE, raw_text=stripped, tokens=tokens)
            elif second == "PARSE":
                return Statement(type=StatementType.XML_PARSE, raw_text=stripped, tokens=tokens)

        if first == "JSON" and len(tokens) > 1:
            second = tokens[1].upper()
            if second == "GENERATE":
                return Statement(type=StatementType.JSON_GENERATE, raw_text=stripped, tokens=tokens)
            elif second == "PARSE":
                return Statement(type=StatementType.JSON_PARSE, raw_text=stripped, tokens=tokens)

        # OO COBOL INVOKE (Hitachi/Micro Focus)
        if first == "INVOKE":
            return Statement(type=StatementType.INVOKE, raw_text=stripped, tokens=tokens)

        # HP/Tandem ENTER TAL
        if first == "ENTER":
            return Statement(type=StatementType.ENTER, raw_text=stripped, tokens=tokens)

        if first == "STOP" and len(tokens) > 1 and tokens[1].upper() == "RUN":
            stmt_type = StatementType.STOP_RUN
        elif first == "GO" and len(tokens) > 1 and tokens[1].upper() == "TO":
            stmt_type = StatementType.GO_TO
        elif first in BLOCK_TERMINATORS:
            return None  # Block terminators handled by block parsers
        elif first in ("ELSE", "WHEN"):
            return None  # Handled by block parsers
        else:
            stmt_type = type_map.get(first, StatementType.UNKNOWN)

        return Statement(type=stmt_type, raw_text=stripped, tokens=tokens)

    def _parse_if_block(self, stmts: List[str], idx: int, stmt: Statement) -> int:
        """Parse IF/ELSE/END-IF block structure."""
        in_else = False
        idx += 1  # Skip past the IF statement itself

        while idx < len(stmts):
            text = stmts[idx]
            upper = text.upper().rstrip(".")

            first_word = _first_word(upper)

            if first_word == "END-IF":
                idx += 1
                return idx

            if first_word == "ELSE":
                in_else = True
                idx += 1
                continue

            # Nested IF
            child = self._classify_statement(text)
            if child:
                if child.type == StatementType.IF:
                    idx = self._parse_if_block(stmts, idx, child)
                    if in_else:
                        stmt.else_children.append(child)
                    else:
                        stmt.children.append(child)
                    continue
                elif child.type == StatementType.EVALUATE:
                    idx = self._parse_evaluate_block(stmts, idx, child)
                    if in_else:
                        stmt.else_children.append(child)
                    else:
                        stmt.children.append(child)
                    continue
                elif child.type == StatementType.READ:
                    idx = self._parse_read_block(stmts, idx, child)
                    if in_else:
                        stmt.else_children.append(child)
                    else:
                        stmt.children.append(child)
                    continue
                else:
                    if in_else:
                        stmt.else_children.append(child)
                    else:
                        stmt.children.append(child)

            idx += 1

        return idx

    def _parse_evaluate_block(self, stmts: List[str], idx: int, stmt: Statement) -> int:
        """Parse EVALUATE/WHEN/END-EVALUATE block structure."""
        current_when_stmts = []
        current_when_value = ""
        idx += 1

        while idx < len(stmts):
            text = stmts[idx]
            upper = text.upper().rstrip(".")
            first_word = _first_word(upper)

            if first_word == "END-EVALUATE":
                if current_when_value:
                    stmt.when_blocks.append((current_when_value, current_when_stmts))
                idx += 1
                return idx

            if first_word == "WHEN":
                if current_when_value:
                    stmt.when_blocks.append((current_when_value, current_when_stmts))
                current_when_value = text.strip().rstrip(".")[5:].strip()  # After "WHEN "
                current_when_stmts = []
                idx += 1
                continue

            child = self._classify_statement(text)
            if child:
                if child.type == StatementType.IF:
                    idx = self._parse_if_block(stmts, idx, child)
                    current_when_stmts.append(child)
                    continue
                else:
                    current_when_stmts.append(child)

            idx += 1

        if current_when_value:
            stmt.when_blocks.append((current_when_value, current_when_stmts))
        return idx

    def _parse_read_block(self, stmts: List[str], idx: int, stmt: Statement) -> int:
        """Parse READ with AT END / NOT AT END / END-READ."""
        # Check if the READ statement itself contains AT END inline
        upper = stmt.raw_text.upper()
        if "END-READ" in upper or "AT END" not in upper:
            # Simple READ or self-contained READ
            idx += 1
            return idx

        # Multi-statement READ block
        in_at_end = False
        in_not_at_end = False
        at_end_stmts = []
        not_at_end_stmts = []
        idx += 1

        while idx < len(stmts):
            text = stmts[idx]
            upper_text = text.upper().rstrip(".")
            first_word = _first_word(upper_text)

            if first_word == "END-READ":
                idx += 1
                break

            if upper_text.startswith("AT END") or upper_text == "AT END":
                in_at_end = True
                in_not_at_end = False
                idx += 1
                continue

            if upper_text.startswith("NOT AT END") or upper_text == "NOT AT END":
                in_not_at_end = True
                in_at_end = False
                idx += 1
                continue

            child = self._classify_statement(text)
            if child:
                if in_not_at_end:
                    not_at_end_stmts.append(child)
                elif in_at_end:
                    at_end_stmts.append(child)

            idx += 1

        # Store block children: AT END in else_children, NOT AT END in children
        stmt.children = not_at_end_stmts
        stmt.else_children = at_end_stmts
        return idx
