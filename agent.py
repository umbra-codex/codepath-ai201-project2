"""
The FitFindr planning loop.

This is the file that makes FitFindr an agent rather than a script. It decides
which tool to run next based on what the last one returned.

If your loop calls all three tools no matter what comes back, you have a list
of function calls. A loop looks at the last result before it picks the next
step. **That branch is the graded part of this unit.**

Build and test your three tools in `tools.py` first. Then come here.

    python agent.py          runs both example paths below
"""

import re

import config
import trace
from mcp_client import MCPError, call_tool
from tools import suggest_outfit
from generate import ModelUnavailable


# ── session state ─────────────────────────────────────────────────────────────

def new_session(query: str, wardrobe: dict) -> dict:
    """
    A fresh session for one user interaction.

    The session is the single source of truth for a run. Every tool result goes
    in here, and the next tool reads it back out.

    You could pass values straight from one call to the next. It would work,
    and you would not be able to test it — you can't print a variable you have
    already overwritten. Going through the session is what makes the state
    visible, and unit 4 has you write a criterion about exactly that.

    Add fields if you need them.
    """
    return {
        "query": query,              # what the user typed
        "parsed": {},                # description / size / max_price you pulled out of it
        "search_results": [],        # everything search_listings returned
        "selected_item": None,       # the one you chose — goes into suggest_outfit
        "wardrobe": wardrobe,        # the user's wardrobe
        "outfit_suggestion": None,   # what suggest_outfit returned
        "fit_card": None,            # what create_fit_card returned
        "notice": None,              # set when the run finished with a caveat
        "error": None,               # set when the run ended early
    }


# ── parsing the query ─────────────────────────────────────────────────────────

# Tried in order; the first one that matches sets the price limit.
_PRICES = [
    # "under $30", "below 30", "less than $30", "up to $30", "max $30"
    re.compile(
        r"\b(?:under|below|less than|up to|at most|max(?:imum)?(?: of)?)\s*\$?\s*(\d+(?:\.\d+)?)",
        re.IGNORECASE,
    ),
    # "30 or less", "$30 or under"
    re.compile(
        r"\$?\s*(\d+(?:\.\d+)?)\s*(?:dollars|bucks)?\s+or\s+(?:less|under|below|cheaper)\b",
        re.IGNORECASE,
    ),
    # a bare "$30"
    re.compile(r"\$\s*(\d+(?:\.\d+)?)"),
]
# "size M", "in size US 8", "size W30 L30", "size 8", "size small"
_SIZE = re.compile(
    r"\b(?:in\s+)?size\s+(us\s*\d+(?:\.\d+)?|w\d+(?:\s+l\d+)?|one size|small|medium|large|\d+(?:\.\d+)?|[a-z]{1,4})\b",
    re.IGNORECASE,
)
_SIZE_WORDS = {"SMALL": "S", "MEDIUM": "M", "LARGE": "L"}


def parse_query(query: str) -> dict:
    """
    Pull a description, a size, and a max_price out of the query with regex.

    Whatever is left after the price and size phrases are removed is the
    description. A bare number after "size" is read as a US shoe size, because
    that is how the data writes them ("size 8" becomes "US 8"). "small",
    "medium", and "large" after "size" become S, M, and L.
    """
    max_price = None
    size = None
    description = query

    for pattern in _PRICES:
        price_match = pattern.search(description)
        if price_match:
            max_price = float(price_match.group(1))
            description = description.replace(price_match.group(0), " ")
            break

    size_match = _SIZE.search(description)
    if size_match:
        size = " ".join(size_match.group(1).split()).upper()
        size = _SIZE_WORDS.get(size, size)
        if re.fullmatch(r"\d+(?:\.\d+)?", size):
            size = f"US {size}"
        description = description.replace(size_match.group(0), " ")

    return {
        "description": " ".join(description.replace(",", " ").split()),
        "size": size,
        "max_price": max_price,
    }


def _no_results_message(parsed: dict) -> str:
    """Say what was searched for and what the user could change."""
    searched = f"No listings matched \"{parsed['description']}\""
    changes = []
    if parsed["size"]:
        searched += f" in size {parsed['size']}"
        changes.append("drop the size or try another one")
    if parsed["max_price"] is not None:
        searched += f" under ${parsed['max_price']:g}"
        changes.append("raise the price limit")
    changes.append("describe the item in different words")
    if len(changes) > 1:
        changes[-1] = "or " + changes[-1]
    joiner = ", " if len(changes) > 2 else " "
    return f"{searched}. You could {joiner.join(changes)}."


_EMPTY_WARDROBE_NOTICE = (
    "Your wardrobe is empty, so the outfit is general styling advice and not "
    "built from pieces you own. Add a few wardrobe items and ask again to get "
    "outfits that use them."
)


def _model_down_message(step: str, exc: ModelUnavailable) -> str:
    """Say which step lost the model, what that cost, and what to try."""
    return (
        f"The search worked, but {step} could not get an answer from the "
        f"model, so there is no fit card. {exc}"
    )


def _fit_card_down_message(exc: MCPError) -> str:
    """Say that the last step failed on the MCP server, and pass on why."""
    return (
        f"The search and the outfit worked, but create_fit_card failed on the "
        f"MCP server, so there is no fit card. {str(exc).splitlines()[0]}"
    )


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Run the loop once and return the finished session.

    Args:
        query:    what the user asked for, in plain language
                  (e.g. "vintage graphic tee under $30, size M").
        wardrobe: a wardrobe dict — get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py.

    Returns:
        The session dict. **Check session["error"] first** — if it isn't None,
        the run ended early and the later fields will still be None.

    ─────────────────────────────────────────────────────────────────────────
    TODO — build this, following the branch rule you wrote in Milestone 2.

      1. Start a session with new_session().

      2. Count the times round the loop, and call trace.check_iterations(count)
         on each one before you go again. It raises when the count passes
         MAX_ITERATIONS in config.py — see trace.py.

      3. Parse the query into a description, a size, and a max_price. Regex,
         string splitting, or asking the model are all fine — say which you
         chose in your README. Put the result in session["parsed"].

      4. Call search_listings() with what you parsed.
         Put the results in session["search_results"].

         ⚠️ THIS IS THE BRANCH. If nothing came back:
              - put a message in session["error"] saying what the user could
                change — "No results" is not that message
              - return the session
              - do NOT call suggest_outfit with nothing

      5. Choose an item — the first result is fine. Put it in
         session["selected_item"].

      6. Call suggest_outfit() with the selected item and the wardrobe.
         Put the result in session["outfit_suggestion"].

      7. Call create_fit_card() with the outfit and the item.
         Put the result in session["fit_card"].

      8. Return the session.

    ─────────────────────────────────────────────────────────────────────────
    IN UNIT 4 you come back and add two things:

      • Trace calls. One per step. `trace.step("search_listings", inputs=...,
        returned=...)` — see trace.py. Your README needs the output.

      • A handler for ModelUnavailable, so a bad key produces a message rather
        than a stack trace. The import is already at the top of this file.
    """
    session = new_session(query, wardrobe)
    session["parsed"] = parse_query(query)

    # Each pass runs one tool, puts its result in the session, and picks the
    # next step from what came back. None means the run is over.
    step = "search_listings"
    count = 0
    while step:
        count += 1
        trace.check_iterations(count)

        if step == "search_listings":
            parsed = session["parsed"]
            # search_listings runs on the MCP server, not as a direct call.
            session["search_results"] = call_tool("search_listings", {
                "description": parsed["description"],
                "size": parsed["size"],
                "max_price": parsed["max_price"],
            })
            # The branch: nothing found means stop here, before any model call.
            if not session["search_results"]:
                session["error"] = _no_results_message(session["parsed"])
                trace.step(
                    "search_listings (via MCP)", inputs=str(parsed),
                    returned=session["search_results"],
                    note="branch: empty, stopping before suggest_outfit",
                )
                step = None
            else:
                session["selected_item"] = session["search_results"][0]
                trace.step(
                    "search_listings (via MCP)", inputs=str(parsed),
                    returned=session["search_results"],
                    note=f"branch: selected {session['selected_item']['title']}",
                )
                step = "suggest_outfit"

        elif step == "suggest_outfit":
            item = session["selected_item"]
            pieces = len(session["wardrobe"].get("items") or [])
            inputs = f"new_item={item['title']}; wardrobe={pieces} items"
            note = ""
            if not pieces:
                session["notice"] = _EMPTY_WARDROBE_NOTICE
                note = "empty wardrobe: general advice, notice set"
            try:
                session["outfit_suggestion"] = suggest_outfit(item, session["wardrobe"])
            except ModelUnavailable as exc:
                session["error"] = _model_down_message(step, exc)
                trace.step(step, inputs=inputs, note=f"ModelUnavailable, stopping: {exc}")
                step = None
            else:
                trace.step(step, inputs=inputs,
                           returned=session["outfit_suggestion"], note=note)
                step = "create_fit_card"

        elif step == "create_fit_card":
            item = session["selected_item"]
            inputs = (
                f"new_item={item['title']}; "
                f"outfit={session['outfit_suggestion'][:40]}…"
            )
            # create_fit_card runs on the MCP server too. The model call happens
            # in the server's process, so a failure there comes back as MCPError
            # and not as ModelUnavailable.
            try:
                session["fit_card"] = call_tool("create_fit_card", {
                    "outfit": session["outfit_suggestion"],
                    "new_item": item,
                })
            except MCPError as exc:
                session["error"] = _fit_card_down_message(exc)
                trace.step("create_fit_card (via MCP)", inputs=inputs,
                           note=f"MCPError, stopping: {str(exc).splitlines()[0]}")
            else:
                trace.step("create_fit_card (via MCP)", inputs=inputs,
                           returned=session["fit_card"])
            step = None

    return session


# ── running it directly ───────────────────────────────────────────────────────

def _show(session: dict) -> None:
    if session["error"]:
        print(f"  stopped: {session['error']}")
        print(f"  fit_card is {session['fit_card']!r} — it should still be None here")
        return

    item = session["selected_item"] or {}
    print(f"  found:    {item.get('title')} — ${item.get('price')} on {item.get('platform')}")
    print(f"  outfit:   {session['outfit_suggestion']}")
    print(f"  fit card: {session['fit_card']}")
    if session["notice"]:
        print(f"  note:     {session['notice']}")


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== A query the data can match ===")
    _show(run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    ))

    print("\n=== A query it can't ===")
    _show(run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    ))

    print(
        "\nThe second one should stop before the fit card. If both paths look "
        "the same,\nthe branch isn't doing anything yet."
    )
