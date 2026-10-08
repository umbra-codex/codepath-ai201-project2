#!/usr/bin/env python3
"""
Scores the revised criterion 3 in criteria.md. ← UNIT 4, MILESTONE 4

    python check_handoff.py

The trace can't settle this one on its own. It is `run_agent`'s own report: the
trace line and the tool call read the same variable, so a check on the trace
trusts the loop to print what it passes.

This replaces the two model tools with stand-ins that write down the `new_item`
they were called with, runs the real loop, and compares each recorded id with
`session["selected_item"]` and with the first search result afterwards.
`create_fit_card` is called over MCP, so its stand-in sits in front of
`call_tool` and passes every other tool through. The search still goes through
MCP. No model is called, because the criterion is about what the tools receive
and not about what the model writes.

It only looks at `new_item`. A wrong wardrobe or outfit argument would get past
it, and so would a tool that ignored the item it was given.
"""

import contextlib
import io
import sys

import agent
from utils.data_loader import get_example_wardrobe

QUERY = "90s track jacket in size M"
real_call_tool = agent.call_tool
TRIES = 5


def run_once() -> tuple[dict, dict]:
    """One run of the loop. Returns what each tool received, and the session."""
    received = {}

    def record_outfit(new_item, wardrobe):
        received["suggest_outfit"] = new_item["id"]
        return "stand-in outfit"

    def record_card(name, arguments):
        if name != "create_fit_card":
            return real_call_tool(name, arguments)
        received["create_fit_card"] = arguments["new_item"]["id"]
        return "stand-in fit card"

    agent.suggest_outfit = record_outfit
    agent.call_tool = record_card

    # run_agent prints its trace as it goes. Not what this check is showing.
    with contextlib.redirect_stdout(io.StringIO()):
        session = agent.run_agent(QUERY, get_example_wardrobe())
    return received, session


def main() -> int:
    print(f"query: {QUERY}")
    passed = 0
    for attempt in range(1, TRIES + 1):
        received, session = run_once()
        selected = (session["selected_item"] or {}).get("id")
        first = (session["search_results"] or [{}])[0].get("id")
        ok = (
            selected is not None
            and selected == first
            and received.get("suggest_outfit") == selected
            and received.get("create_fit_card") == selected
        )
        passed += ok
        print(
            f"  try {attempt}: first result {first}, session has {selected}, "
            f"suggest_outfit got {received.get('suggest_outfit')}, "
            f"create_fit_card got {received.get('create_fit_card')}  "
            f"{'PASS' if ok else 'FAIL'}"
        )
    print(f"{passed} of {TRIES} passed")
    return 0 if passed == TRIES else 1


if __name__ == "__main__":
    sys.exit(main())
