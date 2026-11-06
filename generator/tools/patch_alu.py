# -*- coding: utf-8 -*-
u"""PATCH_ALU -- pravil'nye flagi Z80, vtoroj port chteniya i mux operanda A.

T R I  V E Shch I, vse izmerennye na progone soroka proverok.

1) O P E R A N D  A  U  A L U. Vhod A byl zhestko podklyuchen k registru A.
   Dlya "INC B" eto neverno: ALU schital A+1 i zapisyval rezul tat v B.
   Dlya "LD r,r'" -- tem bolee: tam nuzhno Y = perenosimoe znachenie, a ne
   A + perenosimoe. Teper u registrovogo fajla est vtoroj port chteniya
   Dst_Val (vybor po Sel_Dst), a pered ALU stoit mux:
        Y-osnova = SEL(Ctl_Flags_En, BYTE#0, Dst_Val)
   Smysl: flagi menyayutsya rovno u teh komand, gde ALU schitaet ot A
   (gruppa 80h..BFh i INC/DEC). U ostal nyh (LD, IN, JP) ALU rabotaet kak
   povtoritel: Y = operand, i imenno on popadaet v priemnik.

2) F L A G I. Bylo:
      Flag_N = SEL(Is_Logic, Is_Sub, FALSE)   -- SUB NE stavil N nikogda;
      Flag_C = SEL(Is_Sub, Add_C, Sub_C)      -- logika mogla dat perenos;
      Flag_H = poluperenos AND Is_Arith       -- AND ne stavil H;
      Op 7 (CP) ne popadal ni v odnu vetku.
   Teper po pravilam Z80:
      N = 1 dlya SUB/SBC/CP;
      C = zaym dlya SUB/SBC/CP, perenos dlya ADD/ADC, 0 dlya logiki;
      H = poluperenos dlya arifmetiki, 1 dlya AND, 0 dlya OR/XOR;
      PV = perepolnenie dlya arifmetiki, chetnost dlya logiki.

3) P O L U B A J T Y  F 5  i  F 3 (neoficial'nye, no real'nye: oni berutsya
   iz rezul tata). Stoyali zhestko FALSE, teper berutsya iz bitov 5 i 3.

Vse promezhutochnye signaly -- imenovannye peremennye (pravilo pro fan-out).
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


# ------------------------------------------------ 1. registrovaya chast: Dst_Val
rep(u"""    p.var_out(u"Src_Val", u"BYTE", u"vybrannoe znachenie")""",
    u"""    p.var_out(u"Src_Val", u"BYTE", u"vybrannoe znachenie")
    #  V T O R O J  P O R T  Ch T E N I Ya: znachenie registra-priemnika.
    #  Nuzhen, chtoby ALU schital "priemnik + operand", a ne "A + operand":
    #  bez nego "INC B" uvelichival A i zapisyval ego v B.
    p.var_out(u"Dst_Val", u"BYTE", u"znachenie registra-priemnika")""")

rep(u"""    nr.outvar(u"Src_Val", v, x=F.COL_OUT, y=40)""",
    u"""    nr.outvar(u"Src_Val", v, x=F.COL_OUT, y=40)

    # --- vtoroj port chteniya: registr-priemnik po Sel_Dst -------------------
    nd = p.network(u"CHTENIE PRIEMNIKA: vybor registra po Sel_Dst")
    y = 30
    c_sd = nd.invar(sd, y=y)
    y += 50
    regs_d = []
    for nm in NAMES:
        regs_d.append(nd.invar(nm + u"_In", y=y))
        y += 30
    cases_d = []
    for k in range(16):
        ck = nd.const(u"%d" % k, y=y)
        y += 30
        eq = b_eq(nd, F.COL_BLK, y - 15, c_sd, ck)
        cases_d.append((eq, regs_d[k]))
    vd = sel_chain(nd, c_sd, regs_d[15], cases_d, x=F.COL_BLK2, y0=40,
                   ystep=50, tip=u"BYTE")
    nd.outvar(u"Dst_Val", vd, x=F.COL_OUT, y=40)""")

# ------------------------------------- 2. podklyuchenie novogo vyhoda v vyzovah
rep(u"""             [u"Src_Val", u"A", u"B", u"C", u"D", u"E", u"H", u"L", u"F",
              u"Sa", u"Sb", u"Sc", u"Sd", u"Se", u"Sh", u"Sl", u"Sf",
              u"Addr_HL"],
             x=F.COL_BLK2, y=30, instance=u"fbRFRd")""",
    u"""             [u"Src_Val", u"Dst_Val", u"A", u"B", u"C", u"D", u"E", u"H",
              u"L", u"F", u"Sa", u"Sb", u"Sc", u"Sd", u"Se", u"Sh", u"Sl",
              u"Sf", u"Addr_HL"],
             x=F.COL_BLK2, y=30, instance=u"fbRFRd")""")

rep(u"""    n5.outvar(u"vRFRd_Addr_HL", n5.invar(u"fbRFRd.Addr_HL", y=30))""",
    u"""    n5.outvar(u"vDstVal", n5.invar(u"fbRFRd.Dst_Val", y=30))
    n5.outvar(u"vRFRd_Addr_HL", n5.invar(u"fbRFRd.Addr_HL", y=30))""")

rep(u"""              [u"Src_Val", u"A", u"B", u"C", u"D", u"E", u"H", u"L", u"F",
               u"Sa", u"Sb", u"Sc", u"Sd", u"Se", u"Sh", u"Sl", u"Sf",
               u"Addr_HL"],
              x=F.COL_BLK2, y=30, instance=u"fbRF")""",
    u"""              [u"Src_Val", u"Dst_Val", u"A", u"B", u"C", u"D", u"E", u"H",
               u"L", u"F", u"Sa", u"Sb", u"Sc", u"Sd", u"Se", u"Sh", u"Sl",
               u"Sf", u"Addr_HL"],
              x=F.COL_BLK2, y=30, instance=u"fbRF")
    n10.outvar(u"vDstValW", n10.invar(u"fbRF.Dst_Val", y=520),
               x=F.COL_OUT + 600, y=520)""")

rep(u"""    p.var(u"vMemWrStb", u"BOOL", u"strob zapisi pamyati (s taktom)")""",
    u"""    p.var(u"vDstVal", u"BYTE", u"znachenie registra-priemnika")
    p.var(u"vDstValW", u"BYTE", u"to zhe u ekzemplyara zapisi (ne ispol zuetsya)")
    p.var(u"vALU_A", u"BYTE", u"pervyj operand ALU")
    p.var(u"vMemWrStb", u"BOOL", u"strob zapisi pamyati (s taktom)")""")

# ------------------------------------------ 3. mux operanda A pered ALU --------
rep(u"""    n8.block(u"FB_ALU_Z80",
             [(u"A", n8.invar(u"fbRFRd.A", y=310)),""",
    u"""    #  P E R V Y J  O P E R A N D  A L U.
    #  B Y L O: vhod A zhestko podklyuchen k registru A. Dlya "INC B" eto
    #  neverno (schitalos A+1 i pisалось v B), a dlya "LD r,r'" eshche i
    #  liwno: nuzhno Y = perenosimoe znachenie, a ne A + perenosimoe.
    #  T E P E R': dlya komand, kotorye menyayut flagi (gruppa ALU i INC/DEC),
    #  ALU schitaet ot registra-priemnika (port Dst_Val), a dlya vseh ostal nyh
    #  pervyj operand = 0, i ALU rabotaet povtoritelem: Y = operand.
    c8_fe = n8.invar(u"vCtl_Flags_En", y=500)
    c8_dv = n8.invar(u"vDstVal", y=540)
    alu_a = b_sel(n8, F.COL_BLK, 500, c8_fe, n8.const(u"BYTE#0", y=514), c8_dv)
    n8.outvar(u"vALU_A", alu_a, x=F.COL_OUT, y=500)
    n8.block(u"FB_ALU_Z80",
             [(u"A", n8.invar(u"vALU_A", y=310)),""")

# ------------------------------------------------- 4. flagi S Z H N C ---------
BEGIN = u"""    n4 = p.network(u"FLAGI: S Z H N C")"""
END = u"""    n5.outvar(u"Flag_PV", pv, x=F.COL_OUT + 900, y=200)
"""
i = t.find(BEGIN)
j = t.find(END)
assert i > 0 and j > i, (i, j)
j += len(END)

NEW = u'''    n4 = p.network(u"FLAGI: S Z H N C")
    c_y = n4.invar(u"Y", y=30)
    c_i7 = n4.const(u"16#80", y=70)
    c_z0 = n4.const(u"0", y=110)
    c_addc = n4.invar(u"Add_C", y=150)
    c_subc = n4.invar(u"Sub_C", y=190)
    c_issub = n4.invar(u"Is_Sub", y=430)
    c_islog = n4.invar(u"Is_Logic", y=470)
    c_isar = n4.invar(u"Is_Arith", y=510)
    c_op = n4.invar(op, y=550)
    c_op_b = n4.invar(op, y=590)
    # S = bit 7 rezul tata
    v_s_mask = n4.block(u"AND", [(PIN1, c_y), (PIN2, c_i7)], [POUT],
                        x=F.COL_BLK, y=30)
    v_s = b_eq(n4, F.COL_BLK, 60, v_s_mask, c_i7)
    n4.outvar(u"Flag_S", v_s, x=F.COL_OUT, y=30)
    # Z = rezul tat raven nulyu
    v_z = b_eq(n4, F.COL_BLK, 110, c_y, c_z0)
    n4.outvar(u"Flag_Z", v_z, x=F.COL_OUT, y=110)

    #  Ch T O  B Y L O  N E  T A K  V  F L A G A H:
    #      Flag_N = SEL(Is_Logic, Is_Sub, FALSE)
    #  -- u SUB N stanovilsya NULEM, potomu chto dlya arifmetiki Is_Logic
    #  lozh, i vybor shel v vetku FALSE. A op 7 (CP) ne popadal ni tuda, ni
    #  syuda: on logicheskij (op >= 4), no NE SUB, hotya vedet sebya kak SUB.
    #  Teper est odin imenovannyj priznak "eto vychitanie/zaym" dlya N i C,
    #  on zhe ispol zuetsya dlya perepolneniya.
    n4.outvar(u"vIsCp", b_eq(n4, F.COL_BLK, 550, c_op,
                             n4.const(u"16#07", y=564)),
              x=F.COL_OUT, y=550)
    n4.outvar(u"vBorrow", b_or(n4, F.COL_BLK, 610, c_issub,
                               n4.invar(u"vIsCp", y=624)),
              x=F.COL_OUT, y=610)
    #  C: dlya logiki 0, dlya SUB/SBC/CP -- zaym, dlya ADD/ADC -- perenos
    n4.outvar(u"vAddCM", b_and(n4, F.COL_BLK, 660, c_addc,
                               b_not(n4, F.COL_BLK, 690, c_islog)),
              x=F.COL_OUT, y=660)
    n4.outvar(u"Flag_C", b_sel(n4, F.COL_BLK2, 660,
                               n4.invar(u"vBorrow", y=660),
                               n4.invar(u"vAddCM", y=690), c_subc),
              x=F.COL_OUT + 140, y=30)
    #  N = 1 dlya SUB/SBC/CP
    n4.outvar(u"Flag_N", n4.invar(u"vBorrow", y=740),
              x=F.COL_OUT + 140, y=110)

    # ---- poluperenos H: perenos iz bita 3 v bit 4 ----
    #  F O R M U L A:  H = ((A AND 0Fh) + (B AND 0Fh)) AND 10h  <>  0
    c_i0f = n4.const(u"16#0F", y=210)
    c_i10 = n4.const(u"16#10", y=250)
    c_a4 = n4.invar(a, y=270)
    c_b4h = n4.invar(b, y=300)
    ha = n4.block(u"AND", [(PIN1, c_a4), (PIN2, c_i0f)], [POUT],
                  x=F.COL_BLK, y=270)
    hb = n4.block(u"AND", [(PIN1, c_b4h), (PIN2, c_i0f)], [POUT],
                  x=F.COL_BLK, y=300)
    hsum = b_add(n4, F.COL_BLK2, 280, ha, hb)
    hmask = n4.block(u"AND", [(PIN1, hsum), (PIN2, c_i10)], [POUT],
                     x=F.COL_BLK2 + 160, y=290)
    h_bit = b_eq(n4, F.COL_BLK2 + 320, 300, hmask, c_i10)
    n4.outvar(u"vHBit", b_and(n4, F.COL_BLK2 + 480, 320, h_bit, c_isar),
              x=F.COL_OUT + 600, y=300)
    #  H dlya logiki: u AND on V S E G D A 1, u OR i XOR -- 0. Poetomu vetyka
    #  ne "poluperenos", a nomer operacii: op = 4 -- eto AND.
    n4.outvar(u"vIsAnd", b_eq(n4, F.COL_BLK, 590, c_op_b,
                              n4.const(u"16#04", y=604)),
              x=F.COL_OUT, y=590)
    n4.outvar(u"Flag_H", b_sel(n4, F.COL_BLK2, 780,
                               c_islog,
                               n4.invar(u"vIsAnd", y=780),
                               n4.invar(u"vHBit", y=794)),
              x=F.COL_OUT + 600, y=340)

    # ---------------- 5. P/V: chetnost dlya logiki, perepolnenie dlya arifm ----
    n5 = p.network(u"P/V: chetnost XOR-cepochkoj (logika) ili perepolnenie")
    c_y5 = n5.invar(u"Y", y=30)
    c_islog5 = n5.invar(u"Is_Logic", y=470)
    bits = []
    yy = 30
    for i in range(8):
        sh = b_shr(n5, F.COL_BLK, yy, c_y5, n5.const(u"%d" % i, y=yy + 14))
        m1 = n5.const(u"1", y=yy + 24)
        bt = n5.block(u"AND", [(PIN1, sh), (PIN2, m1)], [POUT],
                      x=F.COL_BLK2, y=yy)
        bits.append(bt)
        yy += 50
    xo = bits[0]
    xo = n5.block(u"XOR", [(PIN1, xo), (PIN2, bits[1])], [POUT],
                  x=F.COL_BLK2 + 160, y=30)
    for i in range(2, 8):
        xo = n5.block(u"XOR", [(PIN1, xo), (PIN2, bits[i])], [POUT],
                      x=F.COL_BLK2 + 160, y=30 + (i - 1) * 45)
    #  XOR vseh vos mi bitov daet 1 pri NEChETNOM chisle edinic. Z80 stavit
    #  P/V = 1 pri Ch E T N O M, znachit sravnivaem s nulem.
    n5.outvar(u"vPar", b_eq(n5, F.COL_BLK2 + 320, 30, xo,
                            n5.const(u"0", y=44)),
              x=F.COL_OUT + 900, y=60)
    #  perepolnenie: ADD -- (A.7 = B.7) i (A.7 <> Y.7);
    #                SUB -- (A.7 <> B.7) i (A.7 <> Y.7)
    c_a5 = n5.invar(a, y=420)
    c_b5 = n5.invar(b, y=460)
    sa = n5.block(u"AND", [(PIN1, c_a5), (PIN2, n5.const(u"16#80", y=434))],
                  [POUT], x=F.COL_BLK2 + 320, y=420)
    sb = n5.block(u"AND", [(PIN1, c_b5), (PIN2, n5.const(u"16#80", y=474))],
                  [POUT], x=F.COL_BLK2 + 320, y=460)
    sy = n5.block(u"AND", [(PIN1, c_y5), (PIN2, n5.const(u"16#80", y=514))],
                  [POUT], x=F.COL_BLK2 + 320, y=500)
    n5.outvar(u"vEqAb", b_eq(n5, F.COL_BLK2 + 480, 420, sa, sb),
              x=F.COL_OUT + 700, y=420)
    n5.outvar(u"vNeAy", b_not(n5, F.COL_BLK2 + 480, 500,
                              b_eq(n5, F.COL_BLK2 + 480, 540, sa, sy)),
              x=F.COL_OUT + 700, y=500)
    n5.outvar(u"Ovf_Add", b_and(n5, F.COL_BLK2 + 640, 420,
                                n5.invar(u"vEqAb", y=420),
                                n5.invar(u"vNeAy", y=434)),
              x=F.COL_OUT + 700, y=460)
    n5.outvar(u"Ovf_Sub", b_and(n5, F.COL_BLK2 + 640, 480,
                                b_not(n5, F.COL_BLK2 + 640, 480,
                                      n5.invar(u"vEqAb", y=494)),
                                n5.invar(u"vNeAy", y=508)),
              x=F.COL_OUT + 700, y=520)
    pv_arith = b_sel(n5, F.COL_BLK2 + 800, 440,
                     n5.invar(u"vBorrow", y=440),
                     n5.invar(u"Ovf_Add", y=430),
                     n5.invar(u"Ovf_Sub", y=460))
    n5.outvar(u"Flag_PV", b_sel(n5, F.COL_BLK2 + 960, 200, c_islog5,
                                pv_arith,
                                n5.invar(u"vPar", y=214)),
              x=F.COL_OUT + 900, y=200)
'''
t = t[:i] + NEW + t[j:]
cnt += 1

#  vBorrow nuzhen i v seti 5 -- obyavlyaem ego v POU
rep(u"""    p.var(u"Ovf_Add", u"BOOL", u"perepolnenie pri slozhenii (tip zakreplen)")""",
    u"""    p.var(u"vIsCp", u"BOOL", u"komanda CP (op = 7)")
    p.var(u"vBorrow", u"BOOL", u"vychitanie ili CP: N = 1, C -- zaym")
    p.var(u"vAddCM", u"BOOL", u"perenos dlya ADD/ADC (u logiki vsegda 0)")
    p.var(u"vHBit", u"BOOL", u"poluperenos arifmetiki")
    p.var(u"vIsAnd", u"BOOL", u"operaciya AND (op = 4): H = 1")
    p.var(u"vPar", u"BOOL", u"chetnost rezul tata")
    p.var(u"vEqAb", u"BOOL", u"A.7 = B.7")
    p.var(u"vNeAy", u"BOOL", u"A.7 <> Y.7")
    p.var(u"Ovf_Add", u"BOOL", u"perepolnenie pri slozhenii (tip zakreplen)")""")

# ------------------------------------- 5. F5 / F3 iz rezul tata ---------------
rep(u"""    n9.block(u"FB_FlagsRegZ80",
             [(u"Flag_S", n9.invar(u"fbALU.Flag_S", y=30)),
              (u"Flag_Z", n9.invar(u"fbALU.Flag_Z", y=70)),
              (u"F5", n9.const(u"FALSE", y=110)),""",
    u"""    #  F 5  i  F 3 -- neoficial nyj, no real nyj bait registra F: oni
    #  berutsya iz rezul tata operacii (bity 5 i 3). Stoyali zhestko FALSE.
    c9_y = n9.invar(u"vY", y=470)
    f5 = b_eq(n9, F.COL_BLK, 470,
              n9.block(u"AND", [(PIN1, c9_y), (PIN2, n9.const(u"16#20", y=484))],
                       [POUT], x=F.COL_BLK - 100, y=470),
              n9.const(u"16#20", y=520))
    f3 = b_eq(n9, F.COL_BLK, 550,
              n9.block(u"AND", [(PIN1, n9.invar(u"vY", y=564)),
                                (PIN2, n9.const(u"16#08", y=578))],
                       [POUT], x=F.COL_BLK - 100, y=550),
              n9.const(u"16#08", y=610))
    n9.block(u"FB_FlagsRegZ80",
             [(u"Flag_S", n9.invar(u"fbALU.Flag_S", y=30)),
              (u"Flag_Z", n9.invar(u"fbALU.Flag_Z", y=70)),
              (u"F5", f5),""")

rep(u"""              (u"F3", n9.const(u"FALSE", y=190)),""",
    u"""              (u"F3", f3),""")

io.open(GEN, u"w", encoding=u"utf-8").write(t)
print(u"patch_alu: %d zamen" % cnt)
print(u"nonascii:", sum(1 for ch in t if ord(ch) > 127))
