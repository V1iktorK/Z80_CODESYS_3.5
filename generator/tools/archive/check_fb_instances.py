# -*- coding: utf-8 -*-
u"""Diagnostika: sverit obyavleniya ekzemplyarov FB s real'nymi tipami.

ZAPUSKAT SISTEMNYM PYTHON 3.

ZADAChA. Kompilyator daet oshibki vida
    'fbAO1Lo' ne yavlyaetsya ekzemplyarom 'FB_Reg16'
    Neizvestnyy tip: 'fbAO1Lo.Q'
Znachit gde-to ekzemplyar ob''yavlen s odnim tipom, a ispolzuetsya kak drugoj.
Nado najti vse takie nesootvetstviya.
"""
import io
import os
import re
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(os.path.dirname(HERE)), u"src")
sys.path.insert(0, HERE)

TC6 = u"{http://www.plcopen.org/xml/tc6_0200}"


def find_all(node, local):
    out = []
    for ch in node.iter():
        if isinstance(ch.tag, str) and (ch.tag == local or ch.tag.endswith(u"}" + local)):
            out.append(ch)
    return out


def main():
    # 1) vse tipy, kotorye est v proekte
    known = set()
    for f in sorted(os.listdir(SRC)):
        if f.endswith(u".plcopenxml"):
            known.add(os.path.splitext(f)[0])
    print(u"tipov POU v proekte: %d" % len(known))

    # 2) obyavleniya ekzemplyarov v kazhdom POU
    for f in sorted(os.listdir(SRC)):
        if not f.endswith(u".plcopenxml"):
            continue
        root = ET.parse(os.path.join(SRC, f)).getroot()
        for pou in find_all(root, u"pou"):
            name = pou.get(u"name")
            iface = find_all(pou, u"interface")
            if not iface:
                continue
            bad = []
            for v in find_all(iface[0], u"variable"):
                derived = None
                for d in find_all(v, u"derived"):
                    derived = d.get(u"name")
                if derived and derived.startswith(u"FB_"):
                    if derived not in known:
                        bad.append((v.get(u"name"), derived, u"NET TAKOGO POU"))
            if bad:
                print(u"!!! %s:" % name)
                for nm, tp, why in bad:
                    print(u"      %-14s : %-16s %s" % (nm, tp, why))
    print(u"gotovo")


if __name__ == u"__main__":
    main()
