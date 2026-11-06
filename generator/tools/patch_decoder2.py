# -*- coding: utf-8 -*-
u"""PATCH_DECODER2 -- vse mnogopotreblyaemye signaly dekodera cherez peremennye.

P R I Ch I N A. Kogda vyhod bloka pitayot dva vhoda, biblioteka fbd_xml
kloniruet vetv', i u klona mozhet ostat'sya N E P O D K L Yu Ch E N N Y J vhod
(eto opisano v shapke fbd_xml). Togda sravnenie EQ schitaet musor.

I Z M E R E N O na real nom progone (sim_dump_cpu):
    "INC A" (3Ch) s Init_F = 1 daval A = 0Eh vmesto 10h, to est vypolnyalas'
    operaciya SUB (kod 2). Znachit sravnenie "IR AND C7h = 05h" (DEC) shello
    ISTINNYM dlya 3Ch, hotya 3Ch AND C7h = 04h. Vyhod AND pitaya srazu dva
    sravneniya, i klon poluchil ne tot vhod.

P R A V I L O, kotoroe teper' soblyudaetsya zdes':
    kazhdyj promezhutochnyj signal imenuetsya (p.var ili imenovannaya vyhodnaya
    peremennaya seti) i chitaetsya OTDEL'NYM ekzemplyarom invar na kazhdoe
    potreblenie. Poetomu:
      * sravneniya s kodami komand vozvrashchayut IMYa (vCmd..);
      * vse vyhody seti sravnenij tozhe imenovannye;
      * vybor rezul'tata ALU i vyhodnye signaly chitayut peremennye.
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


# ---------------------------------------------------------------- 1. eq_const
rep(u'''    n = p.network(u"Dekodirovanie: sravneniya s kodami komand")
    c_ir = n.invar(ir, y=30)
    y = 500

    def cmp_const(val, yy):
        return n.const(u"16#%02X" % val, y=yy + 12)

    def eq_const(val, x, yy):
        return b_eq(n, x, yy, c_ir, cmp_const(val, yy))
''', u'''    n = p.network(u"Dekodirovanie: sravneniya s kodami komand")
    c_ir = n.invar(ir, y=30)
    y = 500
    #  Kolonka imenovannyh peremennyh chasti 2 (nomera registrov).
    XN = 1200

    def cmp_const(val, yy):
        return n.const(u"16#%02X" % val, y=yy + 12)

    def eq_const(val, x, yy):
        u"""Sravnenie IR s kodom + IMENOVANNAYa peremennaya, vozvrat -- imya.

        P O Ch E M U  imya, a ne ssylka na blok: kazhdaya komanda nuzhna v
        neskolkih mestah (Ctl_Is_*, Ctl_Imm_Mode, vyborki), a pryamaya ssylka
        na vyhod EQ daet fan-out. U klona, kak vyясneno eksperimentom s
        importom, mozhet ostat'sya nepodklyuchennyj vhod -- i togda signal
        chitaetsya kak musor. Cherez peremennuyu svyaz' odnokratnaya.
        """
        eq = b_eq(n, x, yy, c_ir, cmp_const(val, yy))
        nm = u"vCmd%02X" % val
        n.outvar(nm, eq, x=XN + 800, y=yy)
        return nm
''')

# ------------------------------------- 2. chast' 2: nomera i kod operacii ALU
BEGIN = u"""    #  ======================================================================
    #  Ch A S T'  2.  N O M E R A  R E G I S T R O V  I  K O D  O P E R A C I I."""
END = u"""    mem_wr = b_or(n, XN + 480, 1200, r_ldhla, mem_wr_auto2)
"""
i = t.find(BEGIN)
j = t.find(END)
assert i > 0 and j > i, (i, j)
j += len(END)

NEW = u'''    #  ======================================================================
    #  Ch A S T'  2.  N O M E R A  R E G I S T R O V  I  K O D  O P E R A C I I.
    #
    #  Bloki etoy chasti stojat v otdel'noy kolonke XN, pravee vseh ostal'nyh,
    #  chtoby tablica komand sleva ostaalas' chitaemoj.
    #
    #  P R A V I L O  (oplacheno otladkoy): kazhdyj promezhutochnyj signal
    #  imenuetsya i chitaetsya otdel'nym ekzemplyarom invar na kazhdoe
    #  potreblenie. Inache biblioteka kloniruet vetv', i u klona mozhet
    #  ostat'sya nepodklyuchennyj vhod -- togda sravnenie schitaet musor.
    #  Izmereno: "IR AND C7h" pitaya srazu dva sravneniya, dlya INC A (3Ch)
    #  vybiralsya kod operacii SUB, i A stanovilsya 0Eh vmesto 10h.
    #  ======================================================================

    def zr2proj(varname, yy):
        u"""Tri bita koda registra Z80 -> nomer registra v numeracii proekta.

        varname -- imya peremennoj s tremya bitami koda r (uzhe vyrezannymi
        iz IR). Vozvrat: (r + 1) AND 7, a dlya (HL) -- nomer 8.
        """
        plus = b_add(n, XN + 160, yy,
                     n.invar(varname, y=yy), n.const(u"BYTE#1", y=yy + 14))
        wrap = n.block(u"AND",
                       [(PIN1, plus), (PIN2, n.const(u"BYTE#7", y=yy + 28))],
                       [POUT], x=XN + 320, y=yy)
        is_hl = b_eq(n, XN + 160, yy + 50,
                     n.invar(varname, y=yy + 50),
                     n.const(u"BYTE#6", y=yy + 64))
        return b_sel(n, XN + 480, yy, is_hl, wrap,
                     n.const(u"BYTE#8", y=yy + 14))

    #  K O D I R O V K A  Z 8 0 (tri bita r v kode komandy):
    #      0 = B   1 = C   2 = D   3 = E   4 = H   5 = L   6 = (HL)   7 = A
    #  N U M E R A C I Ya  P R O E K T A (tak indeksiruetsya FB_RegFileZ80):
    #      0 = A   1 = B   2 = C   3 = D   4 = E   5 = H   6 = L   7 = F
    #      dlya chteniya takzhe: 8 = (HL), 9 = neposredstvennyj operand
    #  P E R E V O D:  nomer_proekta = (r + 1) AND 7, dlya r = 6 -> 8.
    #
    #  P O Ch E M U  P E R E V O D  N U Zh E N. Ran'she dekoder podaval v
    #  registrovuyu chast nomer pryamo iz koda komandy, a numeracii raznye:
    #      "ADD A,B" (80h) chital registr A vmesto B,
    #      "SUB B"   (90h) chital registr C,
    #      "LD A,L"  (7Dh) pisala rezul tat v registr F,
    #      "INC B"   (04h) pisala v registr H.
    #  Padali 29 proverok iz 40 pri polnost'yu rabotayushchih initsializacii,
    #  ALU, pamyati i steke -- potomu chto viny ne bylo ni v odnom iz nih.

    #  bity 0..2 koda komandy -- nomer registra-istochnika,
    #  bity 3..5 -- nomer registra-priemnika.
    n.outvar(u"vLo3", n.block(u"AND", [(PIN1, c_ir),
                                       (PIN2, n.const(u"16#07", y=44))],
                               [POUT], x=XN, y=30), x=XN + 640, y=30)
    n.outvar(u"vHi3", n.block(u"AND", [(PIN1, n4),
                                       (PIN2, n.const(u"16#07", y=104))],
                               [POUT], x=XN, y=90), x=XN + 640, y=90)
    n.outvar(u"vDstProj", zr2proj(u"vHi3", 30), x=XN + 640, y=190)
    n.outvar(u"vSrcProj", zr2proj(u"vLo3", 170), x=XN + 640, y=330)

    #  dva starshih bita koda -- klass komandy (gruppa)
    n.outvar(u"vHi2", n.block(u"AND", [(PIN1, c_ir),
                                       (PIN2, n.const(u"16#C0", y=444))],
                              [POUT], x=XN, y=430), x=XN + 640, y=430)
    n.outvar(u"vIsAluGrp", b_eq(n, XN, 470, n.invar(u"vHi2", y=470),
                                n.const(u"16#80", y=484)),
             x=XN + 640, y=470)
    #  I R  A N D  C 0 h = 4 0 h -- gruppa "LD r,r'" i "LD (HL),r" (40h..7Fh)
    n.outvar(u"vIsLdRr", b_eq(n, XN, 510, n.invar(u"vHi2", y=510),
                              n.const(u"16#40", y=524)),
             x=XN + 640, y=510)

    #  I R  A N D  C 7 h = 0 6 h -- gruppa "LD r,n"
    #  (06h 0Eh 16h 1Eh 26h 2Eh 36h 3Eh). Maskoj, a ne spiskom sravnenij:
    #  tak korotko i srazu vidno, kakie bity otvechayut za klass komandy.
    n.outvar(u"vIrC7", n.block(u"AND", [(PIN1, c_ir),
                                        (PIN2, n.const(u"16#C7", y=564))],
                               [POUT], x=XN, y=550), x=XN + 640, y=550)
    n.outvar(u"vIsLdn", b_eq(n, XN, 590, n.invar(u"vIrC7", y=590),
                             n.const(u"16#06", y=604)),
             x=XN + 640, y=590)
    #  I R  A N D  C 7 h = 0 4 h / 0 5 h -- INC r / DEC r (gruppy x4 / x5).
    #  Ta zhe maska pokryvaet i 3Ch / 3Dh: 3Ch AND C7h = 04h, 3Dh AND C7h = 05h.
    n.outvar(u"vInc4", b_eq(n, XN, 630, n.invar(u"vIrC7", y=630),
                            n.const(u"16#04", y=644)),
             x=XN + 640, y=630)
    n.outvar(u"vDec5", b_eq(n, XN, 670, n.invar(u"vIrC7", y=670),
                            n.const(u"16#05", y=684)),
             x=XN + 640, y=670)
    n.outvar(u"vIncDec", b_or(n, XN, 710, n.invar(u"vInc4", y=710),
                              n.invar(u"vDec5", y=724)),
             x=XN + 640, y=710)

    #  P R I E M N I K.  Dlya gruppy ALU i dlya IN A,(n) on vsegda A (nomer 0).
    n.outvar(u"vDstAOnly", b_or(n, XN, 760, n.invar(u"vIsAluGrp", y=760),
                                n.invar(r_in, y=774)),
             x=XN + 640, y=760)
    n.outvar(u"vDstSel", b_sel(n, XN, 810, n.invar(u"vDstAOnly", y=810),
                               n.invar(u"vDstProj", y=824),
                               n.const(u"BYTE#0", y=838)),
             x=XN + 640, y=810)
    #  priemnik (HL)? Togda registr ne zapisyvaetsya -- rabotaet pamyat'.
    n.outvar(u"vDstMem", b_eq(n, XN, 870, n.invar(u"vHi3", y=870),
                              n.const(u"16#06", y=884)),
             x=XN + 640, y=870)
    #  I S T O Ch N I K.  Dlya "LD r,n" operand beretsya iz IR (kod 9).
    n.outvar(u"vSrcSel", b_sel(n, XN, 920, n.invar(u"vIsLdn", y=920),
                               n.invar(u"vSrcProj", y=934),
                               n.const(u"BYTE#9", y=948)),
             x=XN + 640, y=920)
    #  "LD r,n", u kotorogo priemnik NE (HL): operand beretsya iz IR
    n.outvar(u"vImmLdn", b_and(n, XN, 980, n.invar(u"vIsLdn", y=980),
                               b_not(n, XN, 1010, n.invar(u"vDstMem", y=1010))),
             x=XN + 640, y=980)

    #  K O D  O P E R A C I I  A L U  (Ctl_ALU_Op).
    #
    #  B Y L O  T A K (i eto ne rabotalo):
    #      is_logic = GE(n4, 4)                     -- n4 = IR >> 3
    #      alu_rm   = SEL(is_logic, grp + 2, n4)
    #      alu_log  = alu_rm + 3
    #      alu_sel  = SEL(is_logic, alu_log, alu_rm)
    #  Uslovie "IR >> 3 >= 4" istinno pochti dlya vseh opkodov, poetomu vse
    #  komandy shli po "logicheskoy" vetke i poluchali kod, nikak ne svyazannyy
    #  s operaciej. Izmereno (sim_one, test T13 INC A):
    #      IR = 3Ch, Ctl_ALU_Op = 7 (eto CP), a nuzhno 0 (ADD).
    #
    #  V T O R A Ya  O Sh I B K A, naydennaya po progonu soroka proverok: nomer
    #  operacii bralsya iz MLADSHIH treh bit (IR AND 07h), a v gruppe 80h..BFh
    #  eto nomer registra-istochnika. Nomer operacii stoit v bitah 3..5 -- vHi3.
    #  Iz-za etogo "SUB B" (90h) i "OR B" (B0h) vypolnyalis' kak ADD.
    #
    #  P R A V I L A  Z80 (bity 3..5 gruppy 80h..BFh):
    #      0 ADD   1 ADC   2 SUB   3 SBC   4 AND   5 XOR   6 OR   7 CP
    #  V nashem ALU prinyat drugoy poryadok dlya dvuh operacij:
    #      4 AND   5 OR    6 XOR   7 CP
    #  Znachit nuzhno pomenyat mestami 5 i 6 (XOR i OR).
    #
    #  INC/DEC (x4/x5 i 3Ch/3Dh) -- eto slozhenie ili vychitanie edinicy:
    #  kod operacii 0 (ADD) ili 2 (SUB). Sam operand = 1 podayot vhod B_Forced.
    #  Vse ostalnye komandy ALU ne ispolzuyut, dlya nih kod 0.
    n.outvar(u"vIsXor", b_eq(n, XN, 1060, n.invar(u"vHi3", y=1060),
                             n.const(u"16#05", y=1074)),
             x=XN + 640, y=1060)
    n.outvar(u"vIsOrp", b_eq(n, XN, 1100, n.invar(u"vHi3", y=1100),
                             n.const(u"16#06", y=1114)),
             x=XN + 640, y=1100)
    n.outvar(u"vSw56", b_or(n, XN, 1140, n.invar(u"vIsXor", y=1140),
                            n.invar(u"vIsOrp", y=1154)),
             x=XN + 640, y=1140)
    #  P O M N I T': b_sel(G, IN0, IN1) daet IN0 pri G=FALSE i IN1 pri G=TRUE.
    n.outvar(u"vSwap", b_sel(n, XN, 1190, n.invar(u"vIsXor", y=1190),
                             n.const(u"BYTE#05", y=1204),
                             n.const(u"BYTE#06", y=1218)),
             x=XN + 640, y=1190)
    n.outvar(u"vOpAlu", b_sel(n, XN, 1250, n.invar(u"vSw56", y=1250),
                              n.invar(u"vHi3", y=1264),
                              n.invar(u"vSwap", y=1278)),
             x=XN + 640, y=1250)
    n.outvar(u"vOpDec", b_sel(n, XN, 1320, n.invar(u"vDec5", y=1320),
                              n.const(u"BYTE#00", y=1334),
                              n.const(u"BYTE#02", y=1348)),
             x=XN + 640, y=1320)
    n.outvar(u"vAluSel", b_sel(n, XN, 1390, n.invar(u"vIsAluGrp", y=1390),
                               n.invar(u"vOpDec", y=1404),
                               n.invar(u"vOpAlu", y=1418)),
             x=XN + 640, y=1390)

    #  C T L _ W R _ E N A B L E  -- zapisyvat li registr.
    #  B Y L O  const TRUE: registr pisalsya na L Yu B O J komande.
    #  Posledstvie: "JP 0FA00h" (C3h) zapisyval v B rezul tat ALU, a "CP B"
    #  (B8h) portil akkumulyator, hotya sravnenie ego ne menyaet.
    #  P R A V I L O: zapis' idet tolko dlya LD r,r' / LD r,n / INC r / DEC r /
    #  ALU (krome CP) / IN A,(n), i nikogda -- esli priemnik (HL).
    n.outvar(u"vIsCp", b_and(n, XN, 1460, n.invar(u"vIsAluGrp", y=1460),
                             b_eq(n, XN, 1490, n.invar(u"vHi3", y=1490),
                                  n.const(u"16#07", y=1504))),
             x=XN + 640, y=1460)
    n.outvar(u"vWrL", b_or(n, XN, 1550, n.invar(u"vIsLdRr", y=1550),
                           n.invar(u"vIsLdn", y=1564)),
             x=XN + 640, y=1550)
    n.outvar(u"vWrR", b_or(n, XN, 1600, n.invar(u"vIncDec", y=1600),
                           n.invar(u"vIsAluGrp", y=1614)),
             x=XN + 640, y=1600)
    n.outvar(u"vWrBase", b_or(n, XN, 1650, n.invar(u"vWrL", y=1650),
                              n.invar(u"vWrR", y=1664)),
             x=XN + 640, y=1650)
    n.outvar(u"vWrBase2", b_or(n, XN, 1700, n.invar(u"vWrBase", y=1700),
                               n.invar(r_in, y=1714)),
             x=XN + 640, y=1700)
    n.outvar(u"vWrOk", b_and(n, XN, 1750, n.invar(u"vWrBase2", y=1750),
                             b_not(n, XN, 1780, n.invar(u"vDstMem", y=1780))),
             x=XN + 640, y=1750)
    n.outvar(u"vWrEn", b_and(n, XN, 1830, n.invar(u"vWrOk", y=1830),
                             b_not(n, XN, 1860, n.invar(u"vIsCp", y=1860))),
             x=XN + 640, y=1830)

    #  C T L _ M E M _ R D  i  C T L _ M E M _ W R.
    #  Priamye priznaki opkodov 7Eh / 77h ostavleny otdel'no, chtoby tablica
    #  komand chitalas' bukval'no; maski dobavlyayut ostal'nye sluchai togo zhe
    #  klassa ("LD B,(HL)" i t.p.).
    n.outvar(u"vSrcMem", b_eq(n, XN, 1910, n.invar(u"vLo3", y=1910),
                              n.const(u"16#06", y=1924)),
             x=XN + 640, y=1910)
    n.outvar(u"vMemRdAuto", b_and(n, XN, 1960, n.invar(u"vSrcMem", y=1960),
                                  b_or(n, XN, 1990,
                                       n.invar(u"vIsAluGrp", y=1990),
                                       n.invar(u"vIncDec", y=2004))),
             x=XN + 640, y=1960)
    n.outvar(u"vMemRd", b_or(n, XN, 2050, n.invar(r_ldahl, y=2050),
                             n.invar(u"vMemRdAuto", y=2064)),
             x=XN + 640, y=2050)
    n.outvar(u"vMemWrAuto", b_and(n, XN, 2100, n.invar(u"vIsLdRr", y=2100),
                                  n.invar(u"vDstMem", y=2114)),
             x=XN + 640, y=2100)
    n.outvar(u"vMemWrAuto2", b_and(n, XN, 2150, n.invar(u"vMemWrAuto", y=2150),
                                   b_not(n, XN, 2180,
                                         n.invar(r_halt, y=2180))),
             x=XN + 640, y=2150)
    n.outvar(u"vMemWr", b_or(n, XN, 2230, n.invar(r_ldhla, y=2230),
                             n.invar(u"vMemWrAuto2", y=2244)),
             x=XN + 640, y=2230)
'''
t = t[:i] + NEW + t[j:]
cnt += 1

# --------------------------------- 3. deklaracii peremennyh chasti 2 ----------
DECL_ANCHOR = u'''    # --- gruppy komand ---
'''
DECLS = u'''    #  P R O M E Zh U T O Ch N Y E  S I G N A L Y  Ch A S T I  2.
    #  Vse oni imenovannye: kazhdoe potreblenie chitaet svoyu peremennuyu,
    #  i nikakoj vyhod bloka ne pitayot dva vhoda (inache klon poyavlyaetsya
    #  s nepodklyuchennym vhodom, i sravneniya schitayut musor).
    p.var(u"vLo3", u"BYTE", u"bity 0..2 koda komandy (nomer istochnika)")
    p.var(u"vHi3", u"BYTE", u"bity 3..5 koda komandy (priemnik i kod ALU)")
    p.var(u"vHi2", u"BYTE", u"bity 6..7 koda komandy (klass komandy)")
    p.var(u"vDstProj", u"BYTE", u"nomer registra-priemnika v numeracii proekta")
    p.var(u"vSrcProj", u"BYTE", u"nomer registra-istochnika v numeracii proekta")
    p.var(u"vDstAOnly", u"BOOL", u"priemnik prinuditel no A (ALU, IN A,(n))")
    p.var(u"vDstSel", u"BYTE", u"Ctl_Sel_Dst")
    p.var(u"vDstMem", u"BOOL", u"priemnik -- pamyat (HL), a ne registr")
    p.var(u"vSrcSel", u"BYTE", u"Ctl_Sel_Src")
    p.var(u"vImmLdn", u"BOOL", u"LD r,n: operand beretsya iz IR")
    p.var(u"vIsAluGrp", u"BOOL", u"gruppa ALU (80h..BFh)")
    p.var(u"vIsLdRr", u"BOOL", u"gruppa LD r,r' (40h..7Fh)")
    p.var(u"vIrC7", u"BYTE", u"IR AND C7h -- maska klassov LD r,n i INC/DEC r")
    p.var(u"vIsLdn", u"BOOL", u"gruppa LD r,n")
    p.var(u"vInc4", u"BOOL", u"gruppa x4 (INC r)")
    p.var(u"vDec5", u"BOOL", u"gruppa x5 (DEC r)")
    p.var(u"vIncDec", u"BOOL", u"INC ili DEC: operand raven 1")
    p.var(u"vIsXor", u"BOOL", u"kod operacii Z80 5 (XOR)")
    p.var(u"vIsOrp", u"BOOL", u"kod operacii Z80 6 (OR)")
    p.var(u"vSw56", u"BOOL", u"nuzhno pomenyat kody 5 i 6 mestami")
    p.var(u"vSwap", u"BYTE", u"kod operacii posle obmena")
    p.var(u"vOpAlu", u"BYTE", u"kod operacii dlya gruppy ALU")
    p.var(u"vOpDec", u"BYTE", u"kod operacii dlya INC/DEC (0 ili 2)")
    p.var(u"vAluSel", u"BYTE", u"Ctl_ALU_Op")
    p.var(u"vIsCp", u"BOOL", u"komanda CP: rezul tat v registr ne pishetsya")
    p.var(u"vWrL", u"BOOL", u"zapis razreshena klassom LD")
    p.var(u"vWrR", u"BOOL", u"zapis razreshena ALU ili INC/DEC")
    p.var(u"vWrBase", u"BOOL", u"zapis razreshena komandoj")
    p.var(u"vWrBase2", u"BOOL", u"to zhe s uchetom IN A,(n)")
    p.var(u"vWrOk", u"BOOL", u"zapis razreshena i priemnik ne (HL)")
    p.var(u"vWrEn", u"BOOL", u"Ctl_Wr_Enable")
    p.var(u"vSrcMem", u"BOOL", u"istochnik (HL)")
    p.var(u"vMemRdAuto", u"BOOL", u"chtenie pamyati po maske")
    p.var(u"vMemRd", u"BOOL", u"Ctl_Mem_Rd")
    p.var(u"vMemWrAuto", u"BOOL", u"zapis v pamyat po maske")
    p.var(u"vMemWrAuto2", u"BOOL", u"to zhe, krome HALT")
    p.var(u"vMemWr", u"BOOL", u"Ctl_Mem_Wr")

    # --- gruppy komand ---
'''
rep(DECL_ANCHOR, DECLS)

# ------------------------------ 4. flags_en: cherez peremennye ----------------
rep(u"""    flags_en = b_or(n, F.COL_BLK2 + 320, y + 520, incdec, is_alu_grp)""",
    u"""    flags_en = b_or(n, F.COL_BLK2 + 320, y + 520,
                    n.invar(u"vIncDec", y=y + 520),
                    n.invar(u"vIsAluGrp", y=y + 534))""")

# --------------------- 5. Ctl_Is_Jump i Ctl_Imm_Mode: cherez invar ------------
rep(u"""        (u"Ctl_Is_Jump", b_or(n, F.COL_BLK2 + 480, y + 200,
                              b_or(n, F.COL_BLK2 + 480, y + 160, r_jp, cond_any),
                              r_call), F.COL_OUT),
        (u"Ctl_Is_Jr", r_djnz, F.COL_OUT),""",
    u"""        (u"Ctl_Is_Jump", b_or(n, F.COL_BLK2 + 480, y + 200,
                              b_or(n, F.COL_BLK2 + 480, y + 160,
                                   n.invar(r_jp, y=y + 160), cond_any),
                              n.invar(r_call, y=y + 200)), F.COL_OUT),
        (u"Ctl_Is_Jr", r_djnz, F.COL_OUT),""")

rep(u"""        (u"Ctl_Imm_Mode",
         b_or(n, F.COL_BLK2 + 320, y + 780,
              b_or(n, F.COL_BLK2 + 320, y + 740,
                   b_or(n, F.COL_BLK2 + 320, y + 700,
                        b_or(n, F.COL_BLK2 + 320, y + 660,
                             b_or(n, F.COL_BLK2 + 320, y + 620,
                                  b_or(n, F.COL_BLK2 + 320, y + 580,
                                       b_or(n, F.COL_BLK2 + 320, y + 540,
                                            b_or(n, F.COL_BLK2 + 320, y + 500,
                                                 imm_ldn, r_call),
                                            r_jp),
                                       r_jpz),
                                  r_jpnz),
                             r_in),
                        r_out),
                   r_ldann),
              r_ldnna),
         F.COL_OUT),""",
    u"""        (u"Ctl_Imm_Mode",
         b_or(n, F.COL_BLK2 + 320, y + 780,
              b_or(n, F.COL_BLK2 + 320, y + 740,
                   b_or(n, F.COL_BLK2 + 320, y + 700,
                        b_or(n, F.COL_BLK2 + 320, y + 660,
                             b_or(n, F.COL_BLK2 + 320, y + 620,
                                  b_or(n, F.COL_BLK2 + 320, y + 580,
                                       b_or(n, F.COL_BLK2 + 320, y + 540,
                                            b_or(n, F.COL_BLK2 + 320, y + 500,
                                                 n.invar(u"vImmLdn", y=y + 500),
                                                 n.invar(r_call, y=y + 514)),
                                            n.invar(r_jp, y=y + 540)),
                                       n.invar(r_jpz, y=y + 580)),
                                  n.invar(r_jpnz, y=y + 620)),
                             n.invar(r_in, y=y + 660)),
                        n.invar(r_out, y=y + 700)),
                   n.invar(r_ldann, y=y + 740)),
              n.invar(r_ldnna, y=y + 780)),
         F.COL_OUT),""")

# ---------------------------------------- 6. vyhody: imena vmesto ssylok ------
rep(u"""        (u"Ctl_Wr_Enable", wr_en, F.COL_OUT),
        (u"Ctl_Mem_Rd", mem_rd, F.COL_OUT),
        (u"Ctl_Mem_Wr", mem_wr, F.COL_OUT),
        (u"Ctl_Sel_Dst", dst_sel, F.COL_OUT + 300),
        (u"Ctl_Sel_Src", src_sel, F.COL_OUT + 300),
        (u"Ctl_ALU_Op", alu_sel, F.COL_OUT + 300),
        (u"Ctl_Cond", cond_code, F.COL_OUT),
        (u"Ctl_IncDec", incdec, F.COL_OUT),""",
    u"""        (u"Ctl_Wr_Enable", u"vWrEn", F.COL_OUT),
        (u"Ctl_Mem_Rd", u"vMemRd", F.COL_OUT),
        (u"Ctl_Mem_Wr", u"vMemWr", F.COL_OUT),
        (u"Ctl_Sel_Dst", u"vDstSel", F.COL_OUT + 300),
        (u"Ctl_Sel_Src", u"vSrcSel", F.COL_OUT + 300),
        (u"Ctl_ALU_Op", u"vAluSel", F.COL_OUT + 300),
        (u"Ctl_Cond", cond_code, F.COL_OUT),
        (u"Ctl_IncDec", u"vIncDec", F.COL_OUT),""")

rep(u"""    oy = 30
    for nm_out, srcv, xo in outs:
        n.outvar(nm_out, srcv, x=xo, y=oy)
        oy += 30""",
    u"""    oy = 30
    for nm_out, srcv, xo in outs:
        #  Strokoy zdes' peredayutsya IMENA peremennyh (komandy r_* i signaly
        #  chasti 2). Na kazhdyj vyhod delaem otdel nyj invar -- inache klon
        #  s nepodklyuchennym vhodom, sm. shapku seti.
        if isinstance(srcv, str):
            srcv = n.invar(srcv, y=oy + 8)
        n.outvar(nm_out, srcv, x=xo, y=oy)
        oy += 30""")

# ------------------------------ 7. ubiraem staryy blok is_incdec_r ------------
OLD_INC = u"""    #  C T L _ I N C D E C  -- "operand raven 1".
    #  B Y L O  otdel'no sobiralos' iz grp = 4/5 i opkodov 3Ch/3Dh. No maska
    #  "IR AND C7h" uzhe pokryvaet i to, i drugoe:
    #      3Ch AND C7h = 04h  -- INC A, ona zhe vetka "INC r"
    #      3Dh AND C7h = 05h  -- DEC A
    #  poetomu otdel'naya proverka opkodov ne nuzhna: odin signal vmesto treh.
    incdec = is_incdec_r
"""
rep(OLD_INC, u"")

# --------------------------- 8. cond_any / cond_code cherez invar ------------
rep(u"""    cond_is_z = r_jpz
    cond_nz0 = r_jpnz
    cond_any = b_or(n, F.COL_BLK2, y + 280, cond_is_z, cond_nz0)""",
    u"""    cond_any = b_or(n, F.COL_BLK2, y + 280,
                    n.invar(r_jpz, y=y + 280),
                    n.invar(r_jpnz, y=y + 294))""")

rep(u"""    cond_code = b_sel(n, F.COL_BLK2, y + 320, r_jpz,""",
    u"""    cond_code = b_sel(n, F.COL_BLK2, y + 320,
                      n.invar(r_jpz, y=y + 320),""")

io.open(GEN, u"w", encoding=u"utf-8").write(t)
print(u"patch_decoder2: %d zamen" % cnt)
print(u"nonascii:", sum(1 for ch in t if ord(ch) > 127))
