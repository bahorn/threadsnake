import ast
from passes import \
        RemoveDocstrings, \
        CleanImports, \
        RemoveImports, \
        RenameVariables, \
        RenameFunctions, \
        RenameClasses


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
        for astpass in self._passes:
            cfg = self._cfg.get(astpass.name())
            if cfg is not None:
                astpass.update_config(cfg)
            self._root = astpass.apply(self._root)

    def pack(self):
        """
        Get a minified string representation of the program.
        """
        # print(str(self._root[0]))
        return ast.unparse(self._root)
