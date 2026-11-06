# -*- coding: utf-8 -*-
u"""Razryvaem kolco 'registry -> ALU -> registry' na granice POU.

Chto delaem:
  1) v GVL_Regs dobavlyaem pary Rs_R / Nx_R;
  2) vhody FB_RegFileZ80 (oba ekzemplyara) chitayut GVL_Regs.Rs_*;
  3) vyhody zapisyvayutsya v GVL_Regs.Nx_*;
  4) novaya programma PRG_RegLatch (FBD) perenosit Nx_* -> Rs_* i v zerkalo
     GVL_PLCVisu dlya HMI. Ona zapushchena POSLE PLC_PRG.
"""

import io
import os
import sys

sys.stdout.reconfigure(encoding=u"utf-8")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), u"..", u".."))
GEN = os.path.join(ROOT, u"generator", u"gen_z80.py")

PAIRS = ((u"A", u"A"), (u"B", u"B"), (u"C", u"C"), (u"D", u"D"),
         (u"E", u"E"), (u"H", u"H"), (u"L", u"L"), (u"F", u"F"),
         (u"Sa", u"AltA"), (u"Sb", u"AltB"), (u"Sc", u"AltC"),
         (u"Sd", u"AltD"), (u"Se", u"AltE"), (u"Sh", u"AltH"),
         (u"Sl", u"AltL"), (u"Sf", u"AltF"))

t = io.open(GEN, encoding=u"utf-8").read()
n = 0


def rep(old, new, cnt=1):
    global t, n
    assert t.count(old) == cnt, (u"NET: %r  (%d)" % (old[:90], t.count(old)))
    t = t.replace(old, new, cnt)
    n += cnt


# ---------------------------------------------------------------- 1. GVL_Regs
rep(u"    Nx_Sf : BYTE;   (* on zhe posle pereschyota *)\n",
    u"    Nx_Sf : BYTE;   (* on zhe posle pereschyota *)\n"
    u"    Rs_R : BYTE;   (* schetchik obrashchenij k pamyati (proshlyj skan) *)\n"
    u"    Nx_R : BYTE;   (* on zhe posle pereschyota *)\n")

# --------------------------------------------------- 2. vhody oboih ekzemplyarov
for inst in (u"n5", u"n10"):
    for pin, visu in PAIRS:
        old = u'%s.invar(u"GVL_PLCVisu.%s", y=30)' % (inst, visu)
        new = u'%s.invar(u"GVL_Regs.Rs_%s", y=30)' % (inst, pin)
        rep(old, new)

# ------------------------------------------------------- 3. bit C pri vychitanii
rep(u'c_f = n8.invar(u"fbRF.F", y=270)',
    u'c_f = n8.invar(u"GVL_Regs.Rs_F", y=270)')

# --------------------------------------------------------------- 4. registr F
rep(u'n9.outvar(u"GVL_PLCVisu.F", n9.invar(u"vFlags_F", y=90), x=F.COL_OUT, y=430)',
    u'n9.outvar(u"GVL_Regs.Nx_F", n9.invar(u"vFlags_F", y=90), x=F.COL_OUT, y=430)')

# ------------------------------------------- 5. snyatki -> Nx (vmesto zerkala)
rep(u"""    n10b = p.network(u"SET 10b: snyatki registrov v zerkalo dlya HMI")
    for pin, dst in ((u"A", u"GVL_PLCVisu.A"), (u"B", u"GVL_PLCVisu.B"),
                     (u"C", u"GVL_PLCVisu.C"), (u"D", u"GVL_PLCVisu.D"),
                     (u"E", u"GVL_PLCVisu.E"), (u"H", u"GVL_PLCVisu.H"),
                     (u"L", u"GVL_PLCVisu.L"),
                     (u"Sa", u"GVL_PLCVisu.AltA"), (u"Sb", u"GVL_PLCVisu.AltB"),
                     (u"Sc", u"GVL_PLCVisu.AltC"), (u"Sd", u"GVL_PLCVisu.AltD"),
                     (u"Se", u"GVL_PLCVisu.AltE"), (u"Sh", u"GVL_PLCVisu.AltH"),
                     (u"Sl", u"GVL_PLCVisu.AltL"), (u"Sf", u"GVL_PLCVisu.AltF")):
        n10b.outvar(dst, n10b.invar(u"vReg_" + pin, y=30), x=F.COL_OUT, y=30)""",
    u"""    n10b = p.network(u"SET 10b: sleduyushchee sostoyanie registrov -> GVL_Regs")
    for pin in (u"A", u"B", u"C", u"D", u"E", u"H", u"L", u"F",
                u"Sa", u"Sb", u"Sc", u"Sd", u"Se", u"Sh", u"Sl", u"Sf"):
        n10b.outvar(u"GVL_Regs.Nx_" + pin,
                    n10b.invar(u"vReg_" + pin, y=30), x=F.COL_OUT, y=30)""")

# ------------------------------------------------------------------ 6. registr R
rep(u'n14.invar(u"GVL_PLCVisu.R_Reg", y=30)',
    u'n14.invar(u"GVL_Regs.Rs_R", y=30)')
rep(u'n14.outvar(u"GVL_PLCVisu.R_Reg", n14.invar(u"vR_Q", y=60),',
    u'n14.outvar(u"GVL_Regs.Nx_R", n14.invar(u"vR_Q", y=60),')

# ------------------------------------------------ 7. novaya programma-zashchelka
LATCH = u'''def mk_prg_reglatch():
    u"""PRG_RegLatch -- Z A Shch E L K A  S O S T O Ya N I Ya  R E G I S T R O V.

    Zachem otdelnaya programma, a ne set' v PLC_PRG.

    Registrovyj fajl obrazuet kol co: vhod ALU (A) -> rezul tat (vY) ->
    zapis v registr -> snova vhod ALU. Pokuda i chtenie, i zapis' velis
    v odnoj programme, CODESYS schital takoe kol co algebraicheskoj petlej i
    podstavlyal v nego N O L', a ne znachenie proshlogo skana. Izmereno na
    progone: posle vernoj initsializacii (A = 0Fh) v sleduyushchem skane
    registr stanovilsya 0, i komanda INC A davala 1 vmesto 10h.

    Reshenie -- razryv petli N A  G R A N I C E  P O U:
        PLC_PRG       chitaet GVL_Regs.Rs_* i pishet GVL_Regs.Nx_*;
        PRG_RegLatch  perenosit Nx_* v Rs_* i zapushchena POZzhe v zadache.
    Vnutri kazhdoj programmy petli net, poetomu nikakoj Neyavnoj pamyati ne
    trebuetsya, a poryadok skanov ostaetsya predskazuemym.

    Zdes' zhe obnovlyaetsya zerkalo GVL_PLCVisu dlya vizualizacii:
    Rs_* i zerkalo poluchayut odno i to zhe znachenie Nx_*.
    """
    MIRROR = ((u"A", u"A"), (u"B", u"B"), (u"C", u"C"), (u"D", u"D"),
              (u"E", u"E"), (u"H", u"H"), (u"L", u"L"), (u"F", u"F"),
              (u"Sa", u"AltA"), (u"Sb", u"AltB"), (u"Sc", u"AltC"),
              (u"Sd", u"AltD"), (u"Se", u"AltE"), (u"Sh", u"AltH"),
              (u"Sl", u"AltL"), (u"Sf", u"AltF"))
    p = F.Pou(u"PRG_RegLatch", u"program",
              u"ZAshchelka sostoyaniya registrov: Nx_* -> Rs_* i zerkalo HMI.\\n"
              u"Rabotaet POSLE PLC_PRG, poetomu razryvaet kol co "
              u"'registry -> ALU -> registry' na granice POU.")
    y = 30
    nx = p.network(u"LATCH 1: sleduyushchee sostoyanie stanovitsya tekushchim")
    for pin, visu in MIRROR:
        nx.outvar(u"GVL_Regs.Rs_" + pin, nx.invar(u"GVL_Regs.Nx_" + pin, y=y),
                  x=F.COL_OUT, y=y)
        y += 34
    nx.outvar(u"GVL_Regs.Rs_R", nx.invar(u"GVL_Regs.Nx_R", y=y),
              x=F.COL_OUT, y=y)

    y = 30
    hm = p.network(u"LATCH 2: zerkalo dlya vizualizacii (HMI)")
    for pin, visu in MIRROR:
        hm.outvar(u"GVL_PLCVisu." + visu, hm.invar(u"GVL_Regs.Nx_" + pin, y=y),
                  x=F.COL_OUT, y=y)
        y += 34
    hm.outvar(u"GVL_PLCVisu.R_Reg", hm.invar(u"GVL_Regs.Nx_R", y=y),
              x=F.COL_OUT, y=y)
    return p


'''

rep(u"def mk_plc_prg():", LATCH + u"def mk_plc_prg():")

# ---------------------------------------------------- 8. registraciya v spiske
rep(u'    (u"PLC_PRG", mk_plc_prg),\n]',
    u'    (u"PLC_PRG", mk_plc_prg),\n'
    u'    (u"PRG_RegLatch", mk_prg_reglatch),\n]')

io.open(GEN, u"w", encoding=u"utf-8").write(t)
print(u"gen_z80.py: %d zamen" % n)

# ------------------------------------------------------------------- build.py
BUILD = os.path.join(ROOT, u"generator", u"build.py")
b = io.open(BUILD, encoding=u"utf-8").read()
bn = 0


def brep(old, new):
    global b, bn
    assert b.count(old) == 1, (u"NET: %r (%d)" % (old[:80], b.count(old)))
    b = b.replace(old, new, 1)
    bn += 1


brep(u'u"GVL_Disk", u"GVL_CPM_Extra", u"GVL_BootFlags", u"GVL_Tests_CPM"]',
     u'u"GVL_Disk", u"GVL_CPM_Extra", u"GVL_BootFlags", u"GVL_Tests_CPM",\n'
     u'             u"GVL_Regs"]')
brep(u'    u"PRG_CPM_BDOS", u"TEST_Z80_PREP", u"TEST_Z80", u"TEST_Z80_CPM",\n]',
     u'    u"PRG_CPM_BDOS", u"TEST_Z80_PREP", u"TEST_Z80", u"TEST_Z80_CPM",\n'
     u'    u"PRG_RegLatch",\n]')
brep(u'u"TEST_Z80", u"PRG_CPM_BDOS", u"TEST_Z80_CPM", u"PLC_PRG"]',
     u'u"TEST_Z80", u"PRG_CPM_BDOS", u"TEST_Z80_CPM", u"PLC_PRG",\n'
     u'                     u"PRG_RegLatch"]')
io.open(BUILD, u"w", encoding=u"utf-8").write(b)
print(u"build.py: %d zamen" % bn)
