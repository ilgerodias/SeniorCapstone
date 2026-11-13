
import json
import sys
from pathlib import Path
from datetime import datetime

REQUIRED_FIELDS = (
    "trace_id",
    "span_id",
    "name",
    "kind",
    "start_time",
    "attributes",
    "status",
)

REQUIRED_TOOL_FIELDS = (
    "gen_ai.tool.name",
    "gen_ai.tool.call.id",
    "gen_ai.tool.call.arguments",
    "hackingbuddygpt.tool.result",
)


def validate(path):
    errors = []
    records = 0

    with Path(path).open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                errors.append(f"Line {line_number}: {error}")
                continue

            records += 1

            if not isinstance(record, dict):
                errors.append(
                    f"Line {line_number}: expected JSON object"
                )
                continue

            # Check required JSONL fields
            for field in REQUIRED_FIELDS:
                if field not in record:
                    errors.append(
                        f"Line {line_number}: missing {field}"
                    )

            # Check timestamp format and ordering
            if "start_time" in record:
                try:
                    start = datetime.fromisoformat(
                        record["start_time"]
                    )
                except (ValueError, TypeError):
                    errors.append(
                        f"Line {line_number}: invalid start_time"
                    )
                    continue

                if record.get("end_time") is not None:
                    try:
                        end = datetime.fromisoformat(
                            record["end_time"]
                        )

                        if end < start:
                            errors.append(
                                f"Line {line_number}: "
                                "end_time precedes start_time"
                            )

                    except (ValueError, TypeError):
                        errors.append(
                            f"Line {line_number}: invalid end_time"
                        )

            # Check attributes structure
            attributes = record.get("attributes")

            if "attributes" in record and not isinstance(
                attributes, dict
            ):
                errors.append(
                    f"Line {line_number}: attributes must be an object"
                )
                continue

            # Check required fields for tool-call spans
            if isinstance(attributes, dict):
                if (
                    attributes.get("gen_ai.operation.name")
                    == "execute_tool"
                ):
                    for field in REQUIRED_TOOL_FIELDS:
                        if field not in attributes:
                            errors.append(
                                f"Line {line_number}: "
                                f"missing tool field {field}"
                            )

    if records == 0:
        errors.append("No valid JSONL records found")

    return records, errors


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(
            "Usage: python validate_jsonl.py <file.jsonl>"
        )

    records, errors = validate(sys.argv[1])

    for error in errors:
        print("FAIL:", error)

    if errors:
        sys.exit(1)

    print(f"PASS: {records} JSONL records validated")
