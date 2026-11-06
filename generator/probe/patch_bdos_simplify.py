# -*- coding: utf-8 -*-
u"""patch_bdos_simplify.py -- ubiraet iz FB_CPM_BDOS slozhnoe skleivanie Ret_Mode.

PRICHINA POTERI BLOKOV (izolirovana sravneniem elementov do/posle importa):
    seti 1..4 iz 10 ne doehalis polnost yu -- propali bloki OR i AND,
    kotorye sobirali vyhod Ret_Mode iz sravneniy, opredelennyh v DRUGIH setyah.

Reshenie: ubrat eto skleivanie iz FBD. Vopros "chto delat s pamyat yu" --
eto ne vychislenie, a vybor vetki programmy, i emu mesto v ST-drajvere,
kotoryy i tak upravlyaet vsem protsessom. V FB_CPM_BDOS ostavlyaem
PLOSKUYU TABLITsU sravneniy (EQ po nomeru funktsii) i vyhody dlya konsoli --
eto chitaetsya i perenositsya bez poter.

Udalyayutsya vyhody Ret_Mode, Ret_Val i Set_DMA, F_Size, Out_Mode;
vse oni byli dlya ST-drajvera i teper ne nuzhny.
"""

import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
GEN = os.path.join(ROOT, "generator", "gen_z80.py")

t = io.open(GEN, "r", encoding="utf-8").read()

# --- 1. ubrat obyavleniya lishnih vyhodov --------------------------------------
old = u'''    p.var_out(u"Out_Mode", u"BYTE",
              u"rezhim vyvoda: 0 net, 1 odin simvol, 2 stroka do $")
    p.var_out(u"Ret_Mode", u"BYTE",
              u"chto delat s pamyat yu: 0 net, 1 udalit, 2 sozdat, "
              u"3 ustanovit DMA, 4 razmer fajla, 5 karta blokov")
    p.var_out(u"Ret_Val", u"WORD", u"gotovyy otvet dlya HL")'''
new = u'''    p.var_out(u"Out_Mode", u"BYTE",
              u"rezhim vyvoda: 0 net, 1 odin simvol, 2 stroka do $")'''
assert old in t, u"ne najdeny obyavleniya vyhodov BDOS"
t = t.replace(old, new, 1)

# --- 2. ubrat skleivanie Ret_Mode / Ret_Val ------------------------------------
old2 = u'''    n4.outvar(u"Set_DMA", f26, x=F.COL_OUT, y=30)

    # --- Ret_Mode: kakuyu operatsiyu s pamyat yu vypolnit ST-drajveru ---
    f19m = b_and(n4, F.COL_BLK2 + 160, 230, f19,
                 n4.const(u"1", y=244))
    f22m = b_and(n4, F.COL_BLK2 + 160, 270, f22,
                 n4.const(u"2", y=284))
    f26m = b_and(n4, F.COL_BLK2 + 160, 310, f26,
                 n4.const(u"3", y=324))
    f35m = b_and(n4, F.COL_BLK2 + 160, 350, f35,
                 n4.const(u"4", y=364))
    f27m = b_and(n4, F.COL_BLK2 + 160, 390,
                 b_eq(n4, F.COL_BLK2, 390, c_c4, n4.const(u"27", y=404)),
                 n4.const(u"5", y=414))
    rm1 = b_or(n4, F.COL_BLK2 + 320, 250, f19m, f22m)
    rm2 = b_or(n4, F.COL_BLK2 + 320, 330, rm1, f26m)
    rm3 = b_or(n4, F.COL_BLK2 + 320, 370, rm2, f35m)
    rm4 = b_or(n4, F.COL_BLK2 + 480, 390, rm3, f27m)
    n4.outvar(u"Ret_Mode", rm4, x=F.COL_OUT + 300, y=390)

    # --- 32 F_USERNUM: otvet 0 (polzovatel 0) ---
    f32v = b_and(n4, F.COL_BLK2 + 160, 430, f32, n4.const(u"0", y=444))
    f32w = b_b2w(n4, F.COL_BLK2 + 320, 430, f32v)
    n4.outvar(u"Ret_Val", f32w, x=F.COL_OUT + 300, y=430)'''
new2 = u'''    n4.outvar(u"Set_DMA", f26, x=F.COL_OUT, y=30)'''
assert old2 in t, u"ne najden blok Ret_Mode"
t = t.replace(old2, new2, 1)

# --- 3. ubrat seti, kotorye chitali eti vyhody ---------------------------------
old3 = t[t.index(u"    # ================= SET 6: OTDEL NYE SETI"):t.index(u"    # ================= 18. PEREKhVAT BDOS")]
t = t.replace(old3, u"", 1)

io.open(GEN, "w", encoding="utf-8").write(t)
print(u"PATCH BDOS_SIMPLIFY OK")
