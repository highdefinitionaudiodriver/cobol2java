# cobol2java - COBOL→Java 変換ツール v2.1.0

A desktop GUI and Command Line (CLI) tool for COBOL modernization assessment and Java migration scaffolding — with object-oriented transformation, vendor dialect analysis, pluggable conversion strategies, and 59-language UI localization.

## 主な機能

- Smart OOP Transformation — Generates Java OOP migration candidates from procedural COBOL, including encapsulation, getters/setters, toString(), and Javadoc
- Structured Parser Architecture — Three-phase parser pipeline (DATA DIVISION → PROCEDURE DIVISION → Division-level integration) with declarative verb registry and recursive descent block parsing
- 10 Vendor Dialects — Supports IBM Enterprise COBOL, Fujitsu NetCOBOL, NEC ACOS, Hitachi VOS3, Micro Focus Visual COBOL, Unisys MCP/ClearPath, Bull/Atos GCOS, HP NonStop, GnuCOBOL, and standard COBOL-85/2002/2014
- EXEC SQL / CICS / DLI — Handles embedded SQL, CICS transactions, and IMS/DLI calls with appropriate Java equivalents
- Pluggable Conversion Strategies — Strategy Pattern interfaces for File I/O, SQL, and CICS conversion — swap between JDBC, JPA/Hibernate, VSAM-to-DB, and custom backends
- Auto Vendor Detection — Automatically identifies the COBOL dialect from source code patterns
- 59-Language UI — Fully localized interface covering East Asia, Southeast Asia, South Asia, Europe, Middle East, Africa, and more
- Recursive Subfolder Conversion — Processes COBOL files in nested subfolders, preserving the directory structure in output

## 動作環境

- Windows 10/11, macOS 12+, Linux / Python 3.10 以上

## ダウンロード

- `*.zip` … 実行ファイル一式（解凍してそのまま実行）
- ソースコードは下記リポジトリを参照

## ライセンス / 連絡先

- MIT License
- https://github.com/highdefinitionaudiodriver/cobol2java
- highdefinitionaudiodriver@gmail.com

## 変更履歴

（`CHANGELOG.md` の該当バージョンを転記してください）
