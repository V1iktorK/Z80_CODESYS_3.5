# -*- coding: utf-8 -*-
u"""Pokazat' tipy vseh peremennyh PLC_PRG, osobenno signalov upravleniya.

ZAPUSKAT SISTEMNYM PYTHON 3.
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
XML = os.path.join(ROOT, u"src", u"PLC_PRG.plcopenxml")


def main():
    t = io.open(XML, encoding=u"utf-8").read()
    pat = re.compile(u'<variable name="(\\w+)"><type>(?:<(\\w+)\\s*/>|'
                     u'<derived name="(\\w+)")')
    rows = [(m.group(1), m.group(2) or m.group(3)) for m in pat.finditer(t)]
    want = sys.argv[1] if len(sys.argv) > 1 else u"vCtl"
    sys.stdout.write(u"vsego obyavlenij: %d\n\n" % len(rows))
    for nm, tp in rows:
        if want in nm:
            sys.stdout.write(u"  %-22s %s\n" % (nm, tp))


if __name__ == u"__main__":
    main()
