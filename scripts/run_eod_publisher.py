from __future__ import annotations

import os
import shlex
import sys
from collections.abc import Mapping


def _env(
    environ: Mapping[str, str],
    name: str,
    default: str,
) -> str:
    value = environ.get(name, default).strip()
    return value or default


def build_command(
    environ: Mapping[str, str],
    *,
    python_executable: str = sys.executable,
) -> list[str]:
    mode = _env(
        environ,
        "BOLSABR_UNIVERSE_MODE",
        "auto",
    ).lower()
    snapshot_dir = _env(
        environ,
        "BOLSABR_SNAPSHOT_DIR",
        "/data/serving",
    )

    command = [
        python_executable,
        "scripts/build_eod_options.py",
    ]

    if mode == "auto":
        command.extend(
            [
                "--auto-universe",
                "--universe-limit",
                _env(
                    environ,
                    "BOLSABR_UNIVERSE_LIMIT",
                    "50",
                ),
                "--universe-kind",
                _env(
                    environ,
                    "BOLSABR_UNIVERSE_KIND",
                    "stocks",
                ),
                "--min-financial-volume",
                _env(
                    environ,
                    "BOLSABR_UNIVERSE_MIN_FINANCIAL_VOLUME",
                    "0",
                ),
            ]
        )
    elif mode == "manual":
        underlyings = shlex.split(
            _env(
                environ,
                "BOLSABR_UNDERLYINGS",
                "PETR4",
            )
        )
        if not underlyings:
            raise RuntimeError(
                "manual mode requires BOLSABR_UNDERLYINGS"
            )
        command.extend(underlyings)
    else:
        raise RuntimeError(
            "BOLSABR_UNIVERSE_MODE must be 'auto' or 'manual'"
        )

    command.extend(
        [
            "--output-dir",
            "artifacts/chains",
            "--publish-dir",
            snapshot_dir,
        ]
    )
    return command


def main() -> int:
    command = build_command(os.environ)
    print(
        "Executing:",
        " ".join(shlex.quote(part) for part in command),
        flush=True,
    )
    os.execv(sys.executable, command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
