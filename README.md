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

**What moves through the session:** `query`, then `parsed`, `search_results`, `selected_item`, `outfit_suggestion`, and `fit_card`, each written by one step and read by the next. `wardrobe` is set at the start, and `error` is set only when the search finds nothing.

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
| 1.        |        |       |       |       |       |       |         |
| 2.        |        |       |       |       |       |       |         |
| 3.        |        |       |       |       |       |       |         |
| 4.        |        |       |       |       |       |       |         |
| 5.        |        |       |       |       |       |       |         |

**Real output from one try**, pasted as text, naming the file and function
that produced it:

```

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
| 1   |           |        |         |               |
| 2   |           |        |         |               |
| 3   |           |        |         |               |
| 4   |           |        |         |               |
| 5   |           |        |         |               |

**Diagnoses**

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

```

**Empty search**

```

```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->

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
