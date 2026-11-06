# -*- coding: utf-8 -*-
u"""gen_many_nets.py -- sozdaet POU s 5, 10 i 20 setyami dlya proverki.

Zapuskaetsya OBYChNYM Python. Nuzhno ponyat, perenosyat li CODESYS vse seti
FBD-POU ili est predel.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "generator"))
sys.path.insert(0, os.path.join(ROOT, "generator", "tools"))
import fbd_xml as F

SRC = os.path.join(ROOT, "src")

for n in (5, 10, 20):
    name = u"P%d" % n
    p = F.Pou(name, u"functionBlock", u"probnyy blok s %d setyami" % n)
    p.var_in(u"A", u"BYTE")
    p.var_in(u"B", u"BYTE")
    outs = []
    for k in range(n):
        outs.append(p.var_out(u"Y%d" % k, u"BYTE"))
    for k in range(n):
        net = p.network(u"SET %d" % k)
        a = net.invar(u"A", y=30)
        b = net.invar(u"B", y=60)
        an = net.block(u"AND", [(u"IN1", a), (u"IN2", b)], [u"OUT"],
                       x=F.COL_BLK, y=30)
        net.outvar(u"Y%d" % k, an, x=F.COL_OUT, y=30)
    path = os.path.join(SRC, u"%s.plcopenxml" % name)
    F.write_project(path, [p], name)
    cnt = F.count_elements(path)
    print(u"%s: setey=%d blokov=%d vyhodov=%d" % (name, n, cnt[0], n))
