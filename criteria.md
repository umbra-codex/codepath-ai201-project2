# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**Why this target:**
My search is a plain keyword match, so the same query finds the same item every
try. The two tools after it call the model, and one failed call ends the run
without a fit card, so I allow one miss in five.

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:**
This path never reaches the model. The search is a filter and a keyword count,
so an empty result is empty on every try and the branch has no reason to vary.

---

## 3. The selected item is the item the next two tools receive

Given a query that matches at least one listing, the item the trace shows going
into `suggest_outfit` and `create_fit_card` has the same title as
`session["selected_item"]` — 5 of 5 tries.

**Why this target:**
No model call sits between the search and the handoff, so it either holds on
every try or fails on every try. All 40 listing titles are unique, so a matching
title means the same listing.

> **Revised in unit 4:** Given a query that matches at least one listing, the
> `new_item` that `suggest_outfit` and `create_fit_card` are each called with
> has the same `id` as `session["selected_item"]` in the returned session, and
> that `id` is the first search result's, in 5 of 5 tries. `check_handoff.py`
> records the argument at each call and scores it.
>
> **Why revised:** The original measured the loop's report of the handoff, not
> the handoff. My trace line and the tool call read the same variable, so the
> check trusted `run_agent` to print what it passes. It also never checked that
> the selected item was the first search result. The new version records what
> each tool received, in code the loop does not own, and compares it with the
> session and the search results after the run. I broke the loop three ways to
> test it, and each one failed 5 of 5.

---

## 4. The fit card names the price and the platform once each

Given a query that matches at least one listing, the fit card names the
selected item's price and its platform exactly once each — in at least 4 of 5
tries.

**Why this target:**
The card is raw model text at `TEMPERATURE` 0.9, and `create_fit_card` returns
it unchecked, so the model can drop a fact the prompt gave it or repeat one. One
miss in five is variation; two means my prompt isn't asking clearly enough.


---

## 5. An empty wardrobe gets general advice, not invented pieces

Given a matching query and an empty wardrobe, the agent returns a fit card, and
the outfit suggestion never uses "your" or "you own" for any piece other than
the listed item — in at least 4 of 5 tries.

**Why this target:**
With no wardrobe items in the prompt, the model can still write "your jeans" as
if it had seen a closet. I allow one slip in five. If it happens more often, my
empty-wardrobe prompt is the problem.


---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->


# Capstone acceptance criteria: FitFindr, shape B (harden against failure)

Five criteria for the hardening extension. They were written after the extension was built (the run log in `68b130a`, the fault harness in `d8dfb41`, the boundary in `7c5fc0e`) and before any trial was run or counted. The before run is made at `d8dfb41`, the commit before the boundary, and the after run at `7c5fc0e`.

---

## Capstone 1. A known failure ends with a message, not an exception

Given a failure on one of the three paths the agent already knows can fail, `run_agent` returns a session whose `error` contains the name of the step that failed (`search` or `suggest_outfit`) and one thing the user can do (try again, wait, restart, or run the server on its own), and it raises nothing. 3 of 3 trials.

**The three trials:** one fault each, injected from outside the production code with `faults.py`. Every model request is answered 429 past `MAX_RETRIES` (`model-429`). `mcp_server.py` cannot start, so the search fails (`search-down`). The session's request budget is already spent, so `QuotaGuard` fires (`budget`).

**Why this target:**
At `d8dfb41` all three failures leave `run_agent` as an exception, so the before run should score 0 of 3, each with a different exception type. I use three faults and not one fault three times, because one fault repeated is one result counted three times. Nothing here depends on a live model, so a path either sets `error` or it does not, and 3 of 3 is the only target that fits.

---

## Capstone 2. A caller of the web service gets the session, not a 500

Given the same three faults sent through `serve.py`'s `/ask`, the reply is HTTP 200 with the session as JSON and a non-empty `error`, not a 500 carrying an exception name. 3 of 3 trials.

**The three trials:** `model-429`, `search-down` and `budget`, each one run as `python faults.py --one <id> --serve`.

**Why this target:**
`serve.py` catches whatever escapes `run_agent` and answers 500 with the exception text, and that is what a caller would see. Its own docstring says `/ask` returns the session with `error` in it, so a 200 is the documented behavior. The before run should score 0 of 3, each a 500 with `ExceptionType: text` in the body. Capstone 1 looks at the function. This one looks at the surface a user reaches.

---

## Capstone 3. Every run leaves a record of each step it took, failures included

With the cache off, every run leaves one log line for each step it took, and each line names the step, what went in, what came out or how it failed, and how long it took. 3 of 3 trials, and the line count matches my hand count.

**The three trials:** `vintage graphic tee under $30`, which completes (6 lines: the search, the outfit's model call, the outfit, the fit card's model call, the fit card, the run); `designer ballgown size XXS`, which stops after the search (2 lines); and `model-429` (8 lines: the search, five model calls, the outfit step with an `error`, the run).

**Why this target:**
The search and the fit card run in the MCP server, a second process that exits after each call. A log written only where the loop lives would show the fit card's model call as missing. The failed run is a trial because a record that exists only for runs that finish is no use on the day one does not. The three runs end three different ways, which is why they are the three trials. The log write is unconditional and swallows its own errors, so the only thing that can vary is the run itself, which is why I allow no misses. The counts come from reading the code. I smoke-ran the harness once before writing them, and that run is not a trial. The `run` line already exists at `d8dfb41`, so I expect this to pass before and after.

---

## Capstone 4. The record matches a hand count of what the run spent

The model requests in the record equal my hand count for the same run, retries included, and the tokens in the record equal the tokens I scripted, or the total the program prints for the lines it wrote itself. 3 of 3 trials.

**The three trials:** `AI201_CACHE=0 python app.py ask 'vintage graphic tee under $30'`, which should be 2 requests, with the tokens on the `model_call` lines whose `process` is `app.py` equal to the total the program prints on exit (the server's call is the other line and is not in that total). If the log shows a 429 retry, the hand count adds it and the diagnosis says so. `model-429`, which should be 5 requests and 0 tokens. `fit-card-429`, where the outfit step succeeds on a scripted answer of 120 prompt and 30 output tokens and then the server's five requests are all pushed back, which should be 6 requests and 120 plus 30 tokens.

**Why this target:**
The program's own call counter lives in one process and prints "1 model calls" for a run that made 2, because the fit card's call happens in the server. The log is the only place both are counted. A 429 used a request, so retries count. A cache hit does not, so the cache is off. I expect this to pass before the boundary is built, because the log came first. It is here because every cost number in the write-up comes from this record, and a record I have not checked gives numbers I cannot trust.

---

## Capstone 5. The old paths still work

Given a matching query, the agent runs all three tools and returns a fit card with `error` None. Given a query that matches nothing, it stops before `suggest_outfit` with an `error` that contains `You could`. 3 of 3 trials.

**The three trials:** two matching queries for different items, `vintage graphic tee under $30` (a price ceiling) and `90s track jacket in size M` (a size filter and no price), and the impossible query `designer ballgown size XXS`, which has no price ceiling so that the description is what finds nothing.

**Why this target:**
The boundary in `run_agent` catches three exception types around the loop. One written too wide could swallow the good path or reword a message I already tested. I allow no misses because these paths worked before and the extension was not supposed to touch them. A live model is involved, so a try can fail for a reason unrelated to my change. A miss is `error` None with a wrong or missing card. A failure of the live model is an `error` that names the model, and the diagnosis says so. The before run should score 3 of 3.
