# -*- coding: utf-8 -*-
u"""patch_reginit.py -- dobavlyaet v FB_RegFileZ80 port INICIALIZACII registrov.

ZACheM. Testam (i sbrosu) nuzhno zadat proizvol'nye znacheniya vseh registrov.
Bez etogo nel'zya proverit', naprimer, LD (HL),r -- dlya etogo nuzhno zaranee
ustanovit H i L.

KAK. Dobavlyaem dva vhoda:
    Init_En      : BOOL -- rezhim initsializatsii
    Init_Sel_Dst : BYTE -- nomer registra dlya initsializatsii
Dannye po-prezhnemu podayutsya cherez Wr_Val (glavnaya shema beret ih iz
massiva GVL_InitRegs.Init_Vals). Interfejs rasshiren minimal'no.

PRAVILO PROEKTA: kazhdoe potreblenie signala -- otdel'nyy ekzemplyar invar
ili otdel'nyy vyhod bloka (inache fan-out i CODESYS molcha vybrasyvaet POU).
Zdes Init_En upravlyaet dvumya raz'temami i odnim SEL -- eto tri raznyh
potrebleniya odnogo vhoda POU, chto nedopustimo, poetomu Init_En chitaetsya
TREMY otdel'nymi invar.
"""

import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
GEN = os.path.join(ROOT, "generator", "gen_z80.py")

t = io.open(GEN, "r", encoding="utf-8").read()

# --- 1. novye vhody ------------------------------------------------------------
old = u'''    mem = p.var_in(u"Mem_Rd", u"BYTE", u"znachenie (HL) s shiny")
    imm = p.var_in(u"Imm", u"BYTE", u"neposredstvennyj operand")'''
new = u'''    mem = p.var_in(u"Mem_Rd", u"BYTE", u"znachenie (HL) s shiny")
    imm = p.var_in(u"Imm", u"BYTE", u"neposredstvennyj operand")
    init_en = p.var_in(u"Init_En", u"BOOL",
                       u"rezhim initsializatsii registrov")
    init_dst = p.var_in(u"Init_Sel_Dst", u"BYTE",
                        u"nomer registra pri initsializatsii")'''
assert old in t, u"ne najdeny vhody RegFile"
t = t.replace(old, new)

# --- 2. pereklyuchatel' rezhima v seti zapisi ----------------------------------
old2 = u'''    v_wok = b_and(nw, F.COL_BLK2, 60, v_wen, v_nclr)
    y = 20
    for k in range(16):
        ck = nw.const(u"%d" % k, y=y + 14)
        eq = b_eq(nw, F.COL_BLK2 + 160, y, c_sd, ck)
        w = b_and(nw, F.COL_BLK2 + 320, y, v_wok, eq)
        nw.outvar(u"WE_%d" % k, w, x=F.COL_OUT + 300, y=y)
        y += 55'''
new2 = u'''    v_wok = b_and(nw, F.COL_BLK2, 60, v_wen, v_nclr)
    # Init_En chitaem TREMya otdel'nymi ekzemplyarami (pravilo pro fan-out):
    #   i1 -- v AND "rezhim init", i2 -- v OR, i3 -- v SEL
    c_ien1 = nw.invar(init_en, y=420)
    c_ien2 = nw.invar(init_en, y=460)
    c_ien3 = nw.invar(init_en, y=500)
    i_ok = b_and(nw, F.COL_BLK2, 420, c_ien1, v_wok)
    w_or = b_or(nw, F.COL_BLK2 + 160, 440, i_ok, v_wok)
    # nomer registra: rezhim init -- Init_Sel_Dst, inache Ctl_Sel_Dst
    c_idst = nw.invar(init_dst, y=540)
    dst_eff = b_sel(nw, F.COL_BLK2 + 160, 540, c_ien3, c_sd, c_idst)
    y = 20
    for k in range(16):
        ck = nw.const(u"%d" % k, y=y + 14)
        eq = b_eq(nw, F.COL_BLK2 + 320, y, dst_eff, ck)
        w = b_and(nw, F.COL_BLK2 + 480, y, w_or, eq)
        nw.outvar(u"WE_%d" % k, w, x=F.COL_OUT + 560, y=y)
        y += 55'''
assert old2 in t, u"ne najdena set' zapisi RegFile"
t = t.replace(old2, new2)

io.open(GEN, "w", encoding="utf-8").write(t)
print(u"PATCH REGINIT OK")
