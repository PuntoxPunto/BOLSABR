import pytest

from scripts.run_eod_publisher import build_command


def test_auto_mode_builds_top50_stock_command():
    command = build_command(
        {
            "BOLSABR_UNIVERSE_MODE": "auto",
            "BOLSABR_UNIVERSE_LIMIT": "50",
            "BOLSABR_UNIVERSE_KIND": "stocks",
            "BOLSABR_UNIVERSE_MIN_FINANCIAL_VOLUME": "1000",
            "BOLSABR_SNAPSHOT_DIR": "/data/serving",
        },
        python_executable="python",
    )

    assert command == [
        "python",
        "scripts/build_eod_options.py",
        "--auto-universe",
        "--universe-limit",
        "50",
        "--universe-kind",
        "stocks",
        "--min-financial-volume",
        "1000",
        "--output-dir",
        "artifacts/chains",
        "--publish-dir",
        "/data/serving",
    ]


def test_manual_mode_preserves_multiple_underlyings():
    command = build_command(
        {
            "BOLSABR_UNIVERSE_MODE": "manual",
            "BOLSABR_UNDERLYINGS": "PETR4 VALE3 ITUB4",
            "BOLSABR_SNAPSHOT_DIR": "/tmp/store",
        },
        python_executable="python3",
    )

    assert command == [
        "python3",
        "scripts/build_eod_options.py",
        "PETR4",
        "VALE3",
        "ITUB4",
        "--output-dir",
        "artifacts/chains",
        "--publish-dir",
        "/tmp/store",
    ]


def test_invalid_mode_is_rejected():
    with pytest.raises(RuntimeError):
        build_command(
            {"BOLSABR_UNIVERSE_MODE": "mystery"},
            python_executable="python",
        )
