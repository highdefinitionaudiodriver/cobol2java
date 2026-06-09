# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `--demo` オプション: 同梱サンプル（`examples/sample_legacy_app`）を**入力/出力の指定なしに即変換**し、`demo_output/` に Java を生成（「叩けば即結果」）。デモ実行の単体テストを追加

## [2.1.0] - 2026-06-04

### Fixed
- 条件式変換: COBOL の記号比較演算子を正しく Java へ変換するよう修正（コンパイル不能な Java を生成していたバグ）
  - `WS-X = 5` → `wsX == 5`（従来は `=` のまま＝代入になっていた）
  - `X NOT = 0` → `x != 0` / `X NOT > Y` → `x <= y` / `X NOT < Y` → `x >= y`（従来は `not` が残留）
- CICS サービスインターフェイスのプレースホルダ（`// TODO ...`）が `import // TODO ...;` という不正な import 文として出力されていた問題を修正（コメント行として出力）
- 上記の回帰を防ぐ `tests/test_condition_conversion.py`（10ケース）を追加

### Added
- README に「これは何？（30秒で）」「想定ユースケース・価格帯」セクションを追加（金融・公共向け PoC 提案の判断材料）
- 「完全自動変換ではない」ことを明示する免責ブロックを追加
- SECURITY.md を追加（脆弱性報告フロー、日英併記）
- 商用利用・カスタマイズ依頼の連絡先を README 末尾に明記
- docs/VENDOR_MATRIX.md — 10 ベンダー方言対応マトリクス＋プロジェクト適合性早見表
- **scripts/difficulty_scorer.py** — 既存パイプラインに依存しない移行難易度スコアラー（CSV/HTML 出力）
  - 14 軸（EXEC SQL/CICS/DLI、CALL、GO TO、PERFORM THRU、ALTER、COPY、REDEFINES、COMP-3、FILE_IO、INDEXED、GLOBAL 等）で加重カウント
  - 1〜5 段階の難易度と概算工数（時間／人日）を出力
  - 上司に出せる HTML サマリ出力オプション付き（`--html`）
  - UTF-8 BOM 付き CSV（Excel での文字化け回避）
  - 文字コード自動判定（UTF-8 / SJIS / EUC-JP / CP932 / Latin-1）
- **examples/sample_legacy_app/** — CC0 公開デモコーパス
  - 製造業の受注・在庫・売掛・月次締めシステムを模した 5 本の `.cbl` + COPYBOOK 2 本
  - 難易度 2〜4 が混在し、`difficulty_scorer.py` のキャリブレーション材料として使える
  - EXEC SQL / EXEC CICS / EXEC DLI / COPY / OCCURS / COMP-3 / GO TO / ALTER 等、
    実プロジェクト頻出パターンを意図的に含む
  - **CC0 ライセンス**（パブリックドメイン相当）で誰でも改変・商用利用可

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
