# Security Policy

## Supported Versions / サポートバージョン

| Version | Supported |
|---|---|
| 0.1.x   | ✅ |
| < 0.1   | ❌ |

## 脆弱性の報告 / Reporting a Vulnerability

セキュリティ上の問題を発見した場合は、**Issue や Pull Request での公開報告は避け**、以下のメールアドレスへ直接ご連絡ください。

If you discover a security issue, please **avoid public Issues / PRs** and email directly:

- **連絡先 / Contact**：highdefinitionaudiodriver@gmail.com
- **対応 SLA**：Best effort. Initial response within 72 hours.

報告に含めていただけると助かる情報：

- Affected version
- Reproduction steps (minimal COBOL sample if possible)
- Potential impact (mis-generated Java leading to data corruption, SQL injection in EXEC SQL translation, etc.)
- Suggested fix (if any)

## 本ツール固有のセキュリティ事項

- **本ツールは「Java 化のたたき台」を生成するもの**であり、生成された Java は**そのまま本番投入禁止**です。必ず人手レビューと十分なテストを経てください。
- **入力 COBOL に PII / 機密情報が含まれる場合**、生成 Java や難易度レポートにも転載される可能性があります。社外共有前にサニタイズしてください。
- **EXEC SQL の変換は手書きクエリ前提**であり、パラメータバインドの責任は移行担当者にあります。SQL インジェクション対策は最終 Java コードでのレビュー必須事項です。
