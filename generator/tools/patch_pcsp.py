# -*- coding: utf-8 -*-
u"""PATCH_PCSP -- sostoyanie PC i SP vyvoditsya yavno, adres operanda ispravlen.

Ch E T Y R E  P R I Ch I N Y, vse izmerennye na progone soroka proverok.

1) A D R E S  O P E R A N D A. V rezhime "operand iz koda" (JP nn, CALL nn)
   adresom operanda schitalsya sam nn. Poluchalos kolco: chtoby uznat nn,
   nado prochitat pamyat po nn. Izmereno: "JP 2000h" ostavlyal PC = 0.
   T E P E R operand vsegda chitaetsya s PC+1 (on idet srazu za kodom), a
   dlya (HL) -- s HL. U FB_Memory64K poyavilsya vyhod Op_Word: dva bajta po
   adresu Addr i Addr+1, mladshij vpered (tak lezhit nn v pamyati Z80).

2) V Y B O R  O P E R A N D A  A L U. V seti 8 stoyalo
       src1 := SEL(Mem_Rd, Src_Val, Imm)
       src2 := SEL(Imm_Mode, src1, 1)
   Vtoraya stroka PEREPUTALA vetki: dlya INC/DEC (Imm_Mode = FALSE) podavalsya
   registr, a dlya komand s operandom iz koda -- edinica. Teper vybor idet po
   Ctl_IncDec, kak i dolzhno byt.

3) P R I Z N A K  V E T K I  P E R E H O D A. V seti 12 uslovie schitalos
   tol ko iz flaga Z, poetomu "JP nn" (bezuslovnyj) ne vypolnyalsya, esli Z
   byl sbroshen. Teper Ctl_Cond trehznachnyj: 0 = NZ, 1 = Z, 2 = bezuslovno,
   i bezuslovnye komandy perehodyat vsegda.

4) S O S T O Ya N I E  P C  I  S P. FB_PC_Z80 i FB_SP_StackZ80 chitali
   SVOI ZhE vyhody (PC = invar("Addr"), SP = invar("SP")) -- to zhe kolco
   "vyhod pitayot svoy vhod", iz-za kotorogo registrovaya chast kogda-to
   chitala nuli. Teper PC i SP zhivut v GVL_Regs (Rs_/Nx_), kak i registry,
   a PRG_RegLatch perenosit Nx_ -> Rs_ v konce skana. Seti PC i SP stali
   obychnymi kombinacionnymi cepochkami bez ekzemplyarov.
"""

import io
import os
import sys

sys.stdout.reconfigure(encoding=u"utf-8")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), u"..", u".."))
GEN = os.path.join(ROOT, u"generator", u"gen_z80.py")

t = io.open(GEN, encoding=u"utf-8").read()
cnt = 0


def rep(old, new):
    global t, cnt
    assert t.count(old) == 1, (u"NET ILI NE ODNOZNACHNO (%d): %r"
                               % (t.count(old), old[:120]))
    t = t.replace(old, new, 1)
    cnt += 1


# --------------------------------------------------- 1. GVL_Regs: PC i SP -----
rep(u"""    Rs_R : BYTE;   (* schetchik obrashchenij k pamyati (proshlyj skan) *)
    Nx_R : BYTE;   (* on zhe posle pereschyota *)
""",
    u"""    Rs_R : BYTE;   (* schetchik obrashchenij k pamyati (proshlyj skan) *)
    Nx_R : BYTE;   (* on zhe posle pereschyota *)

    (*  S Ch E T Ch I K  K O M A N D  i  U K A Z A T E L  S T E K A.
        Oni tozhe kol co ("chitaetsya zdes, pishetsya zdes"), poetomu zhivut
        po tem zhe pravilam, chto i registry. *)
    Rs_PC : WORD;   (* adres tekushchej komandy *)
    Nx_PC : WORD;   (* on zhe posle vypolneniya *)
    Rs_SP : WORD;   (* ukazatel steka *)
    Nx_SP : WORD;   (* on zhe posle vypolneniya *)
""")

# ------------------------------------- 2. PRG_RegLatch: perenos i zerkalo -----
rep(u"""    nx.outvar(u"GVL_Regs.Rs_R", nx.invar(u"GVL_Regs.Nx_R", y=y),
              x=F.COL_OUT, y=y)""",
    u"""    nx.outvar(u"GVL_Regs.Rs_R", nx.invar(u"GVL_Regs.Nx_R", y=y),
              x=F.COL_OUT, y=y)
    y += 34
    nx.outvar(u"GVL_Regs.Rs_PC", nx.invar(u"GVL_Regs.Nx_PC", y=y),
              x=F.COL_OUT, y=y)
    y += 34
    nx.outvar(u"GVL_Regs.Rs_SP", nx.invar(u"GVL_Regs.Nx_SP", y=y),
              x=F.COL_OUT, y=y)""")

rep(u"""    hm.outvar(u"GVL_PLCVisu.R_Reg", hm.invar(u"GVL_Regs.Nx_R", y=y),
              x=F.COL_OUT, y=y)""",
    u"""    hm.outvar(u"GVL_PLCVisu.R_Reg", hm.invar(u"GVL_Regs.Nx_R", y=y),
              x=F.COL_OUT, y=y)
    y += 34
    #  PC i SP tozhe zerkalim dlya HMI i dlya testov: ranshe ih pisali seti
    #  PLC_PRG 13 i 11, teper oni zhivut v GVL_Regs i zerkaliruyutsya zdes'.
    hm.outvar(u"GVL_PLCVisu.PC", hm.invar(u"GVL_Regs.Nx_PC", y=y),
              x=F.COL_OUT, y=y)
    y += 34
    hm.outvar(u"GVL_PLCVisu.SP", hm.invar(u"GVL_Regs.Nx_SP", y=y),
              x=F.COL_OUT, y=y)""")

# ------------------------------------------ 3. FB_Memory64K: vyhod Op_Word ---
rep(u"""    SP_Data : WORD;
END_VAR
VAR_OUTPUT
    D_Out   : BYTE;
    Rd_Data : BYTE;
    SP_Out  : WORD;
    Bus_Drv : BYTE;
END_VAR""",
    u"""    SP_Data : WORD;
END_VAR
VAR_OUTPUT
    D_Out   : BYTE;
    Rd_Data : BYTE;
    Op_Word : WORD;
    SP_Out  : WORD;
    Bus_Drv : BYTE;
END_VAR""")

rep(u"""           SP_Out  : WORD -- snyatoe so steka""",
    u"""           Op_Word : WORD -- dva bajta po Addr i Addr+1 (mladshij vpered);
                             tak chitaetsya operand nn u JP nn i CALL nn
           SP_Out  : WORD -- snyatoe so steka""")

rep(u"""(* Port 3: stek -- dva bajta za odin obrat.""",
    u"""(* Port 2b: slovo po adresu operanda -- dlya operandov nn.
   Poryadok bajtov kak u Z80: mladshij lezhit po menshemu adresu.
   P O Ch E M U  O T D E L N Y J  V Y H O D. Ran'she starshij bajt nn brali iz
   vyhoda steka (SP_Out), to est iz pamyati po ukazatelyu steka -- k adresu
   operanda eto otnosheniya ne imeet. Izmereno: "JP 2000h" ostavlyal PC = 0. *)
Op_Word := BYTE_TO_WORD(Z80_Mem[Addr]) OR
           SHL(BYTE_TO_WORD(Z80_Mem[Addr + 1]), 8);

(* Port 3: stek -- dva bajta za odin obrat.""")

# --------------------------------------------- 4. Dekoder: Ctl_Cond 0/1/2 -----
rep(u"""    cond_code = b_sel(n, F.COL_BLK2, y + 320,
                      n.invar(r_jpz, y=y + 320),
                      n.const(u"BYTE#00", y=y + 334),
                      n.const(u"BYTE#01", y=y + 348))""",
    u"""    #  K O D  U S L O V I Ya  D L Ya  Ctl_Cond -- T R E H Z N A Ch N Y J:
    #      0 = NZ (perehod, esli Z sbroshen)
    #      1 = Z  (perehod, esli Z ustanovlen)
    #      2 = perehod bezuslovnyj (JP nn, CALL nn)
    #  B Y L O  dvuhznachno, i set 12 schitala uslovie tol ko po flagu Z.
    #  Posledstvie: "JP 2000h" ne vypolnyalsya pri Z = 0. Izmereno na progone:
    #  u teste T17 (JP 2000h) PC ostavalsya ravnym 0.
    cond_code = b_sel(n, F.COL_BLK2, y + 320,
                      n.invar(u"vCmdCond", y=y + 320),
                      n.const(u"BYTE#02", y=y + 334),
                      b_sel(n, F.COL_BLK2 + 160, y + 320,
                            n.invar(r_jpz, y=y + 320),
                            n.const(u"BYTE#00", y=y + 334),
                            n.const(u"BYTE#01", y=y + 348)))""")

#  vCmdCond -- imya dlya priznaka uslovnogo perehoda (uzhe imenuem, nuzhen 2 raza)
rep(u"""    cond_any = b_or(n, F.COL_BLK2, y + 280,
                    n.invar(r_jpz, y=y + 280),
                    n.invar(r_jpnz, y=y + 294))""",
    u"""    p.var(u"vCmdCond", u"BOOL", u"perehod uslovnyj (JP Z / JP NZ)")
    n.outvar(u"vCmdCond", b_or(n, F.COL_BLK2, y + 280,
                               n.invar(r_jpz, y=y + 280),
                               n.invar(r_jpnz, y=y + 294)),
             x=XN + 800, y=y + 280)
    cond_any = n.invar(u"vCmdCond", y=y + 240)""")

# ---------------------------------------- 5. deklaracii PLC_PRG --------------
rep(u"""    p.var(u"fbPC", u"FB_PC_Z80", u"schetchik komand")
    p.var(u"fbPCLatch", u"FB_Reg16", u"zashchelka PC")
""", u"")

rep(u"""    p.var(u"fbSP", u"FB_SP_StackZ80", u"stek")
""", u"")

rep(u"""    p.var(u"vPCNext", u"WORD", u"PC posle inkrementa")""",
    u"""    p.var(u"vPC_Inc", u"WORD", u"PC + dlina komandy")
    p.var(u"vSP_Addr", u"WORD", u"adres obrashcheniya k steku")
    p.var(u"vSP_Dec", u"WORD", u"SP - 2")
    p.var(u"vSP_Inc", u"WORD", u"SP + 2")
    p.var(u"vSP_Next", u"WORD", u"SP posle operacii")
    p.var(u"vRetAddr", u"WORD", u"adres vozvrata dlya CALL")
    p.var(u"vOpWord", u"WORD", u"operand nn iz pamyati")""")

# ------------------------------------------ 6. set' 6: adres operanda --------
rep(u"""    # ================= 6. ADRES OPERANDA =================
    n6 = p.network(u"SET 6: ADRES OPERANDA: (HL) ili nn")
    c_imm = n6.invar(u"vCtl_Imm_Mode", y=30)
    c_hl = n6.invar(u"fbRFRd.Addr_HL", y=70)
    c_nlo = n6.invar(u"fbMem.Rd_Data", y=110)
    c_nhi = n6.invar(u"fbMem.SP_Out", y=150)
    c_pcn = n6.invar(u"fbPCLatch.Q", y=190)""",
    u"""    # ================= 6. ADRES OPERANDA =================
    #  A D R E S  O P E R A N D A.
    #  B Y L O  T A K: v rezhime "operand iz koda" adresom operanda schitalsya
    #  sam nn, to est vybrannyj uzhe adres perehoda, a starshij bajt nn brali
    #  iz vyhoda STEKA. Poluchalos kolco: chtoby uznat nn, nado prochitat
    #  pamyat po nn, a tam eshche nichego ne zapisano. Izmereno na progone:
    #  u teste T17 ("JP 2000h") PC ostavalsya ravnym 0.
    #  T E P E R': operand vsegda chitaetsya s PC+1 (on idet srazu za kodom
    #  komandy), a dlya kosvennoj adresacii -- s HL. Oba bajta nn sobiraet
    #  vyhod Op_Word u FB_Memory64K.
    n6 = p.network(u"SET 6: ADRES OPERANDA: (HL) ili PC+1")
    c_imm = n6.invar(u"vCtl_Imm_Mode", y=30)
    c_hl = n6.invar(u"fbRFRd.Addr_HL", y=70)
    c_pcn = n6.invar(u"GVL_Regs.Rs_PC", y=190)""")

rep(u"""    n6.outvar(u"vNnHi", b_w2b(n6, F.COL_BLK, 150, c_nhi), x=F.COL_OUT, y=150)
    pc1 = b_add(n6, F.COL_BLK, 190, c_pcn, n6.const(u"WORD#1", y=204))
    n6.outvar(u"GVL_Bus.Bus_Addr_Op", pc1, x=F.COL_OUT, y=190)""",
    u"""    pc1 = b_add(n6, F.COL_BLK, 190, c_pcn, n6.const(u"WORD#1", y=204))
    n6.outvar(u"GVL_Bus.Bus_Addr_Op", pc1, x=F.COL_OUT, y=190)""")

rep(u"""    wh = b_b2w(n6, F.COL_BLK2, 150, n6.invar(u"vNnHi", y=150))
    sh = b_shl(n6, F.COL_BLK2 + 160, 150, wh, n6.const(u"8", y=164))
    wl = b_b2w(n6, F.COL_BLK2, 110, c_nlo)
    nn = n6.block(u"OR", [(PIN1, sh), (PIN2, wl)], [POUT],
                  x=F.COL_BLK2 + 320, y=130)
    asel = b_sel(n6, F.COL_BLK2 + 480, 100, c_imm, c_hl, nn)
    n6.outvar(u"vAddr", asel, x=F.COL_OUT + 300, y=100)""",
    u"""    asel = b_sel(n6, F.COL_BLK2 + 480, 100, c_imm, c_hl,
                 n6.invar(u"GVL_Bus.Bus_Addr_Op", y=104))
    n6.outvar(u"vAddr", asel, x=F.COL_OUT + 300, y=100)""")

# ------------------------------ 7. novaya set' 6b: stek pered pamyat'yu ------
rep(u"""    # ================= 7. PORT OPERANDA =================""",
    u"""    # ================= 6b. STEK =================
    #  P O Ch E M U  S E T'  S T O I T  Z D E S'. Adres obrashcheniya k steku
    #  nuzhen uzhe pri vyzove pamyati (port 3), to est nizhe. Sostoyanie --
    #  GVL_Regs.Rs_SP, sleduyushchee -- GVL_Regs.Nx_SP; perenosit ih
    #  PRG_RegLatch, kak i registry.
    #  B Y L O  T A K: etim zanimalas' set' 11, kotoraya stoit POZzhe pamyati,
    #  i FB_SP_StackZ80 chital svoy zhe vyhod SP (kolco).
    n11 = p.network(u"SET 6b: STEK: SP i adres obrashcheniya")
    c_sp = n11.invar(u"GVL_Regs.Rs_SP", y=30)
    c_push = n11.invar(u"vCtl_Is_CALL", y=70)
    c_pop = n11.invar(u"vCtl_Is_RET", y=110)
    c_pcsp = n11.invar(u"GVL_Regs.Rs_PC", y=150)
    sp_dec = b_sub(n11, F.COL_BLK, 30, c_sp, n11.const(u"WORD#2", y=44))
    sp_inc = b_add(n11, F.COL_BLK, 70, c_sp, n11.const(u"WORD#2", y=84))
    n11.outvar(u"vSP_Dec", sp_dec, x=F.COL_OUT, y=30)
    n11.outvar(u"vSP_Inc", sp_inc, x=F.COL_OUT, y=90)
    #  pri CALL adres zapisi = SP-2, pri RET adres chteniya = SP
    n11.outvar(u"vSP_Addr", b_sel(n11, F.COL_BLK2, 30, c_push, c_sp,
                                  n11.invar(u"vSP_Dec", y=44)),
               x=F.COL_OUT, y=150)
    after_pop = b_sel(n11, F.COL_BLK2, 110, c_pop, c_sp,
                      n11.invar(u"vSP_Inc", y=124))
    n11.outvar(u"vSP_Next", b_sel(n11, F.COL_BLK2 + 320, 70, c_push, after_pop,
                                  n11.invar(u"vSP_Dec", y=64)),
               x=F.COL_OUT, y=210)
    n11.outvar(u"GVL_Regs.Nx_SP", n11.invar(u"vSP_Next", y=270),
               x=F.COL_OUT, y=270)
    #  adres vozvrata dlya CALL: sleduyushchaya komanda posle trehbajtovoj
    n11.outvar(u"vRetAddr", b_add(n11, F.COL_BLK2, 190, c_pcsp,
                                  n11.const(u"WORD#3", y=204)),
               x=F.COL_OUT, y=330)

    # ================= 7. PORT OPERANDA =================""")

# ------------------------------------- 8. set' 7: vyzov pamyati --------------
rep(u"""             [(u"PC", n7.invar(u"fbPCLatch.Q", y=30)),
              (u"Addr", n7.invar(u"vAddr", y=70)),
              (u"Rd", n7.invar(u"vCtl_Mem_Rd", y=110)),
              (u"Wr", n7.invar(u"vCtl_Mem_Wr", y=150)),
              (u"D_Bus", n7.invar(u"GVL_Bus.Bus_Data", y=190)),
              (u"SP_Addr", n7.invar(u"fbSP.SP", y=230)),
              (u"SP_Rd", n7.invar(u"vCtl_Is_RET", y=270)),
              (u"SP_Wr", n7.invar(u"vCtl_Is_CALL", y=310)),
              (u"SP_Data", n7.invar(u"fbPCLatch.Q", y=350))],
             [u"D_Out", u"Rd_Data", u"SP_Out", u"Bus_Drv"],""",
    u"""             [(u"PC", n7.invar(u"GVL_Regs.Rs_PC", y=30)),
              (u"Addr", n7.invar(u"vAddr", y=70)),
              (u"Rd", n7.invar(u"vCtl_Mem_Rd", y=110)),
              (u"Wr", n7.invar(u"vCtl_Mem_Wr", y=150)),
              (u"D_Bus", n7.invar(u"GVL_Bus.Bus_Data", y=190)),
              (u"SP_Addr", n7.invar(u"vSP_Addr", y=230)),
              (u"SP_Rd", n7.invar(u"vCtl_Is_RET", y=270)),
              (u"SP_Wr", n7.invar(u"vCtl_Is_CALL", y=310)),
              (u"SP_Data", n7.invar(u"vRetAddr", y=350))],
             [u"D_Out", u"Rd_Data", u"Op_Word", u"SP_Out", u"Bus_Drv"],""")

rep(u"""    n7.outvar(u"vMem_SP_Out", n7.invar(u"fbMem.SP_Out", y=30))""",
    u"""    n7.outvar(u"vOpWord", n7.invar(u"fbMem.Op_Word", y=30))
    n7.outvar(u"vMem_SP_Out", n7.invar(u"fbMem.SP_Out", y=30))""")

# ------------------------------- 9. set' 8: vybor operanda dlya ALU ---------
rep(u"""    c_iv = n8.invar(u"vCtl_Imm_Mode", y=150)
    c_one = n8.const(u"1", y=190)
    c_zero = n8.const(u"0", y=230)
    c_f = n8.invar(u"GVL_Regs.Rs_F", y=270)
    src1 = b_sel(n8, F.COL_BLK, 70, c_rd8, c_sv, c_mv)
    src2 = b_sel(n8, F.COL_BLK2, 120, c_iv, src1, c_one)""",
    u"""    #  Ch T O  B Y L O  N E  T A K. Vtoraya stroka vybora pereputala vetki:
    #      c_iv = Ctl_Imm_Mode;  src2 = SEL(c_iv, src1, 1)
    #  dlya INC/DEC (Imm_Mode = FALSE) podavalsya registr, a dlya komand s
    #  operandom iz koda -- edinica. To est INC A schital "A + A", a LD A,n
    #  pisal edinicu. Izmereno: u T13 (INC A, A = 0Fh) poluchalos 1Eh.
    #  T E P E R': pervyj vybor -- otkuda vz yat operand (pamyat / IR / registr),
    #  vtoroj -- podmenit li ego edinicej (tol ko dlya INC/DEC).
    c_iv = n8.invar(u"vCtl_IncDec", y=150)
    c_mi = n8.invar(u"vCtl_Imm_Mode", y=330)
    c_one = n8.const(u"BYTE#1", y=190)
    c_f = n8.invar(u"GVL_Regs.Rs_F", y=270)
    #  Ctl_Mem_Rd ILI Ctl_Imm_Mode -- priznak "operand ne iz registra"
    c_src_mem = b_or(n8, F.COL_BLK, 330, c_rd8, c_mi)
    src1 = b_sel(n8, F.COL_BLK, 70, c_src_mem, c_sv, c_mv)
    src2 = b_sel(n8, F.COL_BLK2, 120, c_iv, src1, c_one)""")

# ------------------------------------- 10. set' 11: tol'ko zerkalo -----------
BEGIN11 = u"""    # ================= 11. STEK ================="""
END11 = u"""    n11.outvar(u"GVL_PLCVisu.SP", n11.invar(u"vSP_SP", y=60),
               x=F.COL_OUT, y=400)
"""
i = t.find(BEGIN11)
j = t.find(END11)
assert i > 0 and j > i, (i, j)
j += len(END11)
t = t[:i] + u"""    # ================= 11. STEK =================
    #  S A M A  L O G I K A  S T E K A  perenesena v set' 6b: adres
    #  obrashcheniya k steku nuzhen ran she, chem idet vyzov pamyati.
    #  Zdes' ostaetsya tol'ko poyasnenie, chtoby nomeraciya setej sovpadala
    #  s dokumentaciej.
""" + t[j:]
cnt += 1

# ------------------------------------- 11. set' 12: uslovie i PC ------------
rep(u"""    c_f12 = n12.invar(u"vF", y=70)
    c_40 = n12.const(u"16#40", y=110)
    c_0 = n12.const(u"0", y=150)
    fz = n12.block(u"AND", [(PIN1, c_f12), (PIN2, c_40)], [POUT],
                   x=F.COL_BLK, y=70)
    zset = b_eq(n12, F.COL_BLK, 150, fz, c_0)
    n12.outvar(u"vCond", b_not(n12, F.COL_BLK2, 150, zset), x=F.COL_OUT, y=150)""",
    u"""    #  U S L O V I E  P E R E H O D A. Ctl_Cond trehznachnyj:
    #      0 = NZ (idem, kogda Z sbroshen), 1 = Z (idem, kogda Z ustanovlen),
    #      2 = bezuslovno (JP nn, CALL nn).
    #  B Y L O: uslovie schitalos tol ko iz flaga Z, poetomu bezuslovnyj
    #  "JP 2000h" ne vypolnyalsya pri Z = 0 (izmereno: T17, PC ostavalsya 0).
    c_cc = n12.invar(u"vCtl_Cond", y=30)
    c_f12 = n12.invar(u"GVL_Regs.Rs_F", y=70)
    c_40 = n12.const(u"16#40", y=110)
    c_0 = n12.const(u"0", y=150)
    fz = n12.block(u"AND", [(PIN1, c_f12), (PIN2, c_40)], [POUT],
                   x=F.COL_BLK, y=70)
    #  flag Z ustanovlen
    zf = b_eq(n12, F.COL_BLK, 150, fz, c_40)
    is_z = b_eq(n12, F.COL_BLK, 190, c_cc, n12.const(u"16#01", y=204))
    always = b_eq(n12, F.COL_BLK, 230, c_cc, n12.const(u"16#02", y=244))
    take_cc = b_sel(n12, F.COL_BLK2, 150, is_z,
                    b_not(n12, F.COL_BLK, 300, zf), zf)
    n12.outvar(u"vCond", b_or(n12, F.COL_BLK2 + 160, 190,
                              always, take_cc), x=F.COL_OUT, y=150)""")

rep(u"""               (u"PC_Cur", n12.invar(u"fbPCLatch.Q", y=590)),
               (u"PC_Next", n12.invar(u"fbPC.PC_Next", y=630)),""",
    u"""               (u"PC_Cur", n12.invar(u"GVL_Regs.Rs_PC", y=590)),
               #  PC_Next nuzhen tol ko vetke "perehod ne vypolnyaetsya", gde
               #  PC_Load = FALSE i znachenie ignoriiruetsya. Poeticheski
               #  podaem tekushchij PC -- nikakih skrytyh smyslov.
               (u"PC_Next", n12.invar(u"GVL_Regs.Rs_PC", y=630)),""")

# ----------------------------------------- 12. set' 13: PC yavno -------------
BEGIN13 = u"""    # ================= 13. PC ================="""
END13 = u"""    n13.outvar(u"vPCNext", n13.invar(u"vPC_PC_Next", y=60),
               x=F.COL_OUT, y=70)
"""
i = t.find(BEGIN13)
j = t.find(END13)
assert i > 0 and j > i, (i, j)
j += len(END13)
t = t[:i] + u"""    # ================= 13. PC =================
    #  S Ch E T Ch I K  K O M A N D. Sostoyanie -- GVL_Regs.Rs_PC,
    #  sleduyushchee -- GVL_Regs.Nx_PC; perenosit ih PRG_RegLatch.
    #  Prioritet: Init_En (zagruzka startovogo adresa) > zavershenie perehoda
    #  > inkrement v fa ze vypolneniya.
    #
    #  B Y L O  T A K: ekzemplyar FB_PC_Z80, kotoryj chital SVOY ZhE vyhod
    #  ("Addr") chtoby prinyat reshenie o sleduyushchem znachenii. Eto to zhe
    #  kolco "vyhod pitayot svoy vhod", iz-za kotorogo registrovaya chast
    #  kogda-to chitala nuli. Teper cepochka kombinacionnaya i bez ekzemplyara.
    n13 = p.network(u"SET 13: PC: sleduyushchaya komanda")
    c_pc = n13.invar(u"GVL_Regs.Rs_PC", y=30)
    c_load = n13.invar(u"vPCLoad", y=70)
    c_new = n13.invar(u"vPCNew", y=110)
    c_by = n13.invar(u"vIncBy", y=150)
    c_exec = n13.invar(u"fbClock.Clk_Exec", y=190)
    c_inite = n13.invar(u"GVL_InitRegs.Init_En", y=230)
    c_initpc = n13.invar(u"GVL_InitRegs.Init_PC", y=270)
    by_w = n13.block(u"BYTE_TO_WORD", [(PINU, c_by)], [POUT],
                     x=F.COL_BLK, y=150)
    pc_inc = b_add(n13, F.COL_BLK2, 30, c_pc, by_w)
    n13.outvar(u"vPC_Inc", pc_inc, x=F.COL_OUT, y=30)
    #  inkrement -- tol ko v fa ze vypolneniya, inache schetchik bezhal by
    #  na kazhdom skane, vklyuchaya ostanovki
    take = b_sel(n13, F.COL_BLK2 + 160, 70, c_exec, c_pc,
                 n13.invar(u"vPC_Inc", y=84))
    ld = b_sel(n13, F.COL_BLK2 + 320, 70, c_load, take, c_new)
    fin = b_sel(n13, F.COL_BLK2 + 480, 70, c_inite, ld, c_initpc)
    n13.outvar(u"GVL_Regs.Nx_PC", fin, x=F.COL_OUT, y=110)
""" + t[j:]
cnt += 1

# ------------------------------------- 13. set' 18: PC iz GVL_Regs ----------
rep(u"""    is_bdos = b_eq(n18, F.COL_BLK2, 30,
                   n18.invar(u"fbPCLatch.Q", y=30),""",
    u"""    is_bdos = b_eq(n18, F.COL_BLK2, 30,
                   n18.invar(u"GVL_Regs.Rs_PC", y=30),""")

io.open(GEN, u"w", encoding=u"utf-8").write(t)
print(u"patch_pcsp: %d zamen" % cnt)
print(u"nonascii:", sum(1 for ch in t if ord(ch) > 127))
