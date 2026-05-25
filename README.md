# COBOL2Java

A desktop GUI and Command Line (CLI) tool for COBOL modernization assessment and Java migration scaffolding — with object-oriented transformation, vendor dialect analysis, pluggable conversion strategies, and 59-language UI localization.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)
![Languages](https://img.shields.io/badge/UI_Languages-59-orange)
![Tests](https://img.shields.io/badge/Tests-184%20passed-brightgreen)

## Overview

COBOL2Java parses COBOL source files and generates structured Java migration candidates. Unlike simple line-by-line translators, it performs semantic analysis and produces a modernization baseline: data classes, enums, service layers, file handlers, and reviewable Java code that can be used for impact analysis, estimation, and staged refactoring.

> Positioning: this project is best used as a legacy asset diagnostic and migration planning tool. It helps teams understand what can be converted, what needs human review, and where the high-risk COBOL constructs are before a production modernization project begins.

---

## 🎯 これは何？（30秒で）

- **誰のため**：金融・自治体・保険系で COBOL/メインフレーム資産を抱える情シス・保守 SE／レガシー刷新の PoC を企画している SI ベンダー
- **何が解決される**：「自社の COBOL 資産は Java へどれくらい移行可能か」を、**完全自動変換ではなく「設計書たたき台＋影響分析＋移行難易度スコア」** として可視化。COBOL 人材高齢化・属人化リスクへの初動材料を提供
- **なぜ既存ツールではダメか**：商用変換ツールは高額かつブラックボックス。本ツールは OSS で **10 ベンダー方言（IBM / Fujitsu / NEC / Hitachi / Micro Focus 等）対応・EXEC SQL/CICS/DLI 解析・OOP 変換** を行い、見積もりと意思決定の根拠を提供
- **使う条件**：Python 3.8+ / Windows・macOS・Linux／GUI または CLI

> ⚠️ **本ツールは「完全自動変換」を謳いません**。現実の COBOL 資産（特に金融）は地雷原です。本ツールが出すのは Java 化の**たたき台・影響分析・難易度スコア**であり、最終成果物には人手レビューが必須です。この姿勢を明示することで、PoC 後の信頼性を担保します。

## 💰 想定ユースケース・価格帯

| 用途 | 形態 |
|---|---|
| OSS としての利用（自社 PoC・社内見積もり） | 無料（MIT） |
| サンプル資産の **難易度評価レポート受託** | 応相談 |
| 金融・公共向け **アセスメント支援・追加方言対応・カスタムルール開発** | 個別見積もり |

---

## 🎬 デモ / まず見るもの

<!-- docs/demo.gif に「COBOLフォルダ選択 → 難易度スコアリング → CSV/HTMLレポート確認」までの30秒デモGIFを配置してください。 -->
![COBOL2Java demo](docs/demo.gif)

移行前アセスメントだけを素早く見せる場合：

```bash
python scripts/difficulty_scorer.py examples/sample_legacy_app --html cobol_migration_summary.html
```

出力されるスコアは、完全自動変換の約束ではなく、見積もり・PoC範囲・人手レビュー範囲を決めるための材料です。

---

### Business Use Cases

- COBOL asset inventory and modernization difficulty assessment
- Java migration proof-of-concept generation for stakeholder review
- Impact analysis for EXEC SQL, CICS, DLI, vendor dialects, and file I/O patterns
- Early estimation material for financial, public-sector, insurance, and mainframe renewal projects

### Key Features

- **Smart OOP Transformation** — Generates Java OOP migration candidates from procedural COBOL, including encapsulation, getters/setters, `toString()`, and Javadoc
- **Structured Parser Architecture** — Three-phase parser pipeline (DATA DIVISION → PROCEDURE DIVISION → Division-level integration) with declarative verb registry and recursive descent block parsing
- **10 Vendor Dialects** — Supports IBM Enterprise COBOL, Fujitsu NetCOBOL, NEC ACOS, Hitachi VOS3, Micro Focus Visual COBOL, Unisys MCP/ClearPath, Bull/Atos GCOS, HP NonStop, GnuCOBOL, and standard COBOL-85/2002/2014
- **EXEC SQL / CICS / DLI** — Handles embedded SQL, CICS transactions, and IMS/DLI calls with appropriate Java equivalents
- **Pluggable Conversion Strategies** — Strategy Pattern interfaces for File I/O, SQL, and CICS conversion — swap between JDBC, JPA/Hibernate, VSAM-to-DB, and custom backends
- **Auto Vendor Detection** — Automatically identifies the COBOL dialect from source code patterns
- **59-Language UI** — Fully localized interface covering East Asia, Southeast Asia, South Asia, Europe, Middle East, Africa, and more
- **Recursive Subfolder Conversion** — Processes COBOL files in nested subfolders, preserving the directory structure in output
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

---

## 🤝 商用利用・カスタマイズ依頼

- 個人・社内 PoC 利用は無料（MIT ライセンス）
- 自社 COBOL 資産の難易度評価レポート、独自方言サポート、業界特化（金融・公共）の追加ルール開発は応相談
- 連絡先：highdefinitionaudiodriver@gmail.com

<!-- CODEX-CURRENT-STATUS:START -->
## 現状サマリ (2026-05-25)

- 対象: COBOL2Java
- 作業ブランチ: feat/sellable-v1
- README更新時点の参照コミット: f4939b9 test: add missing cobol test sample files and fix parser usage clause regex
- Python 実行環境向けに requirements.txt を同梱。
- docs ディレクトリ配下に設計・運用・補足資料を配置。
- tests ディレクトリ配下にテストを配置。
- src ディレクトリ配下に主要実装を配置。
- 主要な確認コマンド: python -m pytest または README 記載の Python コマンド
- 次に進めるなら、README 内の利用手順と既存 docs / tests を起点に、未整備の検証手順・引き継ぎメモ・CI 化を補強する。
<!-- CODEX-CURRENT-STATUS:END -->

