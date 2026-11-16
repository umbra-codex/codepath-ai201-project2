"""
The run log: one JSON line for each step of a run and each model call.

Every line has a timestamp, the run it belongs to, the process that wrote it,
what went in, what came out or how it failed, and how long it took in
milliseconds. A run that fails still leaves its lines, up to the step that
failed.

Two processes write to the same file. The agent runs in one, and the MCP server
runs the search and the fit card in another that exits after each call. The run
id and the log path travel to the server through the environment (see
mcp_client.py), so the model call that happens inside the server lands in the
same file under the same run id. That is the only way the call count and the
token count can be added up from the log.

Logging never raises. A full disk must not turn a working run into a failed one.
"""

import json
import os
import sys
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

import config

RUN_ID_ENV = "AI201_RUN_ID"
LOG_PATH_ENV = "AI201_LOG_PATH"

# Long prompts and fit cards would make the log unreadable. The full text is in
# the session and in the run record; the log keeps enough to tell lines apart.
_CLIP = 200


def log_path() -> Path:
    return Path(os.environ.get(LOG_PATH_ENV) or config.LOG_DIR / "fitfindr.jsonl")


def start_run() -> str:
    """Give the next lines a new run id, and put it where the server can read it."""
    run_id = uuid.uuid4().hex[:8]
    os.environ[RUN_ID_ENV] = run_id
    return run_id


def _clip(value):
    if value is None or isinstance(value, (bool, int, float)):
        return value
    text = str(value).replace("\n", " ")
    return text if len(text) <= _CLIP else text[:_CLIP] + "…"


def _first_line(exc: Exception) -> str:
    lines = str(exc).strip().splitlines()
    return f"{type(exc).__name__}: {lines[0] if lines else ''}".rstrip(": ")


def write(**fields) -> None:
    """Append one line. Fields are clipped; the common four are added here."""
    line = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        "run_id": os.environ.get(RUN_ID_ENV, "-"),
        "process": Path(sys.argv[0]).name if sys.argv and sys.argv[0] else "?",
        "pid": os.getpid(),
    }
    try:
        line.update({key: _clip(value) for key, value in fields.items()})
        path = log_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        # Each process opens the file for append and writes one short line (every
        # field is clipped), so on a local disk the two processes' lines do not
        # interleave. There is no lock; this is not promised on a network drive.
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(line, ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001 — a log line is never worth a failed run
        pass


@contextmanager
def step(name: str, input=None, **fixed):
    """
    Time one step and log it, whether it finishes or raises.

        with runlog.step("search_listings", input=parsed) as record:
            results = call_tool(...)
            record["output"] = f"{len(results)} listings"

    Anything put in `record` is written with the line. An exception is logged
    as `error` and then raised again, so the step still fails the way it did.
    """
    record: dict = {}
    started = time.perf_counter()
    try:
        yield record
    except BaseException as exc:  # Ctrl-C too: the step it stopped still gets a line
        # Merged into one dict so a key in `record` named "error" or
        # "duration_ms" replaces ours and cannot raise a TypeError over the
        # exception that is already being logged.
        write(step=name, input=input,
              **{**fixed, **record, "error": _first_line(exc),
                 "duration_ms": _ms(started)})
        raise
    write(step=name, input=input,
          **{**fixed, **record, "duration_ms": _ms(started)})


def _ms(started: float) -> float:
    return round((time.perf_counter() - started) * 1000, 1)


def lines(run_id: str, path=None) -> list[dict]:
    """Every line one run wrote, from every process, in the order written."""
    path = Path(path) if path else log_path()
    if not path.exists():
        return []
    rows = []
    for text in path.read_text(encoding="utf-8").splitlines():
        try:
            row = json.loads(text)
        except ValueError:
            continue
        if row.get("run_id") == run_id:
            rows.append(row)
    return rows


def totals(run_id: str, path=None) -> dict:
    """
    What one run spent, added up from its model_call lines.

    A call counts whether it was answered or pushed back, because a 429 used a
    request. A cache hit is not a call and is not counted.
    """
    calls = prompt = output = 0
    for row in lines(run_id, path):
        if row.get("step") == "model_call":
            calls += 1
            prompt += row.get("prompt_tokens") or 0
            output += row.get("output_tokens") or 0
    return {"model_calls": calls, "prompt_tokens": prompt, "output_tokens": output}
