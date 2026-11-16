#!/usr/bin/env python3
"""
Run the capstone criteria three times and write the run log.

    python run_extension.py --label before
    python run_extension.py --label after

Each criterion in criteria.md ("Capstone 1" to "Capstone 5") has three trials.
This runs all fifteen trials, scores each one against the criterion's own
wording, and does that whole pass three separate times, so a cell in the table
is "trials passed out of 3". A criterion is MET when every one of the three
passes scored 3.

The fault trials go through faults.py, which breaks one thing from the outside
and never calls the model. The four trials that use the real model (Capstone 3
trial 1, Capstone 4 trial 1, Capstone 5 trials 1 and 2) make real requests with
the cache off, so a short pause comes before each, to stay under the rate limit.

It writes two files to results/, named for the label and the time:

    run_<time>_<label>.md      the table, then what each trial saw
    run_<time>_<label>.jsonl   every log line the trials wrote, with a
                               "trial" line before each one

Run it from a checkout of the commit you want to measure. The "before" run is
made on d8dfb41 (a git worktree of it), the "after" run on the commit with the
boundary. The summary names the commit.
"""

import argparse
import os
import platform
import subprocess
import sys
import time
from contextlib import ExitStack
from datetime import datetime
from pathlib import Path

# Before config is imported: real answers, not cached ones.
os.environ["AI201_CACHE"] = "0"

ROOT = Path(__file__).parent
TEE = "vintage graphic tee under $30"
JACKET = "90s track jacket in size M"
IMPOSSIBLE = "designer ballgown size XXS"
ACTION_WORDS = ("try again", "wait", "restart", "mcp_server.py")
SERVER_PROCESSES = ("mcp_server.py", "fault_server.py")  # not the agent's own process

CRITERIA = [
    "1. A known failure ends with a message, not an exception",
    "2. A caller of the web service gets the session, not a 500",
    "3. Every run leaves a record of each step it took, failures included",
    "4. The record matches a hand count of what the run spent",
    "5. The old paths are unchanged",
]


# ── running the agent ─────────────────────────────────────────────────────────

def _first_line(text):
    lines = str(text).strip().splitlines()
    return lines[0] if lines else ""


def agent(query, faults_on=(), via_serve=False):
    """One run of the agent, optionally under faults and optionally through /ask."""
    import faults
    import runlog
    from agent import run_agent
    from utils.data_loader import get_example_wardrobe

    session = raised = http = None
    # A run that never reaches start_run() would otherwise be read back under the
    # previous trial's run id.
    os.environ.pop(runlog.RUN_ID_ENV, None)
    with ExitStack() as stack:
        for fault_id in faults_on:
            for factory in faults.FAULTS[fault_id][1]:
                stack.enter_context(factory())
        try:
            if via_serve:
                from serve import app

                reply = app.test_client().post(
                    "/ask", json={"query": query, "wardrobe": get_example_wardrobe()}
                )
                http, session = reply.status_code, reply.get_json()
            else:
                session = run_agent(query, get_example_wardrobe())
        except Exception as exc:  # noqa: BLE001 — what escaped is the finding
            raised = f"{type(exc).__name__}: {_first_line(exc)}"
    run_id = os.environ.get(runlog.RUN_ID_ENV, "-")
    return {"session": session or {}, "raised": raised, "http": http,
            "run_id": run_id, "rows": runlog.lines(run_id)}


def _calls(rows):
    return [r for r in rows if r.get("step") == "model_call"]


def _tokens(rows):
    return (sum(r.get("prompt_tokens") or 0 for r in rows),
            sum(r.get("output_tokens") or 0 for r in rows))


# ── the fifteen trials: each returns (passed, what it saw, run id) ────────────

def c1(fault, step):
    r = agent(TEE, [fault])
    if r["raised"]:
        return False, f"raised {r['raised']}", r["run_id"]
    error = r["session"].get("error") or ""
    named = step in error
    action = any(w in error.lower() for w in ACTION_WORDS)
    return (bool(error) and named and action,
            f"returned; error names {step!r}: {named}; gives an action: {action}; "
            f"{_first_line(error)[:90]}", r["run_id"])


def c2(fault):
    r = agent(TEE, [fault], via_serve=True)
    body = (r["session"] or {}).get("error") or ""
    ok = r["http"] == 200 and bool(body)
    return ok, f"HTTP {r['http']}; error: {_first_line(body)[:90]}", r["run_id"]


def _has_fields(row):
    return ("step" in row and "input" in row and "duration_ms" in row
            and ("output" in row or "error" in row))


def c3(query, faults_on, expected_steps):
    r = agent(query, faults_on)
    steps = [row.get("step") for row in r["rows"]]
    complete = all(_has_fields(row) for row in r["rows"])
    ok = steps == expected_steps and complete
    return (ok, f"{len(steps)} lines (expected {len(expected_steps)}), fields complete: "
            f"{complete}; steps {steps}", r["run_id"])


def c4_clean():
    import generate

    before = generate.token_counts()
    r = agent(TEE)
    after = generate.token_counts()
    calls = _calls(r["rows"])
    retries = sum(1 for c in calls if c.get("error"))
    expected = 2 + retries
    agent_rows = [c for c in calls if c.get("process") not in SERVER_PROCESSES]
    logged = _tokens(agent_rows)
    printed = (after["prompt"] - before["prompt"], after["output"] - before["output"])
    ok = len(calls) == expected and logged == printed and not r["raised"]
    return (ok, f"{len(calls)} requests (expected {expected}); agent-process tokens in "
            f"the log {logged}, printed total {printed}", r["run_id"])


def c4_fault(fault, expected_requests, expected_tokens):
    r = agent(TEE, [fault])
    calls = _calls(r["rows"])
    tokens = _tokens(calls)
    ok = len(calls) == expected_requests and tokens == expected_tokens
    return (ok, f"{len(calls)} requests logged (hand count {expected_requests}); "
            f"tokens {tokens} (expected {expected_tokens})", r["run_id"])


def c5_matching(query):
    r = agent(query)
    s = r["session"]
    card = s.get("fit_card")
    outfit = s.get("outfit_suggestion")
    item = (s.get("selected_item") or {}).get("title")
    # "Runs all three tools": an item, an outfit with text, and a real fit card
    # (create_fit_card answers "No outfit to write a fit card for." for an empty one).
    ok = (not r["raised"] and s.get("error") is None and bool(item)
          and isinstance(outfit, str) and bool(outfit.strip())
          and isinstance(card, str) and bool(card.strip())
          and not card.startswith("No outfit"))
    return (ok, f"error: {_first_line(r['raised'] or s.get('error') or 'None')[:80]}; "
            f"item {item!r}; outfit {'present' if outfit else 'missing'}; "
            f"fit card {'present' if card else 'missing'}", r["run_id"])


def c5_impossible():
    r = agent(IMPOSSIBLE)
    s = r["session"]
    error = s.get("error") or ""
    ok = (not r["raised"] and "You could" in error
          and s.get("outfit_suggestion") is None and s.get("fit_card") is None)
    return (ok, f"error contains 'You could': {'You could' in error}; no outfit and no "
            f"fit card in the session: "
            f"{s.get('outfit_suggestion') is None and s.get('fit_card') is None}",
            r["run_id"])


# (criterion index, trial name, uses the real model, function)
TRIALS = [
    (0, "model-429", False, lambda: c1("model-429", "suggest_outfit")),
    (0, "search-down", False, lambda: c1("search-down", "search")),
    (0, "budget", False, lambda: c1("budget", "suggest_outfit")),
    (1, "model-429 via /ask", False, lambda: c2("model-429")),
    (1, "search-down via /ask", False, lambda: c2("search-down")),
    (1, "budget via /ask", False, lambda: c2("budget")),
    (2, "clean query", True, lambda: c3(TEE, (), [
        "search_listings", "model_call", "suggest_outfit", "model_call",
        "create_fit_card", "run"])),
    (2, "impossible query", False, lambda: c3(IMPOSSIBLE, (), [
        "search_listings", "run"])),
    (2, "model-429", False, lambda: c3(TEE, ("model-429",), [
        "search_listings", *["model_call"] * 5, "suggest_outfit", "run"])),
    (3, "clean query", True, c4_clean),
    (3, "model-429", False, lambda: c4_fault("model-429", 5, (0, 0))),
    (3, "fit-card-exit", False, lambda: c4_fault("fit-card-exit", 2, (120, 30))),
    (4, "tee", True, lambda: c5_matching(TEE)),
    (4, "jacket", True, lambda: c5_matching(JACKET)),
    (4, "impossible query", False, c5_impossible),
]


# ── the whole thing ───────────────────────────────────────────────────────────

def _git(*args):
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True,
                              text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def main():
    parser = argparse.ArgumentParser(description="Run the capstone criteria three times.")
    parser.add_argument("--label", required=True, choices=["before", "after"])
    parser.add_argument("--passes", type=int, default=3, help="separate times to run it all")
    parser.add_argument("--pause", type=float, default=8.0,
                        help="seconds before each trial that calls the real model")
    parser.add_argument("--out-dir", default=str(ROOT / "results"),
                        help="where the two files go (default: results/ next to this script)")
    args = parser.parse_args()

    commit = _git("rev-parse", "--short", "HEAD") or "unknown"
    # Tracked files only: the before run copies this script into a worktree of
    # the old commit, and the logs it writes are not a change to the code.
    dirty = (" (uncommitted changes)"
             if _git("status", "--porcelain", "--untracked-files=no") else "")
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    log_path = out / f"run_{stamp}_{args.label}.jsonl"
    md_path = out / f"run_{stamp}_{args.label}.md"
    os.environ["AI201_LOG_PATH"] = str(log_path)

    import config
    import runlog

    # scores[c][p] = trials passed on pass p; details[c][p] = one line per trial
    scores = [[0] * args.passes for _ in CRITERIA]
    details = [[[] for _ in range(args.passes)] for _ in CRITERIA]

    for p in range(args.passes):
        for c, name, real, trial in TRIALS:
            if real:
                time.sleep(args.pause)  # outside the trial, so not in any duration
            runlog.write(step="trial", run_id="suite",
                         input=f"pass {p + 1}, criterion {c + 1}, {name}",
                         output=args.label)
            try:
                ok, seen, run_id = trial()
            except Exception as exc:  # noqa: BLE001 — a crashed trial is a failed trial
                ok, seen, run_id = False, f"the trial itself crashed: {type(exc).__name__}: " \
                                          f"{_first_line(exc)}", "-"
            scores[c][p] += 1 if ok else 0
            details[c][p].append((name, ok, seen, run_id))
            print(f"  pass {p + 1}  criterion {c + 1}  {name:<22} "
                  f"{'pass' if ok else 'MISS'}", file=sys.stderr)

    lines = [
        f"# Capstone run log: {args.label}, {stamp}",
        "",
        f"- Commit: {commit}{dirty}",
        f"- Python {platform.python_version()} on {platform.system()}, model "
        f"{config.MODEL}, temperature {config.TEMPERATURE}, cache off",
        f"- Command: python run_extension.py --label {args.label} "
        f"({args.passes} separate passes of the fifteen trials)",
        f"- Log: results/{log_path.name}, with a `trial` line before each trial",
        "",
        "| Criterion | Target | " + " | ".join(f"Run {p + 1}" for p in range(args.passes))
        + " | Verdict |",
        "|---|---|" + "---|" * args.passes + "---|",
    ]
    for c, title in enumerate(CRITERIA):
        verdict = "MET" if all(s == 3 for s in scores[c]) else "MISSED"
        lines.append(f"| {title} | 3 of 3 | "
                     + " | ".join(f"{s}/3" for s in scores[c]) + f" | {verdict} |")

    lines += ["", "## What each trial saw", ""]
    for c, title in enumerate(CRITERIA):
        lines += [f"### Criterion {title}", "",
                  "| Run | Trial | Result | What it saw | Run id |", "|---|---|---|---|---|"]
        for p in range(args.passes):
            for name, ok, seen, run_id in details[c][p]:
                seen = seen.replace("|", "/")
                lines.append(f"| {p + 1} | {name} | {'pass' if ok else 'MISS'} | {seen} | {run_id} |")
        lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines[:16]))
    print(f"\nWrote {md_path} and {log_path}")


if __name__ == "__main__":
    main()
