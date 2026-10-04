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
if it had seen a closet. One slip in five is the model; more than that is my
empty-wardrobe prompt.


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
