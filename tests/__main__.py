import os, sys, unittest
sys.path.append(os.path.realpath('./threadsnake'))

if __name__ == "__main__":
    testsuite = unittest.TestLoader().discover('./tests')
    unittest.TextTestRunner(verbosity=1).run(testsuite)
