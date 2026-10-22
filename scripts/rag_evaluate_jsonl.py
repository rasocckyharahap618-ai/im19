#!/usr/bin/env python3
"""Evaluate saved JSONL retrieval results offline; no network access."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from integrations.rag.evaluation import aggregate_metrics, evaluate_case

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="JSONL with case and retrieved results")
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--output", help="Optional output JSON path; defaults to stdout")
    args = parser.parse_args()
    if not 1 <= args.k <= 50:
        parser.error("--k must be between 1 and 50")
    input_path = Path(args.input).resolve()
    if not input_path.is_file():
        parser.error("Input file does not exist.")
    scored = []
    with input_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                parser.error(f"Invalid JSON on line {line_number}: {exc.msg}")
            if not isinstance(record, dict) or not isinstance(record.get("case"), dict):
                parser.error(f"Line {line_number} must contain a case object.")
            results = record.get("results", [])
            if not isinstance(results, list):
                parser.error(f"Line {line_number} results must be a list.")
            scored.append(evaluate_case(record["case"], results, k=args.k))
    output = json.dumps({"aggregate": aggregate_metrics(scored), "cases": scored}, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(output + "\n", encoding="utf-8")
    else:
        print(output)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
