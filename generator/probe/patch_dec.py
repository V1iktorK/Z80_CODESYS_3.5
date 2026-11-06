# -*- coding: utf-8 -*-
u"""patch_dec.py -- dobavlyaet v FB_DecoderZ80 signaly Ctl_IncDec i Ctl_Cond_Is_Z.

Ctl_IncDec -- TRUE dlya komand INC/DEC (opkody x4/x5 i 3C/3D): nuzhen ALU,
              chtoby podstavit' operand = 1.

Realizatsiya: (IR and 0Fh) = 4 ili 5, ili IR = 3C ili 3D.
"""

import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
GEN = os.path.join(ROOT, "generator", "gen_z80.py")

t = io.open(GEN, "r", encoding="utf-8").read()

# --- 1. obyavlenie vhoda/vyhoda -------------------------------------------------
old = u'''    for v in (u"Ctl_Sel_Dst", u"Ctl_Sel_Src", u"Ctl_ALU_Op", u"Ctl_Cond"):
        p.var_out(v, u"BYTE")'''
new = u'''    for v in (u"Ctl_Sel_Dst", u"Ctl_Sel_Src", u"Ctl_ALU_Op", u"Ctl_Cond"):
        p.var_out(v, u"BYTE")
    p.var_out(u"Ctl_IncDec", u"BOOL", u"TRUE dlya INC/DEC: operand = 1")'''
assert old in t, u"ne najdeny vyhody dekodera"
t = t.replace(old, new)

# --- 2. vychislenie v seti dekodera ---------------------------------------------
old2 = u'''    is_alu = b_and(n, F.COL_BLK2 + 160, y + 520, n4,
                   n.const(u"1", y=y + 534))'''
new2 = u'''    is_alu = b_and(n, F.COL_BLK2 + 160, y + 520, n4,
                   n.const(u"1", y=y + 534))
    # --- Ctl_IncDec: opkody x4/x5 (INC/DEC r) i 3C/3D (INC/DEC A) ---
    g5 = n.block(u"EQ", [(PIN1, grp), (PIN2, n.const(u"16#04", y=y + 574))],
                 [POUT], x=F.COL_BLK2, y=y + 560)
    g6 = n.block(u"EQ", [(PIN1, grp), (PIN2, n.const(u"16#05", y=y + 614))],
                 [POUT], x=F.COL_BLK2, y=y + 600)
    g45 = b_or(n, F.COL_BLK2 + 160, y + 580, g5, g6)
    a1 = eq_const(0x3C, F.COL_BLK2 + 160, y + 640)
    a2 = eq_const(0x3D, F.COL_BLK2 + 160, y + 680)
    a12 = b_or(n, F.COL_BLK2 + 320, y + 660, a1, a2)
    incdec = b_or(n, F.COL_BLK2 + 480, y + 620, g45, a12)'''
assert old2 in t, u"ne najdena tochka vstavki v dekodere"
t = t.replace(old2, new2)

# --- 3. dobavit' v spisok vyhodov ----------------------------------------------
old3 = u'''        (u"Ctl_Cond", cond_any, F.COL_OUT),
    ]'''
new3 = u'''        (u"Ctl_Cond", cond_any, F.COL_OUT),
        (u"Ctl_IncDec", incdec, F.COL_OUT),
    ]'''
assert old3 in t, u"ne najden spisok vyhodov dekodera"
t = t.replace(old3, new3)

io.open(GEN, "w", encoding="utf-8").write(t)
print(u"PATCH DEC OK")
