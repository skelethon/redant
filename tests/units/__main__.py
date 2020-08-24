import os, unittest

loader = unittest.TestLoader()
start_dir = os.path.dirname(os.path.realpath(__file__))
suite = loader.discover(start_dir=start_dir, pattern='*_test.py')
runner = unittest.TextTestRunner()
runner.run(suite)
