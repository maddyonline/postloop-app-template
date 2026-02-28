from __future__ import annotations

import os
import sys

import modal


def main() -> int:
    app_name = os.getenv("MODAL_APP_NAME", "").strip()
    function_name = os.getenv("MODAL_FUNCTION_NAME", "web").strip() or "web"

    if not app_name:
        print("MODAL_APP_NAME is required", file=sys.stderr)
        return 1

    function = modal.Function.from_name(app_name, function_name)
    url = function.get_web_url()
    if not url:
        print(f"Could not resolve web URL for {app_name}/{function_name}", file=sys.stderr)
        return 1

    print(url)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
