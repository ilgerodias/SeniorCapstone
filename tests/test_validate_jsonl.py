
import json

from scripts.validate_jsonl import validate


def make_record():
    return {
        "trace_id": "test",
        "span_id": "123",
        "name": "tool-test",
        "kind": "INTERNAL",
        "start_time": "2026-11-12T14:00:00",
        "end_time": "2026-11-12T14:00:01",
        "status": "OK",
        "attributes": {
            "gen_ai.operation.name": "execute_tool",
            "gen_ai.tool.name": "exec",
            "gen_ai.tool.call.id": "0",
            "gen_ai.tool.call.arguments": "ls",
            "hackingbuddygpt.tool.result": "ok",
        },
    }


def write_log(tmp_path, record):
    path = tmp_path / "test.jsonl"
    path.write_text(json.dumps(record) + "\n", encoding="utf-8")
    return path


def test_valid_tool_call_passes(tmp_path):
    path = write_log(tmp_path, make_record())

    records, errors = validate(path)

    assert records == 1
    assert errors == []


def test_missing_required_field_fails(tmp_path):
    record = make_record()
    del record["span_id"]

    path = write_log(tmp_path, record)
    _, errors = validate(path)

    assert any("missing span_id" in error for error in errors)


def test_invalid_timestamp_order_fails(tmp_path):
    record = make_record()
    record["end_time"] = "2026-11-12T13:00:00"

    path = write_log(tmp_path, record)
    _, errors = validate(path)

    assert any(
        "end_time precedes start_time" in error
        for error in errors
    )


def test_missing_tool_field_fails(tmp_path):
    record = make_record()
    del record["attributes"]["gen_ai.tool.name"]

    path = write_log(tmp_path, record)
    _, errors = validate(path)

    assert any(
        "missing tool field gen_ai.tool.name" in error
        for error in errors
    )


def test_invalid_json_fails(tmp_path):
    path = tmp_path / "invalid.jsonl"
    path.write_text("{invalid json}\n", encoding="utf-8")

    _, errors = validate(path)

    assert errors
    assert any("Line 1:" in error for error in errors)
