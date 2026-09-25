"""Write the OpenAPI schema that the TypeScript client is generated from.

``pnpm contracts`` runs this, then ``openapi-typescript``. CI regenerates both and fails if
the checked-in contract is out of date.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from commerce.config import REPO_ROOT
from commerce.main import create_app

DEFAULT_OUT = REPO_ROOT / "packages" / "contracts" / "openapi.json"


def main() -> None:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUT
    schema = create_app().openapi()
    out.write_text(
        json.dumps(schema, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    print(f"wrote {out.relative_to(REPO_ROOT) if out.is_relative_to(REPO_ROOT) else out}")


if __name__ == "__main__":
    main()
