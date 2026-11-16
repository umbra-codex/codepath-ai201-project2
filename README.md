# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> All three tools are stubs, so that last command will do nothing useful yet.
> That's the starting position.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

<!-- Three or four sentences: what a user asks for, and what they get back. -->

FitFindr takes a request like `vintage graphic tee under $30` and pulls a description, a size, and a price limit out of it. It searches 40 mock listings, picks the best keyword match, and asks a model for an outfit from the user's wardrobe (or general advice if the wardrobe is empty) and a short caption. If nothing matches, it stops before any model call and says what to change.

---

## Tool Inventory

<!-- Four lines per tool. This is worth 2 points and it's the single most
     common place students lose them.

     "Returns a list" earns NOTHING. The description has to say what is IN
     the list.

     The empty case isn't optional either — it's the thing your loop branches
     on, and if you don't decide it here you'll discover it as a crash in
     Milestone 5. -->

### `search_listings`

- **What it does:** Filters listings by price and size, drops any that share no keyword with the description, and ranks the rest by keyword overlap.
- **Inputs:** `description` (str); `size` (str or None), a case-insensitive whole-token match, so `m` matches `S/M` but not `XL`, and a `One Size` listing matches any requested size. Tokens are the parts of a listing's size split on `/`, with text in parentheses removed, so `XL (oversized)` is `XL` and `US 8` needs the full `US 8`. A waist-and-length size is one token too, so `W30 L30` needs the full `W30 L30` and `W30` alone does not match it; `max_price` (float or None), inclusive. `None` skips that filter.
- **Returns:** A list of up to 10 listing dicts, highest score first, ties in data order. Keywords are lowercase words of two or more characters, minus stop words. A listing's keywords come from its `title`, `description`, `category`, `style_tags`, `colors`, and `brand`, and its score is the number it shares with the query. Each has `id`, `title`, `description`, `category`, `size`, `condition`, `platform` (all str), `price` (float), `style_tags` and `colors` (lists of str), and `brand` (str or None).
- **When it has nothing:** An empty list, `[]`.

### `suggest_outfit`

- **What it does:** Asks the model for one or two outfits that pair a listing with the user's wardrobe.
- **Inputs:** `new_item` (dict), one listing; `wardrobe` (dict), whose `items` key is a list of dicts with `id`, `name`, `category`, `colors`, `style_tags`, and optional `notes`. A missing `items` key counts as empty.
- **Returns:** When the wardrobe has items, a non-empty string describing one or two outfits that name wardrobe pieces. Raises `ModelUnavailable` if the model returns no text.
- **When it has nothing:** With an empty wardrobe, a non-empty string of general styling advice that names no wardrobe pieces.

### `create_fit_card`

- **What it does:** Asks the model for a short caption about the item and the outfit.
- **Inputs:** `outfit` (str), the text from `suggest_outfit`; `new_item` (dict), the same listing.
- **Returns:** A string of two to four sentences that mentions the item, its price, and its platform once each. Raises `ModelUnavailable` if the model returns no text.
- **When it has nothing:** If `outfit` is empty or whitespace, the string `"No outfit to write a fit card for."`, with no model call.

---

## Planning Loop

<!-- Your branch rule, stated as a rule — the condition AND both paths — plus
     the file and function that holds it.

     Like this:
       "If search_listings returns an empty list, put a message in the session
        and stop. Otherwise take the first result and go to suggest_outfit."
        — agent.py::run_agent

     The grader checks your code against what you claim here, so the file and
     function have to be real. -->

**Branch rule:** If `search_listings` returns an empty list, put a message in `session["error"]` that says what the user could change, then return the session without calling `suggest_outfit` or `create_fit_card`. Otherwise, put the first result in `session["selected_item"]` and go to `suggest_outfit`.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** Regex, in `agent.py::parse_query`. One set of patterns finds a price limit ("under $30", "$30", "30 or less"), another finds a size after the word "size", and what is left is the description.

**What moves through the session:** `query`, then `parsed`, `search_results`, `selected_item`, `outfit_suggestion`, and `fit_card`, each written by one step and read by the next. `wardrobe` is set at the start, and `error` is set when the search finds nothing or a model call fails. `notice` is set when the wardrobe is empty.

---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query**

```
$ python app.py ask 'vintage graphic tee under $30'

  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

  Outfit:   Outfit one plays with proportions by pairing the baby tee with your baggy straight-leg jeans. Add the black cropped zip hoodie layered over or carried along, and finish with your chunky white sneakers and black crossbody bag for an effortless Y2K streetwear look.

Outfit two leans into a vintage contrast. Tuck the baby tee into your wide-leg khaki trousers, and pull on the vintage black denim jacket. Complete this earthy, retro combination with your black combat boots and the brown leather belt to tie the whole aesthetic together seamlessly.

  Fit card: I scored this adorable Y2K butterfly print baby tee on depop for only $18 and I am completely obsessed with it. I am styling it two ways, first with baggy straight-leg jeans and a cropped black hoodie for the ultimate effortless streetwear vibe. For my second look, I am leaning into a retro contrast by tucking it into wide-leg khaki trousers with a vintage black denim jacket and combat boots.

0 model calls this session, 2 served from cache
```

**The three tools, tested one at a time**

```
$ AI201_CACHE=0 python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"

[{'id': 'lst_002', 'title': 'Y2K Baby Tee — Butterfly Print', 'description': 'Super cute early 2000s baby tee with butterfly graphic. Fitted crop length. Tag says medium but fits like a small.', 'category': 'tops', 'style_tags': ['y2k', 'vintage', 'graphic tee', 'cottagecore'], 'size': 'S/M', 'condition': 'excellent', 'price': 18.0, 'colors': ['white', 'pink', 'purple'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_006', 'title': 'Graphic Tee — 2003 Tour Bootleg Style', 'description': 'Vintage-style bootleg tee with faded graphic. Slightly boxy fit. 100% cotton, soft and worn-in.', 'category': 'tops', 'style_tags': ['graphic tee', 'vintage', 'grunge', 'streetwear', 'band tee'], 'size': 'L', 'condition': 'good', 'price': 24.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_017', 'title': 'Mesh Long-Sleeve Top — Black', 'description': 'Sheer black mesh long-sleeve. Great for layering under a graphic tee or over a bralette. Stretchy material, fits true to size.', 'category': 'tops', 'style_tags': ['y2k', 'grunge', 'goth', 'layering'], 'size': 'S/M', 'condition': 'excellent', 'price': 15.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_033', 'title': 'Vintage Band Tee — Faded Grey', 'description': 'Faded grey band-style tee with distressed graphic. Crew neck. Fits boxy. Well-loved but no holes or major damage.', 'category': 'tops', 'style_tags': ['vintage', 'grunge', 'band tee', 'graphic tee', 'streetwear'], 'size': 'L', 'condition': 'fair', 'price': 19.0, 'colors': ['grey', 'charcoal'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_011', 'title': 'Low-Rise Cargo Pants — Khaki', 'description': 'Y2K era low-rise cargo pants. Lots of pockets. Khaki color, slightly distressed at the hems. Great for layering with a long tee.', 'category': 'bottoms', 'style_tags': ['y2k', 'cargo', '2000s', 'streetwear'], 'size': 'W29', 'condition': 'fair', 'price': 27.0, 'colors': ['khaki', 'tan'], 'brand': None, 'platform': 'poshmark'}, {'id': 'lst_015', 'title': 'Vintage Graphic Hoodie — Faded Black', 'description': 'Faded black pullover hoodie with barely-visible vintage graphic on the chest. Cozy interior. Some pilling but adds to the worn-in look.', 'category': 'tops', 'style_tags': ['vintage', 'grunge', 'graphic', 'streetwear'], 'size': 'L', 'condition': 'fair', 'price': 26.0, 'colors': ['black', 'charcoal'], 'brand': None, 'platform': 'depop'}]
```

```
$ AI201_CACHE=0 python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"

Outfit one: Pair the vintage Levi's 501 jeans with the white ribbed tank top tucked in. Layer the oversized grey crewneck sweatshirt over top, and finish the look with the chunky white sneakers and the black crossbody bag.

Outfit two: Style the jeans with the black cropped zip hoodie and the black combat boots. Cinch the waist using the brown leather belt, and throw on the vintage black denim jacket as your outerwear layer.
```

```
$ AI201_CACHE=0 python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"

I finally scored the vintage Levi's 501 jeans of my dreams on depop for just $38. The medium indigo wash has that perfectly broken-in denim look that makes any outfit instantly cooler. I am styling them with crisp white sneakers for the ultimate effortless streetwear vibe.
```

---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

**Moment 1**

- _What I asked for:_ I asked Claude to build `suggest_outfit` from my Tool Inventory entry and its docstring.
- _What came back:_ When the model sent back empty text, the tool returned the sentence "The model returned no outfit for <title>. Try it again." A second model's review pointed out that `create_fit_card` would caption that sentence as if it were an outfit.
- _What I changed:_ Both model tools now raise `ModelUnavailable` on an empty reply, and the Tool Inventory says so.

**Moment 2**

- _What I asked for:_ I asked Claude to build `create_fit_card` and, as the assignment says, run it three times on one item with the cache off.
- _What came back:_ Three different captions for the $38 Levi's, with the price as "thirty-eight dollars", "thirty eight dollars", and "38 dollars". A search for `$38` finds none of them. An earlier try also read like a seller's post.
- _What I changed:_ The prompt now says to write as the buyer and to put the price in digits. Five more tries each had `$38` once.

**Unit 4**

Claude wrote this unit's code changes, ran both evals, marked each try, and drafted the unit 4 sections of this README from my instructions, one milestone at a time. A second model reviewed every milestone before I committed it. I chose which review findings to fix and made the commits. Claude picked the Milestone 5 improvement, and I let it stand.

**Moment 3**

- _What I asked for:_ I asked Claude to register `search_listings` on the MCP server with a description for an agent that can't see my code.
- _What came back:_ A description that opened "Search 40 secondhand clothing listings" and explained size matching without the One Size rule. Claude also said the MCP results matched the direct call after comparing six queries with `==`. The second model pointed out that `==` treats `18` and `18.0` as equal, and that the description would mislead anyone filtering by size.
- _What I changed:_ The description now says a One Size listing matches any size and gives no count. Claude reran the comparison on ten more inputs with a type check.

**Moment 4**

- _What I asked for:_ I asked Claude to mark the before run and write the verdicts.
- _What came back:_ Criterion 3 marked MET at 5 of 5. The first review said the trace check compared a value with itself, and Claude wrote that it "could not have failed". A later review showed that was false. The old check would have caught the same break Claude used to test the new one.
- _What I changed:_ The revision stayed and the claim came out. `check_handoff.py` records what each tool receives and is tested against three deliberate breaks instead of one.

**Moment 5**

- _What I asked for:_ I asked Claude to diagnose the one failed try and look for a pattern.
- _What came back:_ A pattern built on one failure, then a count, 11 of 15, that hid a 5, 5, 1 split by item. The second model caught both over two reviews, and caught that the diagnosis quoted half of my prompt rule.
- _What I changed:_ The Diagnoses section now quotes the whole rule, gives the split, and says one failed try is too few for a pattern.

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
| --------- | ------ | ----- | ----- | ----- | ----- | ----- | ------- |
| 1. A matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. An impossible query stops before the second tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. The selected item is the item the next two tools receive | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. The fit card names the price and the platform once each | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. An empty wardrobe gets general advice, not invented pieces | 4 of 5 | PASS | PASS | PASS | FAIL | PASS | MET (4/5) |

The full log is `results/run_2026-10-07_2101_before.md`, written by `run_eval.py::main` with the cache off. Each try is one call to `agent.py::run_agent`.

Criterion 5, try 4 is the one FAIL. Its outfit ends with "any pattern or neutral basic in your rotation". "Your" there points at clothes the agent was never shown, so I counted it. It names no single piece, and a looser reading would pass it.

Criterion 3 passed every try, but the check is weak. The trace prints the title from the same object `run_agent` hands to each tool, so it shows what the loop says it passed, and the two only differ if the loop's code changes.

**Real output from one try per criterion**, copied from that log. Every trace is printed by `agent.py::run_agent`, the outfit text comes from `tools.py::suggest_outfit`, and the fit card comes from `tools.py::create_fit_card`.

**Criterion 1, try 1:** `vintage graphic tee under $30`

```
- stopped early: no
- selected_item: Y2K Baby Tee — Butterfly Print ($18.0, depop)
- search_results: 10

Fit card:
I am still obsessed with this butterfly print Y2K baby tee I just scored on depop for only $18. The white, pink, and purple graphic gives me total nostalgic energy, especially when I style it with baggy dark wash jeans and chunky white sneakers for that classic streetwear look. I also love layering it under a vintage black denim jacket with wide-leg khakis and combat boots for an edgy mix of earth tones.

Trace:
[1] search_listings (via MCP)
      in:  {'description': 'vintage graphic tee', 'size': None, 'max_price': 30.0}
      out: 10 items: Y2K Baby Tee — Butterfly Print, Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey … +7 more
      →    branch: selected Y2K Baby Tee — Butterfly Print
[2] suggest_outfit
      in:  new_item=Y2K Baby Tee — Butterfly Print; wardrobe=10 items
      out: Outfit one balances the fitted Y2K baby tee with your baggy straight-leg jeans in dark wash and chunky white s…
[3] create_fit_card
      in:  new_item=Y2K Baby Tee — Butterfly Print; outfit=Outfit one balances the fitted Y2K baby …
      out: I am still obsessed with this butterfly print Y2K baby tee I just scored on depop for only $18. The white, pin…
```

**Criterion 2, try 1:** `designer ballgown size XXS under $5`

```
- stopped early: yes — No listings matched "designer ballgown" in size XXS under $5. You could drop the size or try another one, raise the price limit, or describe the item in different words.
- selected_item: (none)
- search_results: 0

Trace:
[1] search_listings (via MCP)
      in:  {'description': 'designer ballgown', 'size': 'XXS', 'max_price': 5.0}
      out: [] (empty)
      →    branch: empty, stopping before suggest_outfit
```

**Criterion 3, try 1:** `90s track jacket in size M`

```
- stopped early: no
- selected_item: 90s Track Jacket — Navy/White Stripe ($45.0, poshmark)
- search_results: 5

Trace:
[1] search_listings (via MCP)
      in:  {'description': '90s track jacket', 'size': 'M', 'max_price': None}
      out: 5 items: 90s Track Jacket — Navy/White Stripe, 90s Leather Bomber — Black, 90s Silk Slip Dress — Floral, Midi Length … +2 more
      →    branch: selected 90s Track Jacket — Navy/White Stripe
[2] suggest_outfit
      in:  new_item=90s Track Jacket — Navy/White Stripe; wardrobe=10 items
      out: Outfit one pairs the 90s track jacket with the white ribbed tank top, baggy straight-leg jeans, and chunky whi…
[3] create_fit_card
      in:  new_item=90s Track Jacket — Navy/White Stripe; outfit=Outfit one pairs the 90s track jacket wi…
      out: Scored this vintage Champion 90s track jacket on Poshmark for just $45 and I am obsessed. I love throwing it o…
```

**Criterion 4, try 1:** `silk slip dress in midi length under $40`

```
- stopped early: no
- selected_item: 90s Silk Slip Dress — Floral, Midi Length ($30.0, depop)
- search_results: 5

Fit card:
I just scored this dreamy nineties floral silk slip dress on depop for only $30. I am styling it under an oversized grey crewneck and baggy jeans for the ultimate vintage streetwear moment. It also looks so edgy layered with a black denim jacket and combat boots.
```

**Criterion 5, try 4:** `denim jacket under $50`, empty wardrobe

```
- stopped early: no
- selected_item: Denim Jacket — Light Wash, Cropped ($42.0, poshmark)
- search_results: 7

Outfit suggestion:
Grab this Wrangler jacket for instant vintage cool. Since it features a cropped, light-wash cut, it serves as a versatile streetwear staple. Try pairing it with an oversized graphic tee, a pleated miniskirt, and chunky platform boots for an edgy, balanced silhouette. Alternatively, style it over a ribbed black slip dress paired with retro sneakers and a canvas tote bag for an effortless, casual weekend look. The light blue shade makes it easy to mix and match with almost any pattern or neutral basic in your rotation.

Fit card:
I just scored this amazing vintage cropped Wrangler denim jacket on poshmark for only $42 and I am obsessed. I am styling it with an oversized graphic tee, a pleated miniskirt, and chunky platform boots for the ultimate streetwear vibe. It is already my favorite new piece to throw on for an effortless look.
```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| #   | Criterion | Target | Verdict | How I decided |
| --- | --------- | ------ | ------- | ------------- |
| 1   | A matching query completes all three tools | 4 of 5 | MET (5/5) | Each try's trace has all three steps and the session has a fit card. |
| 2   | An impossible query stops before the second tool | 5 of 5 | MET (5/5) | Each trace has only the search step, there is no outfit or fit card, and the message says to drop the size, raise the price limit, or reword. |
| 3   | The selected item is the item the next two tools receive | 5 of 5 | MET (5/5), revised | Both `new_item` titles in each trace equal the selected item's title. That check trusts the loop's own trace, so I revised the criterion. The revised version also passes 5 of 5. |
| 4   | The fit card names the price and the platform once each | 4 of 5 | MET (5/5) | I counted `$30` and `depop` in each of the five cards. Each appears once. |
| 5   | An empty wardrobe gets general advice, not invented pieces | 4 of 5 | MET (4/5) | All five tries returned a fit card. I read each outfit for "your" and "you own". Try 4 has "in your rotation". |

**Diagnoses**

I missed nothing. All five criteria met their unit 3 targets, and one try out of 25 failed.

**The one failed try (criterion 5, try 4):** the place is the model's output from `tools.py::suggest_outfit`. My empty-wardrobe prompt says: `Do not describe any other piece as theirs: introduce each one with "a" or "an", never "your".` For named pieces the rule held. None is called "your" in any of the five tries. The slip is in the last sentence of try 4: "easy to mix and match with almost any pattern or neutral basic in your rotation". The rule covers that sentence, because it describes other pieces as the reader's. But the rule's only concrete instruction is about introducing a piece with "a" or "an", and this sentence introduces none, so the model had the ban with nothing it could apply. The tool and the loop worked.

**The pattern:** one failed try is too few to call a pattern in the failures. What the log does show is how often the model reaches for "your" when it is allowed. In the example-wardrobe outfits that is 5 of 5 for the tee, 5 of 5 for the slip dress, and 1 of 5 for the track jacket. The habit is strong for some items and weak for others, and the empty-wardrobe prompt's 1 of 5 is no better than the track jacket's rate with no ban at all. Five tries can't tell me how much the ban is doing.

**On my targets:** criterion 3 was weaker than its 5 of 5 target looks. The trace is `run_agent`'s own report. The trace line and the tool call read the same variable, so the check trusts the loop to print what it passes. I revised it in `criteria.md` and scored the new version below. Criterion 2 passed 5 of 5 against a 5 of 5 target and has no model call in its path, so that target was right. Criterion 5 used the one miss its 4 of 5 target allows, on a call a looser reader would pass, so I would leave that target where it is. Criteria 1 and 4 allowed one miss in five and used none. The criterion I'd tighten is 4. All 20 fit cards in this run, from four different items, name the price once and the platform once, so I would hold it to 5 of 5. That has a cost: a failed model call would then miss criteria 1 and 4 together.

**Criterion 3, revised and scored:** `check_handoff.py::main` replaces the two model tools with stand-ins that record the `new_item` they are called with, runs `agent.py::run_agent`, and compares each recorded `id` with `session["selected_item"]` and with the first search result. It makes no model calls. Since the stretch move, the `create_fit_card` stand-in sits in front of `call_tool`.

```
$ python check_handoff.py
query: 90s track jacket in size M
  try 1: first result lst_004, session has lst_004, suggest_outfit got lst_004, create_fit_card got lst_004  PASS
  try 2: first result lst_004, session has lst_004, suggest_outfit got lst_004, create_fit_card got lst_004  PASS
  try 3: first result lst_004, session has lst_004, suggest_outfit got lst_004, create_fit_card got lst_004  PASS
  try 4: first result lst_004, session has lst_004, suggest_outfit got lst_004, create_fit_card got lst_004  PASS
  try 5: first result lst_004, session has lst_004, suggest_outfit got lst_004, create_fit_card got lst_004  PASS
5 of 5 passed
```

To see whether the check can fail, I broke `run_agent` three ways, one line at a time. I ran the check after each break and put the line back. All three failed 5 of 5. This is the first try and the total from each run:

```
suggest_outfit gets the second search result
  try 1: first result lst_004, session has lst_004, suggest_outfit got lst_022, create_fit_card got lst_004  FAIL
0 of 5 passed

create_fit_card gets the second search result
  try 1: first result lst_004, session has lst_004, suggest_outfit got lst_004, create_fit_card got lst_022  FAIL
0 of 5 passed

the session selects the second search result
  try 1: first result lst_004, session has lst_022, suggest_outfit got lst_022, create_fit_card got lst_022  FAIL
0 of 5 passed
```

The check has limits. It only looks at `new_item`, so a wrong wardrobe or outfit argument would get past it, and so would a tool that ignored the item it was given.

---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```
$ AI201_CACHE=0 python app.py ask 'vintage graphic tee under $30' --trace
[1] search_listings (via MCP)
      in:  {'description': 'vintage graphic tee', 'size': None, 'max_price': 30.0}
      out: 10 items: Y2K Baby Tee — Butterfly Print, Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey … +7 more
      →    branch: selected Y2K Baby Tee — Butterfly Print
[2] suggest_outfit
      in:  new_item=Y2K Baby Tee — Butterfly Print; wardrobe=10 items
      out: Outfit one pairs the Y2K baby tee with baggy straight-leg jeans, the vintage black denim jacket, and chunky wh…
[3] create_fit_card
      in:  new_item=Y2K Baby Tee — Butterfly Print; outfit=Outfit one pairs the Y2K baby tee with b…
      out: I just scored this adorable Y2K butterfly baby tee on depop for only $18 and I am totally obsessed. I love sty…

  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

  Outfit:   Outfit one pairs the Y2K baby tee with baggy straight-leg jeans, the vintage black denim jacket, and chunky white sneakers. This creates a classic early 2000s streetwear look that balances the fitted butterfly top with relaxed denim. 

Outfit two pairs the Y2K baby tee with wide-leg khaki trousers, the brown leather belt, and chunky white sneakers. Tucking the baby tee into the khakis highlights the waist while blending the sweet pink and purple butterfly print with earthy, minimal tones.

  Fit card: I just scored this adorable Y2K butterfly baby tee on depop for only $18 and I am totally obsessed. I love styling it with baggy straight leg jeans and a black denim jacket for the ultimate early 2000s streetwear vibe. It also looks so cute tucked into wide leg khaki trousers with a leather belt for a sweet yet earthy everyday look.

2 model calls this session, 666 prompt + 180 output tokens
```

**Empty search**

```
$ python app.py ask 'designer ballgown size XXS under $5' --trace
[1] search_listings (via MCP)
      in:  {'description': 'designer ballgown', 'size': 'XXS', 'max_price': 5.0}
      out: [] (empty)
      →    branch: empty, stopping before suggest_outfit

  No listings matched "designer ballgown" in size XXS under $5. You could drop the size or try another one, raise the price limit, or describe the item in different words.

0 model calls this session
```

**On the MCP move:** `search_listings` is registered in `mcp_server.py` under the same name, with the three typed inputs from my Tool Inventory. In `agent.py::run_agent`, the direct call `search_listings(description, size, max_price)` became `call_tool("search_listings", {...})` from `mcp_client.py`, and `agent.py` no longer imports the function. `suggest_outfit` and `create_fit_card` stayed direct calls in this milestone. `create_fit_card` moved later, under Stretch Features. I compared the direct call and the MCP call on the six example queries and ten edge cases, among them no filters, size only, the price ceiling, a One Size listing, and an empty description. Values and types matched every time, including the empty list for the ballgown query, so nothing in the loop's branch had to change. The one difference is speed: each MCP call starts the server as a second Python process and takes between half a second and a second, where the direct call was instant. The move also added a way to fail that the direct call didn't have. If the server can't start, `call_tool` raises `MCPError`, and `run_agent` does not catch it at the search step.

### Failure modes

I triggered each failure before changing any code and wrote down what the agent said. Two of the three needed a change.

**Empty search:** `designer ballgown size XXS under $5` matches nothing. The agent stopped after the search and said what to change, so I left it alone. The output is the empty-search trace above.

**Empty wardrobe:** `--empty-wardrobe` hands `suggest_outfit` a wardrobe with no items. It returned general advice and the run finished with a fit card, but nothing told the user the wardrobe was empty, so the advice read like a normal answer. `run_agent` now puts a note in `session["notice"]`, and `app.py` prints it under the fit card:

```
$ python app.py ask 'denim jacket under $50' --empty-wardrobe --trace
(running with an empty wardrobe)
[1] search_listings (via MCP)
      in:  {'description': 'denim jacket', 'size': None, 'max_price': 50.0}
      out: 7 items: Denim Jacket — Light Wash, Cropped, Vintage Levi's 501 Jeans — Medium Wash, 90s Track Jacket — Navy/White Stripe … +4 more
      →    branch: selected Denim Jacket — Light Wash, Cropped
[2] suggest_outfit
      in:  new_item=Denim Jacket — Light Wash, Cropped; wardrobe=0 items
      out: Grab a light wash cropped Wrangler denim jacket for instant vintage streetwear cred. Wear it over a black grap…
      →    empty wardrobe: general advice, notice set
[3] create_fit_card
      in:  new_item=Denim Jacket — Light Wash, Cropped; outfit=Grab a light wash cropped Wrangler denim…
      out: I am so obsessed with this vintage cropped Wrangler denim jacket I just scored on poshmark for only $42. I am …

  Found:    Denim Jacket — Light Wash, Cropped — $42.0 on poshmark

  Outfit:   Grab a light wash cropped Wrangler denim jacket for instant vintage streetwear cred. Wear it over a black graphic tee paired with a pleated plaid mini skirt and chunky platform loafers for a cool grunge contrast. Alternatively, throw it on over a ribbed white crop top matched with high-waisted wide-leg cargo pants and retro canvas sneakers for an effortless casual vibe. Toss a colorful nylon crossbody bag over the shoulder to tie the whole look together.

  Fit card: I am so obsessed with this vintage cropped Wrangler denim jacket I just scored on poshmark for only $42. I am styling it for a grunge look over a black graphic tee with a plaid mini skirt and chunky platform loafers. It adds the ultimate streetwear vibe to every outfit I throw together.

  Note:     Your wardrobe is empty, so the outfit is general styling advice and not built from pieces you own. Add a few wardrobe items and ask again to get outfits that use them.

0 model calls this session, 2 served from cache
```

**Model unavailable:** I ran `platform sneakers size 8`, which I had not asked before, with the last character of my key changed. I set the changed key for that one command and left `.env` alone. Before the fix, `run_agent` raised `ModelUnavailable` and `app.py` printed it:

```
$ python app.py ask 'platform sneakers size 8'

ModelUnavailable: The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.google.com.

1 model calls this session
```

That is one readable line, but the exception left `run_agent` with nothing in `session["error"]`, so `run_eval.py` would log the try as a crash and `serve.py` would answer with a 500. `run_agent` now catches `ModelUnavailable` around both model tools, puts a message in `session["error"]` that names the step that failed, and stops. Since the stretch move, the fit card step catches `MCPError` instead. This is the run from this milestone:

```
$ python app.py ask 'platform sneakers size 8' --trace
[1] search_listings (via MCP)
      in:  {'description': 'platform sneakers', 'size': 'US 8', 'max_price': None}
      out: 1 items: Platform Sneakers — White Chunky Sole
      →    branch: selected Platform Sneakers — White Chunky Sole
[2] suggest_outfit
      in:  new_item=Platform Sneakers — White Chunky Sole; wardrobe=10 items
      →    ModelUnavailable, stopping: The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.google.com.

  The search worked, but suggest_outfit could not get an answer from the model, so there is no fit card. The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.google.com.

1 model calls this session
```

---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:** one prompt. In `tools.py::suggest_outfit`, I rewrote the rule at the end of the empty-wardrobe prompt. The scenarios, the loop, and the temperature are the same as in the before run.

```
before: Do not describe any other piece as theirs: introduce each one with "a" or "an", never "your".

after:  Do not describe any other piece, or their closet in general, as theirs. Introduce each piece with "a" or "an", and do not write "your" or "you own" anywhere in the answer, including the last sentence.
```

**Which failure it was meant to fix:** criterion 5, try 4 of the before run, where the outfit closed with "in your rotation". My diagnosis was that the ban's only concrete instruction was about introducing a piece, so a closing sentence about the closet had nothing to apply. The new wording names the closet, bans the two phrases anywhere in the answer, and names the last sentence. That try was a borderline call, as I said under the Run Log, so this fix may be chasing one ambiguous sentence.

### Run Log — After

**Before**, repeated from the Run Log section so the two sit together:

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
| --------- | ------ | ----- | ----- | ----- | ----- | ----- | ------- |
| 1. A matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. An impossible query stops before the second tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. The selected item is the item the next two tools receive | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. The fit card names the price and the platform once each | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. An empty wardrobe gets general advice, not invented pieces | 4 of 5 | PASS | PASS | PASS | FAIL | PASS | MET (4/5) |

**After:**

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
| --------- | ------ | ----- | ----- | ----- | ----- | ----- | ------- |
| 1. A matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. An impossible query stops before the second tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. The selected item is the item the next two tools receive | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. The fit card names the price and the platform once each | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. An empty wardrobe gets general advice, not invented pieces | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

The full log is `results/run_2026-10-08_0743_after.md`, written by `run_eval.py::main` with the cache off. I marked each try the same way as in the before run. Row 3 is the original trace check. The revised criterion 3 also passed 5 of 5 after the change, from `python check_handoff.py`.

**The verdicts in one table:**

| Criterion | Target | Before | After |
| --------- | ------ | ------ | ----- |
| 1. A matching query completes all three tools | 4 of 5 | MET (5/5) | MET (5/5) |
| 2. An impossible query stops before the second tool | 5 of 5 | MET (5/5) | MET (5/5) |
| 3. The selected item is the item the next two tools receive | 5 of 5 | MET (5/5) | MET (5/5) |
| 4. The fit card names the price and the platform once each | 4 of 5 | MET (5/5) | MET (5/5) |
| 5. An empty wardrobe gets general advice, not invented pieces | 4 of 5 | MET (4/5) | MET (5/5) |

**Real output from the after run**, criterion 5, try 4, from `tools.py::suggest_outfit` and `tools.py::create_fit_card`. I show try 4 because the before run's try 4 is the one pasted above. The tries are independent.

```
- stopped early: no
- selected_item: Denim Jacket — Light Wash, Cropped ($42.0, poshmark)
- search_results: 7

Outfit suggestion:
This vintage Wrangler denim jacket is a versatile staple. For a classic casual look, layer it over a basic white tee paired with high-waisted black trousers and chunky loafers. Alternatively, create a streetwear-inspired outfit by wearing a graphic hoodie underneath, combined with a pleated tennis skirt and retro canvas sneakers. Both combinations balance the cropped silhouette effortlessly.

Fit card:
I just scored this vintage Wrangler cropped denim jacket on poshmark for only $42 and I am completely obsessed with it. I am styling it over a graphic hoodie with a pleated tennis skirt and retro canvas sneakers for the ultimate streetwear look. It is definitely going to be my new favorite layering piece.
```

**Did it help, and how do I know:** criterion 5 went from 4 of 5 to 5 of 5, and none of the five empty-wardrobe outfits in the after run contains "your" at all. Each one ends on the jacket or the outfit, where one of the before outfits turned to the reader's closet. The result moved the way the diagnosis said it would.

I can't call that proof. The before run was already 4 of 5, and five tries can't separate a prompt that slips one time in five from one that never does. A prompt that slips one time in five would still go 5 of 5 about a third of the time. To know, I would need many more tries of this one scenario.

The new rule is also wider than my criterion. Criterion 5 allows "your" for the listed item, and it has no problem with a phrase like "over your shoulders". The prompt now bans both. None of the ten empty-wardrobe outfits across the two runs uses "your" that way, so my test can't show what the wider ban costs.

The other four criteria were 5 of 5 before and after, so the change broke nothing I measure. The example-wardrobe outfits still use "your" in 11 of 15, the same count as before, which is what I expected because that prompt did not change.

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->

---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->

No criterion is missed after the fix. All five met their targets before it and after it. These are the things I know are still wrong or unproven.

- **The criterion 5 fix is unproven:** it went from 4 of 5 to 5 of 5, and five tries can't tell a prompt that slips one time in five from one that never does. I'd run the empty-wardrobe scenario 30 times with each prompt. I stopped at five because my criteria are written out of five, and each try is two model calls against a limit of 15 a minute.
- **The new prompt bans more than the criterion does:** it forbids "your" for the listed item and in phrases like "over your shoulders". I'd add a scenario that needs one of those and read what the model writes without it. I stopped because the assignment is one change, and loosening the wording would be a second.
- **Three failures still leave `run_agent` as exceptions:** a rate limit that outlasts five retries (`RuntimeError`), the session budget (`QuotaGuard`), and an MCP server that won't start at the search step (`MCPError`). None of them sets `session["error"]`, so `serve.py` answers with a 500 and `run_eval.py` logs a crash. I'd catch each one in `run_agent` with its own message. I stopped at the three failures Milestone 2 names.
- **Criterion 4's target is too easy:** 40 of 40 fit cards across both runs name the price once and the platform once. I'd hold it to 5 of 5. I left the target alone because it was set in unit 3, and the only criterion I revised is one that couldn't be measured.
- **`check_handoff.py` only looks at `new_item`:** a wrong wardrobe or outfit argument would pass it. I'd record every argument. I stopped because criterion 3 is about the item.
- **The trace prints on every run, with or without `--trace`:** `trace.step()` in the starter's `trace.py` always prints. I'd make it print only when `--trace` asks for it. I left the starter file as it came.

<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

## Stretch Features

I'm adding one of the two stretch features: a second tool on MCP. `create_fit_card` moves onto the server next to `search_listings`, and `suggest_outfit` stays a direct call. I'm not doing the retry with looser constraints.

**What changed:** `create_fit_card` is registered in `mcp_server.py` with `outfit` (str) and `new_item` (dict), the same inputs as in my Tool Inventory. In `agent.py::run_agent`, the direct call became `call_tool("create_fit_card", {...})`, and its trace step is labeled `create_fit_card (via MCP)`. The traces pasted earlier in this README are from before the move, so they show the old label. The server now offers two tools:

```
$ python mcp_client.py
Asking mcp_server.py what it offers…

  search_listings
    
Search secondhand clothing listings by keyword. Optional size is a
case-insensitive whole-token match ("M" matches "S/M" but not "XL", and a
One Size listing matches any size); optional max_price is in US dollars,
inclusive. Returns up to 10 listing dicts, best keyword match first, or an
empty list when nothing matches.

    - description: string
    - size: string  (optional)
    - max_price: number  (optional)

  create_fit_card
    
Write a two-to-four sentence first-person caption for a thrift find, as
plain text. outfit is the outfit suggestion to write about. new_item is one
listing dict as returned by search_listings: it needs title, category,
colors, style_tags, size, price (a number, in US dollars) and platform, and
brand may be null. If outfit is empty or only whitespace, returns the string
"No outfit to write a fit card for." without calling a model. Otherwise it
calls a language model, so the text can differ between calls with the same
inputs, and the call returns an error if the model can't be reached.

    - outfit: string
    - new_item: object
```

One full run after the move, with the cache off:

```
$ AI201_CACHE=0 python app.py ask 'vintage graphic tee under $30' --trace
[1] search_listings (via MCP)
      in:  {'description': 'vintage graphic tee', 'size': None, 'max_price': 30.0}
      out: 10 items: Y2K Baby Tee — Butterfly Print, Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey … +7 more
      →    branch: selected Y2K Baby Tee — Butterfly Print
[2] suggest_outfit
      in:  new_item=Y2K Baby Tee — Butterfly Print; wardrobe=10 items
      out: Outfit one pairs the butterfly baby tee with your baggy straight-leg jeans and chunky white sneakers. The fitt…
[3] create_fit_card (via MCP)
      in:  new_item=Y2K Baby Tee — Butterfly Print; outfit=Outfit one pairs the butterfly baby tee …
      out: I scored this adorable Y2K butterfly baby tee on depop for just $18 and I am obsessed. I love styling it with …

  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

  Outfit:   Outfit one pairs the butterfly baby tee with your baggy straight-leg jeans and chunky white sneakers. The fitted top balances the relaxed bottoms, and adding the black cropped zip hoodie on top keeps that authentic Y2K streetwear vibe. 

Outfit two gives the tee a softer touch by tucking it into your wide-leg khaki trousers. Layer the vintage black denim jacket over your shoulders and finish the look with your black combat boots for a cool mix of cottagecore sweetness and edge.

  Fit card: I scored this adorable Y2K butterfly baby tee on depop for just $18 and I am obsessed. I love styling it with baggy straight leg jeans and a black cropped zip hoodie for the ultimate streetwear look. It also looks so cute tucked into wide-leg khakis with chunky boots for that perfect mix of sweet and edgy.

1 model calls this session, 386 prompt + 96 output tokens
```

**What behaved differently:** more than in the first move, because this tool calls a model and the server is a separate process.

- **A model failure arrives as a different error:** the model call now happens on the server, so a bad key at this step comes back as `MCPError` where it used to be `ModelUnavailable`. `run_agent` catches `MCPError` around this call and puts a message in `session["error"]`. A bad key normally fails at `suggest_outfit` first, so I tested this step with a stand-in outfit:

```
[1] search_listings (via MCP)
      in:  {'description': 'vintage graphic tee', 'size': None, 'max_price': 30.0}
      out: 10 items: Y2K Baby Tee — Butterfly Print, Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey … +7 more
      →    branch: selected Y2K Baby Tee — Butterfly Print
[2] suggest_outfit
      in:  new_item=Y2K Baby Tee — Butterfly Print; wardrobe=10 items
      out: Wear it with jeans and white sneakers.
[3] create_fit_card (via MCP)
      in:  new_item=Y2K Baby Tee — Butterfly Print; outfit=Wear it with jeans and white sneakers.…
      →    MCPError, stopping: The tool 'create_fit_card' returned an error: Error executing tool create_fit_card: The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.google.com.

  The search and the outfit worked, but create_fit_card failed on the MCP server, so there is no fit card. The tool 'create_fit_card' returned an error: Error executing tool create_fit_card: The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.google.com.
```

- **The server did not inherit my settings:** the MCP client starts the server with six environment variables (`HOME`, `LOGNAME`, `PATH`, `SHELL`, `TERM`, `USER`). `AI201_CACHE` is not one of them, so an eval with the cache off would still have cached fit cards on the server. `mcp_client.py::_call` now passes the key, the model name, and the cache setting to the server, and nothing else. The capstone added two more names to that list, the run id and the log path. With the cache off, two identical calls gave two different cards and wrote no cache file. With it on, they gave the same card.
- **The error text was lost:** an `MCPError` raised inside the client came out as "unhandled errors in a TaskGroup (1 sub-exception)", with the cause hidden. `mcp_client.py::call_tool` now unwraps it, which is why the message above names the key.
- **The call counter is short by one:** the run above made two model calls and printed "1 model calls this session". The fit card's call is counted in the server's process.
- **Pacing and the session budget do not cover this tool:** `generate.py` keeps its per-minute count and its 300-call budget in process memory, and every MCP call starts a new process with both at zero. Fit card calls are never paced and never counted, so the agent as a whole can send more than 15 requests a minute. I have not run a full eval since the move, so I don't know whether that trips the limit.

Both `mcp_client.py` changes are in a file the starter says is given. I changed it because the two problems were in the client and could not be fixed from `agent.py`.

`check_handoff.py` now sits in front of `call_tool` for this tool. It still passes 5 of 5, and it still fails 0 of 5 when `create_fit_card` is given the second search result.

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**

---

## Capstone

**The Shape**

I picked shape B, harden against failure, and I'm extending FitFindr, my Project 2 agent. The agent has three known failures it does not handle: the search step can raise an error from the MCP server, the session budget guard can fire, and the model can answer 429 until the five retries run out. Each one leaves `run_agent` as an exception, and `serve.py` turns it into a 500 with the exception text in it. I'm adding one failure boundary inside `run_agent` that catches those three and returns a session whose `error` says which step failed and what the user can do about it, keeping anything that already succeeded. I'm also adding a per-step log written to a file, with step names, inputs, outputs and durations, so every run leaves a record, and that record is what I'll measure the before and after with. I estimate the boundary and the fault harness at about an hour, which is inside the ninety minutes.

Out of scope. I thought about three things and I'm not doing them:

- Replacing the per-call MCP subprocess with one long-lived connection. It is why the fit card's model call is missing from the call count, but fixing it means reworking how `mcp_client.py` talks to the server, and the starter says that file is given.
- Changing the retry or rate-limit policy, or adding a fallback model. The boundary reports a failure and does not try harder to avoid one.
- Touching search, the prompts, the fit card wording or the web page.

**The Run Path**

Local, with logs. `RUNNING.md` has it at the top: what the environment needs, the setup from a clean checkout, and one command, `AI201_CACHE=0 python app.py ask 'vintage graphic tee under $30'`. The run writes its record to `logs/fitfindr.jsonl`.

I tested it by cloning the repo from GitHub into a new folder and following `RUNNING.md` line by line: a new virtual environment with `python3.13`, `pip install -r requirements.txt`, `.env` from `.env.example`, then `python test.py` (10 passed) and the command above (a fit card, and a six-line log written by two processes). It did not fail, and the reason is that I had already found two gaps by reading the files, before the clone. `.env.example`, which `RUNNING.md` and `test.py` both tell a reader to copy, was not in the repo. And the default `python3` on my machine is 3.14, which `requirements.txt` rules out. I added the file (`a8223e8`) and wrote the 3.14 warning into `RUNNING.md` before cloning, so the clone passed. A reader who cloned before those two commits would have hit the first, and the second too if their `python3` is 3.14. I did not try the 3.14 failure myself, so "rules out 3.14" is what `requirements.txt` says and not something I observed.

**Instrumentation**

Every run writes JSON lines to `logs/fitfindr.jsonl`, or to the file `AI201_LOG_PATH` names. There is one line for each step (`search_listings`, `suggest_outfit`, `create_fit_card`), one for each model request, and one `run` line that closes the run. Each line has a timestamp, the run id, the process that wrote it, the input, the output or the error, and the duration in milliseconds. A model request line also has the attempt number and the tokens the service reported. The search and the fit card run in the MCP server, a second process, so it writes to the same file under the same run id. That is how the fit card's model call gets counted, and the program's own counter does not: it prints "1 model calls" for a run that made two. The field table is in `RUNNING.md` and the logger is `runlog.py`.

Twelve entries from two ordinary runs, copied from `results/cost_2026-11-15_2011.jsonl`. The first six are `vintage graphic tee under $30` and the next six are `90s track jacket in size M`. Each run has the same six lines in the same order: the search, the outfit's model call, the outfit step, the fit card's model call (written by `mcp_server.py`), the fit card step, and the run. The agent's own lines say `measure_cost.py` because that script started the runs.

```json
{"ts": "2026-11-16T01:11:57.317+00:00", "run_id": "5d0cdcbb", "process": "measure_cost.py", "pid": 2647999, "step": "search_listings", "input": "{'description': 'vintage graphic tee', 'size': None, 'max_price': 30.0}", "output": "10 listings", "duration_ms": 630.0}
{"ts": "2026-11-16T01:11:58.885+00:00", "run_id": "5d0cdcbb", "process": "measure_cost.py", "pid": 2647999, "step": "model_call", "input": "Someone is thinking about buying this thrifted item: Y2K Baby Tee — Butterfly Print; category: tops; colors: white, pink, purple; style: y2k, vintage, graphic tee, cottagecore; size: S/M  Their wardro…", "attempt": 1, "prompt_tokens": 386, "output_tokens": 111, "output": "547 chars", "duration_ms": 1216.0}
{"ts": "2026-11-16T01:11:58.885+00:00", "run_id": "5d0cdcbb", "process": "measure_cost.py", "pid": 2647999, "step": "suggest_outfit", "input": "new_item=Y2K Baby Tee — Butterfly Print; wardrobe=10 items", "output": "Outfit one plays up the Y2K streetwear vibe by pairing the butterfly baby tee with your baggy straight-leg jeans. Add the black cropped zip hoodie layered over top if it gets chilly, and finish the lo…", "duration_ms": 1568.2}
{"ts": "2026-11-16T01:12:00.574+00:00", "run_id": "5d0cdcbb", "process": "mcp_server.py", "pid": 2648009, "step": "model_call", "input": "Write a caption for a post about this thrift find.  The item: Y2K Baby Tee — Butterfly Print; category: tops; colors: white, pink, purple; style: y2k, vintage, graphic tee, cottagecore; size: S/M Pric…", "attempt": 1, "prompt_tokens": 286, "output_tokens": 67, "output": "310 chars", "duration_ms": 982.9}
{"ts": "2026-11-16T01:12:00.848+00:00", "run_id": "5d0cdcbb", "process": "measure_cost.py", "pid": 2647999, "step": "create_fit_card", "input": "new_item=Y2K Baby Tee — Butterfly Print; outfit=Outfit one plays up the Y2K streetwear v…", "output": "I just scored this amazing Y2K butterfly baby tee on depop for only $18 and I am completely obsessed. I love styling it with baggy straight-leg jeans and chunky white sneakers for a total throwback st…", "duration_ms": 1962.2}
{"ts": "2026-11-16T01:12:00.848+00:00", "run_id": "5d0cdcbb", "process": "measure_cost.py", "pid": 2647999, "step": "run", "input": "vintage graphic tee under $30", "output": "completed", "duration_ms": 4161.1}
{"ts": "2026-11-16T01:12:09.293+00:00", "run_id": "1a136770", "process": "measure_cost.py", "pid": 2647999, "step": "search_listings", "input": "{'description': '90s track jacket', 'size': 'M', 'max_price': None}", "output": "5 listings", "duration_ms": 443.9}
{"ts": "2026-11-16T01:12:10.282+00:00", "run_id": "1a136770", "process": "measure_cost.py", "pid": 2647999, "step": "model_call", "input": "Someone is thinking about buying this thrifted item: 90s Track Jacket — Navy/White Stripe; category: outerwear; colors: navy, white; style: 90s, vintage, athletic, streetwear; size: M; brand: Champion…", "attempt": 1, "prompt_tokens": 387, "output_tokens": 126, "output": "660 chars", "duration_ms": 988.7}
{"ts": "2026-11-16T01:12:10.282+00:00", "run_id": "1a136770", "process": "measure_cost.py", "pid": 2647999, "step": "suggest_outfit", "input": "new_item=90s Track Jacket — Navy/White Stripe; wardrobe=10 items", "output": "Grab this Champion track jacket immediately. It is an absolute wardrobe MVP.   Outfit one leans hard into retro streetwear. Pair the track jacket with the white ribbed tank top layered underneath and …", "duration_ms": 989.1}
{"ts": "2026-11-16T01:12:11.663+00:00", "run_id": "1a136770", "process": "mcp_server.py", "pid": 2648121, "step": "model_call", "input": "Write a caption for a post about this thrift find.  The item: 90s Track Jacket — Navy/White Stripe; category: outerwear; colors: navy, white; style: 90s, vintage, athletic, streetwear; size: M; brand:…", "attempt": 1, "prompt_tokens": 304, "output_tokens": 69, "output": "348 chars", "duration_ms": 719.4}
{"ts": "2026-11-16T01:12:11.944+00:00", "run_id": "1a136770", "process": "measure_cost.py", "pid": 2647999, "step": "create_fit_card", "input": "new_item=90s Track Jacket — Navy/White Stripe; outfit=Grab this Champion track jacket immediat…", "output": "Scored this vintage 90s Champion track jacket on poshmark for only $45 and I am completely obsessed. It has the ultimate retro athletic vibe that instantly elevates every casual streetwear look I thro…", "duration_ms": 1661.3}
{"ts": "2026-11-16T01:12:11.944+00:00", "run_id": "1a136770", "process": "measure_cost.py", "pid": 2647999, "step": "run", "input": "90s track jacket in size M", "output": "completed", "duration_ms": 3095.0}
```

Failed runs, two of them, because they fail in two different ways.

A query that matches nothing, `designer ballgown size XXS under $5` (run 11 of the cost measurement). No step raised, so there is no `error` field. The search found 0 listings, and the `run` line's `output` starts with `error:` and carries the message the user sees:

```json
{"ts": "2026-11-16T01:13:51.594+00:00", "run_id": "b24fef1d", "process": "measure_cost.py", "pid": 2647999, "step": "search_listings", "input": "{'description': 'designer ballgown', 'size': 'XXS', 'max_price': 5.0}", "output": "0 listings", "duration_ms": 507.1}
{"ts": "2026-11-16T01:13:51.594+00:00", "run_id": "b24fef1d", "process": "measure_cost.py", "pid": 2647999, "step": "run", "input": "designer ballgown size XXS under $5", "output": "error: No listings matched \"designer ballgown\" in size XXS under $5. You could drop the size or try another one, raise the price limit, or describe the item in different words.", "duration_ms": 507.3}
```

A step that raised. The MCP server could not start, so the search failed (`python faults.py --one search-down`, which points the client at a server file that does not exist). The search step carries an `error` field, and the `run` line closes with the boundary's message. The step line is written before the exception moves on, so the record exists whether or not anything catches it:

```json
{"ts": "2026-11-16T01:35:15.216+00:00", "run_id": "59dc8161", "process": "faults.py", "pid": 2663219, "step": "search_listings", "input": "{'description': 'vintage graphic tee', 'size': None, 'max_price': 30.0}", "error": "MCPError: Couldn't call 'search_listings' over MCP: unhandled errors in a TaskGroup (1 sub-exception)", "duration_ms": 344.4}
{"ts": "2026-11-16T01:35:15.216+00:00", "run_id": "59dc8161", "process": "faults.py", "pid": 2663219, "step": "run", "input": "vintage graphic tee under $30", "output": "error: The search could not be completed over MCP, so nothing else was tried. Run `python mcp_server.py` on its own to see why the server fails, then try again. (Couldn't call 'search_listings' over M…", "duration_ms": 344.7}
```

Two limits in that record. The `error` says "unhandled errors in a TaskGroup (1 sub-exception)", which hides the real cause: the server file was not found. Python printed that on stderr and the log never saw it, so the log says that the search failed and not why. The other limit is that `process` is the name of the script that was started, so the same agent logs as `app.py`, `measure_cost.py` or `faults.py` depending on who ran it.

`results/failure_model-429.jsonl` has a third failure, kept and not pasted: a model that answers 429 five times. It is eight lines. The search, then five `model_call` lines each with an `error` and an `attempt` from 1 to 5, then the outfit step with `error: RateLimitExhausted`, then the `run` line. Both injected runs came from `faults.py`, which replaces the model and the server from outside, so no model was called. The 429 run used a fake clock, so its durations do not include the 32 seconds of waiting a real one would spend.

**What It Costs**

One run costs 2 model requests, about 825 tokens (658.5 prompt and 166.3 output on average), and 3.4 seconds. Those are the averages of ten runs. The cost that matters for this system is requests and tokens, because the model calls are the only part that uses a metered service. I did not turn the tokens into dollars, because I have no measured price to apply. The tokens are what the service reported, not an estimate.

How I measured it: `python measure_cost.py` runs the agent ten times through `run_agent()` with the cache off. It uses the five example queries that match something, twice each, and waits 8 seconds between runs so the rate limit adds no waiting. It adds up requests and tokens from the `model_call` lines in the run log, from both processes, so the fit card's request is included. Seconds are the `run` line's own duration. The runs were made on commit `e2e2ff9`, Python 3.13.15 on Linux, `gemini-3.5-flash-lite`, temperature 0.9, in a fresh virtual environment from `requirements.txt` (`mcp` 1.30.0 and `google-genai` 1.75.0, taken from that install's output, since the summary file does not record package versions). The summary is `results/cost_2026-11-15_2011.md` and the log is the `.jsonl` next to it.

| Run | Query | Requests | Prompt tokens | Output tokens | Seconds | Error |
|---|---|---|---|---|---|---|
| 1 | vintage graphic tee under $30 | 2 | 672 | 178 | 4.2 |  |
| 2 | 90s track jacket in size M | 2 | 691 | 195 | 3.1 |  |
| 3 | silk slip dress in midi length under $40 | 2 | 654 | 147 | 3.1 |  |
| 4 | platform sneakers size 8 | 2 | 655 | 171 | 3.1 |  |
| 5 | denim jacket under $50 | 2 | 635 | 157 | 3.0 |  |
| 6 | vintage graphic tee under $30 | 2 | 662 | 170 | 3.3 |  |
| 7 | 90s track jacket in size M | 2 | 659 | 168 | 3.1 |  |
| 8 | silk slip dress in midi length under $40 | 2 | 658 | 148 | 5.5 |  |
| 9 | platform sneakers size 8 | 2 | 669 | 179 | 3.1 |  |
| 10 | denim jacket under $50 | 2 | 630 | 150 | 3.0 |  |
| 11 (failed run, not in the average) | designer ballgown size XXS under $5 | 0 | 0 | 0 | 0.5 | No listings matched "designer ballgown" in size XXS under $5. You coul |

Total tokens per run ranged from 780 to 886, and seconds from 3.0 to 5.5. Run 8 is the 5.5: its fit card's model call took 3.3 seconds, where the average for that call is 1.0. It still made 2 requests, so there was no retry. Model calls account for 1.9 of the 3.4 seconds (0.9 in the agent, 1.0 in the server). The rest looks like the two trips to the MCP server, each of which starts a new Python process. In run 1 the search took 0.6 seconds, and the fit card step took 2.0 seconds, of which its model call was 1.0.

This is the cost of a run that completes. A query that matches nothing makes 0 requests and took 0.5 seconds (run 11). A run that gets rate limited costs more: each 429 counts as a request in the log, so the outfit step alone can spend 5 requests and return nothing. Ten runs on one day against one model is a small sample, and the output tokens vary from run to run (147 to 195 here, at the same temperature).
