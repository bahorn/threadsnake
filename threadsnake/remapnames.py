"""
Generating shorter names for symbols that get used more.
"""
import itertools


def get_product(alphabet):
    i = 1
    while True:
        for combo in itertools.product(alphabet, repeat=i):
            yield ''.join(combo)
        i += 1

# Need to do this to generate valid code.
keywords = [
    "False",
    "await",
    "else",
    "import",
    "pass",
    "None",
    "break",
    "except",
    "in",
    "raise",
    "True",
    "class",
    "finally",
    "is",
    "return",
    "and",
    "continue",
    "for",
    "lambda",
    "try",
    "as",
    "def",
    "from",
    "nonlocal",
    "while",
    "assert",
    "del",
    "global",
    "not",
    "with"
    "async"
    "elif",
    "if",
    "or",
    "yield",
    "match",
    "case"
]


def map_symbols_to_new_names(symbol_count):
    alphabet = 'abcdefghijklmnopqrstuvwxyz'
    res = {}
    order = sorted(symbol_count.items(), key=lambda x: x[1], reverse=True)
    vnames = get_product(alphabet)
    for (n, _) in order:
        res[n] = next(vnames)
        while res[n] in keywords:
            res[n] = next(vnames)
    return res
