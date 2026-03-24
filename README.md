# COBOL2Java

A desktop GUI and Command Line (CLI) tool that converts COBOL source code into modern, idiomatic Java — with full object-oriented transformation, vendor dialect support, pluggable conversion strategies, and 59-language UI localization.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)
![Languages](https://img.shields.io/badge/UI_Languages-59-orange)
![Tests](https://img.shields.io/badge/Tests-184%20passed-brightgreen)

## Overview

COBOL2Java parses COBOL source files and generates clean, well-structured Java code. Unlike simple line-by-line translators, it performs a full semantic transformation — extracting data classes, enums, service layers, and file handlers into proper Java OOP patterns.

### Key Features

- **Smart OOP Transformation** — Converts procedural COBOL into idiomatic Java classes with proper encapsulation, getters/setters, `toString()`, and Javadoc
- **Structured Parser Architecture** — Three-phase parser pipeline (DATA DIVISION → PROCEDURE DIVISION → Division-level integration) with declarative verb registry and recursive descent block parsing
- **10 Vendor Dialects** — Supports IBM Enterprise COBOL, Fujitsu NetCOBOL, NEC ACOS, Hitachi VOS3, Micro Focus Visual COBOL, Unisys MCP/ClearPath, Bull/Atos GCOS, HP NonStop, GnuCOBOL, and standard COBOL-85/2002/2014
- **EXEC SQL / CICS / DLI** — Handles embedded SQL, CICS transactions, and IMS/DLI calls with appropriate Java equivalents
- **Pluggable Conversion Strategies** — Strategy Pattern interfaces for File I/O, SQL, and CICS conversion — swap between JDBC, JPA/Hibernate, VSAM-to-DB, and custom backends
- **Auto Vendor Detection** — Automatically identifies the COBOL dialect from source code patterns
- **59-Language UI** — Fully localized interface covering East Asia, Southeast Asia, South Asia, Europe, Middle East, Africa, and more
- **Recursive Subfolder Conversion** — Converts COBOL files in nested subfolders, preserving the directory structure in output
- **CLI & CI/CD Ready** — Headless command-line mode for bulk conversions and automated pipelines
- **MVC Architecture** — Clean separation of Model, View, and Controller for the GUI application

## Quick Start

### Option 1: Run the Pre-built Binary

Download the executable for your OS (`COBOL2Java.exe` for Windows, or the respective Linux/macOS binary) from the [Releases](https://github.com/highdefinitionaudiodriver/cobol2java/releases) page and run it directly. No installation needed.

### Option 2: Run from Source

```bash
# Clone the repository
git clone https://github.com/highdefinitionaudiodriver/cobol2java.git
cd cobol2java

# Install dependencies (only PyInstaller for building; the tool itself has no runtime deps)
pip install -r requirements.txt

# Run the GUI
python main.py
```

### Option 3: Build Your Own Binary

```bash
# On Windows
build.bat
# Output: dist/COBOL2Java.exe

# On macOS / Linux
chmod +x build.sh
./build.sh
# Output: dist/COBOL2Java
```

## Usage

### GUI Mode
1. **Launch** the application (`python main.py`, `COBOL2Java.exe`, or `./COBOL2Java`)
2. **Select Input Folder** — directory containing `.cbl`, `.cob`, or `.cobol` files
3. **Select Output Folder** — where generated Java files will be written
4. **Configure Options:**
   - **Package Name** — Java package for generated classes (default: `com.migrated`)
   - **Source Encoding** — character encoding of COBOL files (UTF-8, Shift_JIS, EUC-JP, etc.)
   - **File Extensions** — which extensions to scan (default: `.cbl,.cob,.cobol,.CBL,.COB`)
   - **Vendor Dialect** — select a specific COBOL vendor or use Auto Detect
   - **Checkboxes** — toggle getters/setters, BigDecimal, Javadoc, class extraction, etc.
5. **Click Convert** and monitor progress in the log panel

### CLI Mode (Headless)
You can run the tool from the terminal for automated pipelines or batch processing. Providing both `-i` and `-o` will automatically launch CLI mode.

```bash
python main.py -i ./samples -o ./output --vendor auto --package com.example.migrated
# Or using the binary:
./COBOL2Java -i ./samples -o ./output
```

**Common Arguments:**
- `-i, --input`: Input folder (Required for CLI)
- `-o, --output`: Output folder (Required for CLI)
- `-p, --package`: Package name (default: `com.migrated`)
- `-e, --encoding`: Source file encoding (default: `utf-8`)
- `--vendor`: Dialect (`auto`, `standard`, `ibm`, `fujitsu`, `microfocus`, etc.)
- `--no-getters`: Disable generation of getters/setters
- `--no-javadoc`: Disable Javadoc comment generation

Run `python main.py --help` to see all available options.

## Architecture

```
cobol2java/
├── main.py                        # Entry point (CLI + GUI bootstrap)
├── src/
│   ├── cobol_parser.py            # COBOL lexer & parser → structured AST
│   ├── division_parser.py         # Division-level routing (ID/ENV/DATA/PROC)
│   ├── lark_data_parser.py        # Structured DATA DIVISION parser
│   ├── lark_procedure_parser.py   # Structured PROCEDURE DIVISION parser
│   ├── oop_transformer.py         # AST → Java OOP model (classes, enums, services)
│   ├── java_generator.py          # Java OOP model → .java source files
│   ├── conversion_strategies.py   # Strategy interfaces (File I/O, SQL, CICS)
│   ├── vendor_extensions.py       # Vendor-specific dialect handling (10 vendors)
│   ├── gui_model.py               # GUI Model layer (MVC)
│   ├── gui_view.py                # GUI View layer (MVC)
│   ├── gui_controller.py          # GUI Controller layer (MVC)
│   └── i18n.py                    # Internationalization (59 languages)
├── tests/
│   ├── conftest.py                # Shared pytest fixtures
│   ├── test_data_types.py         # COMP-3, POINTER, data type tests (30 tests)
│   ├── test_copy.py               # COPY statement tests (11 tests)
│   ├── test_control_flow.py       # PERFORM, GO TO, IF/EVALUATE tests (18 tests)
│   ├── test_lark_parser.py        # DATA DIVISION parser tests (37 tests)
│   ├── test_procedure_parser.py   # PROCEDURE DIVISION parser tests (56 tests)
│   └── test_strategies.py         # Conversion strategy tests (32 tests)
├── samples/                       # Sample COBOL programs for testing
├── build.bat / build.sh           # Build scripts (PyInstaller)
└── requirements.txt               # Python dependencies
```

### Conversion Pipeline

```
COBOL Source (.cbl)
    │
    ▼
┌─────────────────────┐
│ CobolParser           │  Preprocessor (fixed/free format) →
│  ├─ DivisionRouter    │  Division detection & dispatch →
│  ├─ LarkDataParser    │  Structured DATA DIVISION parsing →
│  └─ ProcedureParser   │  Declarative verb classification &
│                       │  recursive descent block parsing
└──────────┬────────────┘
           │  CobolProgram (AST)
           ▼
┌─────────────────────┐
│ OopTransformer       │  Extract data classes, enums, service classes,
│                      │  file handlers; map COBOL types → Java types
│                      │  (uses ConversionStrategyRegistry)
└──────────┬──────────┘
           │  JavaProject (OOP model)
           ▼
┌─────────────────────┐
│ JavaCodeGenerator    │  Emit .java files with proper imports, Javadoc,
│                      │  getters/setters, toString(), and formatting
│                      │  (delegates to Strategy for SQL/File I/O/CICS)
└──────────┬──────────┘
           │
           ▼
     Java Source Files (.java)
```

### Conversion Strategy Extension Points

The conversion engine provides pluggable Strategy interfaces for customizing how COBOL constructs map to Java:

| Strategy Interface | Purpose | Default | Alternatives |
|---|---|---|---|
| `FileIoStrategy` | OPEN/CLOSE/READ/WRITE | `DefaultFileIoStrategy` (java.io) | `VsamToDatabaseStrategy` (JDBC) |
| `SqlConversionStrategy` | EXEC SQL | `JdbcSqlStrategy` (PreparedStatement) | `JpaSqlStrategy` (EntityManager) |
| `CicsConversionStrategy` | EXEC CICS | `DefaultCicsStrategy` (abstract interface) | Custom implementation |

**Usage example:**
```python
from src.conversion_strategies import ConversionStrategyRegistry, JpaSqlStrategy, VsamToDatabaseStrategy
from src.java_generator import JavaCodeGenerator
from src.oop_transformer import OopTransformer

# Create a custom strategy registry
registry = ConversionStrategyRegistry()
registry.sql = JpaSqlStrategy()              # EXEC SQL → JPA/Hibernate
registry.file_io = VsamToDatabaseStrategy()  # VSAM → Database tables

# Pass to transformer and generator
transformer = OopTransformer(options, strategy_registry=registry)
generator = JavaCodeGenerator(options, strategy_registry=registry)
```

## Supported Vendor Dialects

| Vendor | Dialect | Key Extensions |
|--------|---------|----------------|
| **IBM** | Enterprise COBOL / z/OS | EXEC CICS, EXEC SQL, EXEC DLI, COMP-5 |
| **Fujitsu** | NetCOBOL | SCREEN SECTION, PIC N, FORMAT |
| **NEC** | ACOS-4 COBOL | ACOS-specific file I/O, custom ACCEPT/DISPLAY |
| **Hitachi** | VOS3 / COBOL2002 | OO extensions, custom PIC clauses |
| **Micro Focus** | Visual COBOL | OO COBOL, .NET/JVM interop, embedded SQL |
| **Unisys** | MCP / ClearPath | Custom I/O, SCREEN handling |
| **Bull/Atos** | GCOS COBOL | GCOS-specific extensions |
| **HP/Tandem** | NonStop COBOL | GUARDIAN API, TAL interop |
| **GnuCOBOL** | OpenCOBOL | CBL_* runtime calls, OSS extensions |
| **Standard** | COBOL-85/2002/2014 | Full standard compliance |

## Supported Languages (UI)

The interface is fully localized in 59 languages:

| Region | Languages |
|--------|-----------|
| **East Asia** | English, 日本語, 中文, 한국어 |
| **Southeast Asia** | ไทย, Tiếng Việt, Bahasa Indonesia, Bahasa Melayu, မြန်မာ, ខ្មែរ, ລາວ, Filipino |
| **South Asia** | हिन्दी, বাংলা, தமிழ், తెలుగు, मराठी, ગુજરાતી, ಕನ್ನಡ, മലയാളം, नेपाली, සිංහල, اردو |
| **Western Europe** | Français, Deutsch, Italiano, Español, Português, Nederlands, Català, Euskara, Galego |
| **Northern Europe** | Svenska, Dansk, Suomi, Norsk |
| **Eastern Europe** | Русский, Українська, Polski, Čeština, Magyar, Română, Български, Hrvatski, Slovenčina, Slovenščina, Srpski, Lietuvių, Latviešu, Eesti |
| **Middle East** | العربية, עברית, فارسی, Türkçe |
| **Caucasus** | ქართული |
| **Africa** | Kiswahili, Afrikaans, አማርኛ |
| **Southern Europe** | Ελληνικά |

## Testing

```bash
# Run all 184 tests
python -m pytest tests/ -v

# Run specific test suites
python -m pytest tests/test_strategies.py -v      # Conversion strategies
python -m pytest tests/test_procedure_parser.py -v # PROCEDURE DIVISION parser
python -m pytest tests/test_lark_parser.py -v      # DATA DIVISION parser
python -m pytest tests/test_data_types.py -v       # Data type mapping
```

## Requirements

- **Python 3.8+** (for running from source)
- **PyInstaller 5.0+** (only for building the EXE)
- **pytest** (for running tests)
- **No runtime dependencies** — the tool uses only Python standard library (`tkinter`, `re`, `dataclasses`, `threading`)

## Contributing

Bug reports and feature requests are welcome via [GitHub Issues](https://github.com/highdefinitionaudiodriver/cobol2java/issues).

## Author

**highdefinitionaudiodriver** — [GitHub](https://github.com/highdefinitionaudiodriver)

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
