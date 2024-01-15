"""
Passes we run over the AST
"""
from ast import \
        FunctionDef, \
        ClassDef, \
        AsyncFunctionDef, \
        Module, \
        Constant, \
        Pass, \
        Import, \
        ImportFrom, \
        NodeTransformer, \
        walk, \
        alias
import copy


def to_module(a):
    m = Module()
    m.body = a
    return m


class ASTPass:
    def __init__(self, cfg={}):
        self._cfg = cfg

    def apply(self, curr_ast):
        return curr_ast

    def update_config(self, cfg):
        self._cfg = cfg

    def name(self):
        return self.__class__.__name__


class RemoveDocstrings(ASTPass):
    TYPES = (FunctionDef, ClassDef, AsyncFunctionDef, Module)

    def apply(self, curr_ast):
        new_ast = copy.deepcopy(curr_ast)
        # https://gist.github.com/phpdude/1ae6f19de213d66286c8183e9e3b9ec1
        for node in walk(new_ast):
            if not isinstance(node, self.TYPES):
                continue

            if not len(node.body):
                continue

            if not hasattr(node.body[0], 'value'):
                continue

            if not isinstance(node.body[0].value, Constant):
                continue

            if not isinstance(node.body[0].value.value, str):
                continue

            before = [Pass()] if len(node.body) == 1 else []
            node.body = before + node.body[1:]

        return new_ast


class CleanImports(ASTPass):
    def apply(self, curr_ast):
        """
        Find global imports and move them all into one line, deduping
        """
        # find the global imports
        imports = []
        imports_from = []
        res = []
        for line in curr_ast.body:
            if isinstance(line, Import):
                imports.append(line)
            elif isinstance(line, ImportFrom):
                imports_from.append(line)
            else:
                res.append(line)

        # Dedup the module names
        names = []
        for import_line in imports:
            for name in import_line.names:
                names.append(name.name)
        names = list(map(alias, set(names)))

        # Cleanup ImportFrom
        # Dedup multiple things from the same module
        # remove things that are in the global namespace already

        # Join everything together
        return to_module([Import(names)] + imports_from + res)


class RemoveImports(ASTPass):
    """
    Remove imports.

    Used if we are combining multiple files together.
    """

    def apply(self, curr_ast):
        if not isinstance(self._cfg, dict):
            return curr_ast

        remove = self._cfg.get('remove')
        if remove is None:
            return curr_ast

        class ImportRemover(NodeTransformer):
            def visit_Import(self, node):
                new = []
                for name in node.names:
                    if name.name not in remove:
                        new.append(name)
                if len(new) == 0:
                    return None

                return Import(new)

            def visit_ImportFrom(self, node):
                for name in remove:
                    module_name = node.module
                    if '.' in module_name and '.' not in name:
                        module_name = module_name.split('.')[0]
                    if module_name == name:
                        return None
                return node

        ap = ImportRemover().visit(curr_ast)
        return ap


class RenameFunctions(ASTPass):
    def apply(self, curr_ast):
        return curr_ast


class RenameVariables(ASTPass):
    def apply(self, curr_ast):
        return curr_ast


class RenameClasses(ASTPass):
    def rename_classes(self, curr_ast):
        return curr_ast
