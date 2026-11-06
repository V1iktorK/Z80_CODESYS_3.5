# -*- coding: utf-8 -*-
u"""Najti v sheme vse SEL, u kotoryh uslovie (vhod G) -- ne BOOL.

ZAPUSKAT SISTEMNYM PYTHON 3.
    python find_bad_sel.py PLC_PRG

ZADAChA. Analizator tipov soobshchil: "SEL vhod 1 (BOOL) <- BITS". Znachit
v uslovii SEL stoit NE bulevo vyrazhenie (naprimer rezul'tat AND dvuh bajtov).
CODESYS takoe otvergaet s C32. Nado najti eti mesta i ponyat, chto tam dolzhno
bylo byt.
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(ROOT, u"src")


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else u"PLC_PRG"
    path = os.path.join(SRC, target + u".plcopenxml")
    t = io.open(path, encoding=u"utf-8").read()

    for m in re.finditer(u'<block localId="(\\d+)" typeName="SEL"', t):
        bid = m.group(1)
        seg = t[m.end():m.end() + 3000]
        g = re.search(u'<variable formalParameter="G">\\s*<connectionPointIn>.*?'
                      u'<connection refLocalId="(\\d+)"', seg, re.S)
        if not g:
            continue
        src = g.group(1)
        iv = re.search(u'<inVariable localId="%s"[^>]*>(.*?)</inVariable>' % src, t, re.S)
        bl = re.search(u'<block localId="%s" typeName="(\\w+)"' % src, t)
        if iv:
            e = re.search(u"<expression>([^<]*)</expression>", iv.group(1))
            who = e.group(1) if e else u"?invar?"
        elif bl:
            who = u"<%s>" % bl.group(1)
        else:
            who = u"localId=%s" % src
        ln = t[:m.start()].count(u"\n") + 1
        sys.stdout.write(u"  SEL localId=%-6s G <- %-24s (stroka %d)\n" % (bid, who, ln))


if __name__ == u"__main__":
    main()
