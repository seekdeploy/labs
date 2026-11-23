"""The same six edits, written once for each editor's grammar.

Every task starts from a fresh copy of fixture.py with the cursor at line 1,
column 1. Keys are tokens: "<Esc>" and "<CR>" are one keystroke each; any
other string is typed literally, one keystroke per character. Saving and
quitting (":wq<CR>") is appended by run.py and not counted, because both
editors need the same keys for it.
"""

FIXTURE = open(__file__.replace("tasks.py", "fixture.py")).read()

def edit(old, new, count=1):
    assert FIXTURE.count(old) >= count, old
    return FIXTURE.replace(old, new, count)

TASKS = [
    {
        "id": "t1-change-word",
        "what": "Rename total_price to order_total on line 1",
        "expected": edit("total_price", "order_total"),
        "nvim": ["w", "cw", "order_total", "<Esc>"],
        "hx":   ["w", "w", "c", "order_total", "<Esc>"],
    },
    {
        "id": "t2-change-in-quotes",
        "what": 'Change "SPRING-SALE" to "WINTER"',
        "expected": edit('"SPRING-SALE"', '"WINTER"'),
        "nvim": ["/SPR", "<CR>", 'ci"', "WINTER", "<Esc>"],
        "hx":   ["/SPR", "<CR>", 'mi"', "c", "WINTER", "<Esc>"],
    },
    {
        "id": "t3-delete-in-parens",
        "what": "Empty the arguments of round(...)",
        "expected": edit("round(subtotal * (1 + tax_rate) - discount, 2)", "round()"),
        "nvim": ["/round(", "<CR>", "f(", "di("],
        # Helix search is a regex where "(" opens a group, so it must be escaped.
        # Unescaped, the search silently fails and "d" deletes the first character
        # of the file (see RUN-LOG.md, "What broke" #3).
        "hx":   ["/round\\(", "<CR>", "mi(", "d"],
    },
    {
        "id": "t4-delete-line",
        "what": "Delete line 2 (the subtotal line)",
        "expected": edit("    subtotal = sum(item.price for item in items)\n", ""),
        "nvim": ["j", "dd"],
        "hx":   ["j", "x", "d"],
    },
    {
        "id": "t5-rename-all",
        "what": "Rename every subtotal to base",
        "expected": FIXTURE.replace("subtotal", "base"),
        "nvim": [":%s/subtotal/base/g", "<CR>"],
        "hx":   ["%", "s", "subtotal", "<CR>", "c", "base", "<Esc>"],
    },
    {
        "id": "t6-delete-last-two-lines",
        "what": "Delete the legacy_helper function (last two lines)",
        "expected": edit("def legacy_helper():\n    pass\n", ""),
        "nvim": ["G", "dk"],
        "hx":   ["ge", "k", "x", "x", "d"],
    },
]

def keystrokes(tokens):
    return sum(1 if t in ("<Esc>", "<CR>") else len(t) for t in tokens)
