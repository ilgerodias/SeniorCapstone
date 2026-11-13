import json
import datetime

from tests.test_log_storage import _drive_run


def test_tool_call_has_required_qa_fields(tmp_path):
    path = _drive_run(str(tmp_path))

    with open(path, encoding="utf-8") as file:
        spans = [json.loads(line) for line in file if line.strip()]

    tools = [
        span for span in spans
        if span["attributes"].get("gen_ai.operation.name") == "execute_tool"
    ]

    assert len(tools) == 1

    tool = tools[0]
    attrs = tool["attributes"]

    start = datetime.datetime.fromisoformat(tool["start_time"])
    end = datetime.datetime.fromisoformat(tool["end_time"])

    assert end >= start, "Tool-call end time must not precede start time"

    assert attrs["gen_ai.tool.name"] == "exec"
    assert attrs["gen_ai.tool.call.id"] == "0"
    assert attrs["gen_ai.tool.call.arguments"] == "ls"
    assert attrs["hackingbuddygpt.tool.result"] == "ok"
