# -*- coding: utf-8 -*-
u"""Najti mertvye chteniya v PLC_PRG: invar-est' , a potrebiteley net.

ZAPUSKAT SISTEMNYM PYTHON 3.

ZADAChA. Uzhe odna takaya ssylka (vCtl_Cond tipa BYTE) dayovala oshibku C32,
hotya ni v chem ne uchastvovala. Nado najti vse ostalnye: element invar
sozdan, no ego localId nikem ne potreblyaetsya.

Kak schitaem: sobiraem vse localId elementov, zatem vse ssylki
<connection refLocalId="N">; esli invar nikto ne ssylaet -- on mertvyy.
"""
import io
import os
import re
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(ROOT, u"src")


def find_all(node, local):
    out = []
    for ch in node.iter():
        if isinstance(ch.tag, str) and (ch.tag == local or ch.tag.endswith(u"}" + local)):
            out.append(ch)
    return out


def main():
    names = sys.argv[1:] or [u"PLC_PRG"]
    for nm in names:
        path = os.path.join(SRC, nm + u".plcopenxml")
        t = io.open(path, encoding=u"utf-8").read()
        root = ET.parse(path).getroot()
        pou = list(find_all(root, u"pou"))[0]

        used = set(re.findall(u'<connection refLocalId="(\\d+)"', t))
        sys.stdout.write(u"=== %s ===\n" % nm)
        dead = 0
        for iv in find_all(pou, u"inVariable"):
            i = iv.get(u"localId")
            if i in used:
                continue
            expr = u""
            for e in find_all(iv, u"expression"):
                expr = u"".join(e.itertext())
            sys.stdout.write(u"   MERTVYY invar: %s\n" % expr)
            dead += 1
        sys.stdout.write(u"   mertvyh: %d\n\n" % dead)


if __name__ == u"__main__":
    main()
