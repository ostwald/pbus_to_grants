import sys
sys.path.append('/Users/ostwald/devel/python/python-lib')

from HyperText.HTML40 import *


def get_nav_bar (page=''):
    nav_bar = DIV(id="navbar")
    nav_bar.append (A ("Home", href="../index.html"))

    nav_bar.append (SPAN ("|", klass="navbar-divider"))
    if page == 'match-results':
        nav_bar.append ("All Records")
    else:
        nav_bar.append (A ("All Records", href="match-results.html"))
    nav_bar.append (SPAN ("|", klass="navbar-divider"))
    if page == 'results-tally':
        nav_bar.append ("Award_ID Tally")
    else:
        nav_bar.append (A ("Award_ID Tally", href="results-tally.html"))
    nav_bar.append (SPAN ("|", klass="navbar-divider"))
    nav_bar.append (A ("QA Notes (GoogleDoc)",
                       target="google_doc",
                       href="https://docs.google.com/document/d/1RIXIBJGO_PrbFnAy1r9qXTY8AjoxDI5C9rrzpO4v0z4"))

    return nav_bar