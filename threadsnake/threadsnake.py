import ast
from passes import \
        RemoveDocstrings, \
        CleanImports, \
        RemoveImports, \
        RenameVariables, \
        RenameFunctions, \
        RenameClasses
from output_real import _Unparser


def unparse(ast_obj):
    unparser = _Unparser()
    return unparser.visit(ast_obj)


class ThreadSnake:
    """
    Base class for users.

    This will apply the chosen minifiers over the ast.
    """

    def __init__(self):
        self._root = ast.parse('').body
        self._passes = [
            RemoveDocstrings(),
            CleanImports(),
            RemoveImports(),
            RenameVariables(),
            RenameFunctions(),
            RenameClasses()
        ]
        self._cfg = {
            'RemoveImports': {
                'remove': ['']
            }
        }

    def add(self, code, module_name=None):
        """
        Add code to the AST
        """
        self._root += ast.parse(code).body
        if module_name is not None:
            self._cfg['RemoveImports']['remove'].append(module_name)

    def apply(self):
        curr = ast.Module()
        curr.body = self._root

        for astpass in self._passes:
            cfg = self._cfg.get(astpass.name())
            if cfg is not None:
                astpass.update_config(cfg)
            curr = astpass.apply(curr)

        self._root = curr

    def pack(self):
        """
        Get a minified string representation of the program.
        """
        return unparse(self._root.body)
