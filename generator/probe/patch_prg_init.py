# -*- coding: utf-8 -*-
u"""patch_prg_init.py -- podklyuchaet GVL_InitRegs k glavnoy sheme.

Chto menyaetsya v PLC_PRG:
  * v oba vyzova FB_RegFileZ80 dobavlyayutsya vhody Init_En i Init_Sel_Dst;
  * v seti zapisi (nomer 10) Wr_Val teper vybiraetsya: v rezhime
    initsializatsii -- Init_Vals[SEL_DST], inache -- rezultat ALU.

Kak vybrat Init_Vals[k] bez fan-out: Init_Vals[k] chitaetsya OTDELNYM
ekzemplyarom invar dlya kazhdogo k, i dalee cepochka SEL po Init_Sel_Dst
(ne po Init_En -- Init_Sel_Dst uzhe nuzhen dlya Init_Sel_Dst vyzova,
poetomu ego chitaem otdel nym ekzemplyarom).
"""

import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
GEN = os.path.join(ROOT, "generator", "gen_z80.py")

t = io.open(GEN, "r", encoding="utf-8").read()

# --- 1. set' chteniya registrov: dobavit Init_En i Init_Sel_Dst --------------
old1 = u'''              (u"Mem_Rd", n5.invar(u"vMemDrv", y=270)),
              (u"Imm", n5.invar(u"vImm", y=310))],
             [u"Src_Val", u"A", u"B", u"C", u"D", u"E", u"H", u"L", u"F",
              u"Sa", u"Sb", u"Sc", u"Sd", u"Se", u"Sh", u"Sl", u"Sf",
              u"Addr_HL"],
             x=F.COL_BLK2, y=30, instance=u"fbRFRd")'''
new1 = u'''              (u"Mem_Rd", n5.invar(u"vMemDrv", y=270)),
              (u"Imm", n5.invar(u"vImm", y=310)),
              (u"Init_En", n5.invar(u"GVL_InitRegs.Init_En", y=350)),
              (u"Init_Sel_Dst", n5.invar(u"GVL_InitRegs.Init_Sel_Dst", y=390))],
             [u"Src_Val", u"A", u"B", u"C", u"D", u"E", u"H", u"L", u"F",
              u"Sa", u"Sb", u"Sc", u"Sd", u"Se", u"Sh", u"Sl", u"Sf",
              u"Addr_HL"],
             x=F.COL_BLK2, y=30, instance=u"fbRFRd")'''
assert old1 in t, u"ne najden vyzov fbRFRd"
t = t.replace(old1, new1)

# --- 2. set' zapisi registrov: dobavit Init_En, Init_Sel_Dst i vybor Wr_Val ---
old2 = u'''    n10.block(u"FB_RegFileZ80",
              [(u"Sel_Dst", n10.invar(u"GVL_Control.Ctl_Sel_Dst", y=30)),
               (u"Sel_Src", n10.invar(u"GVL_Control.Ctl_Sel_Src", y=70)),
               (u"Wr_Val", n10.invar(u"vY", y=110)),
               (u"Wr_En", n10.invar(u"GVL_Control.Ctl_Wr_Enable", y=150)),
               (u"Clk", n10.invar(u"fbClock.Clk_Exec", y=190)),
               (u"CLR", n10.invar(u"GVL_Control.Emu_Reset", y=230)),
               (u"Mem_Rd", n10.invar(u"vMemDrv", y=270)),
               (u"Imm", n10.invar(u"vImm", y=310))],'''
new2 = u'''    # --- vybor dannye dlya zapisi: init ili rezultat ALU ---
    # Cepochka SEL po Init_Sel_Dst: kazhdyy Init_Vals[k] chitaetsya OTDELNYM
    # ekzemplyarom (pravilo pro fan-out), a Init_Sel_Dst -- otdel nym ot togo,
    # kotoryy uhodit v Init_Sel_Dst vyzova RegFile.
    c_isd = n10.invar(u"GVL_InitRegs.Init_Sel_Dst", y=600)
    val_cases = []
    for k in range(16):
        ck = n10.const(u"%d" % k, y=640 + k * 10)
        cond = b_eq(n10, F.COL_BLK, 640 + k * 34, c_isd, ck)
        cval = n10.invar(u"GVL_InitRegs.Init_Vals[%d]" % k, y=650 + k * 34)
        val_cases.append((cond, cval))
    wr_init = sel_chain(n10, c_isd, n10.invar(u"GVL_InitRegs.Init_Vals[15]", y=1200),
                        val_cases, x=F.COL_BLK2, y0=640, ystep=34)
    wr_val = b_sel(n10, F.COL_BLK2 + 320, 110,
                   n10.invar(u"GVL_InitRegs.Init_En", y=1300),
                   n10.invar(u"vY", y=1340), wr_init)
    n10.block(u"FB_RegFileZ80",
              [(u"Sel_Dst", n10.invar(u"GVL_Control.Ctl_Sel_Dst", y=30)),
               (u"Sel_Src", n10.invar(u"GVL_Control.Ctl_Sel_Src", y=70)),
               (u"Wr_Val", wr_val),
               (u"Wr_En", n10.invar(u"GVL_Control.Ctl_Wr_Enable", y=150)),
               (u"Clk", n10.invar(u"fbClock.Clk_Exec", y=190)),
               (u"CLR", n10.invar(u"GVL_Control.Emu_Reset", y=230)),
               (u"Mem_Rd", n10.invar(u"vMemDrv", y=270)),
               (u"Imm", n10.invar(u"vImm", y=310)),
               (u"Init_En", n10.invar(u"GVL_InitRegs.Init_En", y=350)),
               (u"Init_Sel_Dst", n10.invar(u"GVL_InitRegs.Init_Sel_Dst", y=390))],'''
assert old2 in t, u"ne najden vyzov fbRF"
t = t.replace(old2, new2)

io.open(GEN, "w", encoding="utf-8").write(t)
print(u"PATCH PRG_INIT OK")
