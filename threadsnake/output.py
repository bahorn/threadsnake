import ast


class OutputMinifier:
    """
    Take an AST and convert it to a string, applying some minifications.
    """

    def __init__(self):
        pass

    def minify(self, a):
        return ast.unparse(a)
