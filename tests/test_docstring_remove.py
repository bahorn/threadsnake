import unittest
from threadsnake import passes, ast


cases = [
(
'''
def main():
    """
    test docstring
    """
    return 1
''',
'''
def main():
    return 1
'''
    ),
    (
'''
class Blah():
    """
    test docstring
    """
    return 1
''',
'''
class Blah():
    return 1
'''
    ),
(
'''
def blah():
    a = "1"
''',
'''
def blah():
    a = "1"
'''
),
(
'''
def blah():
    a = 1
''',
'''
def blah():
    a = 1
'''
),
(
'''
"""
test
"""
''',
''
)
]


class TestDocstringRemoval(unittest.TestCase):
    def test_funcs(self):
        for a, b in cases:
            a_, b_ = ast.parse(a), ast.parse(b)
            res = ast.unparse(passes.RemoveDocstrings().apply(a_))
            self.assertEqual(res, ast.unparse(b_))
