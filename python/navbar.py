import sys
sys.path.append('/Users/ostwald/devel/python-lib')

from HyperText.HTML40 import *


def get_nav_bar ():
    nav_bar = DIV(id="navbar")
    nav_bar.append (A ("match results", href="match-results.html"))
    nav_bar.append (SPAN ("|", klass="navbar-divider"))
    nav_bar.append (A ("results tally", href="results-tally.html"))
    return nav_bar