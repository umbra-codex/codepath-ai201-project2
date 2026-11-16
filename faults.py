"""
Faults for testing the extension.

Each fault makes one thing fail from the outside, so the agent code that runs
under it is the code that ships. Nothing in the agent imports this file, and no
switch in production code turns a fault on.

Two kinds:

  - faults in the agent's own process, patched into `generate`, `config` or
    `mcp_client` for the length of a `with` block
  - faults in the MCP server's process: the server is started from
    fault_server.py instead of mcp_server.py, with FITFINDR_FAULT set, because
    the fit card's model call happens over there

No fault touches the network. The model is a script (ScriptedClient), the
search reads the local data, and the five retries run on a fake clock so a
fault that ends in 429s takes a moment and not a minute.

Try every fault once, each in its own process with a 60 second cap, so a fault
that hangs is reported as a hang and does not stop the rest:

    python faults.py                 all of them
    python faults.py --one budget    one of them
    python faults.py --serve         all of them, through serve.py's /ask
"""

import argparse
import os
import subprocess
import sys
import time
from contextlib import ExitStack, contextmanager
from pathlib import Path

import config

ROOT = Path(__file__).parent
FAULT_SERVER = ROOT / "fault_server.py"
FAULT_ENV = "FITFINDR_FAULT"
QUERY = "vintage graphic tee under $30"
HANG_AFTER_SECONDS = 60


# ── a model and a clock that follow a script ──────────────────────────────────

class FakeTime:
    """Stands in for generate's `time`, so waiting is instant and still counted."""

    def __init__(self):
        self.now = 1000.0
        self.slept = 0.0

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds
        self.slept += seconds


class _Usage:
    def __init__(self, prompt_tokens, output_tokens):
        self.prompt_token_count = prompt_tokens
        self.candidates_token_count = output_tokens


class _Response:
    def __init__(self, text, prompt_tokens, output_tokens):
        self.text = text
        self.usage_metadata = _Usage(prompt_tokens, output_tokens)


class ScriptedClient:
    """
    Answers model requests from a list instead of the network.

    Each step is "429", "exit", or ("ok", text, prompt_tokens, output_tokens).
    When the list runs out, `then` repeats forever. "exit" kills the process
    mid-request, which is what a server crash looks like from the other side.
    The token counts are made up on purpose: a hand count of a scripted run is
    a number you can add up in your head and check against the log.
    """

    def __init__(self, script, then="429"):
        self.script = list(script)
        self.then = then
        self.requests = 0
        self.models = self  # generate calls client.models.generate_content

    def generate_content(self, **kwargs):
        self.requests += 1
        step = self.script.pop(0) if self.script else self.then
        if step == "429":
            raise Exception(
                "429 RESOURCE_EXHAUSTED. You exceeded your current quota. "
                "Please retry in 1s."
            )
        if step == "exit":
            os._exit(3)
        _, text, prompt_tokens, output_tokens = step
        return _Response(text, prompt_tokens, output_tokens)


@contextmanager
def _swap(obj, name, value):
    old = getattr(obj, name)
    setattr(obj, name, value)
    try:
        yield
    finally:
        setattr(obj, name, old)


# ── faults in the agent's process ─────────────────────────────────────────────

@contextmanager
def model_answers(script, then="429"):
    """The agent's own model calls follow `script`; cache off, clock fake."""
    import generate

    client = ScriptedClient(script, then)
    with ExitStack() as stack:
        stack.enter_context(_swap(generate, "_client", client))
        stack.enter_context(_swap(generate, "time", FakeTime()))
        stack.enter_context(_swap(generate, "_call_times", []))
        stack.enter_context(_swap(generate, "_session_calls", 0))
        stack.enter_context(_swap(config, "CACHE_ENABLED", False))
        yield client


OUTFIT = ("Wear it with the dark jeans and the white sneakers, and keep the "
          "jacket for when it cools down.")


def model_answers_outfit():
    """The outfit step succeeds, so a later fault is the only thing that fails."""
    return model_answers([("ok", OUTFIT, 120, 30)])


def model_always_429():
    """Every model request is pushed back, past MAX_RETRIES."""
    return model_answers([])


@contextmanager
def budget_spent():
    """The session has already used its request budget (SESSION_REQUEST_BUDGET)."""
    import generate

    with ExitStack() as stack:
        stack.enter_context(_swap(generate, "_session_calls", config.SESSION_REQUEST_BUDGET))
        stack.enter_context(_swap(config, "CACHE_ENABLED", False))
        yield


@contextmanager
def search_server_down():
    """mcp_server.py cannot start, so the first MCP call, the search, fails."""
    import mcp_client

    with _swap(mcp_client, "SERVER", ROOT / "no_such_server.py"):
        yield


@contextmanager
def fit_card_server_down():
    """The server will not start for create_fit_card. The search call still works."""
    import mcp_client

    real = mcp_client._call

    async def _call(name, arguments):
        if name == "create_fit_card":
            raise ConnectionError("fault: the server did not start")
        return await real(name, arguments)

    with _swap(mcp_client, "_call", _call):
        yield


# ── faults in the MCP server's process ────────────────────────────────────────

@contextmanager
def server_fault(mode):
    """Start the server from fault_server.py with `mode` installed over there."""
    import mcp
    import mcp_client

    original = mcp.StdioServerParameters

    class Faulted(original):
        def __init__(self, **kwargs):
            env = dict(kwargs.get("env") or {})
            env[FAULT_ENV] = mode
            kwargs["env"] = env
            super().__init__(**kwargs)

    with ExitStack() as stack:
        stack.enter_context(_swap(mcp, "StdioServerParameters", Faulted))
        stack.enter_context(_swap(mcp_client, "SERVER", FAULT_SERVER))
        stack.enter_context(_swap(config, "CACHE_ENABLED", False))
        yield


def fit_card_model_429():
    """Inside the server, every model request is pushed back past MAX_RETRIES."""
    return server_fault("429")


def fit_card_server_exits():
    """The server process dies in the middle of the fit card's model request."""
    return server_fault("exit")


# id -> (what it does, the faults to install together)
FAULTS = {
    "model-429": ("every model request is pushed back past MAX_RETRIES",
                  (model_always_429,)),
    "search-down": ("mcp_server.py cannot start, so the search fails",
                    (search_server_down,)),
    "budget": ("the session budget is already spent",
               (budget_spent,)),
    "fit-card-down": ("the server will not start for the fit card",
                      (model_answers_outfit, fit_card_server_down)),
    "fit-card-429": ("the fit card's model request is pushed back inside the server",
                     (model_answers_outfit, fit_card_model_429)),
    "fit-card-exit": ("the server dies in the middle of the fit card request",
                      (model_answers_outfit, fit_card_server_exits)),
}


# ── trying them ───────────────────────────────────────────────────────────────

def _first_line(text):
    lines = str(text).strip().splitlines()
    return lines[0] if lines else ""


def run_one(fault_id, via_serve=False):
    """
    Run the agent once under one fault and say what came back.

    With via_serve the request goes through serve.py's /ask, so what a caller
    of the web service would see (the status code and the body) is checked too.
    """
    import runlog
    from agent import run_agent
    from utils.data_loader import get_example_wardrobe

    description, factories = FAULTS[fault_id]
    session = raised = http = None
    started = time.perf_counter()
    with ExitStack() as stack:
        for factory in factories:
            stack.enter_context(factory())
        try:
            if via_serve:
                from serve import app

                reply = app.test_client().post(
                    "/ask", json={"query": QUERY, "wardrobe": get_example_wardrobe()}
                )
                http, session = reply.status_code, reply.get_json()
                if http != 200:
                    raised = f"HTTP {http}: {_first_line(session.get('error', ''))}"
            else:
                session = run_agent(QUERY, get_example_wardrobe())
        except Exception as exc:  # noqa: BLE001 — what escaped is the finding
            raised = f"{type(exc).__name__}: {_first_line(exc)}"
    seconds = time.perf_counter() - started

    run_id = os.environ.get(runlog.RUN_ID_ENV, "-")
    rows = runlog.lines(run_id)
    print(f"{fault_id}: {description}")
    if raised:
        print(f"  RAISED   {raised}")
    else:
        status = f"HTTP {http} " if http else ""
        print(f"  RETURNED {status}error: {_first_line(session['error'] or '(none)')}")
        item = (session.get("selected_item") or {}).get("title")
        print(f"  kept     item={item!r} outfit={bool(session.get('outfit_suggestion'))}")
    print(f"  took     {seconds:.1f}s, {len(rows)} log lines, {runlog.totals(run_id)}")


def main():
    parser = argparse.ArgumentParser(description="Try each fault once. No model is called.")
    parser.add_argument("--one", choices=sorted(FAULTS), help="try just this fault")
    parser.add_argument("--serve", action="store_true",
                        help="send each fault through serve.py's /ask and show the status")
    args = parser.parse_args()

    if args.one:
        run_one(args.one, via_serve=args.serve)
        return

    log = config.LOG_DIR / "smoke.jsonl"
    log.unlink(missing_ok=True)
    env = {**os.environ, "AI201_LOG_PATH": str(log)}
    for fault_id in FAULTS:
        try:
            subprocess.run(
                [sys.executable, __file__, "--one", fault_id]
                + (["--serve"] if args.serve else []),
                env=env, timeout=HANG_AFTER_SECONDS, check=False,
            )
        except subprocess.TimeoutExpired:
            print(f"{fault_id}: {FAULTS[fault_id][0]}")
            print(f"  HUNG     no answer after {HANG_AFTER_SECONDS}s, stopped by the harness")
        print()


if __name__ == "__main__":
    main()
