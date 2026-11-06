# -*- coding: utf-8 -*-
u"""PATCH_DECODER -- chinit nomera registrov i kod operacii ALU v FB_DecoderZ80.

Dve oshibki, iz-za kotoryh padali 29 proverok iz 40:

 1) N O M E R A  R E G I S T R O V. Dekoder podaval v registrovuyu chast nomer
    pryamo iz koda komandy, no numeracii raznye:
        Z80:    0=B 1=C 2=D 3=E 4=H 5=L 6=(HL) 7=A
        proekt: 0=A 1=B 2=C 3=D 4=E 5=H 6=L    7=F
    "ADD A,B" (80h) chital A vmesto B, "LD A,L" (7Dh) pisala v F,
    "INC B" (04h) -- v H.

 2) K O D  O P E R A C I I  A L U bral tri MLADSHIH bita (IR AND 07h), a oni
    v gruppe 80h..BFh -- eto nomer registra-istochnika. Nomer operacii stoit
    v bitah 3..5. Poetomu "SUB B" (90h) i "OR B" (B0h) vypolnyalis' kak ADD.

Zdes' zhe Ctl_Wr_Enable perestal byt' const TRUE: teper' zapis' registra
razreshena tolko tem komandam, kotorye ee deystvitelno delat, i nikogda --
esli priemnik (HL) ili esli eto CP (sravnenie registr ne menyaet).
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


# ---------------------------------------------------------------- 1. ubiraem grp
rep(u"""    m7 = n.const(u"16#07", y=y + 14)
    grp = n.block(u"AND", [(PIN1, c_ir), (PIN2, m7)], [POUT],
                  x=F.COL_BLK, y=y + 26)
""", u"")

# ---------------------------------------- 2. pravil'nyy kod operacii + nomera
OLD_ALU = u"""    #  K O D  O P E R A C I I  A L U  (Ctl_ALU_Op).
    #
    #  B Y L O  T A K (i eto ne rabotalo):
    #      is_logic = GE(n4, 4)                     -- n4 = IR >> 3
    #      alu_rm   = SEL(is_logic, grp + 2, n4)
    #      alu_log  = alu_rm + 3
    #      alu_sel  = SEL(is_logic, alu_log, alu_rm)
    #  Uslovie "IR >> 3 >= 4" istinno pochti dlya vseh opkodov, poetomu vse
    #  komandy shli po "logicheskoy" vetke i poluchali kod, nikak ne svyazann yy
    #  s operaciej. Izmereno na progone (sim_one, test T13 INC A):
    #      IR = 3Ch, Ctl_ALU_Op = 7 (eto CP), a nuzhno 0 (ADD)
    #      PLC_PRG.vY = 0, GVL_PLCVisu.A ostalsya 0Fh vmesto 10h
    #  To est A ne uvelichivalsya, potomu chto ALU vypolnyal sravnenie.
    #
    #  P R A V I L A  Z80.
    #  Arifmetiko-logicheskaya gruppa -- opkody 80h..BFh, to est dva starshih
    #  bita ravny 10b. Nomer operacii vnutri gruppy -- tri mladshih bita (grp):
    #      0 ADD   1 ADC   2 SUB   3 SBC   4 AND   5 XOR   6 OR   7 CP
    #  V nashem ALU prinyat drugoy poryadok dlya treh operacij:
    #      4 AND   5 OR    6 XOR   7 CP
    #  Znachit nuzhno pomenyat mestami 5 i 6 (XOR i OR).
    #
    #  INC/DEC (opkody x4/x5 i 3Ch/3Dh) -- eto slozhenie ili vychitanie
    #  edinicy: kod operacii 0 (ADD) ili 2 (SUB). Sam operand = 1 podayot
    #  vhod B_Forced.
    #
    #  Vse ostalnye komandy ALU ne ispolzuyut, dlya nih kod 0.
    hi2 = n.block(u"AND", [(PIN1, c_ir), (PIN2, n.const(u"16#C0", y=y + 10))],
                  [POUT], x=F.COL_BLK, y=y)
    is_alu_grp = n.block(u"EQ", [(PIN1, hi2), (PIN2, n.const(u"16#80", y=y + 30))],
                         [POUT], x=F.COL_BLK, y=y + 26)
    gg4 = n.block(u"EQ", [(PIN1, grp), (PIN2, n.const(u"16#04", y=y + 60))],
                  [POUT], x=F.COL_BLK2, y=y + 46)
    gg5 = n.block(u"EQ", [(PIN1, grp), (PIN2, n.const(u"16#05", y=y + 90))],
                  [POUT], x=F.COL_BLK2, y=y + 76)
    gg6 = n.block(u"EQ", [(PIN1, grp), (PIN2, n.const(u"16#06", y=y + 120))],
                  [POUT], x=F.COL_BLK2, y=y + 106)
    sw56 = b_or(n, F.COL_BLK2 + 160, y + 76, gg5, gg6)
    #  P O M N I T': b_sel(G, IN0, IN1) daet IN0 pri G=FALSE i IN1 pri G=TRUE.
    swap = b_sel(n, F.COL_BLK2 + 160, y + 106, gg5,
                 n.const(u"BYTE#05", y=y + 120),
                 n.const(u"BYTE#06", y=y + 134))
    op_alu = b_sel(n, F.COL_BLK2 + 320, y + 76, sw56, grp, swap)
    op_dec = b_sel(n, F.COL_BLK2 + 320, y + 46, gg5,
                   n.const(u"BYTE#00", y=y + 60),
                   n.const(u"BYTE#02", y=y + 74))
    alu_sel = b_sel(n, F.COL_BLK2 + 480, y + 26, is_alu_grp, op_dec, op_alu)
"""

NEW_ALU = u"""    #  ======================================================================
    #  Ch A S T'  2.  N O M E R A  R E G I S T R O V  I  K O D  O P E R A C I I.
    #
    #  Bloki etoy chasti vyvedeny v otdel'nuyu kolonku XN pravee vseh
    #  ostalnyh -- tak tablica komand sleva ostaetsya chitaemoj.
    #  ======================================================================
    XN = 1200

    #  K O D I R O V K A  Z 8 0 (tri bita r v kode komandy):
    #      0 = B   1 = C   2 = D   3 = E   4 = H   5 = L   6 = (HL)   7 = A
    #  N U M E R A C I Ya  P R O E K T A (tak indeksiruetsya FB_RegFileZ80):
    #      0 = A   1 = B   2 = C   3 = D   4 = E   5 = H   6 = L   7 = F
    #      dlya chteniya takzhe: 8 = (HL), 9 = neposredstvennyj operand
    #  P E R E V O D:  nomer_proekta = (r + 1) AND 7, dlya r = 6 -> 8.
    #
    #  P O Ch E M U  P E R E V O D  N U Zh E N. Ran'she dekoder podaval v
    #  registrovuyu chast nomer pryamo iz koda komandy, a numeracii raznye.
    #  Izmereno na real nom progone (sim_dump_cpu, 40 proverok):
    #      "ADD A,B" (80h) chital registr A vmesto B,
    #      "SUB B"   (90h) chital registr C,
    #      "LD A,L"  (7Dh) pisala rezul tat v registr F,
    #      "INC B"   (04h) pisala v registr H.
    #  Padali 29 proverok iz 40 pri polnost'yu rabotayushchih initsializacii,
    #  ALU, pamyati i steke -- potomu chto viny ne bylo ni v odnom iz nih.
    def zr2proj(bits, yy):
        u\"\"\"Tri bita koda registra Z80 -> nomer registra v numeracii proekta.

        bits -- Src s tremya bitami koda r (uzhe vyrezannymi iz IR).
        Vozvrat: (bits + 1) AND 7, a dlya (HL) -- nomer 8.
        \"\"\"
        plus = b_add(n, XN + 160, yy, bits, n.const(u"BYTE#1", y=yy + 14))
        wrap = n.block(u"AND",
                       [(PIN1, plus), (PIN2, n.const(u"BYTE#7", y=yy + 28))],
                       [POUT], x=XN + 320, y=yy)
        is_hl = b_eq(n, XN + 160, yy + 50, bits,
                     n.const(u"BYTE#6", y=yy + 64))
        return b_sel(n, XN + 480, yy, is_hl, wrap,
                     n.const(u"BYTE#8", y=yy + 14))

    #  bity 0..2 koda komandy -- nomer registra-istochnika
    lo3 = n.block(u"AND", [(PIN1, c_ir), (PIN2, n.const(u"16#07", y=44))],
                  [POUT], x=XN, y=30)
    #  bity 3..5 koda komandy -- nomer registra-priemnika
    hi3 = n.block(u"AND", [(PIN1, n4), (PIN2, n.const(u"16#07", y=104))],
                  [POUT], x=XN, y=90)
    dst_proj = zr2proj(hi3, 30)
    src_proj = zr2proj(lo3, 170)

    #  I R  A N D  C 7 h = 0 6 h  -- gruppa "LD r,n"
    #  (06h 0Eh 16h 1Eh 26h 2Eh 36h 3Eh). Maskoj, a ne spiskom sravnenij:
    #  tak korotko i srazu vidno, kakie bity otvechayut za klass komandy.
    c7 = n.block(u"AND", [(PIN1, c_ir), (PIN2, n.const(u"16#C7", y=344))],
                 [POUT], x=XN, y=330)
    is_ldn_grp = b_eq(n, XN, 370, c7, n.const(u"16#06", y=384))
    #  I R  A N D  C 7 h = 0 4 h / 0 5 h  -- INC r / DEC r (gruppy x4 / x5).
    #  Ta zhe maska pokryvaet i 3Ch / 3Dh: 3Ch AND C7h = 04h, 3Dh AND C7h = 05h.
    c7b = n.block(u"AND", [(PIN1, c_ir), (PIN2, n.const(u"16#C7", y=454))],
                  [POUT], x=XN, y=440)
    is_inc4 = b_eq(n, XN, 480, c7b, n.const(u"16#04", y=494))
    is_dec5 = b_eq(n, XN, 520, c7b, n.const(u"16#05", y=534))
    is_incdec_r = b_or(n, XN, 560, is_inc4, is_dec5)

    #  I R  A N D  C 0 h -- dva starshih bita, to est klass komandy
    hi2 = n.block(u"AND", [(PIN1, c_ir), (PIN2, n.const(u"16#C0", y=594))],
                  [POUT], x=XN, y=580)
    is_alu_grp = b_eq(n, XN + 160, 580, hi2, n.const(u"16#80", y=594))
    #  I R  A N D  C 0 h = 4 0 h  -- gruppa "LD r,r'" i "LD (HL),r" (40h..7Fh)
    is_ld_rr = b_eq(n, XN, 610, hi2, n.const(u"16#40", y=624))
    #  dlya gruppy ALU i dlya IN A,(n) priemnik prinuditel'no A (nomer 0)
    dst_a_only = b_or(n, XN, 660, is_alu_grp, r_in)
    dst_sel = b_sel(n, XN + 160, 660, dst_a_only, dst_proj,
                    n.const(u"BYTE#0", y=674))
    #  priemnik (HL)? Togda registr ne zapisyvaetsya -- rabotaet pamyat'.
    dst_is_mem = b_eq(n, XN, 750, hi3, n.const(u"16#06", y=764))
    #  dlya "LD r,n" operand beretsya iz IR (kod 9), inache -- registr
    src_sel = b_sel(n, XN + 160, 750, is_ldn_grp, src_proj,
                    n.const(u"BYTE#9", y=764))
    #  "LD r,n", u kotorogo priemnik NE (HL): operand beretsya iz IR
    imm_ldn = b_and(n, XN + 320, 750, is_ldn_grp,
                    b_not(n, XN + 320, 780, dst_is_mem))

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
    #  V T O R A Ya  O Sh I B K A, naydennaya po tom zhe progonu: nomer operacii
    #  bralsya iz MLADSHIH treh bit (IR AND 07h), a v gruppe 80h..BFh eto nomer
    #  registra-istochnika. Nomer operacii stoit v bitah 3..5 -- eto hi3.
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
    is_xor = b_eq(n, XN + 160, 830, hi3, n.const(u"16#05", y=844))
    is_orp = b_eq(n, XN + 160, 900, hi3, n.const(u"16#06", y=914))
    sw56 = b_or(n, XN + 320, 830, is_xor, is_orp)
    #  P O M N I T': b_sel(G, IN0, IN1) daet IN0 pri G=FALSE i IN1 pri G=TRUE.
    swap = b_sel(n, XN + 320, 900, is_xor,
                 n.const(u"BYTE#05", y=914),
                 n.const(u"BYTE#06", y=928))
    op_alu = b_sel(n, XN + 480, 830, sw56, hi3, swap)
    op_dec = b_sel(n, XN + 480, 900, is_dec5,
                   n.const(u"BYTE#00", y=914),
                   n.const(u"BYTE#02", y=928))
    alu_sel = b_sel(n, XN + 640, 830, is_alu_grp, op_dec, op_alu)

    #  C T L _ W R _ E N A B L E  -- zapisyvat li registr.
    #  B Y L O  const TRUE: registr pisalsya na L Yu B O J komande.
    #  Posledstvie: "JP 0FA00h" (C3h) zapisyval v B rezul tat ALU, a "CP B"
    #  (B8h) portil akkumulyator, hotya sravnenie ego ne menyaet.
    #  P R A V I L O: zapis' idet tolko dlya LD r,r' / LD r,n / INC r / DEC r /
    #  ALU (krome CP) / IN A,(n), i nikogda -- esli priemnik (HL).
    is_cp = b_and(n, XN, 970, is_alu_grp,
                  b_eq(n, XN, 1000, hi3, n.const(u"16#07", y=1014)))
    wr_l = b_or(n, XN + 160, 970, is_ld_rr, is_ldn_grp)
    wr_r = b_or(n, XN + 160, 1030, is_incdec_r, is_alu_grp)
    wr_base = b_or(n, XN + 320, 970, wr_l, wr_r)
    wr_base2 = b_or(n, XN + 320, 1030, wr_base, r_in)
    wr_ok = b_and(n, XN + 480, 970, wr_base2,
                  b_not(n, XN + 480, 1000, dst_is_mem))
    wr_en = b_and(n, XN + 640, 970, wr_ok, b_not(n, XN + 640, 1000, is_cp))

    #  C T L _ M E M _ R D  i  C T L _ M E M _ W R.
    #  O T D E L N O  ot opkodov 7Eh / 77h ostavleny ih pryamye priznaki, chtoby
    #  tablica komand chitalas' bukval'no; maski nizhe dobavlyayut vse ostalnye
    #  sluchai togo zhe klassa ("LD B,(HL)" i t.p.).
    src_is_mem = b_eq(n, XN, 1090, lo3, n.const(u"16#06", y=1104))
    mem_rd_auto = b_and(n, XN + 160, 1090, src_is_mem,
                        b_or(n, XN + 160, 1130, is_alu_grp, is_incdec_r))
    mem_rd = b_or(n, XN + 320, 1090, r_ldahl, mem_rd_auto)
    mem_wr_auto = b_and(n, XN + 160, 1200, is_ld_rr, dst_is_mem)
    mem_wr_auto2 = b_and(n, XN + 320, 1200, mem_wr_auto,
                         b_not(n, XN + 320, 1240, r_halt))
    mem_wr = b_or(n, XN + 480, 1200, r_ldhla, mem_wr_auto2)
"""

rep(OLD_ALU, NEW_ALU)

# --------------------------------- 4. ubiraem staryy rr_ldn (zamenen maskoj)
rep(u"""    r_ldn = eq_const(0x3E, F.COL_BLK, y); y += 26
""", u"")

# --------------------------------------- 5. Sel_Dst / Sel_Src: staryy blok von
OLD_SEL = u"""    # --- Sel_Dst ---
    #  Z D E S'  T O  Zh E  S A M O E: vmesto vybora "0 ili nomer" stoyAo
    #  logicheskoe I mezhdu usloviem i chislom. Zam enyaem na SEL s yavno
    #  T I P I Z I R O V A N N Y M I  konstantami BYTE#0 i BYTE#k -- togda
    #  vetki cepochki odnoznachno tipa BYTE.
    def sel_byte(cond, val, yy, xx=F.COL_BLK2 + 160):
        return b_sel(n, xx, yy, cond,
                     n.const(u"BYTE#0", y=yy + 14),
                     n.const(u"BYTE#%02X" % val, y=yy + 28))

    sd_a = sel_byte(r_ldn, 0, y + 200)
    sd_b = sel_byte(r_ldhla, 6, y + 240)
    sd_hl = sel_byte(r_ldahl, 7, y + 280)
    sd_sum = b_add(n, F.COL_BLK2 + 320, y + 200, sd_a, sd_b)
    sd_sum2 = b_add(n, F.COL_BLK2 + 320, y + 240, sd_sum, sd_hl)
    dst_a = n.block(u"AND", [(PIN1, n4), (PIN2, n.const(u"16#07", y=y + 294))],
                    [POUT], x=F.COL_BLK2 + 320, y=y + 280)
    dst_b = n.block(u"AND", [(PIN1, grp), (PIN2, n.const(u"16#07", y=y + 334))],
                    [POUT], x=F.COL_BLK2 + 320, y=y + 320)
    dst_c = n.block(u"OR", [(PIN1, dst_a), (PIN2, dst_b)], [POUT],
                    x=F.COL_BLK2 + 480, y=y + 300)
    is_ld = b_or(n, F.COL_BLK2 + 480, y + 240, r_ldahl, r_ldahl)
    #  O S O B Y J  S L U Ch A J  INC A / DEC A (3Ch / 3Dh).
    #  Eto NE pattern "x4/x5"; maski 3Ch = 0011 1100 i 3Dh = 0011 1101
    #  ne dayut nomera registra A. Bez etoj pravki rezul tat INC A
    #  zapisyvalsya v registr 7 (F): izmereno sim_one -- vY = 10h verno,
    #  a GVL_PLCVisu.A ostavalsya 0Fh.
    ia3c = eq_const(0x3C, F.COL_BLK2 + 320, y + 300)
    ia3d = eq_const(0x3D, F.COL_BLK2 + 320, y + 340)
    ia12 = b_or(n, F.COL_BLK2 + 480, y + 320, ia3c, ia3d)
    dst_a0 = b_sel(n, F.COL_BLK2 + 480, y + 260, ia12, dst_c,
                    n.const(u"BYTE#00", y=y + 274))
    dst_sel = b_sel(n, F.COL_BLK2 + 480, y + 200, is_ld, sd_sum2, dst_a0)

    # --- Sel_Src ---
    src_b = n.block(u"AND", [(PIN1, grp), (PIN2, n.const(u"16#07", y=y + 374))],
                    [POUT], x=F.COL_BLK2, y=y + 360)
    src_a = n.block(u"AND", [(PIN1, n4), (PIN2, n.const(u"16#07", y=y + 414))],
                    [POUT], x=F.COL_BLK2, y=y + 400)
    src_hl = sel_byte(r_ldahl, 8, y + 440, xx=F.COL_BLK2)
    src_imm = sel_byte(r_ldn, 9, y + 480, xx=F.COL_BLK2)
    src_sum = b_or(n, F.COL_BLK2 + 160, y + 380, src_a, src_b)
    src_sum2 = b_or(n, F.COL_BLK2 + 160, y + 420, src_sum, src_hl)
    src_sum3 = b_or(n, F.COL_BLK2 + 160, y + 460, src_sum2, src_imm)
    is_load = b_or(n, F.COL_BLK2 + 320, y + 400, is_ld, r_ldn)
    src_sel = b_sel(n, F.COL_BLK2 + 320, y + 380, is_load, src_sum3, dst_a0)
"""
rep(OLD_SEL, u"")

# --------------------------------------------- 6. Ctl_IncDec -- cherez masku IR
OLD_INC = u"""    # --- Ctl_IncDec: opkody x4/x5 (INC/DEC r) i 3C/3D (INC/DEC A) ---
    g5 = n.block(u"EQ", [(PIN1, grp), (PIN2, n.const(u"16#04", y=y + 574))],
                 [POUT], x=F.COL_BLK2, y=y + 560)
    g6 = n.block(u"EQ", [(PIN1, grp), (PIN2, n.const(u"16#05", y=y + 614))],
                 [POUT], x=F.COL_BLK2, y=y + 600)
    g45 = b_or(n, F.COL_BLK2 + 160, y + 580, g5, g6)
    a1 = eq_const(0x3C, F.COL_BLK2 + 160, y + 640)
    a2 = eq_const(0x3D, F.COL_BLK2 + 160, y + 680)
    a12 = b_or(n, F.COL_BLK2 + 320, y + 660, a1, a2)
    incdec = b_or(n, F.COL_BLK2 + 480, y + 620, g45, a12)
"""
NEW_INC = u"""    #  C T L _ I N C D E C  -- "operand raven 1".
    #  B Y L O  otdel'no sobiralos' iz grp = 4/5 i opkodov 3Ch/3Dh. No maska
    #  "IR AND C7h" uzhe pokryvaet i to, i drugoe:
    #      3Ch AND C7h = 04h  -- INC A, ona zhe vetka "INC r"
    #      3Dh AND C7h = 05h  -- DEC A
    #  poetomu otdel'naya proverka opkodov ne nuzhna: odin signal vmesto treh.
    incdec = is_incdec_r
"""
rep(OLD_INC, NEW_INC)

# ---------------------------------------- 7. Ctl_Imm_Mode: maska vmesto r_ldn
rep(u"""                                             r_ldn, r_call),""",
    u"""                                             imm_ldn, r_call),""")

# ------------------------------------------ 8. vyhody dekodera: real'nye signaly
rep(u"""        (u"Ctl_Wr_Enable", n.const(u"TRUE", y=y + 600), F.COL_OUT),""",
    u"""        (u"Ctl_Wr_Enable", wr_en, F.COL_OUT),""")
rep(u"""        (u"Ctl_Mem_Rd", b_or(n, F.COL_BLK2 + 480, y + 260,
                             b_or(n, F.COL_BLK2 + 480, y + 220, r_ldahl, r_ldahl),
                             r_ldahl), F.COL_OUT),
        (u"Ctl_Mem_Wr", r_ldhla, F.COL_OUT),""",
    u"""        (u"Ctl_Mem_Rd", mem_rd, F.COL_OUT),
        (u"Ctl_Mem_Wr", mem_wr, F.COL_OUT),""")

io.open(GEN, u"w", encoding=u"utf-8").write(t)
print(u"gen_z80.py: %d zamen" % cnt)
print(u"nonascii:", sum(1 for ch in t if ord(ch) > 127))
