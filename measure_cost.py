#!/usr/bin/env python3
"""
Measure what one FitFindr run costs.

    python measure_cost.py              ten runs, cache off
    python measure_cost.py --runs 4     fewer, for a quick look

The cost is what the run itself reported, not an estimate off a pricing page:
model requests, prompt tokens, output tokens, and seconds. All of it is added
up from the run log (runlog.totals), which counts the model call inside the MCP
server as well as the agent's own. The agent's printed total misses that one.

The runs use five matching queries, two runs each, so the number is an average
over different items and not one lucky query. The cache is off, so every run
makes real model requests. Then one query that matches nothing is run once, to
leave a failed run in the log. It is listed apart and left out of the average.

The run log goes to results/ next to the summary, and both are meant to be
committed. Both name the commit the runs were made on.
"""

import argparse
import os
import platform
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Before config is imported: five separate answers, not cached ones.
os.environ["AI201_CACHE"] = "0"

ROOT = Path(__file__).parent
FAILING_QUERY = "designer ballgown size XXS under $5"  # matches nothing, on purpose


def _git(*args):
    try:
        out = subprocess.run(["git", *args], cwd=ROOT, capture_output=True,
                             text=True, check=True).stdout.strip()
        return out
    except (OSError, subprocess.CalledProcessError):
        return ""


def _commit():
    short = _git("rev-parse", "--short", "HEAD") or "unknown"
    return short + (" (uncommitted changes)" if _git("status", "--porcelain") else "")


def measure(query, number, label):
    """One run of the agent. Returns what the run log says it cost."""
    import runlog
    from agent import run_agent
    from utils.data_loader import get_example_wardrobe

    crashed = None
    session = {"error": None}
    try:
        session = run_agent(query, get_example_wardrobe())
    except Exception as exc:  # noqa: BLE001 — a crash is a result worth recording
        crashed = f"{type(exc).__name__}: {exc}"

    run_id = os.environ.get(runlog.RUN_ID_ENV, "-")
    rows = runlog.lines(run_id)
    run_line = next((r for r in rows if r.get("step") == "run"), {})
    totals = runlog.totals(run_id)
    return {
        "n": number,
        "label": label,
        "query": query,
        "run_id": run_id,
        "error": crashed or session.get("error"),
        "calls": totals["model_calls"],
        "prompt": totals["prompt_tokens"],
        "output": totals["output_tokens"],
        "seconds": (run_line.get("duration_ms") or 0) / 1000,
        "model_seconds": sum(r.get("duration_ms") or 0
                             for r in rows if r.get("step") == "model_call") / 1000,
    }


def _mean(values):
    return sum(values) / len(values) if values else 0.0


def main():
    parser = argparse.ArgumentParser(description="Measure the cost of one FitFindr run.")
    parser.add_argument("--runs", type=int, default=10, help="how many runs to average")
    parser.add_argument("--pause", type=float, default=8.0,
                        help="seconds to wait between runs, to stay under the rate limit")
    args = parser.parse_args()

    commit = _commit()  # before the runs: the log they write is not a change to the code
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    results = ROOT / "results"
    results.mkdir(exist_ok=True)
    log_path = results / f"cost_{stamp}.jsonl"
    summary_path = results / f"cost_{stamp}.md"
    os.environ["AI201_LOG_PATH"] = str(log_path)

    import config
    from app import EXAMPLE_QUERIES

    queries = [q for q in EXAMPLE_QUERIES if q != FAILING_QUERY]
    plan = [(queries[i % len(queries)], "cost") for i in range(args.runs)]
    plan.append((FAILING_QUERY, "failed run, not in the average"))

    rows = []
    for number, (query, label) in enumerate(plan, start=1):
        if number > 1:
            time.sleep(args.pause)  # outside the run, so it is not in the seconds
        row = measure(query, number, label)
        rows.append(row)
        print(f"\n  run {number}/{len(plan)}: {row['calls']} requests, "
              f"{row['prompt']} + {row['output']} tokens, {row['seconds']:.1f}s"
              f"{'  (error)' if row['error'] else ''}", file=sys.stderr)

    counted = [r for r in rows if r["label"] == "cost"]
    lines = [
        f"# What one run costs: {stamp}",
        "",
        f"- Commit: {commit}",
        f"- Python {platform.python_version()} on {platform.system()}, "
        f"model {config.MODEL}, temperature {config.TEMPERATURE}, cache off",
        f"- Run log: results/{log_path.name} (one JSON line per step and model request)",
        f"- Method: {len(counted)} runs of the agent through run_agent(), "
        f"{args.pause:g} seconds apart. Requests and tokens are summed from the "
        "log's model_call lines, from both processes. Seconds are the run line's "
        "own duration, which includes both model calls and any rate-limit wait.",
        "",
        "| Run | Query | Requests | Prompt tokens | Output tokens | Seconds | Error |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        mark = r["label"] if r["label"] != "cost" else ""
        error = (r["error"] or "").replace("|", "/").splitlines()[0][:70] if r["error"] else ""
        lines.append(
            f"| {r['n']}{' (' + mark + ')' if mark else ''} | {r['query']} | {r['calls']} | "
            f"{r['prompt']} | {r['output']} | {r['seconds']:.1f} | {error} |"
        )
    lines += [
        "",
        f"**Average of the {len(counted)} runs:** "
        f"{_mean([r['calls'] for r in counted]):.1f} requests, "
        f"{_mean([r['prompt'] for r in counted]):.0f} prompt tokens, "
        f"{_mean([r['output'] for r in counted]):.0f} output tokens "
        f"({_mean([r['prompt'] + r['output'] for r in counted]):.0f} total), "
        f"{_mean([r['seconds'] for r in counted]):.1f} seconds "
        f"({_mean([r['model_seconds'] for r in counted]):.1f} of them inside model calls).",
        f"**Range:** {min(r['prompt'] + r['output'] for r in counted)} to "
        f"{max(r['prompt'] + r['output'] for r in counted)} tokens, "
        f"{min(r['seconds'] for r in counted):.1f} to "
        f"{max(r['seconds'] for r in counted):.1f} seconds.",
        f"**Runs that ended in an error:** {sum(1 for r in counted if r['error'])} of "
        f"{len(counted)}.",
        "",
    ]
    summary_path.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"\nWrote {summary_path.relative_to(ROOT)} and {log_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
