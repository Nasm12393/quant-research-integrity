from __future__ import annotations

import argparse
import json
from pathlib import Path

from .audit import SchemaError, audit_files


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit a quantitative research dataset without network access.")
    parser.add_argument("--lives", required=True, type=Path, help="CSV contract-life catalogue")
    parser.add_argument("--market", required=True, type=Path, help="CSV market observations")
    parser.add_argument("--signals", required=True, type=Path, help="CSV signal chronology")
    parser.add_argument("--manifest", type=Path, help="Optional SHA256SUMS manifest")
    parser.add_argument("--json-out", type=Path, help="Optional path for a new report (never overwrites)")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = audit_files(
            lives_path=args.lives,
            market_path=args.market,
            signals_path=args.signals,
            manifest_path=args.manifest,
        )
        rendered = json.dumps(report.to_dict(), indent=2, sort_keys=True)
        if args.json_out is not None:
            args.json_out.parent.mkdir(parents=True, exist_ok=True)
            with args.json_out.open("x", encoding="utf-8") as handle:
                handle.write(f"{rendered}\n")
    except (OSError, SchemaError, UnicodeError) as exc:
        print(json.dumps({"status": "ERROR", "message": str(exc)}, indent=2))
        return 3

    print(rendered)
    return 0 if report.status == "PASS" else 2
