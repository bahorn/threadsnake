import unittest
from threadsnake import passes, ast


func_1_case = '''
def main():
    """
    test docstring
    """
    return 1
'''


func_1_goal = '''
def main():
    return 1
'''


class TestDocstringRemoval(unittest.TestCase):
    def test_funcs(self):
        func1 = ast.parse(func_1_case)
        res = ast.unparse(passes.RemoveDocstrings().apply(func1))
        self.assertEqual(res, ast.unparse(ast.parse(func_1_goal)))
