# -*- coding: utf-8 -*-
u"""patch_prg_hw_fix.py -- ispravlyaet fan-out u FB_HW_IO_PLC.

Osnovnoe pravilo proekta: vyhod bloka ispolzuetsya ODIN raz. U FB_HW_IO_PLC
vyhody In_DI/In_AI0/In_AI1 nuzhny i dlya buferov GVL_HW_Buffer, i (potom)
dlya vyzova FB_IO_Ports. Poetomu markiruem ih:
    vyhod -> lokalnaya peremennaya POU -> potrebiteli chitayut po imeni.
To zhe dlya vyhodov Out_* -- oni idut v set 16.
"""

import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
GEN = os.path.join(ROOT, "generator", "gen_z80.py")

t = io.open(GEN, "r", encoding="utf-8").read()

old = u'''    n15.outvar(u"GVL_HW_Buffer.HW_In_DI", hw.out(u"In_DI"),
               x=F.COL_OUT + 600, y=30)
    n15.outvar(u"GVL_HW_Buffer.HW_In_AI0", hw.out(u"In_AI0"),
               x=F.COL_OUT + 600, y=70)
    n15.outvar(u"GVL_HW_Buffer.HW_In_AI1", hw.out(u"In_AI1"),
               x=F.COL_OUT + 600, y=110)'''
new = u'''    n15.outvar(u"vInDi", hw.out(u"In_DI"), x=F.COL_OUT + 600, y=30)
    n15.outvar(u"vInAI0", hw.out(u"In_AI0"), x=F.COL_OUT + 600, y=70)
    n15.outvar(u"vInAI1", hw.out(u"In_AI1"), x=F.COL_OUT + 600, y=110)
    n15.outvar(u"vOutDO", hw.out(u"Out_DO"), x=F.COL_OUT + 600, y=440)
    n15.outvar(u"vOutAO0", hw.out(u"Out_AO0"), x=F.COL_OUT + 600, y=470)
    n15.outvar(u"vOutAO1", hw.out(u"Out_AO1"), x=F.COL_OUT + 600, y=500)'''
assert old in t, u"ne najden blok vyhodov seti 15"
t = t.replace(old, new, 1)

io.open(GEN, "w", encoding="utf-8").write(t)
print(u"PATCH PRG_HW_FIX OK")
