from __future__ import annotations

import os
import shlex
import sys

from bolsabr.ops.publisher import build_publisher_command


def main() -> int:
    command = build_publisher_command(os.environ)
    print(
        "Executing:",
        " ".join(shlex.quote(part) for part in command),
        flush=True,
    )
    os.execv(sys.executable, command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
