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

**Criterion 3, revised and scored:** `check_handoff.py::main` replaces the two model tools with stand-ins that record the `new_item` they are called with, runs `agent.py::run_agent`, and compares each recorded `id` with `session["selected_item"]` and with the first search result. It makes no model calls.

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

**On the MCP move:** `search_listings` is registered in `mcp_server.py` under the same name, with the three typed inputs from my Tool Inventory. In `agent.py::run_agent`, the direct call `search_listings(description, size, max_price)` became `call_tool("search_listings", {...})` from `mcp_client.py`, and `agent.py` no longer imports the function. `suggest_outfit` and `create_fit_card` are still direct calls. I compared the direct call and the MCP call on the six example queries and ten edge cases, among them no filters, size only, the price ceiling, a One Size listing, and an empty description. Values and types matched every time, including the empty list for the ballgown query, so nothing in the loop's branch had to change. The one difference is speed: each MCP call starts the server as a second Python process and takes between half a second and a second, where the direct call was instant.

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

That is one readable line, but the exception left `run_agent` with nothing in `session["error"]`, so `run_eval.py` would log the try as a crash and `serve.py` would answer with a 500. `run_agent` now catches `ModelUnavailable` around both model tools, puts a message in `session["error"]` that names the step that failed, and stops:

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

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
| --------- | ------ | ----- | ----- | ----- | ----- | ----- | ------- |
| 1.        |        |       |       |       |       |       |         |
| 2.        |        |       |       |       |       |       |         |
| 3.        |        |       |       |       |       |       |         |
| 4.        |        |       |       |       |       |       |         |
| 5.        |        |       |       |       |       |       |         |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->

---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->

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

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
