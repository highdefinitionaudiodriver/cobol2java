---
title: "cobol2java - COBOL→Java 変換ツール を作った — ローカル完結で動かす実用ツール"
emoji: "🛠️"
type: "tech"
topics: ["python", "個人開発", "oss"]
published: false
---

> 本記事は Zenn 用の下書きです。Qiita に出す場合は先頭の frontmatter を削除してください。

## TL;DR

A desktop GUI and Command Line (CLI) tool for COBOL modernization assessment and Java migration scaffolding — with object-oriented transformation, vendor dialect analysis, pluggable conversion strategies, and 59-language UI localization.

- リポジトリ: https://github.com/highdefinitionaudiodriver/cobol2java
- ライセンス: MIT / バージョン: v2.1.0

## 作った背景・課題

（なぜ作ったか。既存ツールの不満、手作業の手間などを 2〜3 段落で。）

## できること

- Smart OOP Transformation — Generates Java OOP migration candidates from procedural COBOL, including encapsulation, getters/setters, toString(), and Javadoc
- Structured Parser Architecture — Three-phase parser pipeline (DATA DIVISION → PROCEDURE DIVISION → Division-level integration) with declarative verb registry and recursive descent block parsing
- 10 Vendor Dialects — Supports IBM Enterprise COBOL, Fujitsu NetCOBOL, NEC ACOS, Hitachi VOS3, Micro Focus Visual COBOL, Unisys MCP/ClearPath, Bull/Atos GCOS, HP NonStop, GnuCOBOL, and standard COBOL-85/2002/2014
- EXEC SQL / CICS / DLI — Handles embedded SQL, CICS transactions, and IMS/DLI calls with appropriate Java equivalents
- Pluggable Conversion Strategies — Strategy Pattern interfaces for File I/O, SQL, and CICS conversion — swap between JDBC, JPA/Hibernate, VSAM-to-DB, and custom backends
- Auto Vendor Detection — Automatically identifies the COBOL dialect from source code patterns
- 59-Language UI — Fully localized interface covering East Asia, Southeast Asia, South Asia, Europe, Middle East, Africa, and more
- Recursive Subfolder Conversion — Processes COBOL files in nested subfolders, preserving the directory structure in output

## 仕組み / 工夫した点

（設計上のポイント。ローカル完結・プライバシー配慮・依存の少なさ など。）

## 使い方

```bash
# インストール・起動例（README から転記）
```

## ハマったところ

（開発中の課題と解決。）

## おわりに

フィードバックは Issues / Star をいただけると励みになります。

リポジトリ: https://github.com/highdefinitionaudiodriver/cobol2java
