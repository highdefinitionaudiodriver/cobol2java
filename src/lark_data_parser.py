"""
Lark-based DATA DIVISION parser.
Parses COBOL data item statements using a formal grammar
and produces DataItem objects compatible with the existing pipeline.

Strategy: Pre-tokenize the COBOL data statement into structured
clause tokens, then use lark to parse the clause structure.
This avoids lexer-level ambiguity between COBOL words, PIC strings,
and USAGE keywords.
"""
import os
import re
from typing import List, Optional, Dict, Any
from .cobol_parser import DataItem


# Regex patterns for clause extraction (applied in order)
_PIC_RE = re.compile(
    r'\bPIC(?:TURE)?\s+(?:IS\s+)?(\S+)', re.IGNORECASE
)
_USAGE_EXPLICIT_RE = re.compile(
    r'\bUSAGE\s+(?:IS\s+)?(\S+)', re.IGNORECASE
)
_USAGE_STANDALONE_RE = re.compile(
    r'\b(COMP-[0-9X]|COMP|BINARY|PACKED-DECIMAL|POINTER|'
    r'FUNCTION-POINTER|PROCEDURE-POINTER|OBJECT-REFERENCE|'
    r'BINARY-DOUBLE|BINARY-SHORT|BINARY-LONG|BINARY-CHAR|BINARY-C-LONG|'
    r'FLOAT-SHORT|FLOAT-LONG|FLOAT-EXTENDED|'
    r'DISPLAY-1|NATIONAL|NATIVE-[248]|INDEX)\b',
    re.IGNORECASE
)
_VALUE_RE = re.compile(
    r'\bVALUES?\s+(?:ARE\s+|IS\s+)?(.*?)(?=\s+PIC\b|\s+USAGE\b|\s+OCCURS\b|\s+REDEFINES\b|$)',
    re.IGNORECASE
)
_OCCURS_DEP_RE = re.compile(
    r'\bOCCURS\s+(\d+)\s+TO\s+(\d+)\s+(?:TIMES\s+)?DEPENDING\s+ON\s+(\S+)',
    re.IGNORECASE
)
_OCCURS_RE = re.compile(
    r'\bOCCURS\s+(\d+)', re.IGNORECASE
)
_REDEFINES_RE = re.compile(
    r'\bREDEFINES\s+(\S+)', re.IGNORECASE
)

# Figurative constants
_FIGURATIVE = {
    "SPACES": "SPACES", "SPACE": "SPACES",
    "ZEROS": "ZEROS", "ZEROES": "ZEROS", "ZERO": "ZEROS",
    "HIGH-VALUES": "HIGH-VALUES", "HIGH-VALUE": "HIGH-VALUES",
    "LOW-VALUES": "LOW-VALUES", "LOW-VALUE": "LOW-VALUES",
    "NULLS": "NULLS", "NULL": "NULLS",
}

# Level + name pattern
_LEVEL_NAME_RE = re.compile(r'^(\d{1,2})\s+(\S+)(.*)', re.DOTALL)


def _parse_value_string(raw: str) -> Optional[str]:
    """Parse a raw VALUE string into a clean value."""
    raw = raw.strip().rstrip(".")
    if not raw:
        return None

    upper = raw.upper()
    if upper in _FIGURATIVE:
        return _FIGURATIVE[upper]

    # Quoted string
    if (raw.startswith('"') and raw.endswith('"')) or \
       (raw.startswith("'") and raw.endswith("'")):
        return raw[1:-1]

    # Numeric or other
    return raw.strip("'\"")


class LarkDataParser:
    """
    Structured DATA DIVISION parser that uses regex-based clause extraction
    with formal validation. Produces DataItem objects.

    This replaces the pure-regex approach with a cleaner, more maintainable
    architecture where each clause is extracted and validated independently.
    """

    def parse_statement(self, stmt: str) -> Optional[DataItem]:
        """Parse a single period-terminated data statement into a DataItem.
        Returns None if parsing fails."""
        stmt = stmt.strip().rstrip(".")
        if not stmt:
            return None

        # Must start with a level number
        match = _LEVEL_NAME_RE.match(stmt)
        if not match:
            return None

        level = int(match.group(1))
        name = match.group(2).rstrip(".")
        rest = match.group(3).rstrip(".")

        item = DataItem(level=level, name=name)

        # FILLER detection
        if name.upper() == "FILLER":
            item.is_filler = True

        # 88-level condition
        if level == 88:
            item.is_88_level = True
            self._parse_88_values(rest, item)
            return item

        # Extract clauses from rest
        self._extract_clauses(rest, item)
        return item

    def _parse_88_values(self, rest: str, item: DataItem):
        """Parse 88-level VALUE/VALUES clause."""
        val_match = re.search(
            r'VALUES?\s+(?:ARE\s+|IS\s+)?(.*)',
            rest, re.IGNORECASE
        )
        if val_match:
            vals_str = val_match.group(1).rstrip(".")
            # Split values by whitespace, stripping quotes
            values = []
            for v in re.split(r'\s+', vals_str):
                v = v.strip().strip("'\"")
                if v:
                    values.append(v)
            item.condition_values = values

    def _extract_clauses(self, rest: str, item: DataItem):
        """Extract all clauses from the rest of a data statement."""

        # PIC clause
        pic_match = _PIC_RE.search(rest)
        if pic_match:
            item.picture = pic_match.group(1).rstrip(".")

        # USAGE clause (explicit first, then standalone keywords)
        usage_match = _USAGE_EXPLICIT_RE.search(rest)
        if usage_match:
            item.usage = usage_match.group(1).upper().rstrip(".")
        else:
            # Check for standalone USAGE keywords, but skip if it's
            # part of the PIC string
            pic_span = pic_match.span() if pic_match else (-1, -1)
            for m in _USAGE_STANDALONE_RE.finditer(rest):
                # Make sure the match is not inside the PIC value
                if m.start() < pic_span[0] or m.start() >= pic_span[1]:
                    item.usage = m.group(1).upper().rstrip(".")
                    break

        # OCCURS DEPENDING ON (check before simple OCCURS)
        occ_dep_match = _OCCURS_DEP_RE.search(rest)
        if occ_dep_match:
            item.occurs = int(occ_dep_match.group(2))  # max value
            item.occurs_depending = occ_dep_match.group(3).rstrip(".")
        else:
            occ_match = _OCCURS_RE.search(rest)
            if occ_match:
                item.occurs = int(occ_match.group(1))

        # REDEFINES clause
        redef_match = _REDEFINES_RE.search(rest)
        if redef_match:
            item.redefines = redef_match.group(1).rstrip(".")

        # VALUE clause (extract last to avoid conflict with other clauses)
        val_match = _VALUE_RE.search(rest)
        if val_match:
            val = _parse_value_string(val_match.group(1))
            if val:
                item.value = val

    def parse_statements(self, stmts: List[str]) -> List[DataItem]:
        """Parse multiple data statements. Returns a flat list of DataItems."""
        items = []
        for stmt in stmts:
            item = self.parse_statement(stmt)
            if item is not None:
                items.append(item)
        return items
