# -*- coding: utf-8 -*-
u"""Pochinit' hvosty strok, isporchennye patch_fb_outputs.py.

ZAPUSKAT SISTEMNYM PYTHON 3.

ChTO SLUChILOS. Shablon zameny zadel tolko nachalo mnogostrochnyh vyzovov
outvar, i v fajle ostalis "hvosty" vida
    n7.outvar(u"vFetch", n7.invar(u"vMem_D_Out", y=60), y=400), x=F.COL_OUT, y=400)
Eto oskolki prezhnego vyzova. Ih nado privesti k normalnomu vidu:
    n7.outvar(u"vFetch", n7.invar(u"vMem_D_Out", y=60), x=F.COL_OUT, y=400)

Skript ishchet stroki, gde posle zakryvayushchey skobki idet zapyataya i
prodolzhenie s x=F.COL_OUT, i ubiraet lishnee.
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GEN = os.path.join(ROOT, u"generator", u"gen_z80.py")

#  hvost vida: ") , y=NNN), x=F.COL_OUT, y=NNN)"  ->  ", x=F.COL_OUT, y=NNN)"
PAT = re.compile(u'\\)\\s*,\\s*y=\\d+\\)\\s*,\\s*(x=F\\.COL_OUT[^\\n]*\\))\\s*$')


def main():
    lines = io.open(GEN, encoding=u"utf-8").read().split(u"\n")
    n = 0
    for i, ln in enumerate(lines):
        if u".outvar(" in ln or ln.lstrip().startswith(u"x="):
            m = PAT.search(ln)
            if m:
                lines[i] = PAT.sub(u', ' + u'\\1', ln)
                sys.stdout.write(u"%5d: %s\n" % (i + 1, lines[i].strip()))
                n += 1
    io.open(GEN, u"w", encoding=u"utf-8").write(u"\n".join(lines))
    sys.stdout.write(u"\nispravleno strok: %d\n" % n)


if __name__ == u"__main__":
    main()
