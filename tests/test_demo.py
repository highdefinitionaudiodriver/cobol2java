"""--demo（同梱サンプル即変換）の検証。叩けば即結果が出ることを保証する。"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_bundled_sample_exists():
    sample = ROOT / "examples" / "sample_legacy_app"
    assert sample.is_dir()
    assert any(sample.glob("*.cbl"))


def test_demo_generates_java(tmp_path):
    out = tmp_path / "demo_out"
    result = subprocess.run(
        [sys.executable, str(ROOT / "main.py"), "--demo", "-o", str(out)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert result.returncode == 0, result.stderr
    java_files = list(out.rglob("*.java"))
    assert len(java_files) >= 1, "デモ変換で Java が1つも生成されていません"
