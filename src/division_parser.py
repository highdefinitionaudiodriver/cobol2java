"""
Unified Division-level COBOL parser.
Handles the top-level program structure: division detection, dispatching,
and section-level routing for IDENTIFICATION, ENVIRONMENT, and DATA divisions.

This module provides a clean separation of concerns:
- Preprocessor: handles fixed/free format, comments, continuations
- DivisionRouter: detects divisions and dispatches to handlers
- IdentificationParser: extracts PROGRAM-ID, AUTHOR, etc.
- EnvironmentParser: extracts SELECT/ASSIGN/FILE-CONTROL
- DataSectionRouter: routes to WORKING-STORAGE, LINKAGE, FILE sections
"""
import re
from typing import List, Tuple, Optional
from .cobol_parser import (
    CobolProgram, DataItem, FileDefinition,
)


# ============================================================
# Division boundary keywords
# ============================================================

_DIVISION_KEYWORDS = {
    "IDENTIFICATION": ("IDENTIFICATION DIVISION", "ID DIVISION"),
    "ENVIRONMENT": ("ENVIRONMENT DIVISION",),
    "DATA": ("DATA DIVISION",),
    "PROCEDURE": ("PROCEDURE DIVISION",),
}

_DATA_SECTION_KEYWORDS = (
    "WORKING-STORAGE SECTION",
    "LOCAL-STORAGE SECTION",
    "LINKAGE SECTION",
    "FILE SECTION",
    "SCREEN SECTION",
    "REPORT SECTION",
    "COMMUNICATION SECTION",
)

_DATA_SECTION_MAP = {
    "WORKING-STORAGE SECTION": "working_storage",
    "LOCAL-STORAGE SECTION": "local_storage",
    "LINKAGE SECTION": "linkage_section",
    "SCREEN SECTION": "screen_section",
}


# ============================================================
# Preprocessor
# ============================================================

class CobolPreprocessor:
    """Handles fixed/free format detection, comment removal, and line continuations."""

    def process(self, raw_lines: List[str]) -> List[str]:
        """Preprocess raw source lines into clean content lines."""
        processed = self._process_fixed_format(raw_lines)

        # Fallback to free-format if fixed format yields poor results
        if not processed or all(len(line.strip()) < 3 for line in processed):
            processed = self._process_free_format(raw_lines)

        return processed

    def _process_fixed_format(self, raw_lines: List[str]) -> List[str]:
        """Process as fixed-format COBOL (columns 7-72)."""
        processed = []
        for line in raw_lines:
            line = line.rstrip("\n\r")

            if len(line) >= 7:
                indicator = line[6] if len(line) > 6 else " "
                # Comment or debug line
                if indicator in ("*", "/", "D", "d"):
                    continue
                # Continuation line
                if indicator == "-":
                    if processed:
                        cont = line[7:72].strip() if len(line) > 7 else ""
                        processed[-1] = processed[-1].rstrip() + " " + cont
                    continue
                content = line[6:72] if len(line) > 6 else ""
            else:
                content = line

            content = content.rstrip()
            if content.strip():
                processed.append(content.strip())

        return processed

    def _process_free_format(self, raw_lines: List[str]) -> List[str]:
        """Process as free-format COBOL."""
        processed = []
        for line in raw_lines:
            line = line.rstrip("\n\r").rstrip()
            if line.strip().startswith("*>"):
                continue
            if line.strip():
                processed.append(line.strip())
        return processed


# ============================================================
# Identification Division Parser
# ============================================================

class IdentificationParser:
    """Extracts PROGRAM-ID, CLASS-ID, AUTHOR, DATE-WRITTEN."""

    # Declarative field extraction rules
    _FIELD_PATTERNS = [
        ("PROGRAM-ID", r'PROGRAM-ID\.\s*(\S+)', "program_id"),
        ("CLASS-ID", r'CLASS-ID\.\s*(\S+)', "class_id"),
        ("AUTHOR", r'AUTHOR\.\s*(.*)', "author"),
        ("DATE-WRITTEN", r'DATE-WRITTEN\.\s*(.*)', "date_written"),
    ]

    def parse_line(self, line: str, program: CobolProgram):
        """Parse a single line from the IDENTIFICATION DIVISION."""
        upper = line.upper()
        for keyword, pattern, attr in self._FIELD_PATTERNS:
            if keyword in upper:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    value = match.group(1).rstrip(".")
                    setattr(program, attr, value)
                    # CLASS-ID also sets program_id and has_class_id
                    if attr == "class_id":
                        program.has_class_id = True
                        if not program.program_id:
                            program.program_id = value
                return


# ============================================================
# Environment Division Parser
# ============================================================

class EnvironmentParser:
    """Parses ENVIRONMENT DIVISION: SELECT/ASSIGN, COPY, FILE-CONTROL."""

    # Declarative clause extraction for SELECT statements
    _SELECT_CLAUSES = [
        ("select_name", r'SELECT\s+(\S+)'),
        ("assign_to", r'ASSIGN\s+TO\s+["\']?(\S+?)["\']?[\s.]'),
        ("organization", r'ORGANIZATION\s+IS\s+(\S+)'),
        ("file_status", r'FILE\s+STATUS\s+(?:IS\s+)?(\S+)'),
    ]

    def parse(self, lines: List[str], idx: int,
              program: CobolProgram) -> int:
        """Parse the ENVIRONMENT DIVISION. Returns next index."""
        while idx < len(lines):
            line = lines[idx]
            upper = line.upper()

            # Stop at next division
            if any(d in upper for d in ("DATA DIVISION", "PROCEDURE DIVISION")):
                return idx

            # SELECT statement
            if upper.startswith("SELECT"):
                idx = self._parse_select(lines, idx, program)
                continue

            # COPY statement
            copy_match = re.search(r'COPY\s+(\S+)', upper)
            if copy_match:
                program.copy_members.append(copy_match.group(1).rstrip("."))

            idx += 1
        return idx

    def _parse_select(self, lines: List[str], idx: int,
                      program: CobolProgram) -> int:
        """Parse a SELECT statement (may span multiple lines)."""
        select_text = lines[idx]
        while not select_text.rstrip().endswith(".") and idx + 1 < len(lines):
            idx += 1
            select_text += " " + lines[idx]

        file_def = FileDefinition()
        for attr, pattern in self._SELECT_CLAUSES:
            match = re.search(pattern, select_text, re.IGNORECASE)
            if match:
                setattr(file_def, attr, match.group(1).rstrip("."))

        program.files.append(file_def)
        idx += 1
        return idx


# ============================================================
# Data Section Router
# ============================================================

class DataSectionRouter:
    """Routes DATA DIVISION sections to appropriate parsers."""

    def __init__(self, cobol_parser):
        """Takes a reference to the CobolParser for data section parsing."""
        self._cobol_parser = cobol_parser

    def route(self, lines: List[str], idx: int, upper: str,
              program: CobolProgram) -> Optional[int]:
        """Route to the appropriate section parser. Returns new idx or None."""
        # Check standard sections (WORKING-STORAGE, LOCAL-STORAGE, etc.)
        for section_keyword, attr_name in _DATA_SECTION_MAP.items():
            if section_keyword in upper:
                target_list = getattr(program, attr_name)
                idx += 1
                return self._cobol_parser._parse_data_section(
                    lines, idx, target_list
                )

        # FILE SECTION
        if "FILE SECTION" in upper:
            idx += 1
            return self._cobol_parser._parse_file_section(lines, idx, program)

        return None


# ============================================================
# Division Router (main orchestrator)
# ============================================================

class DivisionRouter:
    """
    Top-level COBOL program parser.
    Detects divisions and dispatches to specialized parsers.
    """

    def __init__(self, cobol_parser):
        self.id_parser = IdentificationParser()
        self.env_parser = EnvironmentParser()
        self.data_router = DataSectionRouter(cobol_parser)
        self._cobol_parser = cobol_parser

    def parse(self, lines: List[str], program: CobolProgram):
        """Parse all divisions of a COBOL program."""
        self._cobol_parser._current_program = program
        idx = 0
        current_division = ""

        while idx < len(lines):
            line = lines[idx]
            upper = line.upper()

            # Division detection
            division = self._detect_division(upper)
            if division:
                current_division = division
                if division == "PROCEDURE":
                    idx += 1
                    self._cobol_parser._parse_procedure_division(
                        lines, idx, program
                    )
                    return
                idx += 1
                continue

            # Dispatch to division-specific parser
            if current_division == "IDENTIFICATION":
                self.id_parser.parse_line(line, program)
            elif current_division == "ENVIRONMENT":
                idx = self.env_parser.parse(lines, idx, program)
                continue
            elif current_division == "DATA":
                new_idx = self.data_router.route(
                    lines, idx, upper, program
                )
                if new_idx is not None:
                    idx = new_idx
                    continue

            idx += 1

    def _detect_division(self, upper: str) -> Optional[str]:
        """Detect which division a line belongs to."""
        for div_name, keywords in _DIVISION_KEYWORDS.items():
            for keyword in keywords:
                if keyword in upper:
                    return div_name
        return None
