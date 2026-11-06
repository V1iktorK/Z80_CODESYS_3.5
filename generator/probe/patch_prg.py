# -*- coding: utf-8 -*-
u"""patch_prg.py -- dobavlyaet v gen_z80.py glavnuyu shemu PLC_PRG i FB_AlwaysTrue.

Glavnaya shema -- eto tot samyj "konveer" iz plana: odinnadtsat' setey,
posle dovatelno raspolozhennyh tak, chtoby kazhdyj blok chital tol'ko to,
chto zapisali bloki s menshim nomerom (formalnoe uslovie otsutstviya gonok).
"""

import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
GEN = os.path.join(ROOT, "generator", "gen_z80.py")

PRG = u'''

def mk_always_true():
    u"""FB_AlwaysTrue -- postoyanno TRUE. Nuzhen kak signal "proizoshel skan".

    V FBD net podachi konsantnogo BOOL napryamuyu v inostrannyj blok tak,
    chtoby eto bylo citаемо, poetomu delaem otdel'nyj POU.
    """
    p = F.Pou(u"FB_AlwaysTrue", u"function",
              u"Postoyanno TRUE. Ispol'zuetsya kak signal 'novyj skan'.")
    p.var_in(u"Dummy", u"BOOL", u"ne ispolzuetsya (nuzhen dlya neputstogo interfejsa)")
    p.var_out(u"Q", u"BOOL", u"vsegda TRUE")
    n = p.network(u"Q := TRUE")
    c = n.invar(u"Dummy", y=30)
    nn = b_not(n, F.COL_BLK, 30, c)
    nn2 = b_not(n, F.COL_BLK2, 30, nn)
    n.outvar(u"Q", nn2, x=F.COL_OUT, y=30)
    return p


def mk_plc_prg():
    u"""PLC_PRG -- GLAVNAYa SHEMA: konveer emulyatora.

    Poryadok setey = poryadok ispolneniya. Kazhdaya set' chitaet tol'ko to,
    chto zapisali predyduwie -- eto formalnoe uslovie otsutstviya gonok.

    Vse ekzemplyary FB obyavleny v VAR etogo POU, poetomu vyzovy idut cherez
    instanceName (sm. fbd_xml.Network.block, parametr instance).
    """
    p = F.Pou(u"PLC_PRG", u"program",
              u"GLAVNAYa SHEMA emulyatora Z80.\\n"
              u"ODIN SKAN PLC = ODNA KOMANDA (v dva polutakta: decode i exec).\\n"
              u"Poryadok setey sootvetstvuet poryadku ispolneniya.")
    p.var(u"fbClock", u"FB_Clock", u"dvuhfaznyj takt")
    p.var(u"fbPC", u"FB_PC_Z80", u"schetchik komand")
    p.var(u"fbIR", u"FB_Reg8Latch", u"registr komandy")
    p.var(u"fbDec", u"FB_DecoderZ80", u"dekoder komand")
    p.var(u"fbRF", u"FB_RegFileZ80", u"registrovaya chast'")
    p.var(u"fbMem", u"FB_Memory64K", u"pamyat' 64 KB")
    p.var(u"fbALU", u"FB_ALU_Z80", u"ALU")
    p.var(u"fbFlags", u"FB_FlagsRegZ80", u"registr flagov")
    p.var(u"fbSP", u"FB_SP_StackZ80", u"stek")
    p.var(u"fbCtl", u"FB_ControlUnit", u"upravlenie potokom")
    p.var(u"fbPCLatch", u"FB_Reg16", u"zashchelka PC")
    p.var(u"fbR", u"FB_Reg8", u"registr R")
    p.var(u"fbAlways", u"FB_AlwaysTrue", u"signal 'novyj skan'")
    p.var(u"fbSelAddr", u"FB_Reg16", u"zashchelka adresa operanda")
    p.var(u"dAddr", u"WORD", u"vybrannyj adres operanda")
    p.var(u"dDst", u"BYTE", u"tekushchij bajt priemnika (dlya (HL))")
    p.var(u"dSrc", u"BYTE", u"vybrannyj operand dlya ALU")
    p.var(u"dCond", u"BOOL", u"uslovie perehoda")

    # ================= SET 1: takt =================
    n1 = p.network(u"SET 1: TAkT -- dve fazy za skan")
    c_en = n1.invar(u"GVL_Control.Emu_Run", y=30)
    al = n1.block(u"FB_AlwaysTrue", [(u"Dummy", c_en)], [u"Q"],
                  x=F.COL_BLK, y=70, instance=u"fbAlways")
    clk = n1.block(u"FB_Clock", [(u"Enable", c_en), (u"Scan", al)], [u"Busy"],
                   x=F.COL_BLK2, y=30, instance=u"fbClock")
    # Clk_Decode i Clk_Exec -- vyhodami v peremennye zerkala dlya HMI
    n1.outvar(u"GVL_PLCVisu.Busy", clk, x=F.COL_OUT, y=30)
    cd = n1.block(u"FB_Clock", [(u"Enable", c_en), (u"Scan", al)], [u"Clk_Decode"],
                  x=F.COL_BLK2 + 160, y=70, instance=u"fbClock")
    n1.outvar(u"GVL_PLCVisu.Clk_Decode", cd, x=F.COL_OUT, y=70)
    ce = n1.block(u"FB_Clock", [(u"Enable", c_en), (u"Scan", al)], [u"Clk_Exec"],
                  x=F.COL_BLK2 + 160, y=110, instance=u"fbClock")
    n1.outvar(u"GVL_PLCVisu.Clk_Exec", ce, x=F.COL_OUT, y=110)

    # ================= SET 2: adres komandy =================
    n2 = p.network(u"SET 2: VBORKA -- PC na pamyat', kod v IR")
    c_pc = n2.invar(u"fbPCLatch.Q", y=30)
    n2.outvar(u"GVL_Bus.Bus_Addr", c_pc, x=F.COL_OUT, y=30)
    # pamyat' chitaet po PC i vydaet kod komandy
    n2.outvar(u"GVL_PLCVisu.Bus_Addr", c_pc, x=F.COL_OUT, y=70)
    d_out = n2.invar(u"fbMem.D_Out", y=110)
    # IR zashchelkivaetsya po pervoj faze
    ir = n2.block(u"FB_Reg8Latch",
                  [(u"D", d_out), (u"EN", n2.const(u"TRUE", y=150)),
                   (u"Clk", n2.invar(u"GVL_PLCVisu.Clk_Decode", y=190)),
                   (u"CLR", n2.const(u"FALSE", y=230))],
                  [u"Q"], x=F.COL_BLK2, y=110, instance=u"fbIR")
    n2.outvar(u"GVL_PLCVisu.IR", ir, x=F.COL_OUT + 140, y=110)

    # ================= SET 3: DEKODIROVANIE =================
    n3 = p.network(u"SET 3: DEKODIROVANIE IR -> signaly upravleniya")
    c_ir = n3.invar(u"fbIR.Q", y=30)
    dec = n3.block(u"FB_DecoderZ80", [(u"IR", c_ir)],
                   [u"Ctl_Is_CALL", u"Ctl_Is_RET", u"Ctl_Is_DJNZ", u"Ctl_Is_HALT",
                    u"Ctl_Is_Jump", u"Ctl_Is_Jr", u"Ctl_Imm_Mode", u"Ctl_Flags_En",
                    u"Ctl_Wr_Enable", u"Ctl_Mem_Rd", u"Ctl_Mem_Wr",
                    u"Ctl_Sel_Dst", u"Ctl_Sel_Src", u"Ctl_ALU_Op", u"Ctl_Cond"],
                   x=F.COL_BLK, y=30, instance=u"fbDec")
    for pin, dst in ((u"Ctl_Is_CALL", u"GVL_Control.Ctl_Is_CALL"),
                     (u"Ctl_Is_RET", u"GVL_Control.Ctl_Is_RET"),
                     (u"Ctl_Is_DJNZ", u"GVL_Control.Ctl_Is_DJNZ"),
                     (u"Ctl_Is_HALT", u"GVL_Control.Ctl_Is_HALT"),
                     (u"Ctl_Is_Jump", u"GVL_Control.Ctl_Is_Jump"),
                     (u"Ctl_Imm_Mode", u"GVL_Control.Ctl_Imm_Mode"),
                     (u"Ctl_Flags_En", u"GVL_Control.Ctl_Flags_En"),
                     (u"Ctl_Wr_Enable", u"GVL_Control.Ctl_Wr_Enable"),
                     (u"Ctl_Mem_Rd", u"GVL_Control.Ctl_Mem_Rd"),
                     (u"Ctl_Mem_Wr", u"GVL_Control.Ctl_Mem_Wr"),
                     (u"Ctl_Sel_Dst", u"GVL_Control.Ctl_Sel_Dst"),
                     (u"Ctl_Sel_Src", u"GVL_Control.Ctl_Sel_Src"),
                     (u"Ctl_ALU_Op", u"GVL_Control.Ctl_ALU_Op"),
                     (u"Ctl_Cond", u"GVL_Control.Ctl_Cond")):
        n3.outvar(dst, dec.out(pin), x=F.COL_OUT + 300, y=30)

    # ================= SET 4: CHTENIE REGISTROV =================
    n4 = p.network(u"SET 4: CHTENIE operandov iz registrov")
    c_dst = n4.invar(u"GVL_Control.Ctl_Sel_Dst", y=30)
    c_src = n4.invar(u"GVL_Control.Ctl_Sel_Src", y=70)
    rf = n4.block(u"FB_RegFileZ80",
                  [(u"Sel_Dst", c_dst), (u"Sel_Src", c_src),
                   (u"Wr_Val", n4.invar(u"fbALU.Y", y=110)),
                   (u"Wr_En", n4.invar(u"GVL_Control.Ctl_Wr_Enable", y=150)),
                   (u"Clk", n4.invar(u"GVL_PLCVisu.Clk_Exec", y=190)),
                   (u"CLR", n4.invar(u"GVL_Control.Emu_Reset", y=230)),
                   (u"Mem_Rd", n4.invar(u"fbMem.Bus_Drv", y=270)),
                   (u"Imm", n4.invar(u"fbMem.Rd_Data", y=310))],
                  [u"Src_Val", u"A", u"B", u"C", u"D", u"E", u"H", u"L", u"F",
                   u"Sa", u"Sb", u"Sc", u"Sd", u"Se", u"Sh", u"Sl", u"Sf",
                   u"Addr_HL"],
                  x=F.COL_BLK2, y=30, instance=u"fbRF")
    for pin, dst in ((u"A", u"GVL_PLCVisu.A"), (u"B", u"GVL_PLCVisu.B"),
                     (u"C", u"GVL_PLCVisu.C"), (u"D", u"GVL_PLCVisu.D"),
                     (u"E", u"GVL_PLCVisu.E"), (u"H", u"GVL_PLCVisu.H"),
                     (u"L", u"GVL_PLCVisu.L"), (u"F", u"GVL_PLCVisu.F"),
                     (u"Sa", u"GVL_PLCVisu.AltA"), (u"Sb", u"GVL_PLCVisu.AltB"),
                     (u"Sc", u"GVL_PLCVisu.AltC"), (u"Sd", u"GVL_PLCVisu.AltD"),
                     (u"Se", u"GVL_PLCVisu.AltE"), (u"Sh", u"GVL_PLCVisu.AltH"),
                     (u"Sl", u"GVL_PLCVisu.AltL")):
        n4.outvar(dst, rf.out(pin), x=F.COL_OUT + 600, y=30)

    # ================= SET 5: VYBOR ADRESA OPERANDA =================
    n5 = p.network(u"SET 5: VYBOR ADRESA OPERANDA -- (HL) ili nn")
    c_imm = n5.invar(u"GVL_Control.Ctl_Imm_Mode", y=30)
    c_hl = n5.invar(u"fbRF.Addr_HL", y=70)
    # nn: adres lezhit srazu za kodom komandy -> PC+1, a starshij bajt na PC+2
    c_pc1 = n5.invar(u"fbPC.PC_Next", y=110)
    c_nn_lo = n5.invar(u"fbMem.Rd_Data", y=150)
    c_nn_hi = n5.invar(u"fbMem.SP_Out", y=190)
    c_one = n5.const(u"1", y=230)
    pc2 = b_add(n5, F.COL_BLK, 110, c_pc1, c_one)
    # chitaem starshij bajt nn otdelnym adresom
    n5.outvar(u"GVL_Bus.Bus_Addr", pc2, x=F.COL_OUT, y=110)
    wh = b_b2w(n5, F.COL_BLK, 190, c_nn_hi)
    sh = b_shl(n5, F.COL_BLK2, 190, wh, n5.const(u"8", y=204))
    wl = b_b2w(n5, F.COL_BLK2, 150, c_nn_lo)
    nn_addr = n5.block(u"OR", [(PIN1, sh), (PIN2, wl)], [POUT],
                       x=F.COL_BLK2 + 160, y=170)
    # vybor: rezhim nn -> sobrannyj adres, inache -> para HL
    addr_sel = b_sel(n5, F.COL_BLK2 + 320, 100, c_imm, c_hl, nn_addr)

    # ================= SET 6: VYBOR OPERANDA DLYa ALU =================
    n6 = p.network(u"SET 6: VYBOR OPERANDA dlya ALU -- registr, (HL) ili n")
    c_rd = n6.invar(u"GVL_Control.Ctl_Mem_Rd", y=30)
    c_srcv = n6.invar(u"fbRF.Src_Val", y=70)
    c_memv = n6.invar(u"fbMem.Rd_Data", y=110)
    src_sel = b_sel(n6, F.COL_BLK, 70, c_rd, c_srcv, c_memv)

    # ================= SET 7: ALU =================
    n7 = p.network(u"SET 7: ALU -- vychislenie rezul'tata")
    c_op = n7.invar(u"GVL_Control.Ctl_ALU_Op", y=30)
    c_a = n7.invar(u"fbRF.A", y=70)
    c_fc = n7.invar(u"fbRF.F", y=110)
    c_one7 = n7.const(u"1", y=150)
    c_zero7 = n7.const(u"0", y=190)
    # perenos na vhod ALU -- bit 0 registra flagov
    m1 = n7.const(u"1", y=230)
    cbit = n7.block(u"AND", [(PIN1, c_fc), (PIN2, m1)], [POUT],
                    x=F.COL_BLK, y=110)
    cin_b = b_eq(n7, F.COL_BLK, 190, cbit, c_one7)
    # dlya INC/DEC operand = 1
    alu = n7.block(u"FB_ALU_Z80",
                   [(u"A", c_a), (u"B", src_sel), (u"Op", c_op),
                    (u"Carry_In", cin_b), (u"B_Forced", c_one7),
                    (u"IncDec", n7.invar(u"GVL_Control.Ctl_IncDec", y=270))],
                   [u"Y", u"Flag_S", u"Flag_Z", u"Flag_H", u"Flag_PV",
                    u"Flag_N", u"Flag_C"],
                   x=F.COL_BLK2, y=30, instance=u"fbALU")
    n7.outvar(u"GVL_PLCVisu.Bus_Data", alu.out(u"Y"), x=F.COL_OUT + 300, y=30)

    # ================= SET 8: FLAGI =================
    n8 = p.network(u"SET 8: REGISTR FLAGOV")
    fl = n8.block(u"FB_FlagsRegZ80",
                  [(u"Flag_S", alu.out(u"Flag_S")), (u"Flag_Z", alu.out(u"Flag_Z")),
                   (u"F5", n8.const(u"FALSE", y=90)),
                   (u"Flag_H", alu.out(u"Flag_H")),
                   (u"F3", n8.const(u"FALSE", y=150)),
                   (u"Flag_PV", alu.out(u"Flag_PV")),
                   (u"Flag_N", alu.out(u"Flag_N")),
                   (u"Flag_C", alu.out(u"Flag_C")),
                   (u"En", n8.invar(u"GVL_Control.Ctl_Flags_En", y=210))],
                  [u"F"], x=F.COL_BLK2, y=30, instance=u"fbFlags")

    # ================= SET 9: STEK =================
    n9 = p.network(u"SET 9: STEK -- SP i obmen s pamyat'yu")
    c_psh = n9.invar(u"GVL_Control.Ctl_Is_CALL", y=30)
    c_pop = n9.invar(u"GVL_Control.Ctl_Is_RET", y=70)
    sp = n9.block(u"FB_SP_StackZ80",
                  [(u"Push", c_psh), (u"Pop", c_pop),
                   (u"Val_In", n9.invar(u"fbPCLatch.Q", y=110)),
                   (u"Mem_Rd", n9.invar(u"fbMem.Rd_Data", y=150))],
                  [u"SP", u"Val_Out", u"Addr", u"D_Out", u"Wr", u"Rd"],
                  x=F.COL_BLK2, y=30, instance=u"fbSP")
    n9.outvar(u"GVL_PLCVisu.SP", sp.out(u"SP"), x=F.COL_OUT + 300, y=30)

    # ================= SET 10: UPRAVLENIE POTOKOM =================
    n10 = p.network(u"SET 10: UPRAVLENIE POTOKOM -- JP / CALL / RET / DJNZ / HALT")
    # uslovie: dlya JP Z berem flag Z, dlya JP NZ -- ego inversiyu
    c_cond = n10.invar(u"GVL_Control.Ctl_Cond", y=30)
    c_f = n10.invar(u"fbRF.F", y=70)
    c_zero10 = n10.const(u"0", y=110)
    c_neq = n10.const(u"16#40", y=150)
    fz = n10.block(u"AND", [(PIN1, c_f), (PIN2, c_neq)], [POUT],
                   x=F.COL_BLK, y=70)
    z_set = b_eq(n10, F.COL_BLK, 110, fz, c_zero10)
    n10.outvar(u"dCond", b_not(n10, F.COL_BLK2, 110, z_set), x=F.COL_OUT, y=110)
    # sravnenie s nul'm dlya DJNZ
    c_b = n10.invar(u"fbRF.B", y=190)
    bz = b_eq(n10, F.COL_BLK, 190, c_b, c_zero10)
    ctl = n10.block(u"FB_ControlUnit",
                    [(u"Cond_True", n10.invar(u"dCond", y=230)),
                     (u"Is_Jump", n10.invar(u"GVL_Control.Ctl_Is_Jump", y=270)),
                     (u"Is_Jr", n10.invar(u"GVL_Control.Ctl_Is_DJNZ", y=310)),
                     (u"Is_CALL", n10.invar(u"GVL_Control.Ctl_Is_CALL", y=350)),
                     (u"Is_RET", n10.invar(u"GVL_Control.Ctl_Is_RET", y=390)),
                     (u"Is_DJNZ", n10.invar(u"GVL_Control.Ctl_Is_DJNZ", y=430)),
                     (u"Is_HALT", n10.invar(u"GVL_Control.Ctl_Is_HALT", y=470)),
                     (u"Imm", nn_addr),
                     (u"Ret_Addr", n10.invar(u"fbSP.Rd_Data", y=510)),
                     (u"PC_Cur", n10.invar(u"fbPCLatch.Q", y=550)),
                     (u"PC_Next", n10.invar(u"fbPC.PC_Next", y=590)),
                     (u"B_Zero", bz),
                     (u"Emu_Reset", n10.invar(u"GVL_Control.Emu_Reset", y=630))],
                    [u"PC_New", u"PC_Load", u"Halted", u"Inc_By"],
                    x=F.COL_BLK2 + 160, y=30, instance=u"fbCtl")
    n10.outvar(u"GVL_PLCVisu.Halted", ctl.out(u"Halted"), x=F.COL_OUT + 300, y=30)

    # ================= SET 11: PROGRAM COUNTER =================
    n11 = p.network(u"SET 11: PC -- sleduyushchaya komanda")
    ctl2 = n11.block(u"FB_ControlUnit",
                     [(u"Cond_True", n11.invar(u"dCond", y=30)),
                      (u"Is_Jump", n11.invar(u"GVL_Control.Ctl_Is_Jump", y=70)),
                      (u"Is_Jr", n11.invar(u"GVL_Control.Ctl_Is_DJNZ", y=110)),
                      (u"Is_CALL", n11.invar(u"GVL_Control.Ctl_Is_CALL", y=150)),
                      (u"Is_RET", n11.invar(u"GVL_Control.Ctl_Is_RET", y=190)),
                      (u"Is_DJNZ", n11.invar(u"GVL_Control.Ctl_Is_DJNZ", y=230)),
                      (u"Is_HALT", n11.invar(u"GVL_Control.Ctl_Is_HALT", y=270)),
                      (u"Imm", nn_addr),
                      (u"Ret_Addr", n11.invar(u"fbSP.Rd_Data", y=310)),
                      (u"PC_Cur", n11.invar(u"fbPCLatch.Q", y=350)),
                      (u"PC_Next", n11.invar(u"fbPC.PC_Next", y=390)),
                      (u"B_Zero", n11.invar(u"dCond", y=430)),
                      (u"Emu_Reset", n11.invar(u"GVL_Control.Emu_Reset", y=470))],
                     [u"PC_New", u"PC_Load"],
                     x=F.COL_BLK, y=30, instance=u"fbCtl")
    pc = n11.block(u"FB_PC_Z80",
                   [(u"Load_Val", ctl2.out(u"PC_New")),
                    (u"Load", ctl2.out(u"PC_Load")),
                    (u"Inc", n11.const(u"TRUE", y=510)),
                    (u"Inc_By", n11.invar(u"fbCtl.Inc_By", y=550))],
                   [u"Addr", u"PC_Next"], x=F.COL_BLK2, y=30, instance=u"fbPC")
    latch = n11.block(u"FB_Reg16",
                      [(u"D", pc.out(u"Addr")),
                       (u"EN", n11.invar(u"GVL_PLCVisu.Clk_Exec", y=590)),
                       (u"CLR", n11.invar(u"GVL_Control.Emu_Reset", y=630))],
                      [u"Q"], x=F.COL_BLK2 + 160, y=30, instance=u"fbPCLatch")
    n11.outvar(u"GVL_PLCVisu.PC", latch, x=F.COL_OUT + 300, y=30)

    return p

'''

t = io.open(GEN, "r", encoding="utf-8").read()

marker = u"\nBUILDERS = ["
assert marker in t, u"ne najden BUILDERS"
t = t.replace(marker, PRG + u"\nBUILDERS = [", 1)

# dobavit' v spisok
t = t.replace(u'    (u"PRG_LoadTestProgram", mk_prg_load_test),\n]',
              u'    (u"PRG_LoadTestProgram", mk_prg_load_test),\n'
              u'    # glavnaya shema i vspomogatelnye\n'
              u'    (u"FB_AlwaysTrue", mk_always_true),\n'
              u'    (u"PLC_PRG", mk_plc_prg),\n]')

io.open(GEN, "w", encoding="utf-8").write(t)
print(u"PATCH PRG OK")
