from __future__ import annotations

import argparse
from pathlib import Path

from csv_buddy import clean_csv, write_csv


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Clean a CSV and print a small summary.")
    p.add_argument("input", type=Path, help="Input CSV file path")
    p.add_argument("--out", type=Path, default=Path("out/cleaned.csv"), help="Output cleaned CSV path")
    p.add_argument("--no-write", action="store_true", help="Do not write cleaned CSV")
    return p


def main() -> int:
    args = build_parser().parse_args()
    if not args.input.exists():
        raise SystemExit(f"Input file not found: {args.input}")

    columns, rows, summary = clean_csv(args.input)

    print(f"Input rows (excluding header): {summary.rows_in}")
    print(f"Output rows (after dropping empty rows): {summary.rows_out}")
    print("")
    print("Missing values by column:")
    for col in columns:
        print(f"- {col}: {summary.missing_by_column.get(col, 0)}")

    if summary.numeric_stats:
        print("")
        print("Numeric column stats (min/max/avg):")
        for col, st in summary.numeric_stats.items():
            print(f"- {col}: min={st['min']:.3f} max={st['max']:.3f} avg={st['avg']:.3f}")

    if not args.no_write:
        write_csv(args.out, columns=columns, rows=rows)
        print("")
        print(f"Wrote cleaned CSV: {args.out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

