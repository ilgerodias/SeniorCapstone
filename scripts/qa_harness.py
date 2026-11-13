
import argparse
import sys
from pathlib import Path

from validate_jsonl import validate


def main():
    parser = argparse.ArgumentParser(
        description="Validate hackingBuddyGPT JSONL logs"
    )
    parser.add_argument(
        "--log-dir",
        type=Path,
        default=Path("logs"),
        help="Directory containing JSONL log files",
    )
    args = parser.parse_args()

    log_dir = args.log_dir

    if not log_dir.is_dir():
        print(f"ERROR: Log directory not found: {log_dir}")
        return 1

    log_files = sorted(log_dir.glob("log-*.jsonl"))

    if not log_files:
        print(f"ERROR: No run logs found in {log_dir}")
        return 1

    passed = 0
    failed = 0

    for log_file in log_files:
        print(f"\nChecking: {log_file.name}")

        try:
            records, errors = validate(log_file)
        except (OSError, UnicodeError) as error:
            print(f"FAIL: Could not read file: {error}")
            failed += 1
            continue

        if errors:
            for error in errors:
                print(f"FAIL: {error}")
            failed += 1
        else:
            print(f"PASS: {records} records validated")
            passed += 1

    print("\nQA SUMMARY")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
