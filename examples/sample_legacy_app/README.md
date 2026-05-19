# Sample Legacy COBOL Application — 公開デモコーパス

本ディレクトリは **cobol2java の難易度スコアラー（`scripts/difficulty_scorer.py`）と
Java OOP 変換パイプライン** を試すための、公開・改変自由なサンプル COBOL です。

> 💡 これらのファイルは**実プロジェクトの COBOL を模した教育用サンプル**で、
> CC0（パブリックドメイン）相当として配布します。
> 自由に変換実験・テスト・スクリーンショット用デモにご利用ください。

---

## 想定シナリオ

ある中堅製造業の社内システム（受注・在庫・売掛管理）が **IBM Enterprise COBOL on z/OS** で動いている。
EXEC SQL（DB2）と一部 CICS、COMP-3 数値、PERFORM THRU、COPY によるレコード共有
など、**実プロジェクトでよくある「全部入り」のレガシー要素**を意図的に含めています。

### ファイル構成と難易度

| ファイル | 想定難易度 | 主な内容 |
|---|---|---|
| `01_customer_master.cbl` | ⭐ **1 (簡単)** | 顧客マスタの単純な PROCEDURE、I/O のみ |
| `02_order_entry.cbl` | ⭐⭐ **2** | 受注入力、PERFORM ループ、IF/EVALUATE |
| `03_inventory_check.cbl` | ⭐⭐⭐ **3** | 在庫照合、COPY による共通レコード、ファイル I/O |
| `04_billing_proc.cbl` | ⭐⭐⭐⭐ **4** | 売掛計算、EXEC SQL（DB2 想定）、GO TO 多用 |
| `05_period_close.cbl` | ⭐⭐⭐⭐⭐ **5** | 月次締め、CICS / DLI 混在、ALTER 文、複雑な PERFORM THRU |
| `COPYBOOKS/CUSTOMER.cpy` | — | 共通 COPY 定義（顧客レコード） |
| `COPYBOOKS/COMMON.cpy` | — | 共通定義（日付・コード変換） |

`difficulty_scorer.py` でこのディレクトリ全体を走査すると、難易度 1〜5 が
バラけて出力される構成になっています：

```bash
python scripts/difficulty_scorer.py examples/sample_legacy_app/ --html report.html
```

実測出力例（v0.1 スコアラーで本サンプルを走査した結果）：

```
=== 集計 ===
  難易度 1: 0 ファイル
  難易度 2: 2 ファイル   ← 01_customer_master.cbl, 02_order_entry.cbl
  難易度 3: 1 ファイル   ← 03_inventory_check.cbl
  難易度 4: 2 ファイル   ← 04_billing_proc.cbl, 05_period_close.cbl
  難易度 5: 0 ファイル
  概算合計工数: 約 84 時間 (≒ 10.5 人日)
```

> 📝 **スコアラーのキャリブレーション**：設計者が「難易度 5 相当」と想定した
> `05_period_close.cbl` は実際には難易度 4 と判定されました。
> v0.1 スコアラーは保守的に判定する傾向があるため、**設計者の主観難易度と
> ±1 程度の差異** は想定されます。実プロジェクトでは「相対的なランク付け」
> として利用してください。

---

## ライセンス

このディレクトリ内の `.cbl` / `.cpy` は **CC0 1.0 Universal**（パブリックドメイン相当）で
公開します。誰でも自由に複製・改変・商用利用が可能です。

> ⚠️ 業務 COBOL 資産は機密情報・著作物であることが多いため、本サンプル以外を
> 公開・配布する際は必ずライセンスを確認してください。

---

## 関連

- 親リポジトリ: [cobol2java](https://github.com/highdefinitionaudiodriver/cobol2java)
- 診断スクリプト: `scripts/difficulty_scorer.py`
- 対応ベンダー方言: `docs/VENDOR_MATRIX.md`
