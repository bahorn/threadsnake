"""
Basic python minifier, meant for script packing.

When merging multiple files, this can break your code.
"""
import ast


def to_module(a):
    m = ast.Module()
    m.body = a
    return m


class Pass:
    def __init__(self, cfg={}):
        self._cfg = cfg

    def apply(self, curr_ast):
        return curr_ast

    def update_config(self, cfg):
        self._cfg = cfg

    def name(self):
        return self.__class__.__name__


class RemoveDocstrings(Pass):
    def apply(self, curr_ast):
        new_ast = curr_ast.body
        for node in new_ast:
            if not isinstance(node, (ast.FunctionDef, ast.ClassDef,
                                     ast.AsyncFunctionDef, ast.Module)):
                continue

            if not len(node.body):
                continue

            if not isinstance(node.body[0], ast.Expr):
                continue

            if not hasattr(node.body[0], 'value') or not isinstance(node.body[0].value, ast.Str):
                continue

            before = [ast.Pass()] if len(node.body) == 1 else []
            node.body = before + node.body[1:]

        return to_module(new_ast)


class CleanImports(Pass):
    def apply(self, curr_ast):
        """
        Find global imports and move them all into one line, deduping
        """
        # find the global imports
        imports = []
        imports_from = []
        res = []
        for line in curr_ast.body:
            if isinstance(line, ast.Import):
                imports.append(line)
            elif isinstance(line, ast.ImportFrom):
                imports_from.append(line)
            else:
                res.append(line)

        # Dedup the module names
        names = []
        for import_line in imports:
            for name in import_line.names:
                names.append(name.name)
        names = list(map(ast.alias, set(names)))

        # Cleanup ImportFrom
        # Dedup multiple things from the same module
        # remove things that are in the global namespace already

        # Join everything together
        return to_module([ast.Import(names)] + imports_from + res)


class RemoveImports(Pass):
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

        class ImportRemover(ast.NodeTransformer):
            def visit_Import(self, node):
                new = []
                for name in node.names:
                    if name.name not in remove:
                        new.append(name)
                if len(new) == 0:
                    return None

                return ast.Import(new)

        ap = ImportRemover().visit(curr_ast)
        return ap


class RenameFunctions(Pass):
    def apply(self, curr_ast):
        return curr_ast


class RenameVariables(Pass):
    def apply(self, curr_ast):
        return curr_ast


class RenameClasses(Pass):
    def rename_classes(self, curr_ast):
        return curr_ast
