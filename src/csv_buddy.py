from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Sequence


_NON_WORD_RE = re.compile(r"[^a-z0-9_]+")


@dataclass(frozen=True)
class CsvSummary:
    rows_in: int
    rows_out: int
    columns: list[str]
    missing_by_column: dict[str, int]
    numeric_stats: dict[str, dict[str, float]]


def detect_delimiter(sample_lines: Sequence[str]) -> str:
    comma = sum(line.count(",") for line in sample_lines)
    semicolon = sum(line.count(";") for line in sample_lines)
    return ";" if semicolon > comma else ","


def normalize_header(name: str) -> str:
    name = name.strip().lower()
    name = re.sub(r"\s+", "_", name)
    name = _NON_WORD_RE.sub("", name)
    name = re.sub(r"_+", "_", name).strip("_")
    return name or "col"


def normalize_row(row: dict[str, str]) -> dict[str, str]:
    return {key: (value.strip() if value is not None else "") for key, value in row.items()}


def is_empty_row(row: dict[str, str]) -> bool:
    return all((value.strip() == "") for value in row.values())


def read_csv_rows(path: Path, *, encoding: str = "utf-8") -> tuple[list[str], list[dict[str, str]]]:
    text = path.read_text(encoding=encoding, errors="replace")
    lines = [line for line in text.splitlines() if line is not None]
    sample = lines[:20]
    delimiter = detect_delimiter(sample)

    reader = csv.DictReader(lines, delimiter=delimiter, skipinitialspace=True)
    raw_headers = reader.fieldnames or []
    headers: list[str] = []
    used: dict[str, int] = {}
    for raw in raw_headers:
        base = normalize_header(raw or "")
        count = used.get(base, 0) + 1
        used[base] = count
        headers.append(base if count == 1 else f"{base}_{count}")
    header_map = {raw: norm for raw, norm in zip(raw_headers, headers)}

    rows: list[dict[str, str]] = []
    for raw in reader:
        normalized: dict[str, str] = {}
        for raw_key, value in raw.items():
            key = header_map.get(raw_key) or normalize_header(str(raw_key))
            normalized[key] = value if value is not None else ""
        rows.append(normalize_row(normalized))

    return headers, rows


def drop_empty_rows(rows: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    return [row for row in rows if not is_empty_row(row)]


def count_missing(rows: Iterable[dict[str, str]], columns: Sequence[str]) -> dict[str, int]:
    missing: dict[str, int] = {c: 0 for c in columns}
    for row in rows:
        for col in columns:
            if row.get(col, "").strip() == "":
                missing[col] += 1
    return missing


def try_numeric(values: Iterable[str]) -> list[float] | None:
    floats: list[float] = []
    for v in values:
        v = v.strip()
        if v == "":
            continue
        try:
            floats.append(float(v))
        except ValueError:
            return None
    return floats


def numeric_column_stats(rows: Iterable[dict[str, str]], columns: Sequence[str]) -> dict[str, dict[str, float]]:
    stats: dict[str, dict[str, float]] = {}
    rows_list = list(rows)
    for col in columns:
        floats = try_numeric([r.get(col, "") for r in rows_list])
        if floats is None or len(floats) == 0:
            continue
        stats[col] = {
            "min": min(floats),
            "max": max(floats),
            "avg": sum(floats) / len(floats),
        }
    return stats


def clean_csv(path: Path) -> tuple[list[str], list[dict[str, str]], CsvSummary]:
    columns, rows = read_csv_rows(path)
    rows_in = len(rows)
    cleaned_rows = drop_empty_rows(rows)
    missing = count_missing(cleaned_rows, columns)
    numeric = numeric_column_stats(cleaned_rows, columns)
    summary = CsvSummary(
        rows_in=rows_in,
        rows_out=len(cleaned_rows),
        columns=list(columns),
        missing_by_column=missing,
        numeric_stats=numeric,
    )
    return columns, cleaned_rows, summary


def iter_write_rows(columns: Sequence[str], rows: Iterable[dict[str, str]]) -> Iterator[dict[str, str]]:
    for row in rows:
        yield {c: row.get(c, "") for c in columns}


def write_csv(path: Path, *, columns: Sequence[str], rows: Iterable[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(columns))
        writer.writeheader()
        writer.writerows(iter_write_rows(columns, rows))
