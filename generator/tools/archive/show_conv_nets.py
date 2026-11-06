# -*- coding: utf-8 -*-
u"""Pokazat', v kakih setyah PLC_PRG sto yat konvertory i sdvigi.

ZAPUSKAT SISTEMNYM PYTHON 3.
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
XML = os.path.join(ROOT, u"src", u"PLC_PRG.plcopenxml")

WANT = (u"BYTE_TO_WORD", u"SHL", u"WORD_TO_BYTE", u"WORD_TO_INT", u"INT_TO_WORD",
        u"BOOL_TO_BYTE")


def main():
    t = io.open(XML, encoding=u"utf-8").read().split(u"\n")
    cur = u""
    for i, ln in enumerate(t, 1):
        s = ln.strip()
        if s.startswith(u"<!-- SET"):
            cur = s.strip(u"<!-> ")
        for w in WANT:
            if u'typeName="%s"' % w in s:
                sys.stdout.write(u"%5d  %-14s  %s\n" % (i, w, cur))


if __name__ == u"__main__":
    main()
