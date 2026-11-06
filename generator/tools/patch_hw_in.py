# -*- coding: utf-8 -*-
u"""PATCH_HW_IN -- podaet testovyy obraz vhodov PLK v bufery Z80.

Z A Ch E M. V etoj ustanovke moduli vvoda ne skonfigurirovany (%IX ne privyazan,
sm. zhurnal, preduprezhdeniya C373), poetomu PLC_DI_0..7 i PLC_AI_0/1 vsegda
ravny nulyu. Stend CP/M podaet testovyy obraz v GVL_HW_IO (A5h po diskretnym i
1234h/5678h po analogovym), i ran'she on nichem ne byl svyazan s buferami --
iz-za etogo vse 14 proverok gruppy IO/HW chitali nol.

Ch T O  D E L A E M: vhod FB_HW_IO_PLC sobiraetsya iz dvuh istochnikov:
    diskretnye: OR(fizicheskiy kanal, testovyy obraz);
    analogovye: esli testovoe znachenie ne nol -- ono, inache kanal.
Na real noj sborke testovyy obraz raven nulyu i nichego ne menyaet.
"""

import io
import sys

sys.stdout.reconfigure(encoding=u"utf-8")

P = r"generator\gen_z80.py"
t = io.open(P, encoding=u"utf-8").read()
n = 0


def rep(old, new):
    global t, n
    assert t.count(old) == 1, (t.count(old), repr(old[:80]))
    t = t.replace(old, new, 1)
    n += 1


old0 = u'                   [(u"DI_0", n15.invar(u"PLC_DI_0", y=30)),'
new0 = (u'                   [#  D I S K R E T N Y E  V H O D Y: fizicheskiy kanal ILI\n'
        u'                    #  testovyy obraz. V etoj ustanovke moduli vvoda ne\n'
        u'                    #  skonfigurirovany (%IX ne privyazan), poetomu %IX vsegda 0,\n'
        u'                    #  i edinstvennyy istochnik -- GVL_HW_IO. Na real noj sborke\n'
        u'                    #  testovyy obraz raven nulyu, i OR nichego ne menyaet.\n'
        u'                    (u"DI_0", b_or(n15, F.COL_BLK, 30,\n'
        u'                                   n15.invar(u"PLC_DI_0", y=30),\n'
        u'                                   n15.invar(u"GVL_HW_IO.DI_0", y=45))),')
rep(old0, new0)

for k in range(1, 8):
    old = (u'                    (u"DI_%d", n15.invar(u"PLC_DI_%d", y=%d)),'
           % (k, k, 30 + k * 30))
    new = (u'                    (u"DI_%d", b_or(n15, F.COL_BLK, %d,\n'
           u'                                   n15.invar(u"PLC_DI_%d", y=%d),\n'
           u'                                   n15.invar(u"GVL_HW_IO.DI_%d", y=%d))),'
           % (k, 30 + k * 30, k, 30 + k * 30, k, 45 + k * 30))
    rep(old, new)

oldA = (u'                    (u"AI_0", n15.invar(u"PLC_AI_0", y=270)),\n'
        u'                    (u"AI_1", n15.invar(u"PLC_AI_1", y=300)),')
newA = (u'                    #  A N A L O G O V Y E  V H O D Y: esli testovoe znachenie\n'
        u'                    #  zadano (ne nol) -- berem ego, inache fizicheskiy kanal.\n'
        u'                    (u"AI_0", b_sel(n15, F.COL_BLK, 270,\n'
        u'                                    b_eq(n15, F.COL_BLK, 330,\n'
        u'                                         n15.invar(u"GVL_HW_IO.AI_0", y=330),\n'
        u'                                         n15.const(u"0", y=344)),\n'
        u'                                    n15.invar(u"PLC_AI_0", y=270),\n'
        u'                                    n15.invar(u"GVL_HW_IO.AI_0", y=300),\n'
        u'                                    tip=u"INT")),\n'
        u'                    (u"AI_1", b_sel(n15, F.COL_BLK, 400,\n'
        u'                                    b_eq(n15, F.COL_BLK, 460,\n'
        u'                                         n15.invar(u"GVL_HW_IO.AI_1", y=460),\n'
        u'                                         n15.const(u"0", y=474)),\n'
        u'                                    n15.invar(u"PLC_AI_1", y=400),\n'
        u'                                    n15.invar(u"GVL_HW_IO.AI_1", y=430),\n'
        u'                                    tip=u"INT")),')
rep(oldA, newA)

io.open(P, u"w", encoding=u"utf-8").write(t)
print(u"patch_hw_in: %d zamen" % n)
print(u"nonascii: %d" % sum(1 for c in t if ord(c) > 127))
