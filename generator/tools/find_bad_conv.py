# -*- coding: utf-8 -*-
u"""Najti v ST-neveroyatnye konversii i drugie opechatki.

ZAPUSKAT SISTEMNYM PYTHON 3.
    python find_bad_conv.py

ZADAChA. Kompilyator soobshchil "C0046: Identifikator 'BYTE_TO_BYTE' ne zadаn"
i "WORD_TO_WORD ne zadаn". Eto vyzovy funkcij, kotoryh ne sushchestvuet:
v IEC net preobrazovaniya tipa v samogo sebya. Ih nado najti vse i zamениt
na pravilnye (WORD_TO_BYTE, BYTE_TO_WORD i t. d.) libo ubrat.
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(ROOT, u"src")

TYPES = (u"BOOL", u"BYTE", u"WORD", u"DWORD", u"SINT", u"USINT", u"INT",
         u"UINT", u"DINT", u"UDINT", u"LINT", u"ULINT", u"REAL", u"LREAL")


def main():
    pat = re.compile(u"\\b(%s)_TO_(%s)\\b" % (u"|".join(TYPES), u"|".join(TYPES)))
    total = 0
    for f in sorted(os.listdir(SRC)):
        if not f.endswith(u".plcopenxml"):
            continue
        t = io.open(os.path.join(SRC, f), encoding=u"utf-8").read()
        for m in pat.finditer(t):
            if m.group(1) != m.group(2):
                continue
            # nomer stroki v fajle
            ln = t[:m.start()].count(u"\n") + 1
            ctx = t[max(0, m.start() - 90):m.start() + 70].replace(u"&#xA;", u" | ")
            sys.stdout.write(u"%-24s str.%-4d %s\n     ...%s...\n"
                             % (f[:-12], ln, m.group(0), ctx[-140:]))
            total += 1
    sys.stdout.write(u"\nneveroyatnyh konversij: %d\n" % total)


if __name__ == u"__main__":
    main()
