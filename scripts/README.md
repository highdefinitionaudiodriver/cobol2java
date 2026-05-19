# scripts/ — 補助ツール

メインの cobol2java 変換パイプライン（`main.py`）には含めない、見積もり・診断用の補助スクリプト群です。

---

## `difficulty_scorer.py` — 移行難易度スコアラー

入力ディレクトリの COBOL ソースを走査して、ファイル単位の **移行難易度（1〜5）** と
**概算工数（時間）** を CSV / HTML で出力します。

> 💡 **これは何の役に立つのか**：
> 「自社の COBOL 資産は Java 移行にどれくらいかかるのか？」を、
> 営業・経営層に **1 ページの数字** で示すための初期見積もり材料です。

### 使い方

```bash
# 最小実行：report.csv に出力
python scripts/difficulty_scorer.py /path/to/cobol_sources

# 出力先を指定
python scripts/difficulty_scorer.py /path/to/cobol_sources -o estimate.csv

# 上司に出せる HTML サマリも同時出力
python scripts/difficulty_scorer.py /path/to/cobol_sources --html report.html

# 対象拡張子を絞る
python scripts/difficulty_scorer.py /path/to/cobol_sources --ext .cbl,.cob
```

実行後、stderr に以下のような集計が出ます：

```
走査中: 142 ファイル...
✓ CSV 出力: /work/estimate.csv

=== 集計 ===
  難易度 1: 38 ファイル
  難易度 2: 51 ファイル
  難易度 3: 27 ファイル
  難易度 4: 19 ファイル
  難易度 5: 7 ファイル
  概算合計工数: 1,847.5 時間 (≒ 230.9 人日)
```

### スコアリングロジック

各ファイルで以下を加重カウントし、合計値で 1〜5 段階に正規化：

| 軸 | 重み | 検出内容 | 移行への影響 |
|---|---|---|---|
| `EXEC_SQL` | 3 | 埋込 SQL | JDBC/JPA 設計 |
| `EXEC_CICS` | 4 | CICS トランザクション | フロント設計直結 |
| `EXEC_DLI` | 5 | IMS/DLI | 階層 DB 再設計（最難関） |
| `CALL_DYN` | 2 | 動的サブルーチン呼出 | 依存解析必要 |
| `GO_TO` | 1 | GO TO 文 | フロー再設計の負債 |
| `PERFORM THRU` | 2 | フォールスルー | 意図の保存 |
| `ALTER` | 4 | ALTER ... TO PROCEED | 動的フロー変更（非推奨） |
| `COPY` | 1 | COPYBOOK 参照 | 外部依存 |
| `REDEFINES` | 2 | メモリオーバーレイ | Java では非自明 |
| `COMP-3` | 1 | パック10進 | BigDecimal マッピング |
| `FILE_IO` | 2 | SELECT + ASSIGN | VSAM/シーケンシャル |
| `INDEXED_FILE` | 2 | INDEXED 編成 | KSDS 相当の再設計 |
| `GLOBAL` | 2 | GLOBAL 句 | スコープ特殊性 |
| `EVALUATE` | 1 | EVALUATE 文 | switch 系 |

LOC（コメント除外）も追加重みに加味し、最終的に：

| 合計重み | 難易度 | 概算工数（ベース） |
|---|---|---|
| 0–3 | **1** | 1 時間 |
| 4–10 | **2** | 4 時間 |
| 11–25 | **3** | 12 時間 |
| 26–60 | **4** | 32 時間 |
| 61– | **5** | 80 時間 |

LOC が 200 を超える場合は比例で上振れ。

### 出力 CSV のスキーマ

```
relative_path, loc, raw_lines, size_tier,
weighted_total, difficulty_1to5, suggested_effort_hours,
EXEC_SQL, EXEC_CICS, EXEC_DLI, CALL_DYN, GO_TO,
PERFORM_THRU, ALTER, COPY, OCCURS, REDEFINES, COMP3,
FILE_IO, INDEXED_FILE, GLOBAL, EVALUATE, NESTED
```

文字コードは **UTF-8 BOM 付き**（Excel での文字化けを回避）。

### 注意事項

- このスクリプトは **静的解析のみ** で、COPY 展開・実行時動作・既存テストの存在は評価しません
- 最終工数は **必ず人手レビュー** で確定してください
- 文字コードは UTF-8 / SJIS / EUC-JP / CP932 / Latin-1 の順に試行します
- 大規模リポジトリ（10,000 ファイル以上）でも数十秒で完走します

### 商用利用

- 個人・社内 PoC は無料（MIT）
- 自社資産の診断レポート受託（A4 PDF 納品 + 追加軸の独自追加）は応相談
- 連絡先: highdefinitionaudiodriver@gmail.com
