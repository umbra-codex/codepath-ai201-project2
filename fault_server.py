"""
The MCP server with one fault installed. Used by faults.py, never by the agent.

The fit card's model request happens in the server's process, so a fault in the
agent's process cannot reach it. faults.py starts this file in place of
mcp_server.py and sets FITFINDR_FAULT; this installs the fault in this process
and then runs the real server, so the tools that run are the tools that ship.

    429     every model request is pushed back, past MAX_RETRIES
    exit    the process dies in the middle of the first model request
"""

import os
import sys

import generate
from faults import FakeTime, ScriptedClient

mode = os.environ.get("FITFINDR_FAULT", "")
if mode == "429":
    generate._client = ScriptedClient([], then="429")
    generate.time = FakeTime()
elif mode == "exit":
    generate._client = ScriptedClient(["exit"])
else:
    sys.exit(f"fault_server.py: unknown FITFINDR_FAULT {mode!r}")

from mcp_server import mcp  # noqa: E402 — after the fault, so the tools see it

if __name__ == "__main__":
    mcp.run()
