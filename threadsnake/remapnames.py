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
kwords = [
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


class SymbolMapper:
    def __init__(self):
        self._keywords = kwords.copy()

    def add_to_keywords(self, name):
        if isinstance(name, list):
            self._keywords += name
        else:
            self._keywords.append(name)

    def map_symbols(self, symbol_count):
        alphabet = 'abcdefghijklmnopqrstuvwxyz'
        res = {}
        order = sorted(symbol_count.items(), key=lambda x: x[1], reverse=True)
        vnames = get_product(alphabet)
        for (n, _) in order:
            res[n] = next(vnames)
            while res[n] in self._keywords:
                res[n] = next(vnames)
        return res
