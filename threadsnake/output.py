"""
Code to map 
"""
import ast


def minify_import(statement):
    return 'import ' + ','.join(module.name for module in statement.names)


def minify_importfrom(statement):
    return f'from {statement.module} import ' +  \
            ','.join(module.name for module in statement.names)


def minify_function(func):
    decorator_list = []
    print(func.args.posonlyargs)
    print(func.args.args)
    print(func.args.vararg)
    print(func.args.kwonlyargs)
    print(func.args.kw_defaults)
    print(func.args.kwarg)
    print(ast.unparse(func.args.defaults[0]))
    decorators = '\n'.join(
        map(lambda x: '@' + minifier(x), func.decorator_list)
    )
    return f'{decorators}\ndef {func.name}():\n    ' + '\n    '.join(map(minifier, func.body))


def minifier(a):
    match a:
        case ast.Import():
            return minify_import(a)
        case ast.ImportFrom():
            return minify_importfrom(a)
        case ast.FunctionDef():
            return minify_function(a)
        case ast.ClassDef():
            return ast.unparse(a)
        case _:
            return ast.unparse(a)


class OutputMinifier:
    """
    Take an AST and convert it to a string, applying some minifications.
    """

    def __init__(self):
        pass

    def minify(self, a):
        return '\n'.join(map(minifier, a))
