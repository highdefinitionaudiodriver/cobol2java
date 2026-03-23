"""
Structured PROCEDURE DIVISION parser.
Replaces the ad-hoc regex-based classification and block parsing
with a formally structured recursive descent parser.

Key improvements over the original:
- Statement classification via declarative verb registry (easy to extend)
- Unified block parser handles IF, EVALUATE, READ, PERFORM blocks
- Better separation of concerns: segmentation → classification → block building
- Extensible for new COBOL block constructs without code duplication
"""
import re
from typing import List, Optional, Tuple, Dict, Callable
from .cobol_parser import (
    Statement, StatementType, Paragraph, Section, CobolProgram,
    COBOL_VERBS, BLOCK_TERMINATORS, _first_word, _is_verb_start,
)


# ============================================================
# Verb Registry: declarative mapping of COBOL verbs to types
# ============================================================

# Single-word verbs
_SINGLE_VERB_MAP: Dict[str, StatementType] = {
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
    "INVOKE": StatementType.INVOKE,
    "ENTER": StatementType.ENTER,
}

# Two-word verb compounds: (first, second) -> StatementType
_COMPOUND_VERB_MAP: Dict[Tuple[str, str], StatementType] = {
    ("STOP", "RUN"): StatementType.STOP_RUN,
    ("GO", "TO"): StatementType.GO_TO,
    ("XML", "GENERATE"): StatementType.XML_GENERATE,
    ("XML", "PARSE"): StatementType.XML_PARSE,
    ("JSON", "GENERATE"): StatementType.JSON_GENERATE,
    ("JSON", "PARSE"): StatementType.JSON_PARSE,
}

# EXEC sub-type mapping
_EXEC_TYPE_MAP: Dict[str, StatementType] = {
    "SQL": StatementType.EXEC_SQL,
    "CICS": StatementType.EXEC_CICS,
    "DLI": StatementType.EXEC_DLI,
}

# Block statement types that need recursive parsing
_BLOCK_STARTERS = {
    StatementType.IF,
    StatementType.EVALUATE,
    StatementType.READ,
}


# ============================================================
# Statement Classifier
# ============================================================

class StatementClassifier:
    """Classifies raw statement text into typed Statement objects."""

    def classify(self, text: str) -> Optional[Statement]:
        """Classify a segmented statement text into a Statement object."""
        stripped = text.strip().rstrip(".")
        if not stripped:
            return None

        tokens = stripped.split()
        first = tokens[0].upper() if tokens else ""

        # Skip block terminators and control keywords (handled by block parsers)
        if first in BLOCK_TERMINATORS or first in ("ELSE", "WHEN"):
            return None

        # EXEC blocks
        if first == "EXEC":
            return self._classify_exec(stripped, tokens)

        # Compound verbs (two-word)
        if len(tokens) > 1:
            compound = (first, tokens[1].upper())
            if compound in _COMPOUND_VERB_MAP:
                return Statement(
                    type=_COMPOUND_VERB_MAP[compound],
                    raw_text=stripped,
                    tokens=tokens,
                )

        # Single-word verbs
        stmt_type = _SINGLE_VERB_MAP.get(first, StatementType.UNKNOWN)
        return Statement(type=stmt_type, raw_text=stripped, tokens=tokens)

    def _classify_exec(self, stripped: str, tokens: List[str]) -> Statement:
        """Classify EXEC ... END-EXEC statements."""
        exec_type = tokens[1].upper() if len(tokens) > 1 else "OTHER"
        stmt_type = _EXEC_TYPE_MAP.get(exec_type, StatementType.EXEC_OTHER)
        return Statement(type=stmt_type, raw_text=stripped, tokens=tokens)


# ============================================================
# Block Parser: unified recursive descent
# ============================================================

class BlockParser:
    """Parses block structures (IF, EVALUATE, READ) recursively."""

    def __init__(self, classifier: StatementClassifier):
        self.classifier = classifier

    def parse_block(self, stmts: List[str], idx: int,
                    stmt: Statement) -> int:
        """Dispatch to the appropriate block parser based on statement type."""
        if stmt.type == StatementType.IF:
            return self._parse_if(stmts, idx, stmt)
        elif stmt.type == StatementType.EVALUATE:
            return self._parse_evaluate(stmts, idx, stmt)
        elif stmt.type == StatementType.READ:
            return self._parse_read(stmts, idx, stmt)
        return idx + 1

    def _parse_child(self, stmts: List[str], idx: int,
                     text: str) -> Tuple[Optional[Statement], int]:
        """Parse a child statement, handling nested blocks."""
        child = self.classifier.classify(text)
        if child and child.type in _BLOCK_STARTERS:
            idx = self.parse_block(stmts, idx, child)
            return child, idx
        if child:
            return child, idx + 1
        return None, idx + 1

    def _parse_if(self, stmts: List[str], idx: int,
                  stmt: Statement) -> int:
        """Parse IF / ELSE / END-IF block."""
        in_else = False
        idx += 1

        while idx < len(stmts):
            text = stmts[idx]
            first = _first_word(text.upper().rstrip("."))

            if first == "END-IF":
                return idx + 1

            if first == "ELSE":
                in_else = True
                idx += 1
                continue

            child, idx = self._parse_child(stmts, idx, text)
            if child:
                if in_else:
                    stmt.else_children.append(child)
                else:
                    stmt.children.append(child)
            # idx already advanced by _parse_child

        return idx

    def _parse_evaluate(self, stmts: List[str], idx: int,
                        stmt: Statement) -> int:
        """Parse EVALUATE / WHEN / END-EVALUATE block."""
        current_when_value = ""
        current_when_stmts: List[Statement] = []
        idx += 1

        while idx < len(stmts):
            text = stmts[idx]
            first = _first_word(text.upper().rstrip("."))

            if first == "END-EVALUATE":
                if current_when_value:
                    stmt.when_blocks.append((current_when_value, current_when_stmts))
                return idx + 1

            if first == "WHEN":
                if current_when_value:
                    stmt.when_blocks.append((current_when_value, current_when_stmts))
                current_when_value = text.strip().rstrip(".")[5:].strip()
                current_when_stmts = []
                idx += 1
                continue

            child, idx = self._parse_child(stmts, idx, text)
            if child:
                current_when_stmts.append(child)

        if current_when_value:
            stmt.when_blocks.append((current_when_value, current_when_stmts))
        return idx

    def _parse_read(self, stmts: List[str], idx: int,
                    stmt: Statement) -> int:
        """Parse READ / AT END / NOT AT END / END-READ block."""
        upper = stmt.raw_text.upper()
        if "END-READ" in upper or "AT END" not in upper:
            return idx + 1

        in_at_end = False
        in_not_at_end = False
        at_end_stmts: List[Statement] = []
        not_at_end_stmts: List[Statement] = []
        idx += 1

        while idx < len(stmts):
            text = stmts[idx]
            upper_text = text.upper().rstrip(".")
            first = _first_word(upper_text)

            if first == "END-READ":
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

            child, idx = self._parse_child(stmts, idx, text)
            if child:
                if in_not_at_end:
                    not_at_end_stmts.append(child)
                elif in_at_end:
                    at_end_stmts.append(child)

        stmt.children = not_at_end_stmts
        stmt.else_children = at_end_stmts
        return idx


# ============================================================
# Procedure Division Parser
# ============================================================

class ProcedureDivisionParser:
    """
    Structured parser for the PROCEDURE DIVISION.
    Segments lines into statements, classifies them, and
    builds the paragraph/section/statement tree.
    """

    def __init__(self):
        self.classifier = StatementClassifier()
        self.block_parser = BlockParser(self.classifier)

    def parse(self, proc_statements: List[str], program: CobolProgram):
        """Parse segmented procedure statements into the program structure."""
        current_paragraph = None
        current_section = None
        idx = 0

        while idx < len(proc_statements):
            stmt_text = proc_statements[idx]
            upper = stmt_text.upper().rstrip(".")

            # Section header: NAME SECTION.
            section_match = re.match(
                r'^([A-Z0-9][-A-Z0-9]*)\s+SECTION\s*\.?$', upper
            )
            if section_match:
                current_section = Section(name=section_match.group(1))
                program.sections.append(current_section)
                current_paragraph = None
                idx += 1
                continue

            # Paragraph header: NAME. (not a verb, not a terminator)
            para_match = re.match(r'^([A-Z0-9][-A-Z0-9]*)\s*\.?$', upper)
            if para_match and not _is_verb_start(upper.rstrip(".")):
                para_name = para_match.group(1)
                if para_name not in BLOCK_TERMINATORS and \
                   para_name not in ("ELSE", "WHEN"):
                    current_paragraph = Paragraph(name=para_name)
                    if current_section:
                        current_section.paragraphs.append(current_paragraph)
                    else:
                        program.paragraphs.append(current_paragraph)
                    idx += 1
                    continue

            # Auto-create paragraph if needed
            if current_paragraph is None:
                current_paragraph = Paragraph(name="MAIN")
                if current_section:
                    current_section.paragraphs.append(current_paragraph)
                else:
                    program.paragraphs.append(current_paragraph)

            # Classify and handle statement
            stmt = self.classifier.classify(stmt_text)
            if stmt:
                # Track EXEC flags
                self._track_exec_flags(stmt, program)

                # Track CALL targets
                if stmt.type == StatementType.CALL:
                    call_match = re.search(
                        r'CALL\s+["\'](\S+)["\']',
                        stmt_text, re.IGNORECASE
                    )
                    if call_match:
                        program.called_programs.append(call_match.group(1))

                # Handle block structures
                if stmt.type in _BLOCK_STARTERS:
                    idx = self.block_parser.parse_block(
                        proc_statements, idx, stmt
                    )
                    current_paragraph.statements.append(stmt)
                    continue
                else:
                    current_paragraph.statements.append(stmt)

            idx += 1

    def _track_exec_flags(self, stmt: Statement, program: CobolProgram):
        """Track EXEC SQL/CICS/DLI flags on the program."""
        if stmt.type == StatementType.EXEC_SQL:
            program.has_exec_sql = True
        elif stmt.type == StatementType.EXEC_CICS:
            program.has_exec_cics = True
        elif stmt.type == StatementType.EXEC_DLI:
            program.has_exec_dli = True
