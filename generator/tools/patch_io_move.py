# -*- coding: utf-8 -*-
u"""PATCH_IO_MOVE -- set' I/O-portov pered ALU i podacha Rd_Data v registr.

P R I Ch I N A. Komanda IN A,(n) ne popadala v registr: vybor operanda dlya
ALU bral iz pamyati BAJT NOMERA PORTA (Mem[PC+1]), potomu chto dlya vseh
komand s operandom iz koda on odin i tot zhe. Dannye porta (Rd_Data iz
FB_IO_Ports) vyrabatyvalis' v seti 16, kotoraya stoit POSLE ALU i posle
zapisi registra, i nikuda ne podavalis'.

Ch T O  D E L A E M.
 1) Set' I/O-portov perenesena V P E R E D ALU (srazu posle pamyati): ona
    nuzhna tol ko adres porta (vImm) i A dlya zapisi, i teper ee rezul tat
    dostupen vyboru operanda.
 2) Dlya zapisi v port bеrem GVL_Regs.Rs_A (tekuushchee znachenie A), a ne
    vyhod registrovogo fajla -- tot vyhod uzhe soderzhit novoe znachenie.
 3) Pered vyborom operanda vveden mux: dlya IN A,(n) berem dannye porta,
    dlya vseh ostal nyh -- kak ranshe (pamyat' ili registr).
"""

import io
import sys

sys.stdout.reconfigure(encoding=u"utf-8")

P = r"generator\gen_z80.py"
t = io.open(P, encoding=u"utf-8").read()
n = 0

BEGIN = u"    # ================= 16. I/O-PORTY Z80 =================\n"
END = u"    # ================= 17. BIOS =================\n"
i = t.find(BEGIN)
j = t.find(END)
assert i > 0 and j > i, (i, j)
block = t[i:j]
t = t[:i] + t[j:]
n += 1

# vnutri bloka: A dlya zapisi -- iz sostoyaniya, a ne iz vyhoda FB
old_a = u'                    (u"D_Write", n16.invar(u"fbRF.A", y=120)),'
new_a = (u'                    #  dlya zapisi v port nuzhno T E K U Shch E E znachenie A:\n'
         u'                    #  vyhod registrovogo fajla k etomu momentu uzhe\n'
         u'                    #  soderzhit novoe (selektoru zapisi ono i nuzhno, a nam -- net).\n'
         u'                    (u"D_Write", n16.invar(u"GVL_Regs.Rs_A", y=120)),')
assert block.count(old_a) == 1
block = block.replace(old_a, new_a, 1)

# vstavlyaem pered ALU
ANCHOR = u"    # ================= 8. ALU =================\n"
assert t.count(ANCHOR) == 1
t = t.replace(ANCHOR, block + ANCHOR, 1)

# mux dannyh porta v vybor operanda ALU
old = (u'    c_src_mem = b_or(n8, F.COL_BLK, 330, c_rd8, c_mi)\n'
       u'    src1 = b_sel(n8, F.COL_BLK, 70, c_src_mem, c_sv, c_mv)')
new = (u'    c_src_mem = b_or(n8, F.COL_BLK, 330, c_rd8, c_mi)\n'
       u'    #  I N  A , ( n ): operand -- dannye porta, a NE nomer porta.\n'
       u'    #  Dlya etogo iz Mem[PC+1] uzhe izvlechen nomer porta, i set 16\n'
       u'    #  (ona teper stoit VYShE) otvechaet znacheniem porta.\n'
       u'    c8_in = n8.invar(u"vCtl_Is_IN", y=700)\n'
       u'    imm_eff = b_sel(n8, F.COL_BLK, 700, c8_in,\n'
       u'                     n8.invar(u"vIOData", y=700),\n'
       u'                     n8.invar(u"vImm", y=714))\n'
       u'    n8.outvar(u"vImmEff", imm_eff, x=F.COL_OUT, y=700)\n'
       u'    src1 = b_sel(n8, F.COL_BLK, 70, c_src_mem, c_sv,\n'
       u'                 n8.invar(u"vImmEff", y=744))')
assert t.count(old) == 1
t = t.replace(old, new, 1)
n += 1

old_pv = u'    p.var(u"vPCPlus1", u"WORD", u"PC + 1: adres operanda")'
new_pv = (u'    p.var(u"vPCPlus1", u"WORD", u"PC + 1: adres operanda")\n'
          u'    p.var(u"vImmEff", u"BYTE", u"operand dlya ALU: pamyat ili dannye porta")')
assert t.count(old_pv) == 1
t = t.replace(old_pv, new_pv, 1)
n += 1

io.open(P, u"w", encoding=u"utf-8").write(t)
print(u"patch_io_move: %d zamen" % n)
print(u"nonascii: %d" % sum(1 for c in t if ord(c) > 127))
