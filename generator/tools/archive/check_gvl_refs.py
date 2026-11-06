# -*- coding: utf-8 -*-
u"""Proverka: vse li ssylki GVL_x.imya sushchestvuyut v deklaraciyah GVL.

ZAPUSKAT SISTEMNYM PYTHON 3.

ZADAChA. Kompilyator daet "C4: 'Ctl_Is_CALL' ne yavlyaetsya komponentom
'GVL_Control'": shema ssylaetsya na GVL_Control.Ctl_Is_CALL, a v GVL_Control
takogo imeni net. Eto tot zhe klass oshibki, chto neobyavlennye ekzemplyary i
signaly, tolko urovnem vyshe -- mezhdu POU i GVL.

Proverka idet po VSEM shemam i vsem GVL srazu, poetomu nahodit vse
nesootvetstviya za odin progon, a ne po odnomu soobshcheniyu kompilyatora.
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(os.path.dirname(HERE)), u"src")


def gvl_members():
    out = {}
    for f in sorted(os.listdir(SRC)):
        if not f.endswith(u".gvl"):
            continue
        name = f[:-4]
        t = io.open(os.path.join(SRC, f), encoding=u"utf-8").read()
        # ubiraem kommentarii, chtoby ne putat ih s obyavleniyami
        t = re.sub(u"\\(\\*.*?\\*\\)", u" ", t, flags=re.S)
        out[name] = set(re.findall(u"(?m)^\\s*(\\w+)\\s*:", t))
    return out


def main():
    gvls = gvl_members()
    sys.stdout.write(u"GVL v proekte: %d, imen v nih: %d\n\n"
                     % (len(gvls), sum(len(v) for v in gvls.values())))

    ref = re.compile(u"<expression>(GVL_[A-Za-z0-9_]+)\\.([A-Za-z0-9_]+)</expression>")
    bad = {}
    total = 0
    for f in sorted(os.listdir(SRC)):
        if not f.endswith(u".plcopenxml"):
            continue
        t = io.open(os.path.join(SRC, f), encoding=u"utf-8").read()
        for m in ref.finditer(t):
            total += 1
            g, mem = m.group(1), m.group(2)
            if g not in gvls:
                bad.setdefault(f, set()).add(u"%s.%s (net takogo GVL)" % (g, mem))
            elif mem not in gvls[g]:
                bad.setdefault(f, set()).add(u"%s.%s" % (g, mem))

    sys.stdout.write(u"vsego ssylok GVL_x.y: %d\n\n" % total)
    if not bad:
        sys.stdout.write(u"VSE SSYLKI KORREKTNY\n")
        return 0
    for f in sorted(bad):
        sys.stdout.write(u"%-24s BIITYH SSYLOK: %d\n" % (f, len(bad[f])))
        for s in sorted(bad[f]):
            sys.stdout.write(u"      %s\n" % s)
    return 1


if __name__ == u"__main__":
    sys.exit(main())
