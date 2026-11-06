# -*- coding: utf-8 -*-
u"""PATCH_FETCH2 -- vyborka i zashchelka IR v ODNOJ seti.

V pervoj versii vyborka stoyala v otdel'noj seti VYShE, a kod komandy peredavalsya
cherez peremennuyu vFetchCode. Eto ne rabotaet: chuzhaya set' vidaet znachenie
proshlogo skana, i v IR popadal kod, vybrannyj ran'she (izmereno: u T17 v IR
okazalsya 55h -- dannye operanda proshlogo testa).

P R A V I L O  P R O E K T A: vyhod bloka chitaetsya v T O J  Zh E  seti, gde on
vychislen, -- tak sdelano dlya fbALU.Y i fbMem.Rd_Data. Poetomu vyzov fbFetch
perenesen vnutr' seti zashchelki IR, pered nej.
"""

import io
import sys

sys.stdout.reconfigure(encoding=u"utf-8")

P = r"generator\gen_z80.py"
t = io.open(P, encoding=u"utf-8").read()
n = 0


def rep(old, new):
    global t, n
    assert t.count(old) == 1, (t.count(old), repr(old[:90]))
    t = t.replace(old, new, 1)
    n += 1


# ubiram otdel'nuyu set' vyborki
i = t.find(u'    n3a = p.network(u"SET 2b: VYBORKA: chitaem kod komandy po PC")\n')
j = t.find(u'    # ================= 3. FETCH =================\n')
assert i > 0 and j > i, (i, j)
t = t[:i] + t[j:]
n += 1

# perenosim vyzov fbFetch vnutr' seti zashchelki
rep(u'    n3 = p.network(u"SET 3: VBORKA: kod komandy v IR")\n'
    u'    c_irq = n3.invar(u"fbIR.Q", y=210)\n'
    u'    n3.outvar(u"GVL_PLCVisu.IR", c_irq, x=F.COL_OUT, y=210)\n'
    u'    n3.block(u"FB_Reg8Latch",\n'
    u'             [(u"D", n3.invar(u"vFetchCode", y=30)),',
    u'    #  V Y B O R K A  I  Z A Shch E L K A  -- V  O D N O J  S E T I.\n'
    u'    #  Vyhod bloka chitaetsya v toj zhe seti, gde on vychislen (pravilo\n'
    u'    #  proekta). Otdel naya set' vyborki vidavala znachenie proshlogo skana,\n'
    u'    #  i v IR popadal kod predydushchej komandy.\n'
    u'    n3 = p.network(u"SET 3: VYBORKA: kod komandy v IR")\n'
    u'    #  O T D E L \' N Y J  E K Z E M P L Ya R  P A M Ya T I  T O L \' K O  D L Ya  K O D A.\n'
    u'    #  U FB_Memory64K net svoego sostoyaniya (massiv v GVL_Memory), poetomu\n'
    u'    #  vtoroj ekzemplyar bezopasen; pishet tol ko osnovnoj.\n'
    u'    n3.block(u"FB_Memory64K",\n'
    u'              [(u"PC", n3.invar(u"GVL_Regs.Rs_PC", y=430)),\n'
    u'               (u"Addr", n3.const(u"WORD#0", y=470)),\n'
    u'               (u"Rd", n3.const(u"FALSE", y=510)),\n'
    u'               (u"Wr", n3.const(u"FALSE", y=550)),\n'
    u'               (u"D_Bus", n3.const(u"BYTE#0", y=590)),\n'
    u'               (u"SP_Addr", n3.const(u"WORD#0", y=630)),\n'
    u'               (u"SP_Rd", n3.const(u"FALSE", y=670)),\n'
    u'               (u"SP_Wr", n3.const(u"FALSE", y=710)),\n'
    u'               (u"SP_Data", n3.const(u"WORD#0", y=750)),\n'
    u'               (u"Wr_Addr", n3.const(u"WORD#0", y=790)),\n'
    u'               (u"Wr_Data", n3.const(u"BYTE#0", y=830)),\n'
    u'               (u"Wr_Stb", n3.const(u"FALSE", y=870))],\n'
    u'              [u"D_Out", u"Rd_Data", u"Op_Word", u"SP_Out", u"Bus_Drv"],\n'
    u'              x=F.COL_BLK2, y=430, instance=u"fbFetch")\n'
    u'    n3.outvar(u"vFetchCode", n3.invar(u"fbFetch.D_Out", y=30),\n'
    u'               x=F.COL_OUT, y=400)\n'
    u'    c_irq = n3.invar(u"fbIR.Q", y=210)\n'
    u'    n3.outvar(u"GVL_PLCVisu.IR", c_irq, x=F.COL_OUT, y=210)\n'
    u'    n3.block(u"FB_Reg8Latch",\n'
    u'             [(u"D", n3.invar(u"fbFetch.D_Out", y=340)),')

io.open(P, u"w", encoding=u"utf-8").write(t)
print(u"patch_fetch2: %d zamen" % n)
print(u"nonascii: %d" % sum(1 for c in t if ord(c) > 127))
