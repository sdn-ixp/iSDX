import sys

'''
Execute a main, which may exist in a different directory,
but use the current directory of this file (launch.py)
as the first component of python's search path (sys.path).
This allows us to get rid of in-code modifications of sys.path.
'''

if len(sys.argv) < 2:
    print 'Usage: python launch <module> [args]'
    print 'where <module> points to something that contains a main() function'
    sys.exit(1)

exec 'from '+sys.argv[1]+' import main'
sys.argv = sys.argv[1:]
main(sys.argv)
