# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- README に「これは何？（30秒で）」「想定ユースケース・価格帯」セクションを追加（金融・公共向け PoC 提案の判断材料）
- 「完全自動変換ではない」ことを明示する免責ブロックを追加
- SECURITY.md を追加（脆弱性報告フロー、日英併記）
- 商用利用・カスタマイズ依頼の連絡先を README 末尾に明記

## [0.1.0]

### Added
- COBOL → Java OOP 変換ツール初版（GUI + CLI）
- 3 フェーズパーサ（DATA / PROCEDURE / Division 統合）
- 10 ベンダー方言対応（IBM / Fujitsu / NEC / Hitachi / Micro Focus / Unisys / Bull / HP NonStop / GnuCOBOL / Standard）
- EXEC SQL / CICS / DLI 解析
- Strategy Pattern による File I/O / SQL / CICS の変換戦略切り替え
- 自動ベンダー検出
- 59 言語 UI ローカライゼーション
- 184 件のテストスイート
- PyInstaller による Windows / macOS / Linux 単体バイナリ配布
