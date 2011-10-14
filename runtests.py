import os
import pydis

def test_file(path, versions):
    for version in versions:
        os.system('%s -m py_compile "%s"' % (version, path))
        print pydis.dis(path + 'c')

versions = ['python2.5', 'python3.1']
test_file('tests/datatypes.py', versions)