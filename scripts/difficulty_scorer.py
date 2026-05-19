#!/usr/bin/env python3
"""
COBOL 移行難易度スコアラー — CSV 出力

既存の cobol2java 変換パイプラインに依存せず、入力ディレクトリの COBOL ソース
（.cbl / .cob / .cobol / .CBL / .COB）を走査して 1〜5 の難易度スコアと内訳を CSV
で出力します。

判定基準は「実プロジェクトの工数見積もりに直結するシグナル」を 7 軸で計測：

    1: 単純 DATA + 簡単な PROCEDURE のみ
    2: 簡単な PERFORM / IF / 算術
    3: ファイル I/O・COPY・サブプログラム
    4: EXEC SQL / EXEC CICS / GO TO 多用
    5: EXEC DLI / GLOBAL データ / 動的呼出 / RDB+CICS+IMS の混在

このスクリプトは**最終判断材料ではなく、見積もりのたたき台**を作るためのものです。
COPY 元の解決や大規模クロスリファレンスは行いません。

使い方:
    python scripts/difficulty_scorer.py <input_dir>            # report.csv に出力
    python scripts/difficulty_scorer.py <input_dir> -o out.csv
    python scripts/difficulty_scorer.py <input_dir> --html report.html
"""

from __future__ import annotations

import argparse
import csv
import html
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterable

# --- 既定の対象拡張子 ----------------------------------------------------------
DEFAULT_EXTENSIONS = (".cbl", ".cob", ".cobol", ".CBL", ".COB", ".COBOL")

# --- スコアリングルール --------------------------------------------------------
# 各パターンは「正規表現」と「1 マッチごとに加算される重み」のペア。
# 行頭の `*` コメント行は除外して評価する。
PATTERNS: list[tuple[str, str, int, str]] = [
    # (axis_name, regex, weight, description)
    ("EXEC_SQL",     r"\bEXEC\s+SQL\b",                          3, "埋込 SQL — DB 接続・カーソル設計が必要"),
    ("EXEC_CICS",    r"\bEXEC\s+CICS\b",                         4, "CICS トランザクション — フロント設計に直結"),
    ("EXEC_DLI",     r"\bEXEC\s+DLI\b",                          5, "IMS/DLI — 階層 DB の再設計が必要（最難関）"),
    ("CALL_DYN",     r"\bCALL\s+['\"]?[A-Z0-9-]+['\"]?(?!\s+USING)|\bCALL\s+[A-Z][\w-]*\s*(?:USING)?",
                                                                  2, "サブプログラム呼出 — 依存解析必要"),
    ("GO_TO",        r"\bGO\s+TO\b",                             1, "GO TO — フロー再設計の負債"),
    ("PERFORM_THRU", r"\bPERFORM\s+[\w-]+\s+THR(?:OUGH|U)\b",    2, "PERFORM THRU — フォールスルー意図の保存"),
    ("ALTER",        r"\bALTER\s+[\w-]+\s+TO\s+PROCEED\b",       4, "ALTER — 動的フロー変更（非推奨構文）"),
    ("COPY",         r"\bCOPY\s+[\w-]+",                         1, "COPY — 外部依存（COPYBOOK が必要）"),
    ("OCCURS",       r"\bOCCURS\s+\d+",                          1, "OCCURS — 配列構造"),
    ("REDEFINES",    r"\bREDEFINES\b",                           2, "REDEFINES — メモリオーバーレイ（Java では非自明）"),
    ("COMP3",        r"\bCOMP-3\b|\bPACKED-DECIMAL\b",           1, "COMP-3 — パック10進数（BigDecimal マッピング）"),
    ("FILE_IO",      r"\bSELECT\s+[\w-]+\s+ASSIGN\s+TO\b",       2, "ファイル I/O — VSAM/シーケンシャル"),
    ("INDEXED_FILE", r"\bORGANIZATION\s+IS\s+INDEXED\b",         2, "INDEXED ファイル — KSDS 相当の再設計"),
    ("GLOBAL",       r"\bGLOBAL\b(?=.*(?:CLAUSE|VARIABLE))",     2, "GLOBAL — スコープ・寿命の特殊性"),
    ("EVALUATE",     r"\bEVALUATE\b",                            1, "EVALUATE — switch 系構文"),
    ("NESTED",       r"\bPROGRAM-ID\b",                          1, "ネスト or 複数プログラム単位"),
]

# 行数ベースの軸
SIZE_TIERS = [
    (0,    100,  0, "tiny"),
    (100,  500,  1, "small"),
    (500,  2000, 2, "medium"),
    (2000, 10000, 3, "large"),
    (10000, 10**9, 4, "huge"),
]


@dataclass
class FileScore:
    path: str
    relative_path: str
    loc: int                       # コメント除外後の行数
    raw_lines: int
    size_tier: str
    weighted_total: int
    difficulty_1to5: int            # 1〜5
    suggested_effort_hours: float
    hits: dict = field(default_factory=dict)


def is_comment(line: str) -> bool:
    """COBOL の固定形式 7 桁目 `*` または `/` でコメント判定（CR/LF はずらして許容）"""
    if not line.strip():
        return True
    # 固定形式：行頭 6 桁シーケンス番号 + 7 桁目フラグ
    if len(line) >= 7:
        if line[6] in ("*", "/"):
            return True
    # 自由形式: 行頭スペース後の `*>`
    return bool(re.match(r"\s*\*>", line))


def read_text(path: Path) -> str:
    """文字コードを順に試して読み込む（COBOL 資産は SJIS/EUC が多い）"""
    for enc in ("utf-8-sig", "utf-8", "cp932", "shift_jis", "euc_jp", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="latin-1", errors="replace")


def score_file(path: Path, root: Path) -> FileScore:
    text = read_text(path)
    raw_lines = text.count("\n") + 1
    code_lines = [ln for ln in text.splitlines() if not is_comment(ln)]
    loc = len(code_lines)
    code_joined = "\n".join(code_lines).upper()

    hits: dict[str, int] = {}
    weighted_total = 0
    for axis, regex, weight, _desc in PATTERNS:
        n = len(re.findall(regex, code_joined, flags=re.IGNORECASE))
        if n:
            hits[axis] = n
            weighted_total += n * weight

    # サイズによる追加重み
    size_weight = 0
    size_tier = "tiny"
    for lo, hi, w, tier in SIZE_TIERS:
        if lo <= loc < hi:
            size_weight = w
            size_tier = tier
            break
    weighted_total += size_weight

    # 1〜5 段階に正規化（実プロジェクトのキャリブレーション目安）
    if weighted_total <= 3:
        difficulty = 1
    elif weighted_total <= 10:
        difficulty = 2
    elif weighted_total <= 25:
        difficulty = 3
    elif weighted_total <= 60:
        difficulty = 4
    else:
        difficulty = 5

    # 概算工数（経験則：難易度 1=1h, 2=4h, 3=12h, 4=32h, 5=80h）
    effort_table = {1: 1, 2: 4, 3: 12, 4: 32, 5: 80}
    suggested = float(effort_table[difficulty])
    # LOC が大きいときは比例で上振れ
    if loc > 200 and difficulty < 5:
        suggested *= 1 + (loc - 200) / 1000

    rel = str(path.relative_to(root)) if root in path.parents or root == path.parent else str(path)
    return FileScore(
        path=str(path),
        relative_path=rel,
        loc=loc,
        raw_lines=raw_lines,
        size_tier=size_tier,
        weighted_total=weighted_total,
        difficulty_1to5=difficulty,
        suggested_effort_hours=round(suggested, 1),
        hits=hits,
    )


def collect_files(root: Path, extensions: Iterable[str]) -> list[Path]:
    files: list[Path] = []
    ext_set = {e.lower() for e in extensions}
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in ext_set:
            files.append(p)
    return sorted(files)


def write_csv(scores: list[FileScore], out_path: Path) -> None:
    axis_keys = [p[0] for p in PATTERNS]
    headers = [
        "relative_path", "loc", "raw_lines", "size_tier",
        "weighted_total", "difficulty_1to5", "suggested_effort_hours",
    ] + axis_keys
    with out_path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, lineterminator="\r\n")
        w.writerow(headers)
        for s in scores:
            row = [
                s.relative_path, s.loc, s.raw_lines, s.size_tier,
                s.weighted_total, s.difficulty_1to5, s.suggested_effort_hours,
            ] + [s.hits.get(k, 0) for k in axis_keys]
            w.writerow(row)


def write_html(scores: list[FileScore], out_path: Path) -> None:
    """簡易 HTML レポート — 上司に見せられる、難易度ヒストグラム + Top 20 表"""
    by_diff = {i: 0 for i in range(1, 6)}
    total_effort = 0.0
    for s in scores:
        by_diff[s.difficulty_1to5] += 1
        total_effort += s.suggested_effort_hours

    top20 = sorted(scores, key=lambda s: s.weighted_total, reverse=True)[:20]
    rows = []
    for s in top20:
        hit_summary = ", ".join(f"{k}:{v}" for k, v in sorted(s.hits.items(), key=lambda x: -x[1])[:5])
        rows.append(
            f"<tr><td>{html.escape(s.relative_path)}</td>"
            f"<td>{s.loc}</td>"
            f"<td><strong class='d{s.difficulty_1to5}'>{s.difficulty_1to5}</strong></td>"
            f"<td>{s.suggested_effort_hours:.1f} h</td>"
            f"<td>{html.escape(hit_summary)}</td></tr>"
        )

    histogram = "".join(
        f"<div class='bar'><span>難易度 {d}</span>"
        f"<div class='fill d{d}' style='width:{(by_diff[d] / max(1, len(scores))) * 100:.1f}%'></div>"
        f"<span class='n'>{by_diff[d]} ファイル</span></div>"
        for d in range(1, 6)
    )

    html_text = f"""<!DOCTYPE html>
<html lang="ja"><head><meta charset="UTF-8"><title>COBOL 移行難易度レポート</title>
<style>
  body {{ font-family: "Yu Gothic UI", "Hiragino Sans", sans-serif; max-width: 980px; margin: 24px auto; color: #222; padding: 0 20px; }}
  h1 {{ font-size: 22px; border-bottom: 3px solid #c62828; padding-bottom: 6px; }}
  .summary {{ background: #f5f5f5; padding: 16px; border-radius: 6px; margin: 16px 0; }}
  .summary p {{ margin: 4px 0; }}
  .bar {{ display: flex; align-items: center; gap: 12px; margin: 6px 0; font-size: 13px; }}
  .bar > span:first-child {{ width: 80px; }}
  .bar .fill {{ height: 18px; border-radius: 3px; }}
  .bar .n {{ font-variant-numeric: tabular-nums; color: #666; }}
  .d1 {{ background: #4caf50; color: #2e7d32; }}
  .d2 {{ background: #8bc34a; color: #558b2f; }}
  .d3 {{ background: #ffb300; color: #ef6c00; }}
  .d4 {{ background: #ef5350; color: #c62828; }}
  .d5 {{ background: #b71c1c; color: #b71c1c; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 16px; font-size: 13px; }}
  th, td {{ border-bottom: 1px solid #ddd; padding: 8px 10px; text-align: left; }}
  th {{ background: #fafafa; }}
  .meta {{ font-size: 11px; color: #888; margin-top: 24px; }}
</style></head><body>
<h1>COBOL 移行難易度レポート</h1>
<div class="summary">
  <p><strong>対象ファイル数</strong>: {len(scores)}</p>
  <p><strong>合計 LOC（コメント除外）</strong>: {sum(s.loc for s in scores):,}</p>
  <p><strong>概算合計工数</strong>: {total_effort:,.1f} 時間 ≒ {total_effort/8:,.1f} 人日</p>
</div>
<h2>難易度ヒストグラム</h2>
{histogram}
<h2>難易度の高いファイル Top 20</h2>
<table>
<thead><tr><th>ファイル</th><th>LOC</th><th>難易度</th><th>概算工数</th><th>主な検出</th></tr></thead>
<tbody>{''.join(rows)}</tbody>
</table>
<p class="meta">⚠️ 本レポートは静的解析による <strong>見積もり用たたき台</strong> です。COPY 展開・実行時動作・既存テストの存在は考慮していません。最終工数は人手レビューで確定してください。<br>
生成: {datetime.now().isoformat(timespec='seconds')} / cobol2java difficulty_scorer.py</p>
</body></html>"""
    out_path.write_text(html_text, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="COBOL 資産の移行難易度を 1〜5 で採点して CSV/HTML を出力"
    )
    parser.add_argument("input_dir", help="走査対象のディレクトリ")
    parser.add_argument("-o", "--output", default="report.csv", help="CSV 出力先（デフォルト: report.csv）")
    parser.add_argument("--html", default=None, help="任意の HTML サマリ出力先")
    parser.add_argument(
        "--ext", default=",".join(DEFAULT_EXTENSIONS),
        help=f"カンマ区切りの対象拡張子（デフォルト: {','.join(DEFAULT_EXTENSIONS)}）",
    )
    args = parser.parse_args(argv)

    root = Path(args.input_dir).resolve()
    if not root.is_dir():
        print(f"エラー: ディレクトリではありません: {root}", file=sys.stderr)
        return 2

    extensions = [e.strip() for e in args.ext.split(",") if e.strip()]
    files = collect_files(root, extensions)
    if not files:
        print(f"対象ファイルが見つかりません（{','.join(extensions)}）", file=sys.stderr)
        return 1

    print(f"走査中: {len(files)} ファイル...", file=sys.stderr)
    scores = [score_file(p, root) for p in files]

    out_csv = Path(args.output).resolve()
    write_csv(scores, out_csv)
    print(f"✓ CSV 出力: {out_csv}", file=sys.stderr)

    if args.html:
        out_html = Path(args.html).resolve()
        write_html(scores, out_html)
        print(f"✓ HTML 出力: {out_html}", file=sys.stderr)

    # サマリを stderr に
    by_d = {i: 0 for i in range(1, 6)}
    total_effort = 0.0
    for s in scores:
        by_d[s.difficulty_1to5] += 1
        total_effort += s.suggested_effort_hours
    print("\n=== 集計 ===", file=sys.stderr)
    for d in range(1, 6):
        print(f"  難易度 {d}: {by_d[d]} ファイル", file=sys.stderr)
    print(f"  概算合計工数: {total_effort:,.1f} 時間 (≒ {total_effort/8:,.1f} 人日)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
