# COBOL ベンダー方言 対応マトリクス

本ドキュメントは COBOL2Java がサポートする COBOL ベンダー方言と、対応レベルの一覧です。
**移行プロジェクトの初期見積もり時、自社資産のベンダーがどの程度カバーされているかを判断する材料として使ってください。**

---

## 対応レベルの定義

| バッジ | 意味 |
|---|---|
| ✅ **Stable** | 主要構文・I/O・EXEC SQL を一通りカバー。実プロジェクトの PoC で使用実績あり |
| ⚠ **Beta** | パーサーは動作、Java 出力もされるが、ベンダー固有拡張の一部に未対応 |
| 🚧 **Experimental** | 主要構文のみ。ベンダー固有のサブシステム拡張は要レビュー |
| ❌ **Not Supported** | 未着手 |

---

## メインフレーム系

| ベンダー | 製品 | 対応状況 | 備考 |
|---|---|---|---|
| IBM | Enterprise COBOL for z/OS | ✅ Stable | CICS / DB2 EXEC SQL / VSAM 解析対応 |
| IBM | COBOL for AIX | ⚠ Beta | EXEC SQL 一部、CICS 未対応 |
| Fujitsu | NetCOBOL | ⚠ Beta | PowerBSORT / SYSOUT 自動置換対応 |
| Fujitsu | COBOL85 | 🚧 Experimental | 旧資産向け、構造体は基本対応 |
| NEC | ACOS COBOL | 🚧 Experimental | RIQS との接続箇所は要レビュー |
| Hitachi | VOS3 COBOL | 🚧 Experimental | 共通レコード辞書（COPY）対応 |
| Unisys | MCP / ClearPath COBOL | 🚧 Experimental | DMSII 接続は手動マッピング前提 |
| Bull / Atos | GCOS COBOL | 🚧 Experimental | IDS/II は対象外 |
| HP | NonStop COBOL | 🚧 Experimental | TMF トランザクション境界は要レビュー |

---

## オープン系・PC系

| ベンダー | 製品 | 対応状況 | 備考 |
|---|---|---|---|
| Micro Focus | Visual COBOL / Net Express | ✅ Stable | .NET COBOL の一部構文は要レビュー |
| Open Source | GnuCOBOL | ✅ Stable | リファレンス実装として活用 |
| 標準 | COBOL-85 / 2002 / 2014 | ✅ Stable | OOP COBOL 構文も基本対応 |

---

## サブシステム別対応状況

### EXEC SQL / 埋込 SQL

| データベース | 対応状況 | 備考 |
|---|---|---|
| IBM DB2 (z/OS) | ✅ Stable | カーソル・ホスト変数・SQLCA 対応 |
| Oracle Pro*COBOL | ⚠ Beta | カーソルは対応、PL/SQL 呼出は要レビュー |
| Microsoft SQL Server | ⚠ Beta | ストアド呼出の戻り値マッピングは手動 |

### CICS

| 機能 | 対応状況 | 出力先 |
|---|---|---|
| EXEC CICS SEND / RECEIVE | ⚠ Beta | Java の REST コントローラ雛形 |
| EXEC CICS LINK / XCTL | 🚧 Experimental | Java サービス呼出に変換、要レビュー |
| EXEC CICS READ / WRITE (VSAM) | 🚧 Experimental | JDBC または独自 DAO 雛形 |

### IMS / DLI

| 機能 | 対応状況 | 出力先 |
|---|---|---|
| EXEC DLI GET UNIQUE / NEXT | 🚧 Experimental | Java DAO 雛形（要設計レビュー） |
| EXEC DLI ISRT / DLET | 🚧 Experimental | 同上 |

---

## ファイル I/O

| COBOL 構文 | 対応状況 | Java 出力先 |
|---|---|---|
| Sequential I/O | ✅ Stable | `BufferedReader` / `BufferedWriter` |
| Indexed I/O (VSAM KSDS) | ⚠ Beta | JDBC または独自 DAO（Strategy 切替） |
| Relative I/O | 🚧 Experimental | 同上 |
| LINE SEQUENTIAL | ✅ Stable | `BufferedReader` |

---

## 移行プロジェクト適合性 早見表

| あなたの環境 | 推奨アプローチ |
|---|---|
| IBM z/OS + DB2 + CICS | **✅ 本ツールでの PoC を推奨**。診断レポートで難易度評価可能 |
| Fujitsu NetCOBOL + PostgreSQL | **✅ Beta レベルでカバー**。手修正箇所の見積もりに有効 |
| NEC ACOS + RIQS | **⚠ 要事前検討**。RIQS 接続は手動マッピング前提 |
| Hitachi VOS3 | **⚠ 要事前検討**。COPY ライブラリ提供が前提 |
| Micro Focus Visual COBOL (Windows) | **✅ 本ツールでの PoC を推奨**。手元検証しやすい |
| 標準 COBOL-85 / GnuCOBOL | **✅ 本ツールでの PoC を推奨**。リファレンス的に動作 |

---

## ベンダー追加・拡張のご相談

特定ベンダーの方言・サブシステムへの対応強化が必要な場合は応相談（個別見積もり）。
業界（金融・公共・保険）特化のカスタムルール開発も承ります。

- 連絡先：highdefinitionaudiodriver@gmail.com

---

> ⚠️ **本マトリクスは「自動変換可」ではなく「パーサが理解できる」レベルを示します**。
> 生成された Java コードは必ず人手レビューと十分なテストを経てください。
