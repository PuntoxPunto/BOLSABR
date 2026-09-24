from __future__ import annotations

import os

import uvicorn


def main() -> None:
    host = os.environ.get("BOLSABR_API_HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(
        "bolsabr.api.app:app",
        host=host,
        port=port,
        proxy_headers=True,
        forwarded_allow_ips="*",
    )


if __name__ == "__main__":
    main()
