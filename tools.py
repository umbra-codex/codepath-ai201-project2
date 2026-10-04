"""
The three FitFindr tools.

Each one is a standalone function you can call and test on its own, before any
of them are wired into the loop. Build and test them one at a time — three
untested tools joined by a loop is one problem that looks like six, because you
can't tell which layer is lying to you.

    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)             → str
    create_fit_card(outfit, new_item)              → str

All three are stubs right now. They run and they do nothing — that's the
starting position and it's deliberate.

⚠️ Before you write any of them, fill in the **Tool Inventory** section of your
README (Milestone 2). Four lines per tool: what it does, each input with its
type, exactly what it returns, and what it returns when it has nothing to give.
That last line is what your loop branches on. "Returns a list" earns nothing —
the description has to say what is *in* the list.
"""

import re

import config
from generate import ModelUnavailable, generate
from utils.data_loader import load_listings

# ── Tool 1: search_listings ───────────────────────────────────────────────────

_STOP_WORDS = {
  # articles, conjunctions, prepositions
  "a", "an", "the", "and", "or", "but", "nor", "so", "yet", "if", "than",
  "then", "as", "at", "by", "for", "from", "in", "into", "of", "on", "onto",
  "to", "with", "about", "around", "between", "through", "during",
  "under", "below", "within", "per",
  # pronouns and determiners
  "me", "my", "mine", "we", "us", "our", "you", "your", "yours", "he", "she",
  "it", "its", "they", "them", "their", "this", "that", "these", "those",
  "some", "any", "each", "every", "other", "another", "such", "both",
  "either", "which", "what", "who", "whom", "whose", "where", "when", "why",
  "how", "there", "here",
  # verbs and auxiliaries
  "is", "am", "are", "was", "were", "be", "been", "being", "do", "does",
  "did", "have", "has", "had", "can", "could", "will", "would", "should",
  "may", "might", "must", "get", "got", "go", "goes", "make", "makes",
  # contractions (the regex keeps apostrophes)
  "i'm", "i'd", "i've", "i'll", "it's", "that's", "there's", "let's",
  "you're", "we're", "they're", "don't", "doesn't", "can't", "won't",
  "isn't", "aren't",
  # query filler: how people phrase a request
  "want", "wants", "wanted", "need", "needs", "looking", "look", "find",
  "search", "searching", "show", "give", "buy", "something", "anything",
  "thing", "things", "stuff", "item", "items", "piece", "pieces", "please",
  "like", "maybe", "kind", "sort", "type", "style", "styled", "ideally",
  "prefer", "preferably", "wear", "wearing", "pair", "match",
  # price and size phrasing (handled by max_price and size, not keywords)
  "price", "priced", "cost", "costs", "budget", "cheap", "affordable",
  "dollar", "dollars", "bucks", "usd", "max", "less", "most",
  "size", "sized", "sizes",
  # listing boilerplate that appears everywhere and distinguishes nothing
  "very", "super", "really", "quite", "just", "only", "also", "too", "not",
  "no", "great", "good", "nice", "perfect", "perfectly", "beautifully",
  "genuinely", "otherwise", "major", "stunning", "condition", "worn",
  "slightly", "fit", "fits", "color", "colors", "material", "adds",
  "nothing", "none",
}

def _keywords(text: str) -> set[str]:
    """Lowercase words worth matching on, stop words are removed."""
    words = re.findall(r"[a-z0-9']+", (text or "").lower())
    return {w for w in words if w not in _STOP_WORDS and len(w) > 1}


def _size_tokens(size: str) -> set[str]:
    """Uppercase size tokens: split on "/", text in parentheses removed."""
    cleaned = re.sub(r"\([^)]*\)", " ", size or "")
    parts = [" ".join(p.split()).upper() for p in cleaned.split("/")]
    return {p for p in parts if p}


def _size_matches(wanted: str, listing_size: str) -> bool:
    """Whole-token match. A One Size listing matches any requested size."""
    if not wanted:
        return True
    listing_tokens = _size_tokens(listing_size)
    if any(token.startswith("ONE SIZE") for token in listing_tokens):
        return True
    return bool(_size_tokens(wanted) & listing_tokens)


def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the listings data for items matching a description, and optionally a
    size and a price ceiling.

    This is the tool that doesn't call the model, which makes it the easiest one
    to test and the one to move onto MCP in unit 4.

    Args:
        description: keywords describing what the user wants
                     (e.g. "vintage graphic tee").
        size:        a size string to filter by, or None to skip size filtering.
                     Match case-insensitively — "M" should match "S/M".

                     ⚠️ Read the sizes in the data before you reach for a plain
                     substring test. `"s" in "us 9"` is True, and so is
                     `"l" in "xl"`. A filter that returns shoes when someone
                     asked for a small top reads like a broken search, and it
                     will quietly cost you in unit 4 when you test criterion 1.
                     What counts as a size match is part of your spec — decide
                     it and write it into your Tool Inventory.
        max_price:   maximum price, inclusive, or None to skip price filtering.

    Returns:
        A list of matching listing dicts, best match first.
        **Returns an empty list when nothing matches — an empty list, not None,
        and not an exception.** Your loop branches on this.

    Each listing dict has these fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand (str or None), platform

    Note that `brand` is None for most listings. That is deliberate and
    realistic — thrift listings often have no brand. If something you write
    assumes a brand is always there, you will find out in unit 4.

    TODO:
        1. Load every listing with load_listings().
        2. Filter by max_price and by size, when each is provided.
        3. Score what's left by keyword overlap with `description`.
        4. Drop anything scoring zero.
        5. Sort by score, highest first, and return the listing dicts —
           at most config.SEARCH_RESULT_LIMIT of them.

    Test it from a terminal before you move on:
        python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
    """
    wanted = _keywords(description)
    if not wanted:
        return []

    scored = []
    for listing in load_listings():
        if max_price is not None and listing["price"] > max_price:
            continue
        if not _size_matches(size, listing["size"]):
            continue

        text = " ".join([
            listing["title"],
            listing["description"],
            listing["category"],
            " ".join(listing["style_tags"]),
            " ".join(listing["colors"]),
            listing["brand"] or "",
        ])
        score = len(wanted & _keywords(text))
        if score > 0:
            scored.append((score, listing))

    # sort() is stable, so equal scores stay in data order.
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [listing for _, listing in scored[:config.SEARCH_RESULT_LIMIT]]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────


_STYLIST = (
    "You are a thrift stylist. Write plain text with no markdown and no "
    "preamble. Keep it under 120 words."
)


def _describe_item(item: dict) -> str:
    """One line about a listing for a prompt. Leaves the brand out when there is none."""
    parts = [
        item["title"],
        f"category: {item['category']}",
        f"colors: {', '.join(item['colors'])}",
        f"style: {', '.join(item['style_tags'])}",
        f"size: {item['size']}",
    ]
    if item.get("brand"):
        parts.append(f"brand: {item['brand']}")
    return "; ".join(parts)


def _describe_wardrobe(items: list[dict]) -> str:
    """One line per wardrobe piece, for a prompt."""
    lines = []
    for piece in items:
        line = (
            f"- {piece['name']} ({piece['category']}; "
            f"colors: {', '.join(piece['colors'])}; "
            f"style: {', '.join(piece['style_tags'])})"
        )
        if piece.get("notes"):
            line += f" Note: {piece['notes']}"
        lines.append(line)
    return "\n".join(lines)


def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest one or two outfits.

    This one calls the model, through `generate()`. You don't need to think
    about rate limits — the adapter handles pacing for you.

    Args:
        new_item: a listing dict — the item the user is considering.
        wardrobe: a wardrobe dict with an 'items' key holding a list of items.
                  **It may be empty.** Handle that.

    Returns:
        A non-empty string with outfit suggestions.
        With an empty wardrobe, return general styling advice rather than
        raising or returning "". Unit 4 has you trigger the empty wardrobe on
        purpose, so decide now what it should do.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If it is, ask the model for general styling ideas for this item.
        3. If it isn't, format the wardrobe items into the prompt and ask for
           specific combinations naming pieces the user already owns.
        4. Return the model's response.

    Test it from a terminal before you move on:
        python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
    """
    items = wardrobe.get("items") or []

    if not items:
        prompt = (
            f"Someone is thinking about buying this thrifted item:\n"
            f"{_describe_item(new_item)}\n\n"
            f"You know nothing about what they own. Give general styling "
            f"advice for the item: one or two outfit ideas built from the "
            f"kinds of pieces that go with it. Do not describe any other piece "
            f"as theirs: introduce each one with \"a\" or \"an\", never "
            f"\"your\"."
        )
    else:
        prompt = (
            f"Someone is thinking about buying this thrifted item:\n"
            f"{_describe_item(new_item)}\n\n"
            f"Their wardrobe:\n{_describe_wardrobe(items)}\n\n"
            f"Suggest one or two outfits that pair the item with pieces from "
            f"the wardrobe. Name each wardrobe piece you use, as it is "
            f"written above. Use only pieces from that list."
        )

    outfit = generate(prompt, system=_STYLIST)
    if not outfit:
        # generate() returns "" when the model sends back no text. Raising keeps
        # a failed call from reaching create_fit_card looking like an outfit.
        raise ModelUnavailable(
            f"The model returned no text for {new_item['title']}. Try it again."
        )
    return outfit


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────


_CAPTION_WRITER = (
    "You write short social captions about thrifted clothes. Reply with the "
    "caption only: plain text, no markdown, no hashtags, no quotation marks "
    "around it."
)


def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Write a short caption someone would actually post about the find.

    This calls the model too.

    Args:
        outfit:   the outfit suggestion string from suggest_outfit().
        new_item: the listing dict for the item.

    Returns:
        A two-to-four sentence caption.
        If `outfit` is empty or whitespace, return a descriptive message rather
        than raising.

    The caption should read like a real post rather than a product description,
    mention the item and its price and platform once each, and be specific about
    the vibe.

    It should also come out **differently for different inputs**. If you run
    this three times on the same item and get three word-for-word identical
    strings, it's one of two things, and both are near the top of `config.py`:

        • CACHE_ENABLED — the adapter handed back an answer it already had
        • TEMPERATURE   — at 0.0 the model gives the same words every time

    TODO:
        1. Guard against an empty or whitespace-only `outfit`.
        2. Build a prompt with the item details and the outfit.
        3. Call generate() and return the response.

    Test it from a terminal before you move on:
        python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
    """
    if not outfit or not outfit.strip():
        return "No outfit to write a fit card for."

    price = f"${new_item['price']:g}"
    prompt = (
        f"Write a caption for a post about this thrift find.\n\n"
        f"The item: {_describe_item(new_item)}\n"
        f"Price: {price}\n"
        f"Platform: {new_item['platform']}\n\n"
        f"How it will be worn:\n{outfit.strip()}\n\n"
        f"Write two to four sentences in first person, as the person who just "
        f"bought it and is showing it off, not as someone selling it. Say "
        f"what the item is. "
        f"Mention the price exactly once, written in digits as {price}, and "
        f"the platform ({new_item['platform']}) exactly once. Be specific "
        f"about the vibe of the outfit."
    )

    card = generate(prompt, system=_CAPTION_WRITER)
    if not card:
        # Same reason as in suggest_outfit: an empty reply is a failed call.
        raise ModelUnavailable(
            f"The model returned no text for {new_item['title']}. Try it again."
        )
    return card
