
import json
import subprocess
import sys
from pathlib import Path

HARNESS = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "qa_harness.py"
)


def run_harness(log_dir):
    return subprocess.run(
        [
            sys.executable,
            str(HARNESS),
            "--log-dir",
            str(log_dir),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def make_valid_record():
    return {
        "trace_id": "test",
        "span_id": "123",
        "name": "test-run",
        "kind": "INTERNAL",
        "start_time": "2026-11-12T14:00:00",
        "end_time": "2026-11-12T14:00:01",
        "attributes": {},
        "status": {"code": "OK"},
    }


def test_valid_log_passes(tmp_path):
    log_file = tmp_path / "log-valid.jsonl"
    log_file.write_text(
        json.dumps(make_valid_record()) + "\n",
        encoding="utf-8",
    )

    result = run_harness(tmp_path)

    assert result.returncode == 0
    assert "Passed: 1" in result.stdout
    assert "Failed: 0" in result.stdout


def test_invalid_log_fails(tmp_path):
    log_file = tmp_path / "log-invalid.jsonl"
    log_file.write_text(
        '{"trace_id":"test"}\n',
        encoding="utf-8",
    )

    result = run_harness(tmp_path)

    assert result.returncode == 1
    assert "Failed: 1" in result.stdout


def test_empty_directory_fails(tmp_path):
    result = run_harness(tmp_path)

    assert result.returncode == 1
    assert "No run logs found" in result.stdout


def test_missing_directory_fails(tmp_path):
    missing_dir = tmp_path / "missing"

    result = run_harness(missing_dir)

    assert result.returncode == 1
    assert "Log directory not found" in result.stdout
