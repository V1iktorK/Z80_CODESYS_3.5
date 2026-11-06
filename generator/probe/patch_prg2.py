# -*- coding: utf-8 -*-
u"""patch_prg2.py -- perepisyvaet mk_plc_prg pravilno.

Ispravlyaem glavnuyu oshibku pervoj redaktsii: odin ekzemplyar FB vyzyvalsya
neskolko raz (fbClock tri raza, fbCtl dva raza). V FBD eto zapreshcheno --
kazhdyj ekzemplyar vyzyvaetsya ODIN raz za skan, a ego vyhody berutsya po
imeni (kak 'fbClock.Clk_Decode'), inache biblioteka padaet s
'Vyhod vyzova FB razvetvlyaetsya ... Ekzemplyar FB dublirovat nelzya'.

Takzhe poryadok setey peresmotren: registrovaya chast' razdelen na CHTENIE
(set 4) i ZAPIS' (set 8), chtoby ne bylo kol'tsevoj zavisimosti
RF -> ALU -> RF v odnoj seti.

Poryadok ispolneniya (formalnoe uslovie otsutstviya gonok):
  1  takt            2  PC (Addr)
  3  FETCH (IR)      4  DEKODER
  5  CHTENIE RF      6  ADRES operanda
  7  PORТ operanda   8  ALU
  9  FLAGI          10  ZAPIS' RF
 11  STEK           12  UPRAVLENIE
 13  PC latch       14  R
"""

import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
GEN = os.path.join(ROOT, "generator", "gen_z80.py")

NEW = u'''def mk_plc_prg():
    u"""PLC_PRG -- GLAVNAYa SHEMA: konveer emulyatora.

    PRAVILO FBD, kotoroe zdes' soblyudaetsya strogo: kazhdyj ekzemplyar FB
    vyzyvaetsya ODIN raz za skan. Povtornyj vyzov odnogo ekzemplyara
    privodit k oshibke importa. Poetomu vyhody chitayutsya po imeni
    ('fbClock.Clk_Decode'), a ne povtornym vyzovom.

    Poryadok setey = poryadok ispolneniya: kazhdaya set' chitaet tolko to,
    chto zapisali predyduwie.
    """
    p = F.Pou(u"PLC_PRG", u"program",
              u"GLAVNAYa SHEMA emulyatora Z80.\\n"
              u"ODIN SKAN PLC = ODNA KOMANDA (v dva polutakta: decode i exec).\\n"
              u"Poryadok setey sootvetstvuet poryadku ispolneniya.")
    p.var(u"fbClock", u"FB_Clock", u"dvuhfaznyj takt")
    p.var(u"fbAlways", u"FB_AlwaysTrue", u"signal novyj skan")
    p.var(u"fbPC", u"FB_PC_Z80", u"schetchik komand")
    p.var(u"fbPCLatch", u"FB_Reg16", u"zashchelka PC")
    p.var(u"fbIR", u"FB_Reg8Latch", u"registr komandy")
    p.var(u"fbDec", u"FB_DecoderZ80", u"dekoder")
    p.var(u"fbRF", u"FB_RegFileZ80", u"registrovaya chast'")
    p.var(u"fbRFRd", u"FB_RegFileZ80", u"chtenie registrov (net zapisi)")
    p.var(u"fbMem", u"FB_Memory64K", u"pamyat' 64 KB")
    p.var(u"fbALU", u"FB_ALU_Z80", u"ALU")
    p.var(u"fbFlags", u"FB_FlagsRegZ80", u"registr flagov")
    p.var(u"fbSP", u"FB_SP_StackZ80", u"stek")
    p.var(u"fbCtl", u"FB_ControlUnit", u"upravlenie potokom")
    p.var(u"fbR", u"FB_Reg8", u"registr R")
    p.var(u"vRun", u"BOOL", u"razreshenie raboty")
    p.var(u"vScan", u"BOOL", u"signal novogo skana")
    p.var(u"vAddr", u"WORD", u"adres operanda")
    p.var(u"vImm", u"BYTE", u"neposredstvennyj operand (n)")
    p.var(u"vNnHi", u"BYTE", u"starshij bajt adresa nn")
    p.var(u"vSrc", u"BYTE", u"operand dlya ALU")
    p.var(u"vCond", u"BOOL", u"uslovie perehoda")
    p.var(u"vBZero", u"BOOL", u"schetchik DJNZ obnulilsya")
    p.var(u"vPCLoad", u"BOOL", u"zagruzit' PC")
    p.var(u"vPCNew", u"WORD", u"novoe znachenie PC")
    p.var(u"vIncBy", u"BYTE", u"dlina komandy")
    p.var(u"vY", u"BYTE", u"rezul'tat ALU")
    p.var(u"vF", u"BYTE", u"registr flagov")
    p.var(u"vSpRd", u"BYTE", u"bajt so steka")
    p.var(u"vMemDrv", u"BYTE", u"chto na shinu pri chtenii")
    p.var(u"vFetch", u"BYTE", u"vybrannyj kod komandy")
    p.var(u"vPCNext", u"WORD", u"PC posle inkrementa")

    # ================= 1. TAkT =================
    n1 = p.network(u"SET 1: TAkT -- dve fazy za skan")
    c_run = n1.invar(u"GVL_Control.Emu_Run", y=30)
    n1.outvar(u"vRun", c_run, x=F.COL_OUT, y=30)
    al = n1.block(u"FB_AlwaysTrue", [(u"Dummy", c_run)], [u"Q"],
                  x=F.COL_BLK, y=70, instance=u"fbAlways")
    n1.outvar(u"vScan", al, x=F.COL_OUT, y=70)
    n1.block(u"FB_Clock", [(u"Enable", c_run), (u"Scan", al)],
             [u"Clk_Decode", u"Clk_Exec", u"Busy"],
             x=F.COL_BLK2, y=30, instance=u"fbClock")

    # ================= 2. PC =================
    n2 = p.network(u"SET 2: PC -- adres tekushchej komandy na shinu")
    c_pc = n2.invar(u"fbPCLatch.Q", y=30)
    n2.outvar(u"GVL_Bus.Bus_Addr", c_pc, x=F.COL_OUT, y=30)
    n2.outvar(u"GVL_PLCVisu.Bus_Addr", c_pc, x=F.COL_OUT, y=70)

    # ================= 3. FETCH =================
    n3 = p.network(u"SET 3: VBORKA -- kod komandy v IR")
    c_irq = n3.invar(u"fbIR.Q", y=210)
    n3.outvar(u"GVL_PLCVisu.IR", c_irq, x=F.COL_OUT, y=210)
    n3.block(u"FB_Reg8Latch",
             [(u"D", n3.invar(u"fbMem.D_Out", y=30)),
              (u"EN", n3.const(u"TRUE", y=70)),
              (u"Clk", n3.invar(u"fbClock.Clk_Decode", y=110)),
              (u"CLR", n3.invar(u"GVL_Control.Emu_Reset", y=150))],
             [u"Q"], x=F.COL_BLK2, y=30, instance=u"fbIR")

    # ================= 4. DEKODER =================
    n4 = p.network(u"SET 4: DEKODIROVANIE -- IR vo vse signaly upravleniya")
    n4.block(u"FB_DecoderZ80", [(u"IR", c_irq)],
             [u"Ctl_Is_CALL", u"Ctl_Is_RET", u"Ctl_Is_DJNZ", u"Ctl_Is_HALT",
              u"Ctl_Is_Jump", u"Ctl_Is_Jr", u"Ctl_Imm_Mode", u"Ctl_Flags_En",
              u"Ctl_Wr_Enable", u"Ctl_Mem_Rd", u"Ctl_Mem_Wr",
              u"Ctl_Sel_Dst", u"Ctl_Sel_Src", u"Ctl_ALU_Op", u"Ctl_Cond",
              u"Ctl_IncDec"],
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
                     (u"Ctl_Cond", u"GVL_Control.Ctl_Cond"),
                     (u"Ctl_IncDec", u"GVL_Control.Ctl_IncDec")):
        n4.outvar(dst, n4.invar(u"fbDec", y=250).out(pin) if False else
                  n4.block(u"FB_RS", [(u"SET", n4.const(u"FALSE", y=280)),
                                      (u"RESET", n4.const(u"TRUE", y=310))],
                           [u"Q1"], x=2000, y=300, instance=u"fbDec").out(pin)
                  if False else n4.invar(u"fbDec." + pin, y=250),
                  x=F.COL_OUT + 300, y=30)

    # ================= 5. CHTENIE REGISTROV =================
    n5 = p.network(u"SET 5: CHTENIE REGISTROV -- bez zapisi")
    n5.block(u"FB_RegFileZ80",
             [(u"Sel_Dst", n5.invar(u"GVL_Control.Ctl_Sel_Dst", y=30)),
              (u"Sel_Src", n5.invar(u"GVL_Control.Ctl_Sel_Src", y=70)),
              (u"Wr_Val", n5.const(u"0", y=110)),
              (u"Wr_En", n5.const(u"FALSE", y=150)),
              (u"Clk", n5.invar(u"fbClock.Clk_Exec", y=190)),
              (u"CLR", n5.invar(u"GVL_Control.Emu_Reset", y=230)),
              (u"Mem_Rd", n5.invar(u"vMemDrv", y=270)),
              (u"Imm", n5.invar(u"vImm", y=310))],
             [u"Src_Val", u"A", u"B", u"C", u"D", u"E", u"H", u"L", u"F",
              u"Sa", u"Sb", u"Sc", u"Sd", u"Se", u"Sh", u"Sl", u"Sf",
              u"Addr_HL"],
             x=F.COL_BLK2, y=30, instance=u"fbRFRd")
    n5.outvar(u"GVL_Bus.Bus_Addr_HL", n5.invar(u"fbRFRd.Addr_HL", y=550),
              x=F.COL_OUT + 600, y=550)

    # ================= 6. ADRES OPERANDA =================
    n6 = p.network(u"SET 6: ADRES OPERANDA -- (HL) ili nn")
    c_imm = n6.invar(u"GVL_Control.Ctl_Imm_Mode", y=30)
    c_hl = n6.invar(u"fbRFRd.Addr_HL", y=70)
    c_nlo = n6.invar(u"fbMem.Rd_Data", y=110)
    c_nhi = n6.invar(u"fbMem.SP_Out", y=150)
    c_pcn = n6.invar(u"fbPCLatch.Q", y=190)
    n6.outvar(u"vNnHi", c_nhi, x=F.COL_OUT, y=150)
    pc1 = b_add(n6, F.COL_BLK, 190, c_pcn, n6.const(u"1", y=204))
    n6.outvar(u"GVL_Bus.Bus_Addr_Op", pc1, x=F.COL_OUT, y=190)
    wh = b_b2w(n6, F.COL_BLK, 150, c_nhi)
    sh = b_shl(n6, F.COL_BLK2, 150, wh, n6.const(u"8", y=164))
    wl = b_b2w(n6, F.COL_BLK2, 110, c_nlo)
    nn = n6.block(u"OR", [(PIN1, sh), (PIN2, wl)], [POUT],
                  x=F.COL_BLK2 + 160, y=130)
    asel = b_sel(n6, F.COL_BLK2 + 320, 100, c_imm, c_hl, nn)
    n6.outvar(u"vAddr", asel, x=F.COL_OUT + 300, y=100)

    # ================= 7. PORT OPERANDA =================
    n7 = p.network(u"SET 7: PORT OPERANDA -- chtenie/zapis' po vychislennomu adresu")
    n7.block(u"FB_Memory64K",
             [(u"PC", n7.invar(u"fbPCLatch.Q", y=30)),
              (u"Addr", n7.invar(u"vAddr", y=70)),
              (u"Rd", n7.invar(u"GVL_Control.Ctl_Mem_Rd", y=110)),
              (u"Wr", n7.invar(u"GVL_Control.Ctl_Mem_Wr", y=150)),
              (u"D_Bus", n7.invar(u"GVL_PLCVisu.Bus_Data", y=190)),
              (u"SP_Addr", n7.invar(u"fbSP.SP", y=230)),
              (u"SP_Rd", n7.invar(u"GVL_Control.Ctl_Is_RET", y=270)),
              (u"SP_Wr", n7.invar(u"GVL_Control.Ctl_Is_CALL", y=310)),
              (u"SP_Data", n7.invar(u"fbPCLatch.Q", y=350))],
             [u"D_Out", u"Rd_Data", u"SP_Out", u"Bus_Drv"],
             x=F.COL_BLK2, y=30, instance=u"fbMem")
    n7.outvar(u"vFetch", n7.invar(u"fbMem.D_Out", y=400), x=F.COL_OUT, y=400)
    n7.outvar(u"vMemDrv", n7.invar(u"fbMem.Bus_Drv", y=440), x=F.COL_OUT, y=440)
    n7.outvar(u"vImm", n7.invar(u"fbMem.Rd_Data", y=480), x=F.COL_OUT, y=480)
    n7.outvar(u"vSpRd", n7.invar(u"fbMem.SP_Out", y=520), x=F.COL_OUT, y=520)

    # ================= 8. ALU =================
    n8 = p.network(u"SET 8: ALU")
    c_rd8 = n8.invar(u"GVL_Control.Ctl_Mem_Rd", y=30)
    c_sv = n8.invar(u"fbRFRd.Src_Val", y=70)
    c_mv = n8.invar(u"vImm", y=110)
    c_iv = n8.invar(u"vImm", y=150)
    c_one = n8.const(u"1", y=190)
    c_zero = n8.const(u"0", y=230)
    c_f = n8.invar(u"fbRF.F", y=270)
    src1 = b_sel(n8, F.COL_BLK, 70, c_rd8, c_sv, c_mv)
    src2 = b_sel(n8, F.COL_BLK2, 120, c_iv, src1, c_one)
    n8.outvar(u"vSrc", src2, x=F.COL_OUT, y=120)
    cbit = n8.block(u"AND", [(PIN1, c_f), (PIN2, c_one)], [POUT],
                    x=F.COL_BLK, y=270)
    cin_b = b_eq(n8, F.COL_BLK2, 250, cbit, c_one)
    n8.block(u"FB_ALU_Z80",
             [(u"A", n8.invar(u"fbRFRd.A", y=310)),
              (u"B", src2),
              (u"Op", n8.invar(u"GVL_Control.Ctl_ALU_Op", y=350)),
              (u"Carry_In", cin_b),
              (u"B_Forced", c_one),
              (u"IncDec", n8.invar(u"GVL_Control.Ctl_IncDec", y=390))],
             [u"Y", u"Flag_S", u"Flag_Z", u"Flag_H", u"Flag_PV", u"Flag_N",
              u"Flag_C"],
             x=F.COL_BLK2 + 160, y=200, instance=u"fbALU")
    n8.outvar(u"vY", n8.invar(u"fbALU.Y", y=430), x=F.COL_OUT, y=430)
    n8.outvar(u"GVL_PLCVisu.Bus_Data", n8.invar(u"fbALU.Y", y=470),
              x=F.COL_OUT, y=470)

    # ================= 9. FLAGI =================
    n9 = p.network(u"SET 9: REGISTR FLAGOV")
    n9.block(u"FB_FlagsRegZ80",
             [(u"Flag_S", n9.invar(u"fbALU.Flag_S", y=30)),
              (u"Flag_Z", n9.invar(u"fbALU.Flag_Z", y=70)),
              (u"F5", n9.const(u"FALSE", y=110)),
              (u"Flag_H", n9.invar(u"fbALU.Flag_H", y=150)),
              (u"F3", n9.const(u"FALSE", y=190)),
              (u"Flag_PV", n9.invar(u"fbALU.Flag_PV", y=230)),
              (u"Flag_N", n9.invar(u"fbALU.Flag_N", y=270)),
              (u"Flag_C", n9.invar(u"fbALU.Flag_C", y=310)),
              (u"En", n9.invar(u"GVL_Control.Ctl_Flags_En", y=350))],
             [u"F"], x=F.COL_BLK2, y=30, instance=u"fbFlags")
    n9.outvar(u"vF", n9.invar(u"fbFlags.F", y=390), x=F.COL_OUT, y=390)
    n9.outvar(u"GVL_PLCVisu.F", n9.invar(u"fbFlags.F", y=430), x=F.COL_OUT, y=430)

    # ================= 10. ZAPIS' V REGISTRY =================
    n10 = p.network(u"SET 10: ZAPIS' REZUL'TATA v registr")
    n10.block(u"FB_RegFileZ80",
              [(u"Sel_Dst", n10.invar(u"GVL_Control.Ctl_Sel_Dst", y=30)),
               (u"Sel_Src", n10.invar(u"GVL_Control.Ctl_Sel_Src", y=70)),
               (u"Wr_Val", n10.invar(u"vY", y=110)),
               (u"Wr_En", n10.invar(u"GVL_Control.Ctl_Wr_Enable", y=150)),
               (u"Clk", n10.invar(u"fbClock.Clk_Exec", y=190)),
               (u"CLR", n10.invar(u"GVL_Control.Emu_Reset", y=230)),
               (u"Mem_Rd", n10.invar(u"vMemDrv", y=270)),
               (u"Imm", n10.invar(u"vImm", y=310))],
              [u"Src_Val", u"A", u"B", u"C", u"D", u"E", u"H", u"L", u"F",
               u"Sa", u"Sb", u"Sc", u"Sd", u"Se", u"Sh", u"Sl", u"Sf",
               u"Addr_HL"],
              x=F.COL_BLK2, y=30, instance=u"fbRF")
    for pin, dst in ((u"A", u"GVL_PLCVisu.A"), (u"B", u"GVL_PLCVisu.B"),
                     (u"C", u"GVL_PLCVisu.C"), (u"D", u"GVL_PLCVisu.D"),
                     (u"E", u"GVL_PLCVisu.E"), (u"H", u"GVL_PLCVisu.H"),
                     (u"L", u"GVL_PLCVisu.L"),
                     (u"Sa", u"GVL_PLCVisu.AltA"), (u"Sb", u"GVL_PLCVisu.AltB"),
                     (u"Sc", u"GVL_PLCVisu.AltC"), (u"Sd", u"GVL_PLCVisu.AltD"),
                     (u"Se", u"GVL_PLCVisu.AltE"), (u"Sh", u"GVL_PLCVisu.AltH"),
                     (u"Sl", u"GVL_PLCVisu.AltL")):
        n10.outvar(dst, n10.invar(u"fbRF." + pin, y=400), x=F.COL_OUT + 600, y=400)

    # ================= 11. STEK =================
    n11 = p.network(u"SET 11: STEK -- SP i obmen s pamyat'yu")
    n11.block(u"FB_SP_StackZ80",
              [(u"Push", n11.invar(u"GVL_Control.Ctl_Is_CALL", y=30)),
               (u"Pop", n11.invar(u"GVL_Control.Ctl_Is_RET", y=70)),
               (u"Val_In", n11.invar(u"fbPCLatch.Q", y=110)),
               (u"Mem_Rd", n11.invar(u"vSpRd", y=150))],
              [u"SP", u"Val_Out", u"Addr", u"D_Out", u"Wr", u"Rd"],
              x=F.COL_BLK2, y=30, instance=u"fbSP")
    n11.outvar(u"GVL_PLCVisu.SP", n11.invar(u"fbSP.SP", y=400),
               x=F.COL_OUT, y=400)

    # ================= 12. UPRAVLENIE POTOKOM =================
    n12 = p.network(u"SET 12: UPRAVLENIE -- JP / CALL / RET / DJNZ / HALT")
    c_cond = n12.invar(u"GVL_Control.Ctl_Cond", y=30)
    c_f12 = n12.invar(u"vF", y=70)
    c_40 = n12.const(u"16#40", y=110)
    c_0 = n12.const(u"0", y=150)
    fz = n12.block(u"AND", [(PIN1, c_f12), (PIN2, c_40)], [POUT],
                   x=F.COL_BLK, y=70)
    zset = b_eq(n12, F.COL_BLK, 150, fz, c_0)
    n12.outvar(u"vCond", b_not(n12, F.COL_BLK2, 150, zset), x=F.COL_OUT, y=150)
    c_b12 = n12.invar(u"fbRF.B", y=190)
    n12.outvar(u"vBZero", b_eq(n12, F.COL_BLK, 190, c_b12, c_0),
               x=F.COL_OUT, y=190)
    n12.block(u"FB_ControlUnit",
              [(u"Cond_True", n12.invar(u"vCond", y=230)),
               (u"Is_Jump", n12.invar(u"GVL_Control.Ctl_Is_Jump", y=270)),
               (u"Is_Jr", n12.invar(u"GVL_Control.Ctl_Is_DJNZ", y=310)),
               (u"Is_CALL", n12.invar(u"GVL_Control.Ctl_Is_CALL", y=350)),
               (u"Is_RET", n12.invar(u"GVL_Control.Ctl_Is_RET", y=390)),
               (u"Is_DJNZ", n12.invar(u"GVL_Control.Ctl_Is_DJNZ", y=430)),
               (u"Is_HALT", n12.invar(u"GVL_Control.Ctl_Is_HALT", y=470)),
               (u"Imm", n12.invar(u"vAddr", y=510)),
               (u"Ret_Addr", n12.invar(u"vSpRd", y=550)),
               (u"PC_Cur", n12.invar(u"fbPCLatch.Q", y=590)),
               (u"PC_Next", n12.invar(u"fbPC.PC_Next", y=630)),
               (u"B_Zero", n12.invar(u"vBZero", y=670)),
               (u"Emu_Reset", n12.invar(u"GVL_Control.Emu_Reset", y=710))],
              [u"PC_New", u"PC_Load", u"Halted", u"Inc_By"],
              x=F.COL_BLK2 + 160, y=30, instance=u"fbCtl")
    n12.outvar(u"vPCNew", n12.invar(u"fbCtl.PC_New", y=750), x=F.COL_OUT, y=750)
    n12.outvar(u"vPCLoad", n12.invar(u"fbCtl.PC_Load", y=790), x=F.COL_OUT, y=790)
    n12.outvar(u"vIncBy", n12.invar(u"fbCtl.Inc_By", y=830), x=F.COL_OUT, y=830)
    n12.outvar(u"GVL_PLCVisu.Halted", n12.invar(u"fbCtl.Halted", y=870),
               x=F.COL_OUT, y=870)

    # ================= 13. PC =================
    n13 = p.network(u"SET 13: PC -- sleduyushchaya komanda")
    pc = n13.block(u"FB_PC_Z80",
                   [(u"Load_Val", n13.invar(u"vPCNew", y=30)),
                    (u"Load", n13.invar(u"vPCLoad", y=70)),
                    (u"Inc", n13.const(u"TRUE", y=110)),
                    (u"Inc_By", n13.invar(u"vIncBy", y=150))],
                   [u"Addr", u"PC_Next"], x=F.COL_BLK, y=30, instance=u"fbPC")
    n13.outvar(u"vPCNext", pc.out(u"PC_Next"), x=F.COL_OUT, y=70)
    latch = n13.block(u"FB_Reg16",
                      [(u"D", pc.out(u"Addr")),
                       (u"EN", n13.invar(u"fbClock.Clk_Exec", y=190)),
                       (u"CLR", n13.invar(u"GVL_Control.Emu_Reset", y=230))],
                      [u"Q"], x=F.COL_BLK2, y=30, instance=u"fbPCLatch")
    n13.outvar(u"GVL_PLCVisu.PC", latch, x=F.COL_OUT + 300, y=30)

    # ================= 14. R =================
    n14 = p.network(u"SET 14: REGISTR R -- inkrementiruetsya kazhduyu komandu")
    n14.block(u"FB_Reg8",
              [(u"D", n14.invar(u"GVL_PLCVisu.R_Next", y=30)),
               (u"EN", n14.invar(u"fbClock.Clk_Exec", y=70)),
               (u"CLR", n14.invar(u"GVL_Control.Emu_Reset", y=110))],
              [u"Q"], x=F.COL_BLK2, y=30, instance=u"fbR")
    n14.outvar(u"GVL_PLCVisu.R", n14.invar(u"fbR.Q", y=150), x=F.COL_OUT, y=150)
    return p


'''

t = io.open(GEN, "r", encoding="utf-8").read()

start = t.index(u"def mk_plc_prg():")
end = t.index(u"\nBUILDERS = [")
t = t[:start] + NEW + t[end + 1:]

io.open(GEN, "w", encoding="utf-8").write(t)
print(u"PATCH PRG2 OK")
