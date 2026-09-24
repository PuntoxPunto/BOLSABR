from __future__ import annotations

import argparse
import json
from pathlib import Path

from bolsabr.serving.snapshot_store import FilesystemSnapshotStore


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Publish a precomputed Option Chain API v0.1 JSON snapshot."
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Path to an Option Chain API v0.1 JSON file.",
    )
    parser.add_argument(
        "--snapshot-dir",
        type=Path,
        default=Path("data/serving"),
        help="Serving store root. Default: data/serving",
    )
    args = parser.parse_args()

    payload = json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Option Chain snapshot root must be a JSON object")

    stored = FilesystemSnapshotStore(args.snapshot_dir).publish(payload)
    print(
        json.dumps(
            {
                "ticker": stored.ticker,
                "ref_date": stored.ref_date.isoformat(),
                "path": str(stored.path),
                "etag": stored.etag,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
