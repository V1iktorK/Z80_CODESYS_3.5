# -*- coding: utf-8 -*-
u"""gen_z80.py -- generator FBD-shem emulyatora Z80 (PLCopenXML dlya CODESYS 3.5 SP17).

Zapuskaetsya OBYCHNYM Python (vne CODESYS): na vyhode poluchayutsya fajly
src/*.plcopenxml, kotorye zatem importiruet drajver build.py uzhe vnutri CODESYS.

Shemy opisyvayutsya kodom: kazhdyj FB stroitsya kak spisok setej (Network),
vnutri seti -- vhodnye peremennye, bloki i vyhodnye peremennye.
Signaly idut strogo sleva napravo.

Biblioteka fbd_xml.py i pravila dialekta vzyaty iz proekta 8080_EMU
(sm. tools/fbd_xml.py, shapka fajla: 6 vyyasnennyh eksperimentalno pravil).
Klyuchevoe iz nih: CODESYS 3.5 SP17 molcha vybrasyvaet POU, esli kakoj-libo
vyhod pitaet bolshe odnogo vhoda, -- biblioteka lechit eto klonirovaniem
vetvej (_expand_fanout), no dlya zapominayushchih blokov klonirovat nelzya,
poetomu takie signaly v nashih shemah vyvodyatsya v otdelnuyu peremennuyu.
"""

import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "tools"))

import fbd_xml as F

ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "src")
LOG = os.path.join(ROOT, "log", "gen_z80.log")

# ---------------------------------------------------------------------------
# Imena vyvodov blokov.
#
# VYYASNENO EKSPERIMENTALNO (generator/probe/probe_pins.py, probe_ops_import.py):
# import XML padaet s oshibkoj "Otsutstvuet obyazatelnyj atribut formalParameter",
# esli u LYUBOGO vhoda bloka ne ukazano imya vyvoda. Pustaya stroka ne goditsya --
# atribut dolzhen prisutstvovat. Pri etom CODESYS sopostavlyaet vyvody
# PO POZICII, poetomu konkretnye imena ne vazhny; vazhna lish ih nepustota.
# Dlya naglyadnosti ispolzuem tradicionnye IN1/IN2/IN.
# ---------------------------------------------------------------------------
PIN1 = u"IN1"
PIN2 = u"IN2"
PINU = u"IN"
POUT = u"OUT"
# SEL: vhod vybora + dva informacionnyh vhoda; MUX: to zhe (K -- nomer vhoda)
SEL_G = u"G"
MUX_K = u"K"

_lines = []


def log(m):
    _lines.append(u"%s" % (m,))


def flush_log():
    f = io.open(LOG, "w", encoding="utf-8")
    f.write(u"\n".join(_lines) + u"\n")
    f.close()


# =============================================================================
#  Opisanie shem
# =============================================================================

def mk_reg8():
    u"""FB_Reg8 -- 8-bitnyj registr so strobirovaniem zapisi i sbrosom.

    Q := 0, esli CLR; inache D, esli EN; inache prezhnee Q.

    Realizaciya: odin blok SEL, vyhod kotorogo zaveden obratno na IN0.
    Imenno eta obratnaya svyaz i est pamyat (v FBD drugogo sposoba net).
    """
    p = F.Pou(u"FB_Reg8", u"functionBlock",
              u"8-bitnyj registr so strobirovannoj zapis'yu i sBrosom.\n"
              u"Q := 0 pri CLR; inache D pri EN; inache prezhnee Q.")
    d = p.var_in(u"D", u"BYTE", u"dannye dlya zapisi")
    en = p.var_in(u"EN", u"BOOL", u"razreshenie zapisi")
    clr = p.var_in(u"CLR", u"BOOL", u"sBros (prioritet vyshe EN)")
    p.var_out(u"Q", u"BYTE", u"tekuchee sostoyanie")

    n = p.network(u"WR zapisi: EN i NE CLR")
    # poryadok vazhen dlya chitaemosti: NOT -> AND -> SEL
    c_clr = n.invar(clr, y=90)
    c_en = n.invar(en, y=50)
    c_d = n.invar(d, y=20)
    c_q = n.invar(u"Q", y=120)          # obratnaya svyaz (chtenie vyhodnoj peremennoj)

    v_not = n.block(u"NOT", [(PINU, c_clr)], [POUT], x=F.COL_BLK, y=90)
    v_and = n.block(u"AND", [(PIN1, c_en), (PIN2, v_not)], [POUT],
                    x=F.COL_BLK2, y=50)
    v_sel = n.block(u"SEL", [(u"G", v_and), (u"IN0", c_q), (u"IN1", c_d)],
                    [u"OUT"], x=F.COL_BLK2 + 160, y=50)
    n.outvar(u"Q", v_sel, x=F.COL_OUT + 140, y=50)
    return p


def mk_reg16():
    u"""FB_Reg16 -- to zhe, chto FB_Reg8, no 16 bit (WORD)."""
    p = F.Pou(u"FB_Reg16", u"functionBlock",
              u"16-bitnyj registr so strobirovannoj zapis'yu i sBrosom.\n"
              u"Polnaya kopiya FB_Reg8 s tipom WORD.")
    d = p.var_in(u"D", u"WORD", u"dannye dlya zapisi")
    en = p.var_in(u"EN", u"BOOL", u"razreshenie zapisi")
    clr = p.var_in(u"CLR", u"BOOL", u"sBros")
    p.var_out(u"Q", u"WORD", u"tekuchee sostoyanie")

    n = p.network(u"WR zapisi: EN i NE CLR")
    c_clr = n.invar(clr, y=90)
    c_en = n.invar(en, y=50)
    c_d = n.invar(d, y=20)
    c_q = n.invar(u"Q", y=120)

    v_not = n.block(u"NOT", [(PINU, c_clr)], [POUT], x=F.COL_BLK, y=90)
    v_and = n.block(u"AND", [(PIN1, c_en), (PIN2, v_not)], [POUT],
                    x=F.COL_BLK2, y=50)
    v_sel = n.block(u"SEL", [(u"G", v_and), (u"IN0", c_q), (u"IN1", c_d)],
                    [u"OUT"], x=F.COL_BLK2 + 160, y=50)
    n.outvar(u"Q", v_sel, x=F.COL_OUT + 140, y=50)
    return p


def mk_rtrig():
    u"""FB_RTrig -- detektor perednego fronta: Q := CLK AND NOT M.

    M -- pamyat' predydushchego znacheniya CLK (obratnaya svyaz' cherez SEL).
    Napisan sami, a ne vzyat iz biblioteki Standard: v etoj ustanovke
    biblioteka daet oshibku C77 (otsutstvuet zavisimost' CBML).
    """
    p = F.Pou(u"FB_RTrig", u"functionBlock",
              u"Detektor perednego fronta.\nQ := CLK AND NOT M, gde M -- predydushchij CLK.")
    clk = p.var_in(u"CLK", u"BOOL", u"vhodnoj signal")
    clr = p.var_in(u"CLR", u"BOOL", u"sBros pamyati")
    p.var_out(u"Q", u"BOOL", u"impul's odin skan pri 0->1")
    p.var_out(u"M", u"BOOL", u"predydushchee znachenie CLK (dlya otladki)")

    n = p.network(u"front: CLK i NE M")
    c_clk = n.invar(clk, y=40)
    c_clr = n.invar(clr, y=140)
    c_m = n.invar(u"M", y=90)

    v_not = n.block(u"NOT", [(PINU, c_m)], [POUT], x=F.COL_BLK, y=90)
    v_and = n.block(u"AND", [(PIN1, c_clk), (PIN2, v_not)], [POUT],
                    x=F.COL_BLK2, y=40)
    n.outvar(u"Q", v_and, x=F.COL_OUT, y=40)
    v_sel = n.block(u"SEL", [(u"G", c_clr), (u"IN0", c_m), (u"IN1", c_clk)],
                    [u"OUT"], x=F.COL_BLK2, y=120)
    n.outvar(u"M", v_sel, x=F.COL_OUT, y=120)
    return p


def mk_ftrig():
    u"""FB_FTrig -- detektor zadnego fronta: Q := NOT CLK AND M."""
    p = F.Pou(u"FB_FTrig", u"functionBlock",
              u"Detektor zadnego fronta.\nQ := NOT CLK AND M, gde M -- predydushchij CLK.")
    clk = p.var_in(u"CLK", u"BOOL", u"vhodnoj signal")
    clr = p.var_in(u"CLR", u"BOOL", u"sBros pamyati")
    p.var_out(u"Q", u"BOOL", u"impul's odin skan pri 1->0")
    p.var_out(u"M", u"BOOL", u"predydushchee znachenie CLK")

    n = p.network(u"zadnij front: NE CLK i M")
    c_clk = n.invar(clk, y=40)
    c_clr = n.invar(clr, y=140)
    c_m = n.invar(u"M", y=90)

    v_not = n.block(u"NOT", [(PINU, c_clk)], [POUT], x=F.COL_BLK, y=40)
    v_and = n.block(u"AND", [(PIN1, v_not), (PIN2, c_m)], [POUT],
                    x=F.COL_BLK2, y=60)
    n.outvar(u"Q", v_and, x=F.COL_OUT, y=60)
    v_sel = n.block(u"SEL", [(u"G", c_clr), (u"IN0", c_m), (u"IN1", c_clk)],
                    [u"OUT"], x=F.COL_BLK2, y=120)
    n.outvar(u"M", v_sel, x=F.COL_OUT, y=120)
    return p


def mk_rs():
    u"""FB_RS -- trigger s prioritetom sbrosa: Q1 := 0 pri RESET, inache SET."""
    p = F.Pou(u"FB_RS", u"functionBlock",
              u"Trigger s prioritetom SBROSA.\nQ1 := FALSE pri RESET, inache SET, inache prezhnee.")
    st = p.var_in(u"SET", u"BOOL", u"ustanovit'")
    rs = p.var_in(u"RESET", u"BOOL", u"snyat' (prioritet vyshe SET)")
    p.var_out(u"Q1", u"BOOL", u"tekuchee sostoyanie")

    n = p.network(u"zapis': RESET ili SET")
    c_set = n.invar(st, y=40)
    c_res = n.invar(rs, y=90)
    c_q = n.invar(u"Q1", y=140)

    v_not = n.block(u"NOT", [(PINU, c_res)], [POUT], x=F.COL_BLK, y=90)
    v_and = n.block(u"AND", [(PIN1, v_not), (PIN2, c_set)], [POUT],
                    x=F.COL_BLK2, y=40)
    v_or = n.block(u"OR", [(PIN1, v_and), (PIN2, c_res)], [POUT],
                   x=F.COL_BLK2 + 160, y=60)
    v_sel = n.block(u"SEL", [(u"G", v_or), (u"IN0", c_q), (u"IN1", c_set)],
                    [u"OUT"], x=F.COL_BLK2 + 320, y=60)
    n.outvar(u"Q1", v_sel, x=F.COL_OUT + 300, y=60)
    return p


# =============================================================================
#  Vspomogatelnye postroiteli
# =============================================================================

def sel_chain(n, g, in0, cases, x=200, y0=40, ystep=55, tip=None):
    u"""Cepochka SEL: posledovatelnyj vybor odnogo iz neskolkih znachenij.

    cases -- spisok (istochnik-uslovie BOOL, istochnik-znachenie).
    Ekran == TRUE -> beretsya ego znachenie, inache idem dalshe.
    Poslednij sluchaj primenyaetsya, kogda vse usloviya lozhny (rezervnyj put).

    Tak realizuetsya MUX bez fan-out: znachenie usloviya ispolzuetsya rovno
    odin raz, poetomu biblioteka ne stanet klonirovat vetvi.

    T I P  C E P O Ch K I  Z A D A E T S Ya  Ya V N O (parametr tip).
    P O Ch E M U. V IEC 61131-3 blok SEL obobshchennyj (ANY): ego tip
    vyvoditsya po vetkam IN0/IN1. Kogda v odnoj cepochke vstrechayutsya
    raznye tipy -- naprimer odna vetka daet BOOL, a drugaya BYTE, --
    CODESYS ne mozhet ih soglasovat i vybiraet USINT dlya vseh. V otchyote
    eto vyglyadit kak pohavnye pary, kotorye nikak ne svyazat s konkretnym
    POU (ni imeni, ni nomera stroki):
        C32: Nevozmozhno konvertirovat tip 'BOOL' v tip 'USINT'
        C32: Nevozmozhno konvertirovat tip 'USINT' v tip 'BOOL'
    Imenno eti 8 par i byli v FB_ALU_Z80.

    Kak lechim: kazhdaya vetka (i rezervnaya IN0, i kazhdyj vybor) snachala
    popadaet v SOBSTVENNUYU peremennuyu N U Zh N O G O tipa. Cherez
    sootvetstvuyushchuyu konversiyu (BOOL_TO_BOOL, BYTE_TO_BYTE i t. d.)
    znachenie stanovitsya odnoznachno tipizirovannym, i vse vetki SEL
    stanovyatsya odnogo tipa.

    V A Zh N O  P O  P O R Ya D K U. Vyhodnye peremennye obyavlyayutsya
    v seti P E R E D blokami, kotorye ih pitayut: biblioteka trebuet,
    chtoby ssylka vsegda shla "nazad". Poetomu vetki sobirayutsya v spiske
    zaranee, a tsepochka SEL stroitsya s K O N Ts A (ot poslednego
    usloviya k pervomu) -- togda peremennaya kazhdoj vetki uzhe obyavlena,
    kogda do nee dohodit ochered.
    """
    tip = (tip or u"BYTE").upper()
    #  T I P I Z A C I Ya  V E T O K -- sm. Network.typed() v fbd_xml.py.
    #  U kazhdoj vetki tip zadayotsya Y A V N O (BYTE#16#00 vmesto 16#00),
    #  poetomu obobshchennyj SEL poluchaet odnoznachnyj tip i pary oshibok
    #  "C32: BOOL <-> USINT" ischezayut.
    #
    #  Chto bylo pereprobovano ranee i N E  P O D O Sh L O (chtoby ne
    #  povtoryat):
    #   1) konversiya "BYTE_TO_BYTE" dlya vetok -- v CODESYS takoy funkcii
    #      NET: 76 oshibok "C46: Identifikator 'BYTE_TO_BYTE' ne zadan";
    #   2) promezhutochnye peremennye v T E L E seti -- CODESYS obyavlyaet
    #      ih "lazy" i ne vyvodit tip;
    #   3) promezhutochnye peremennye v obyavlenii POU so vsemi
    #      prisvoeniyami v odnoj seti -- kompilyator na etom ZAVISAET.
    #  Rabotaet imenno yavnaya tipizaciya literala: vybora u kompilyatora
    #  ne ostayotsya.
    in0 = n.typed(in0, tip)
    cases = [(cond, n.typed(val, tip)) for cond, val in cases]
    cur = in0
    y = y0
    for cond, val in cases:
        d = n.block(u"SEL", [(u"G", cond), (u"IN0", cur), (u"IN1", val)], [POUT],
                    x=x, y=y)
        cur = d
        y += ystep
    return cur


def bool_case(n, x, y, kind, a, b=None):
    u"""Sravnenie: kind='EQ' -> a = b; kind='NE' -> a <> b."""
    if b is None:
        return n.block(kind, [(PINU, a)], [POUT], x=x, y=y)
    return n.block(kind, [(PIN1, a), (PIN2, b)], [POUT], x=x, y=y)


def b_and(n, x, y, a, b):
    return n.block(u"AND", [(PIN1, a), (PIN2, b)], [POUT], x=x, y=y)


def b_or(n, x, y, a, b):
    return n.block(u"OR", [(PIN1, a), (PIN2, b)], [POUT], x=x, y=y)


def b_not(n, x, y, a):
    return n.block(u"NOT", [(PINU, a)], [POUT], x=x, y=y)


def b_sel(n, x, y, g, in0, in1, tip=u"BYTE"):
    u"""Vybor iz dvuh: G=0 -> in0, G=1 -> in1.

    tip -- tip rezul tata, po umolchaniyu u"BYTE".

    P O Ch E M U  T I P  Z A D A E T S Ya  V S E G D A. Blok SEL
    obobshchennyj (ANY): ego tip vyvoditsya po vetkam IN0/IN1.
    Esli odna vetka -- peremennaya BYTE, a drugaya -- "golyj"
    literal 1, kompilyator sam vybiraet tip literala i v cepochke
    iz neskolkih SEL oshibaetsya. V otchyote eto vyglyadit kak pary
        C32: Nevozmozhno konvertirovat tip BOOL v tip USINT
        C32: Nevozmozhno konvertirovat tip USINT v tip BOOL
    bez imeni POU i nomera seti.

    Kak tolko tip peredan, kazhdyj CHISLOVOJ literal v vetke
    perepisyvaetsya v yavnom vide (1 -> BYTE#1), i vybora
    u kompilyatora ne ostayotsya. Peremennye i vyhody blokov
    ne tronutsya: u nih tip uzhe est.
    """
    if tip:
        in0 = n.typed(in0, tip)
        in1 = n.typed(in1, tip)
    return n.block(u"SEL", [(u"G", g), (u"IN0", in0), (u"IN1", in1)],
                    [POUT], x=x, y=y)


def b_add(n, x, y, a, b):
    return n.block(u"ADD", [(PIN1, a), (PIN2, b)], [POUT], x=x, y=y)


def b_sub(n, x, y, a, b):
    return n.block(u"SUB", [(PIN1, a), (PIN2, b)], [POUT], x=x, y=y)


def b_bool2byte(n, name, x, y, src):
    u"""BOOL -> BYTE, rezul tat GARANTIROVANNO tipa BYTE.

    P O Ch E M U  N E  BOOL_TO_BYTE. Standartnaya konversiya BOOL_TO_BYTE
    v CODESYS daet USINT, a ne BYTE (BYTE -- eto bitovaya stroka, dlya nee
    obobshchennye bloki vyvodyat USINT). Kak tolko takoy vyhod popadaet
    v cepochku SEL, tipy vetok raskhodyatsya, i sborka padaet s
        C32: Nevozmozhno konvertirovat tip 'BOOL' v tip 'USINT'
        C32: Nevozmozhno konvertirovat tip 'USINT' v tip 'BOOL'.

    Zdes strob 0/1 sobiraetsya cherez SEL, u kotorogo OBE vetki --
    yavno tipizirovannye literaly BYTE#0 i BYTE#1. Tip vyvoda
    odnoznachen, poetomu rezul tat mozhno bez opasenij stavit v lyubuyu
    cepochku BYTE.

    P A R A M E T R  name ostavlen radi sovmestimosti vyzovov i bolshe
    ne trebuet obyavleniya peremennoj: ran'she zdes delalas zapis
    v obyavlennyj BYTE, i CODESYS schital takuyu peremennuyu "lazy"
    ("Tip lazy peremennoj ... ne mozhet byt razreshen").
    """
    return n.block(u"SEL",
                   [(u"G", src),
                    (u"IN0", n.const(u"BYTE#0", y=y)),
                    (u"IN1", n.const(u"BYTE#1", y=y + 14))],
                   [POUT], x=x, y=y)


def b_eq(n, x, y, a, b):
    return n.block(u"EQ", [(PIN1, a), (PIN2, b)], [POUT], x=x, y=y)


def b_shl(n, x, y, a, k):
    return n.block(u"SHL", [(PIN1, a), (PIN2, k)], [POUT], x=x, y=y)


def b_shr(n, x, y, a, k):
    return n.block(u"SHR", [(PIN1, a), (PIN2, k)], [POUT], x=x, y=y)


def b_b2w(n, x, y, a):
    return n.block(u"BYTE_TO_WORD", [(PINU, a)], [POUT], x=x, y=y)


def b_w2b(n, x, y, a):
    return n.block(u"WORD_TO_BYTE", [(PINU, a)], [POUT], x=x, y=y)


# =============================================================================
#  Generatory shem (prodolzhenie)
# =============================================================================

def mk_reg8latch():
    u"""FB_Reg8Latch -- registr so VSTROENNOJ zashchelkoj (dlya dvuhfaznogo takta).

    Zashchelka: Latch := EN AND Clk. Zapis proishodit tolko na takte Clk,
    poetomu znachenie, vystavlennoe na shinu v faze dekodirovaniya, ne budet
    isporcheno zapisyu v faze ispolneniya.
    """
    p = F.Pou(u"FB_Reg8Latch", u"functionBlock",
              u"8-bitnyj registr s vstroennoj zashchelkoj.\n"
              u"Zapis' proishodit tol'ko pri EN i Clk (pomehoustojchivo k dvuhfaznomu taktu).")
    d = p.var_in(u"D", u"BYTE", u"dannye")
    en = p.var_in(u"EN", u"BOOL", u"razreshenie zapisi")
    clk = p.var_in(u"Clk", u"BOOL", u"takt: zapis' tol'ko na fronte")
    clr = p.var_in(u"CLR", u"BOOL", u"sBros")
    p.var_out(u"Q", u"BYTE", u"tekuchee sostoyanie")

    n = p.network(u"zashchelka EN i Clk")
    c_d = n.invar(d, y=20)
    c_en = n.invar(en, y=60)
    c_clk = n.invar(clk, y=90)
    c_clr = n.invar(clr, y=140)
    c_q = n.invar(u"Q", y=190)

    v_and = b_and(n, F.COL_BLK, 60, c_en, c_clk)
    v_not = b_not(n, F.COL_BLK, 140, c_clr)
    v_and2 = b_and(n, F.COL_BLK2, 80, v_and, v_not)
    v_sel = b_sel(n, F.COL_BLK2 + 160, 80, v_and2, c_q, c_d)
    n.outvar(u"Q", v_sel, x=F.COL_OUT + 140, y=80)
    return p


def mk_bitunpack8():
    u"""FB_BitUnpack8 -- raspakovka BYTE -> ARRAY[0..7] OF BOOL.

    ZDES PROISHODIT PREOBRAZOVANIE BYTE <-> ARRAY[0..7] OF BOOL.
    Dlya kazhdogo bita: Bits[i] := (In AND 2^i) <> 0.
    """
    p = F.Pou(u"FB_BitUnpack8", u"functionBlock",
              u"Raspakovka BYTE v ARRAY[0..7] OF BOOL.\n"
              u"Bits[0] -- mladshij bit. Primenyaetsya dlya flagov i chetnosti.")
    inp = p.var_in(u"In", u"BYTE", u"ishodnyj bajt")
    p.var_out(u"Bits", u"ARRAY[0..7] OF BOOL", u"bity, Bits[0] = MLD")

    n = p.network(u"raspakovka po bitam")
    c_in = n.invar(inp, y=40)
    y = 40
    for i in range(8):
        mask = n.const(u"16#%02X" % (1 << i), y=y)
        a = n.block(u"AND", [(PIN1, c_in), (PIN2, mask)], [POUT],
                    x=F.COL_BLK, y=y)
        z = n.const(u"0", y=y + 12)
        ne = b_eq(n, F.COL_BLK2, y, z, a)
        n.outvar(u"Bits[%d]" % i, ne, x=F.COL_OUT, y=y)
        y += 45
    return p


def _byte_inv(n, x, y, src):
    u"""Inversiya bajta cherez XOR s FFh (NOT dlya BYTE nenadezhen po tipu)."""
    ff = n.const(u"16#FF", y=y + 14)
    return n.block(u"XOR", [(PIN1, src), (PIN2, ff)], [POUT], x=x, y=y)


def mk_regfile():
    u"""FB_RegFileZ80 -- registrovaya chast Z80: 16 registrov i vyborka.

    Osnovnoj nabor: A B C D E H L F.  Alternativnyj: A' B' C' D' E' H' L' F'.
    Zapis idet v odin registr po Sel_Dst, chtenie -- iz odnogo po Sel_Src.
    Vyborka realizovana cepochkoj SEL (bez fan-out), kod 10 = Mem_Rd (HL),
    kod 11 = Imm (neposredstvennyj operand iz IR).
    """
    p = F.Pou(u"FB_RegFileZ80", u"functionBlock",
              u"Registrovaya chast' Z80: 16 registrov (osnovnoj i alternativnyj nabory).\n"
              u"Zapis' po Sel_Dst, chtenie po Sel_Src cherez cepochku SEL.")
    sd = p.var_in(u"Sel_Dst", u"BYTE", u"nomer registra-priemnika 0..15")
    ss = p.var_in(u"Sel_Src", u"BYTE", u"nomer registra-istochnika 0..11")
    wv = p.var_in(u"Wr_Val", u"BYTE", u"znachenie dlya zapisi")
    we = p.var_in(u"Wr_En", u"BOOL", u"razreshenie zapisi")
    clk = p.var_in(u"Clk", u"BOOL", u"takt zashchelki")
    clr = p.var_in(u"CLR", u"BOOL", u"sBros vseh registrov")
    mem = p.var_in(u"Mem_Rd", u"BYTE", u"znachenie (HL) s shiny")
    imm = p.var_in(u"Imm", u"BYTE", u"neposredstvennyj operand")
    init_en = p.var_in(u"Init_En", u"BOOL",
                       u"rezhim initsializatsii registrov")
    init_dst = p.var_in(u"Init_Sel_Dst", u"BYTE",
                        u"nomer registra pri initsializatsii")
    p.var_out(u"Src_Val", u"BYTE", u"vybrannoe znachenie")
    for v in (u"A", u"B", u"C", u"D", u"E", u"H", u"L", u"F",
              u"Sa", u"Sb", u"Sc", u"Sd", u"Se", u"Sh", u"Sl", u"Sf"):
        p.var_out(v, u"BYTE", u"registr")
    p.var_out(u"Addr_HL", u"WORD", u"adres pary HL (dlya kosvennoj adresatsii)")
    #  S I G N A L Y   Z A P I S I.  Set' zapisi vyrabatyvaet 16 strobov
    #  WE_k (po odnomu na registr), i oni idut v shemu chteniya/zapisi.
    #  Eto obychnye vnutrennie peremennye POU, i bez ih ob''yavleniya
    #  kompilyator soobshchaet "C77: Neizvestnyy tip: 'WE_0'".
    for _k in range(16):
        p.var(u"WE_%d" % _k, u"BOOL", u"razreshenie zapisi registra %d" % _k)

    NAMES = [u"A", u"B", u"C", u"D", u"E", u"H", u"L", u"F",
             u"Sa", u"Sb", u"Sc", u"Sd", u"Se", u"Sh", u"Sl", u"Sf"]

    # --- zapis: 16 kanalov -------------------------------------------------
    nw = p.network(u"ZAPIS': WE_dst := Wr_En i (Sel_Dst = k)")
    c_wv = nw.invar(wv, y=20)
    c_we = nw.invar(we, y=45)
    c_clk = nw.invar(clk, y=70)
    c_clr = nw.invar(clr, y=95)
    c_sd = nw.invar(sd, y=120)
    v_wen = b_and(nw, F.COL_BLK, 45, c_we, c_clk)
    v_nclr = b_not(nw, F.COL_BLK, 95, c_clr)
    v_wok = b_and(nw, F.COL_BLK2, 60, v_wen, v_nclr)
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
        y += 55

    # --- chtenie: cepochka SEL ------------------------------------------------
    nr = p.network(u"CHTENIE: vybor registra po Sel_Src")
    y = 30
    c_ss = nr.invar(ss, y=y)
    y += 50
    c_mem = nr.invar(mem, y=y)
    y += 40
    c_imm = nr.invar(imm, y=y)
    y += 50
    regs = []
    for nm in NAMES:
        regs.append(nr.invar(nm, y=y))
        y += 30
    # rezervnyj put -- neposredstvennyj operand
    cur = (c_imm, c_imm)
    cases = []
    for k in range(11):
        src = c_mem if k == 10 else regs[k]
        ck = nr.const(u"%d" % k, y=y)
        y += 30
        eq = b_eq(nr, F.COL_BLK, y - 15, c_ss, ck)
        cases.append((eq, src))
    #  Src_Val -- eto BYTE (kody registrov 0..11 v pole BYTE).
    v = sel_chain(nr, c_ss, cur[0], cases, x=F.COL_BLK2, y0=40, ystep=50,
                  tip=u"BYTE")
    nr.outvar(u"Src_Val", v, x=F.COL_OUT, y=40)

    # --- adres pary HL: (H shl 8) or L -------------------------------------
    # Nuzhen dlya kosvennoj adresatsii (HL): za odin skan pamyat dolzhna
    # poluchit gotovyj 16-bitnyj adres, poetomu sobiraem ego zdes.
    na = p.network(u"SBORKA ADRESA HL")
    c_h = na.invar(u"H", y=30)
    c_l = na.invar(u"L", y=70)
    wh = b_b2w(na, F.COL_BLK, 30, c_h)
    shl = b_shl(na, F.COL_BLK2, 30, wh, na.const(u"8", y=44))
    wl = b_b2w(na, F.COL_BLK2, 70, c_l)
    hl = na.block(u"OR", [(PIN1, shl), (PIN2, wl)], [POUT],
                  x=F.COL_BLK2 + 160, y=50)
    na.outvar(u"Addr_HL", hl, x=F.COL_OUT + 140, y=50)

    # ================= HRANENIE REGISTROV =================
    #  E T O G O  N E  B Y L O  V O V S E. Set' "ZAPIS'" vyrabatyvala
    #  shestnadtsat' strobov WE_0..WE_15 -- a potrebitelej u nih ne bylo:
    #  ni odin registr ne zapominal znachenie. Vyhody A, B, ... Sf
    #  obyavleny, no nikogda ne prisvaivalis', poetomu V S E G D A  ravny
    #  nulyu. Posledstvie na real nom progone: ALU schital s A=B=0, i vse
    #  40 proverok padali, a initsializatsiya registrov molchala.
    #
    #  K A K  U S T R O E N  O D I N  R E G I S T R (na kazhdyj iz 16):
    #      vhod  = SEL(CLR,  prezhnee_znachenie,  BYTE#0)   -- sBros
    #      zapis'= AND(WE_k, NOT CLR)                        -- strob
    #      vyhod = SEL(zapis', prezhnee_znachenie, Wr_Val)
    #  Chtenie sobstvennogo vyhoda vnutri FB daet znachenie PROSHLOGO skana
    #  (prisvaivanie idet v konce seti) -- eto i est pamyat' registra.
    ns = p.network(u"HRANENIE: 16 registrov, zapis' po strobam WE_k")
    for k, nm in enumerate(NAMES):
        yy = 30 + k * 90
        cq = ns.invar(nm, y=yy)
        cwe = ns.invar(u"WE_%d" % k, y=yy + 20)
        cwv = ns.invar(wv, y=yy + 40)
        cclr = ns.invar(clr, y=yy + 60)
        nclr = ns.block(u"NOT", [(PINU, cclr)], [POUT], x=F.COL_BLK, y=yy + 60)
        wen = ns.block(u"AND", [(PIN1, cwe), (PIN2, nclr)], [POUT],
                       x=F.COL_BLK, y=yy + 20)
        sel_w = ns.block(u"SEL", [(u"G", wen), (u"IN0", cq), (u"IN1", cwv)],
                         [u"OUT"], x=F.COL_BLK2, y=yy + 20)
        zbyt = ns.const(u"BYTE#0", y=yy + 80)
        sel_c = ns.block(u"SEL",
                         [(u"G", cclr), (u"IN0", sel_w), (u"IN1", zbyt)],
                         [u"OUT"], x=F.COL_BLK2 + 160, y=yy + 20)
        ns.outvar(nm, sel_c, x=F.COL_OUT + 140, y=yy + 20)

    return p


def mk_adder8():
    u"""FB_ADDER8 -- polnyj 8-bitnyj summator s perenosom.

    Schitaet A + B v 16 bitah, chtoby poluchit perenos iz bita 8 (on v starshem
    bajte), i perenos iz bita 4 (polusumma mladshih tetrad).
    """
    p = F.Pou(u"FB_ADDER8", u"function",
              u"Polnyj 8-bitnyj summator.\n"
              u"Sum = A+B (16 bit), Carry8 = perenos iz bita 8, "
              u"Carry4 = perenos iz bita 4.",
              ret_type=u"WORD")
    a = p.var_in(u"A", u"BYTE")
    b = p.var_in(u"B", u"BYTE")
    #  P O Ch E M U  N E  "S" i  N E  "C8". V otchyote kompilyatora eti imena
    #  davali "C0007: Vmesto 'S' trebuetsya vyrazhenie" i "C0009: Obnaruzhen
    #  nedopustimyj simvol 'S'". Odnobukvennye imena S i C sovpadayut s
    #  pristavkami tipov IEC (SINT, STRING, ...), i razobrat ikh parseru
    #  ne udalos. Imena pereimenovany v Sum / Carry8 / Carry4.
    p.var_out(u"Sum", u"WORD", u"A+B v 16 bitah")
    p.var_out(u"Carry8", u"BOOL", u"perenos iz bita 8")
    p.var_out(u"Carry4", u"BOOL", u"perenos iz bita 4")

    n = p.network(u"summa v 16 bitah")
    c_a = n.invar(a, y=40)
    c_b = n.invar(b, y=80)
    wa = b_b2w(n, F.COL_BLK, 40, c_a)
    wb = b_b2w(n, F.COL_BLK, 80, c_b)
    s = b_add(n, F.COL_BLK2, 60, wa, wb)
    n.outvar(u"Sum", s, x=F.COL_OUT, y=60)
    # perenos iz bita 8 -- bit 0 starshego bajta
    hi = b_shr(n, F.COL_BLK2 + 160, 40, s, n.const(u"8", y=54))
    #  WORD#1, a ne prosto 1: sravnivaem WORD s chislom, a bezrisovyy
    #  literal CODESYS vyvodit kak INT i delayot neyavnuyu WORD->INT (C196).
    one = n.const(u"WORD#1", y=100)
    c8 = b_eq(n, F.COL_BLK2 + 320, 60, hi, one)
    n.outvar(u"Carry8", c8, x=F.COL_OUT + 300, y=60)
    # perenos iz bita 4 -- polusumma mladshih tetrad
    m15 = n.const(u"16#0F", y=160)
    l1 = n.block(u"AND", [(PIN1, c_a), (PIN2, m15)], [POUT], x=F.COL_BLK, y=150)
    l2 = n.block(u"AND", [(PIN1, c_b), (PIN2, m15)], [POUT], x=F.COL_BLK, y=190)
    ls = b_add(n, F.COL_BLK2, 170, l1, l2)
    m16 = n.const(u"16#10", y=220)
    c4 = n.block(u"EQ", [(PIN1, ls), (PIN2, m16)], [POUT],
                 x=F.COL_BLK2 + 160, y=170)
    n.outvar(u"Carry4", c4, x=F.COL_OUT + 140, y=170)
    return p


def mk_alu():
    u"""FB_ALU_Z80 -- ALU: ADD, ADC, SUB, SBC, AND, OR, XOR, CP + vse flagi.

    Tri seti: arifmetika (16-bitnaya summa), logicheskie operacii, vybor
    rezultata po kodu operacii, vychislenie flagov.
    """
    p = F.Pou(u"FB_ALU_Z80", u"functionBlock",
              u"Arifmetiko-logicheskoe ustrojstvo Z80.\n"
              u"Op: 0 ADD, 1 ADC, 2 SUB, 3 SBC, 4 AND, 5 OR, 6 XOR, 7 CP.\n"
              u"Vse dokumentirovannye flagi: S Z H P/V N C.")
    a = p.var_in(u"A", u"BYTE", u"akkumulyator")
    b = p.var_in(u"B", u"BYTE", u"vtoroj operand")
    op = p.var_in(u"Op", u"BYTE", u"kod operacii 0..7")
    cin = p.var_in(u"Carry_In", u"BOOL", u"vhod perenosa dlya ADC/SBC")
    bfor = p.var_in(u"B_Forced", u"BYTE",
                    u"gotovyj operand dlya INC/DEC (edinit sa)")
    incdec = p.var_in(u"IncDec", u"BOOL",
                      u"TRUE dlya INC/DEC: operand beretsya iz B_Forced")
    p.var_out(u"Y", u"BYTE", u"rezul'tat")
    p.var_out(u"Flag_S", u"BOOL", u"znak")
    p.var_out(u"Flag_Z", u"BOOL", u"nol'")
    p.var_out(u"Flag_H", u"BOOL", u"poluperenos")
    p.var_out(u"Flag_PV", u"BOOL", u"chetnost' / perepolnenie")
    p.var_out(u"Flag_N", u"BOOL", u"vychitanie")
    p.var_out(u"Flag_C", u"BOOL", u"perenos / zaym")

    #  M E Zh S E T E V Y E   S I G N A L Y.  Ih nado OB''YaVIT.
    #  Seti 1..5 svyazany po imenam (Set_Lo, Is_Sub i t.d.), a imya v IEC
    #  sushchestvuet tolko togda, kogda ono ob''yavleno. Bez etogo kompilyator
    #  soobshchaet "C77: Neizvestnyy tip: 'Add_Lo'" -- on schitaet neznakomoe
    #  imya tipom, a ne peremennoj.
    p.var(u"Is_Logic", u"BOOL", u"op >= 4: logika (AND/OR/XOR/CP)")
    p.var(u"Is_Sub", u"BOOL", u"op = 2..3: vychitanie (SUB/SBC)")
    p.var(u"Is_Arith", u"BOOL", u"arifmetika (ADD/ADC/SUB/SBC)")
    p.var(u"Add_C", u"BOOL", u"perenos 16-bitnogo slozheniya")
    p.var(u"Sub_C", u"BOOL", u"zaym 16-bitnogo vychitaniya")
    p.var(u"Add_Lo", u"BYTE", u"mladshij bajt summy")
    p.var(u"Sub_Lo", u"BYTE", u"mladshij bajt raznosti")
    for _k in range(6):
        p.var(u"Sel_Op%d" % _k, u"BOOL", u"op = %d" % _k)
    #  T I P I Z I R O V A N N Y E  R E Z U L'TATY  L O G I K I.
    #  P O Ch E M U  O N I  N U Zh N Y. Bloki AND / OR / XOR v IEC obobshchennye
    #  (ANY_BIT): konkretnyj tip vyvoditsya po operandam, a kogda takoy vyhod
    #  popadaet v obobshchennyj vhod SEL, CODESYS ne mozhet zakreplyaet tip
    #  i beret BOOL -- bazovyj dlya ANY_BIT. V cepochke vybora Y eto davalo
    #  smeshannye vetki i rovno te oshibki, kotorye nikak ne svyazat s POU:
    #      C32: Nevozmozhno konvertirovat tip 'BOOL'  v tip 'USINT'
    #      C32: Nevmozhno konvertirovat tip 'USINT' v tip 'BOOL'
    #  Najdeno bisekciej po ekzemplyaram (generator\tools\probe_fb.py):
    #  probe s ODNOJ FB_ALU_Z80 daval 4 oshibki iz 8.
    #  P R A V I L O  P R O E K T A, uzhe oplachennoe otladkoj (sm. zhurnal
    #  sborki): vyhod obobshchennogo bloka pered obobshchennym potrebitelem
    #  provodit cherez YaVNUYU peremennuyu nuzhnogo tipa -- togda tip
    #  zakreplyaetsya obyavleniem POU i soglasovanie stanovitsya odnoznachnym.
    p.var(u"Logic_And", u"BYTE", u"A and B (tip zakreplen yavno)")
    p.var(u"Logic_Or", u"BYTE", u"A or B (tip zakreplen yavno)")
    p.var(u"Logic_Xor", u"BYTE", u"A xor B (tip zakreplen yavno)")
    p.var(u"Ovf_Add", u"BOOL", u"perepolnenie pri slozhenii (tip zakreplen)")
    p.var(u"Ovf_Sub", u"BOOL", u"perepolnenie pri vychitanii (tip zakreplen)")

    # ---------------- 1. arifmetika ----------------
    n1 = p.network(u"ARIFMETIKA: 16-bitnaya summa i raznost'")
    c_a = n1.invar(a, y=40)
    c_b = n1.invar(b, y=80)
    c_bfor = n1.invar(bfor, y=400)
    c_incdec = n1.invar(incdec, y=440)
    # dlya INC/DEC operand -- edinitsa (B_Forced), inache -- registr B
    b_eff = b_sel(n1, F.COL_BLK, 400, c_incdec, c_b, c_bfor)
    c_cin = n1.invar(cin, y=120)
    c1 = n1.const(u"BYTE#1", y=160)
    y = 40
    c_op = n1.invar(op, y=200)
    # ADC: pribavit perenos
    bin_ = b_sel(n1, F.COL_BLK, 80, c_cin, b_eff, c1)
    wa = b_b2w(n1, F.COL_BLK, 40, c_a)
    wb = b_b2w(n1, F.COL_BLK2, 80, bin_)
    addres = b_add(n1, F.COL_BLK2 + 160, 60, wa, wb)
    add_lo = b_w2b(n1, F.COL_BLK2 + 320, 60, addres)
    add_hi = b_shr(n1, F.COL_BLK2 + 320, 100, addres, n1.const(u"8", y=114))
    #  Sravnivaem starshij bajt (WORD) s E D I N I Ts E J, i poetomu
    #  literal dolzhen byt tipizirovan: bezrisovyy "1" CODESYS vyvodit
    #  kak INT i delayot neyavnuyu WORD->INT (preduprezhdenie C196).
    c1w = n1.const(u"WORD#1", y=174)
    add_c = b_eq(n1, F.COL_BLK2 + 480, 100, add_hi, c1w)
    # SUB: A - B (perenos = ZAYM)
    subres = b_sub(n1, F.COL_BLK2 + 160, 220, wa, wb)
    sub_lo = b_w2b(n1, F.COL_BLK2 + 320, 220, subres)
    # zaym est' togda i tol'ko togda, kogda pri slozhenii perenosa NE bylo
    sub_c = b_not(n1, F.COL_BLK2 + 480, 260, add_c)
    # --- priznaki grupp operacij ---
    # Op >= 4 -> logicheskaya operaciya (AND/OR/XOR/CP po alfavitu ALU)
    c4 = n1.const(u"16#04", y=340)
    is_logic_op = n1.block(u"GE", [(PIN1, c_op), (PIN2, c4)], [POUT],
                           x=F.COL_BLK2 + 480, y=340)
    # Op v diapazone 2..3 -> vychitanie (SUB/SBC/CP)
    is_sub_op = b_and(n1, F.COL_BLK2 + 480, 380,
                      n1.block(u"GE", [(PIN1, c_op), (PIN2, n1.const(u"2", y=394))],
                               [POUT], x=F.COL_BLK2 + 320, y=380),
                      n1.block(u"LE", [(PIN1, c_op), (PIN2, n1.const(u"3", y=434))],
                               [POUT], x=F.COL_BLK2 + 320, y=420))
    # arifmetika (ADD/ADC/SUB/SBC) -- vse, chto ne logika
    is_arith_op = b_not(n1, F.COL_BLK2 + 640, 380, is_logic_op)

    # VYVOD MEZhSETEVYH SIGNALOV V PEREMENNYE.
    # Zachem: kazhdyj iz etih signalov ispol'zuetsya v NESKOL'KIH setyah.
    # Esli ostavit' ih kak ssylki na bloki, to pri razvorachivanii fan-out
    # biblioteka nachnet KLONIROVAT' vsyu vethv' vnizu po graf -- vmeste s
    # blokami i vhodami, -- i POU razduvaetsya. Cherez poimenovannuyu
    # peremennuyu svyaz' stanovitsya odnokratnoj i glubokogo klonirovaniya net.
    n1.outvar(u"Is_Logic", is_logic_op, x=F.COL_OUT + 600, y=340)
    n1.outvar(u"Is_Sub", is_sub_op, x=F.COL_OUT + 600, y=380)
    n1.outvar(u"Is_Arith", is_arith_op, x=F.COL_OUT + 600, y=420)
    n1.outvar(u"Add_C", add_c, x=F.COL_OUT + 600, y=100)
    n1.outvar(u"Sub_C", sub_c, x=F.COL_OUT + 600, y=260)
    n1.outvar(u"Add_Lo", add_lo, x=F.COL_OUT + 600, y=180)
    n1.outvar(u"Sub_Lo", sub_lo, x=F.COL_OUT + 600, y=220)

    # ---------------- 2. logika ----------------
    n2 = p.network(u"LOGIKA: AND / OR / XOR")
    c_a2 = n2.invar(a, y=40)
    c_b2 = n2.invar(b, y=80)
    v_and = n2.block(u"AND", [(PIN1, c_a2), (PIN2, c_b2)], [POUT],
                     x=F.COL_BLK, y=40)
    v_or = n2.block(u"OR", [(PIN1, c_a2), (PIN2, c_b2)], [POUT],
                    x=F.COL_BLK, y=90)
    v_xor = n2.block(u"XOR", [(PIN1, c_a2), (PIN2, c_b2)], [POUT],
                     x=F.COL_BLK, y=140)
    #  V Y V O D  V  Ya V N O  T I P I Z I R O V A N N Y E  P E R E M E N N Y E.
    #  Bez etogo vyhody AND / OR / XOR (obobshchennye ANY_BIT) uhodili pryamo
    #  v SEL i vyzyvali C32 -- sm. poyasnenie u obyavleniya Logic_And.
    n2.outvar(u"Logic_And", v_and, x=F.COL_OUT, y=40)
    n2.outvar(u"Logic_Or", v_or, x=F.COL_OUT, y=90)
    n2.outvar(u"Logic_Xor", v_xor, x=F.COL_OUT, y=140)

    # ---------------- 3. vybor rezul'tata po kodu operacii ----------------
    # VAZhNO (vyyasneno bisekciej: imenno eta set' teryalas' pri importe):
    #   1) sravneniya Op -> IMENOVANNYE peremennye: inache odin vyhod EQ pitaya
    #      neskol'ko SEL, daet fan-out i glubokoe klonirovanie;
    #   2) znacheniya peredayutsya PRYaMYMI ssylkami na bloki -- kabel ot bloka
    #      k bloku eto normal'no, problema tol'ko v vetvlenii odnogo vyhoda;
    #   3) dlya 7 variantov hvataet 6 SEL: poslednij variant sluzhit rezervnym
    #      putem IN0, poetomu otdel'noe uslovie dlya nego ne nuzhno.
    n3 = p.network(u"VYBOR rezul'tata: sravneniya Op i cepochka SEL")
    # Kazhdoe potreblenie -- OTDELNYJ ekzemplyar invar. Pochemu: esli odin i
    # tot zhe element pitat dva vhoda, biblioteka kloniruet ego vethv', a u
    # klona (vyyasneno eksperimentom) mozhet ostat'sya NEPODKLYuChENNYJ vhod.
    # Otdel'nye ekzemplyary delaya klonirovanie nenuzhnym.
    c_addlo_v1 = n3.invar(u"Add_Lo", y=30)
    c_addlo_v2 = n3.invar(u"Add_Lo", y=60)
    c_sublo_v1 = n3.invar(u"Sub_Lo", y=90)
    c_sublo_v2 = n3.invar(u"Sub_Lo", y=120)
    c_op_cmp = n3.invar(op, y=150)
    cmp_refs = []
    yc = 40
    for k in range(6):
        ck = n3.const(u"%d" % k, y=yc + 12)
        # sravnivaem kod operacii s nomerom varianta
        eq = b_eq(n3, F.COL_BLK, yc, c_op_cmp, ck)
        n3.outvar(u"Sel_Op%d" % k, eq, x=F.COL_OUT, y=yc)
        cmp_refs.append(u"Sel_Op%d" % k)
        yc += 40
    #  Vetki -- T O L K O odnoznachno tipizirovannye istochniki: vyhodnye
    #  peremennye seti 1 (BYTE) i peremennye logiki iz seti 2 (BYTE).
    #  Ran'she zdes stoyali pryamye ssylki na bloki AND / OR / XOR, i cepochka
    #  poluchalas smeshannoj -- sm. poyasnenie u obyavleniya Logic_And.
    vals = [c_addlo_v1, c_addlo_v2, c_sublo_v1, c_sublo_v2,
            n3.invar(u"Logic_And", y=200),
            n3.invar(u"Logic_Or", y=215),
            n3.invar(u"Logic_Xor", y=230)]
    cur = vals[6]                      # rezervnyj put = XOR (kod 6)
    y = 280
    for k in range(5, -1, -1):
        ccond = n3.invar(cmp_refs[k], y=y + 12)
        cur = b_sel(n3, F.COL_BLK2, y, ccond, cur, vals[k])
        y += 45
    n3.outvar(u"Y", cur, x=F.COL_OUT + 300, y=280)

    # ---------------- 4. flagi: S, Z, H, N, C ----------------
    n4 = p.network(u"FLAGI: S Z H N C")
    c_y = n4.invar(u"Y", y=30)
    c_i7 = n4.const(u"16#80", y=70)
    c_z0 = n4.const(u"0", y=110)
    c_cin4 = n4.invar(cin, y=150)
    c_b4 = n4.invar(b, y=190)   # dlya H ispol'zuem B_Forced ne nuzhno: INC/DEC
                                # schitaet H po formule s B=1, sm. set' 4
    # mezhsetevye signaly -- cherez imena; kazhdoe potreblenie otdel'nym
    # ekzemplyarom invar, chtoby ne vyzyvat' klonirovanie (sm. set' 3)
    c_issub = n4.invar(u"Is_Sub", y=430)
    c_issub2 = n4.invar(u"Is_Sub", y=445)
    c_islog = n4.invar(u"Is_Logic", y=470)
    c_islog2 = n4.invar(u"Is_Logic", y=485)
    c_isar = n4.invar(u"Is_Arith", y=510)
    c_addc = n4.invar(u"Add_C", y=550)
    c_subc = n4.invar(u"Sub_C", y=590)
    # S = Y.7
    #  V N I M A N I E: ran'she zdes' stoyalo pryamo
    #      Flag_S := Y AND 16#80
    #  Eto D V E  oshibki v odnoj stroke:
    #   1) T I P. AND dvuh bajtov daet BYTE, a Flag_S obyavlen BOOL --
    #      kompilyator soobshchal "C32: Nevozmozhno konvertirovat tip 'USINT'
    #      v tip 'BOOL'" (BYTE on schitaet cherez USINT);
    #   2) S M Y S L. Rezul tat AND -- eto 16#80 ili 16#00, a ne 1/0.
    #  Pravil no: sravnit' maskirovannyj bit s samoj maskoj.
    v_s_mask = n4.block(u"AND", [(PIN1, c_y), (PIN2, c_i7)], [POUT],
                        x=F.COL_BLK, y=30)
    v_s = b_eq(n4, F.COL_BLK, 60, v_s_mask, c_i7)
    n4.outvar(u"Flag_S", v_s, x=F.COL_OUT, y=30)
    # Z = (Y = 0)
    v_z = b_eq(n4, F.COL_BLK, 110, c_y, c_z0)
    n4.outvar(u"Flag_Z", v_z, x=F.COL_OUT, y=110)
    # C berem iz 16-bitnoj summy: dlya ADD -- perenos, dlya SUB -- zaym
    v_c = b_sel(n4, F.COL_BLK2, 30, c_issub, c_addc, c_subc)
    n4.outvar(u"Flag_C", v_c, x=F.COL_OUT + 140, y=30)
    # ---- poluperenos H: perenos iz bita 3 v bit 4 ----
    #  F O R M U L A:  H = ((A AND 0Fh) + (B AND 0Fh)) AND 10h  <>  0
    #  To est skladyvaem MLADShIE TETRADY i smotrim, peresek li rezul tat
    #  granitsu tetrady.
    #
    #  Chto zdes' bylo N E T A K (dve oshibki srazu):
    #    Flag_H := ((A AND 08h) AND (B AND 08h)) OR ((NOT (Y AND 08h)) AND (A AND 08h))
    #    1) T I P: AND nad dvumya bajtami daet BYTE, potom OR -- tozhe BYTE,
    #       a posledniy AND uzhe smeshannyj (BYTE i BOOL), i rezul tat
    #       prisvaivalsya peremennoj BOOL. Otsyuda pary C32 'BOOL' <-> 'USINT';
    #    2) S M Y S L: eto voobshche ne poluperenos -- maskirovanie ne daet
    #       perenosa iz bita 3.
    #  Vse bloki teper' odnotipnye: AND/ADD nad BYTE, sravnenie i AND -- BOOL.
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
    h_fin = b_and(n4, F.COL_BLK2 + 480, 320, h_bit, c_isar)
    n4.outvar(u"Flag_H", h_fin, x=F.COL_OUT + 600, y=300)
    # N = 1 dlya SUB/SBC/CP
    v_n = b_sel(n4, F.COL_BLK2, 110, c_islog2, c_issub2,
                n4.const(u"FALSE", y=124))
    n4.outvar(u"Flag_N", v_n, x=F.COL_OUT + 140, y=110)

    # ---------------- 5. P/V: chetnost' dlya logiki, perepolnenie dlya arifm ----------------
    n5 = p.network(u"P/V: chetnost' XOR-cepochkoj (logika) ili perepolnenie (arifmetika)")
    c_y5 = n5.invar(u"Y", y=30)
    # otdel'nye ekzemplyary dlya kazhdogo potrebleniya (sm. poyasnenie v seti 3)
    c_issub5 = n5.invar(u"Is_Sub", y=430)
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
    #  Ch E T N O S T'  D L Ya  P / V.
    #  XOR vseh vos mi bitov daet 0, esli edinichetnoe chislo, i 1, esli
    #  nechetnoye. Z80 stavir P/V = 1 pri Ch E T N O M chisle edinic,
    #  znachit nuzhno sravnit' s nulem.
    #
    #  Bylo:  par = NOT(xo)  -- i eto D V E oshibki:
    #   1) NOT nad bajtom daet bajt (0FFh ili 0FEh), a ne logiku;
    #   2) tip: Flag_PV obyavlen BOOL, a poluchal USINT. Kompilyator i
    #      soobshchal "C32: Nevozmozhno konvertirovat tip 'USINT' v tip 'BOOL'".
    par = b_eq(n5, F.COL_BLK2 + 320, 30, xo, n5.const(u"0", y=44))
    # perepolnenie: ADD -> (A.7 = B.7) i (A.7 <> Y.7); SUB -> (A.7 <> B.7) i (A.7 <> Y.7)
    c_a5 = n5.invar(a, y=420)
    c_b5 = n5.invar(b, y=460)
    sa = n5.block(u"AND", [(PIN1, c_a5), (PIN2, n5.const(u"16#80", y=434))],
                  [POUT], x=F.COL_BLK2 + 320, y=420)
    sb = n5.block(u"AND", [(PIN1, c_b5), (PIN2, n5.const(u"16#80", y=474))],
                  [POUT], x=F.COL_BLK2 + 320, y=460)
    sy = n5.block(u"AND", [(PIN1, c_y5), (PIN2, n5.const(u"16#80", y=514))],
                  [POUT], x=F.COL_BLK2 + 320, y=500)
    eq_ab_add = b_eq(n5, F.COL_BLK2 + 480, 420, sa, sb)
    eq_ab_sub = b_not(n5, F.COL_BLK2 + 480, 460, eq_ab_add)
    ne_ay = b_not(n5, F.COL_BLK2 + 480, 500, b_eq(n5, F.COL_BLK2 + 480, 540, sa, sy))
    ovf_add = b_and(n5, F.COL_BLK2 + 640, 420, eq_ab_add, ne_ay)
    ovf_sub = b_and(n5, F.COL_BLK2 + 640, 480, eq_ab_sub, ne_ay)
    #  I zdes' to zhe samoe: vyhody obobshchennogo AND provedeny cherez
    #  yavnye peremennye BOOL, inache sleduyushchiy SEL poluchaet vetki
    #  bez zakreplennogo tipa (sm. Logic_And i kommentarij k nemu).
    n5.outvar(u"Ovf_Add", ovf_add, x=F.COL_OUT + 700, y=420)
    n5.outvar(u"Ovf_Sub", ovf_sub, x=F.COL_OUT + 700, y=480)
    pv_arith = b_sel(n5, F.COL_BLK2 + 800, 440, c_issub5,
                     n5.invar(u"Ovf_Add", y=430),
                     n5.invar(u"Ovf_Sub", y=460))
    pv = b_sel(n5, F.COL_BLK2 + 960, 200, c_islog5, pv_arith, par)
    n5.outvar(u"Flag_PV", pv, x=F.COL_OUT + 900, y=200)

    return p


def mk_flagsreg():
    u"""FB_FlagsRegZ80 -- registr flagov F (bity 7..0: S Z F5 H F3 P/V N C).

    Sborka bajta idet SHL + ADD: F := (S<<7) + (Z<<6) + ... + C.
    VNIMANIE: vhody nazvany s prefiksom Flag_ (i F5/F3 otdelno), potomu chto
    odnosimvolnye S i C v IEC 61131-3 zarezervirovany pod tipy (SINT/INT)
    i kompilyator ih otvergaet.
    """
    p = F.Pou(u"FB_FlagsRegZ80", u"functionBlock",
              u"Registr flagov F (S Z F5 H F3 PV N C).\n"
              u"Sbor bajta: SHL + ADD. Zapominanie po frontu En.")
    p.var_in(u"Flag_S", u"BOOL", u"znak")
    p.var_in(u"Flag_Z", u"BOOL", u"nol'")
    p.var_in(u"F5", u"BOOL", u"nedokumentirovannyj (hranim)")
    p.var_in(u"Flag_H", u"BOOL", u"poluperenos")
    p.var_in(u"F3", u"BOOL", u"nedokumentirovannyj (hranim)")
    p.var_in(u"Flag_PV", u"BOOL", u"chetnost' / perepolnenie")
    p.var_in(u"Flag_N", u"BOOL", u"vychitanie")
    p.var_in(u"Flag_C", u"BOOL", u"perenos / zaym")
    p.var_in(u"En", u"BOOL", u"razreshenie zapisi")
    #  I N I C I A L I Z A C I Ya  F. Bez neyo testy, kotorye proveryayut
    #  "flagi ne dolzhny izmenit sya" (naprimer LD), vsegda padali: registr
    #  flagov ne zagruzhalsya iz Init_Vals[7] i nachinalsya s nulya vmesto
    #  Init_F. Izmereno na progone: Init_F = FFh, a GVL_PLCVisu.F = 00h.
    p.var_in(u"Init_En", u"BOOL", u"rezhim initsializatsii flagov")
    p.var_in(u"Init_Val", u"BYTE", u"nachal noe znachenie F")
    p.var_out(u"F", u"BYTE", u"upakovannyj registr flagov")
    #  P R O M E Zh U T O Ch N Y E  P E R E M E N N Y E  T I P A  BYTE.
    #  Ikh trebuet konversiya BOOL -> BYTE: dlya CODESYS rezul tat etoy
    #  konversii -- USINT, a ne BYTE, i pryamaya podacha ego v SHL/ADD
    #  (obobshchennye bloki) daet C32. Sm. b_bool2byte() nizhe.

    n = p.network(u"Sborka F: SHL + ADD")
    items = [(p.var_in.__self__ if False else u"Flag_S", 7),
             (u"Flag_Z", 6), (u"F5", 5), (u"Flag_H", 4),
             (u"F3", 3), (u"Flag_PV", 2), (u"Flag_N", 1), (u"Flag_C", 0)]
    terms = []
    y = 30
    for nm_, shift in items:
        c = n.invar(nm_, y=y)
        #  Ch E R E Z  Ya V N U Yu  P E R E M E N N U Yu BYTE: inache vyhod
        #  BOOL_TO_BYTE (dlya CODESYS eto USINT) idet pryamo v SHL i ADD --
        #  obobshchennye bloki, -- i kompilyator daet
        #      C32: Nevozmozhno konvertirovat tip 'BOOL' v tip 'USINT'.
        tb = b_bool2byte(n, u"vBit_%d" % shift, F.COL_BLK, y, c)
        sh = b_shl(n, F.COL_BLK2 + 120, y, tb, n.const(u"%d" % shift, y=y + 14))
        terms.append(sh)
        y += 50
    acc = terms[0]
    y = 30
    for t in terms[1:]:
        acc = b_add(n, F.COL_BLK2 + 160, y, acc, t)
        y += 40
    en = n.invar(u"En", y=y + 20)
    fb = n.invar(u"F", y=y + 60)
    res = b_sel(n, F.COL_BLK2 + 320, 60, en, fb, acc)
    #  init imeet V Y S Sh I J  prioritet, chem obychnaya zapis'
    c_ien = n.invar(u"Init_En", y=y + 100)
    c_ivl = n.invar(u"Init_Val", y=y + 140)
    res2 = b_sel(n, F.COL_BLK2 + 480, 60, c_ien, res, c_ivl)
    n.outvar(u"F", res2, x=F.COL_OUT + 300, y=60)
    return p


def mk_decoder():
    u"""FB_DecoderZ80 -- centralnyj uzel: IR -> signaly upravleniya.

    Vse vyhody vychislyayutsya PRYAMO iz koda komandy (bez promezhutochnogo
    dekodirovaniya polej) -- tak shema chitaetsya kak tablica komand.

    Kodirovka Sel_Dst / Sel_Src:
      0..7  = A B C D E H L F      (osnovnoj nabor)
      8..15 = A' B' C' D' E' H' L' F' (alternativnyj, Sel_Dst)
      Sel_Src: 8 = (HL), 9 = Imm, 10..15 = A'..L'
    Alfavit operacij ALU: 0 ADD, 1 ADC, 2 SUB, 3 SBC, 4 AND, 5 OR, 6 XOR, 7 CP.
    """
    p = F.Pou(u"FB_DecoderZ80", u"functionBlock",
              u"Dekoder komand Z80: IR -> signaly upravleniya.\n"
              u"Podderzhany: NOP LD ADD SUB INC DEC AND OR XOR CP JP JPcc CALL RET "
              u"HALT DJNZ RST.")
    ir = p.var_in(u"IR", u"BYTE", u"kod operacii")
    for v in (u"Ctl_Is_CALL", u"Ctl_Is_RET", u"Ctl_Is_DJNZ", u"Ctl_Is_HALT",
              u"Ctl_Is_Jump", u"Ctl_Is_Jr", u"Ctl_Imm_Mode", u"Ctl_Flags_En",
              u"Ctl_Wr_Enable", u"Ctl_Mem_Rd", u"Ctl_Mem_Wr"):
        p.var_out(v, u"BOOL")
    for v in (u"Ctl_Sel_Dst", u"Ctl_Sel_Src", u"Ctl_ALU_Op", u"Ctl_Cond"):
        p.var_out(v, u"BYTE")
    p.var_out(u"Ctl_IncDec", u"BOOL", u"TRUE dlya INC/DEC: operand = 1")
    p.var_out(u"Ctl_Is_IN", u"BOOL", u"komanda IN A,(n)")
    p.var_out(u"Ctl_Is_OUT", u"BOOL", u"komanda OUT (n),A")
    p.var_out(u"Ctl_IO_Rd", u"BOOL", u"strob chteniya porta")
    p.var_out(u"Ctl_IO_Wr", u"BOOL", u"strob zapisi porta")

    n = p.network(u"Dekodirovanie: sravneniya s kodami komand")
    c_ir = n.invar(ir, y=30)
    y = 500

    def cmp_const(val, yy):
        return n.const(u"16#%02X" % val, y=yy + 12)

    def eq_const(val, x, yy):
        return b_eq(n, x, yy, c_ir, cmp_const(val, yy))

    # --- gruppy komand ---
    y = 30
    r_call = eq_const(0xCD, F.COL_BLK, y); y += 26
    r_ret = eq_const(0xC9, F.COL_BLK, y); y += 26
    r_halt = eq_const(0x76, F.COL_BLK, y); y += 26
    r_djnz = eq_const(0x10, F.COL_BLK, y); y += 26
    r_jp = eq_const(0xC3, F.COL_BLK, y); y += 26
    r_jpz = eq_const(0xCA, F.COL_BLK, y); y += 26
    r_jpnz = eq_const(0xC2, F.COL_BLK, y); y += 26
    r_ldn = eq_const(0x3E, F.COL_BLK, y); y += 26
    r_ldahl = eq_const(0x7E, F.COL_BLK, y); y += 26
    r_ldhla = eq_const(0x77, F.COL_BLK, y); y += 26
    r_ldann = eq_const(0x3A, F.COL_BLK, y); y += 26
    r_ldnna = eq_const(0x32, F.COL_BLK, y); y += 26
    r_in = eq_const(0xDB, F.COL_BLK, y); y += 26
    r_out = eq_const(0xD3, F.COL_BLK, y); y += 26

    # --- ALU Op ---
    n4 = n.block(u"SHR", [(PIN1, c_ir), (PIN2, n.const(u"3", y=y))], [POUT],
                 x=F.COL_BLK, y=y)
    m7 = n.const(u"16#07", y=y + 14)
    grp = n.block(u"AND", [(PIN1, c_ir), (PIN2, m7)], [POUT],
                  x=F.COL_BLK, y=y + 26)
    add3 = b_add(n, F.COL_BLK2, y, grp, n.const(u"1", y=y + 14))
    add3b = b_add(n, F.COL_BLK2, y + 40, add3, n.const(u"1", y=y + 54))
    sub2 = b_sub(n, F.COL_BLK2, y + 80, grp, n.const(u"2", y=y + 94))
    sub3 = b_sub(n, F.COL_BLK2, y + 120, grp, n.const(u"3", y=y + 134))
    c4 = n.const(u"16#04", y=y + 160)
    is_logic = n.block(u"GE", [(PIN1, n4), (PIN2, c4)], [POUT],
                       x=F.COL_BLK2, y=y + 160)
    alu_rm = b_sel(n, F.COL_BLK2 + 160, y, is_logic, add3b, n4)
    alu_log = b_add(n, F.COL_BLK2 + 160, y + 60, alu_rm, n.const(u"3", y=y + 74))
    alu_sel = b_sel(n, F.COL_BLK2 + 320, y, is_logic, alu_log, alu_rm)

    # --- uslovnye perehody ---
    #  Ch T O  Z D E S'  B Y L O  N E  T A K. Stoyalo
    #      cond_is_z = b_and(r_jpz, const 1)
    #      cond_nz0  = b_and(r_jpnz, const 0)
    #  No r_jpz i r_jpnz -- uzhe BOOL (rezul tat sravneniya), a "1" i "0" --
    #  chislovye literaly. AND nad BOOL i chislom ne imeet smysla i daet
    #  smeshannyy tip; dalee OR poluchaet BYTE, a vyhod Ctl_Cond obyavlen BOOL.
    #      C32: Nevozmozhno konvertirovat tip 'BOOL' v tip 'USINT'
    #  Po smyslu zdes' nuzhno prosto vzyat' sam signal.
    cond_is_z = r_jpz
    cond_nz0 = r_jpnz
    cond_any = b_or(n, F.COL_BLK2, y + 280, cond_is_z, cond_nz0)
    #  K O D  U S L O V I Ya  D L Ya  Ctl_Cond.
    #  Ctl_Cond obyavlen BYTE -- eto K O D usloviya Z80:
    #      0 = NZ, 1 = Z
    #  A tuda podavalsya cond_any (priznak BOOL "perehod uslovnyy"), i
    #  kompilyator soobshchal
    #      C32: Nevozmozhno konvertirovat tip 'BOOL' v tip 'BYTE'.
    #  Teper' vybirayutsya imenno kody, i tip sovpadaet s obyavleniem.
    cond_code = b_sel(n, F.COL_BLK2, y + 320, r_jpz,
                      n.const(u"BYTE#00", y=y + 334),
                      n.const(u"BYTE#01", y=y + 348))

    # --- Sel_Dst ---
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
    dst_sel = b_sel(n, F.COL_BLK2 + 480, y + 200, is_ld, sd_sum2, dst_c)

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
    src_sel = b_sel(n, F.COL_BLK2 + 320, y + 380, is_load, src_sum3, dst_c)

    # --- Ctl_IncDec: opkody x4/x5 (INC/DEC r) i 3C/3D (INC/DEC A) ---
    g5 = n.block(u"EQ", [(PIN1, grp), (PIN2, n.const(u"16#04", y=y + 574))],
                 [POUT], x=F.COL_BLK2, y=y + 560)
    g6 = n.block(u"EQ", [(PIN1, grp), (PIN2, n.const(u"16#05", y=y + 614))],
                 [POUT], x=F.COL_BLK2, y=y + 600)
    g45 = b_or(n, F.COL_BLK2 + 160, y + 580, g5, g6)
    a1 = eq_const(0x3C, F.COL_BLK2 + 160, y + 640)
    a2 = eq_const(0x3D, F.COL_BLK2 + 160, y + 680)
    a12 = b_or(n, F.COL_BLK2 + 320, y + 660, a1, a2)
    incdec = b_or(n, F.COL_BLK2 + 480, y + 620, g45, a12)

    #  C T L _ F L A G S _ E N -- zhestko po gruppe komand.
    #
    #  B Y L O : flags_en = OR(is_alu, r_ldahl), gde is_alu = (IR >> 3 <> 0).
    #  Eto uslovie N I Ch E G O  N E  Z N A Ch I T: "IR >> 3" ne ravno nulyu
    #  pochti dlya vseh opkodov. Izmer na real nom progone (sim_strobes):
    #      Init_En=FALSE  Ctl_Flags_En=TRUE   F=BYTE#0    IR=BYTE#195 (JP)
    #      Init_En=FALSE  Ctl_Flags_En=TRUE   F=BYTE#68   IR=BYTE#118 (HALT)
    #  To est flagi perezapisyvalis posle K A Zh D O J komandy, vklyuchaya
    #  JP i HALT, kotorye ih menyat ne dolzhny. Posledstvie: vse 40 testov
    #  padali, potomu chto oni proveryayut "flagi ne izmenilis" -- a F k
    #  momentu sravneniya uzhe byl drugim (0x44 vmesto Init_F).
    #
    #  P R A V I L O  Z80. Flagy menyayut tolko:
    #     * arifmetika i logika 80h..BFh  (ADD/ADC/SUB/SBC/AND/OR/XOR/CP r);
    #     * INC/DEC registra       x4/x5 i 3Ch/3Dh;
    #  a takzhe DAA, CPL, SCF, CCF -- ih v etom proekte net.
    #  Zdes strogaya proverka "IR v diapazone 80h..BFh": dva starshih bita
    #  ravny 10b. Eto i est gruppa ALU.
    hi2 = n.block(u"AND", [(PIN1, c_ir), (PIN2, n.const(u"16#C0", y=y + 498))],
                  [POUT], x=F.COL_BLK2, y=y + 486)
    is_alu_grp = n.block(u"EQ",
                         [(PIN1, hi2), (PIN2, n.const(u"16#80", y=y + 534))],
                         [POUT], x=F.COL_BLK2 + 160, y=y + 520)
    flags_en = b_or(n, F.COL_BLK2 + 320, y + 520, incdec, is_alu_grp)

    outs = [
        (u"Ctl_Is_CALL", r_call, F.COL_OUT),
        (u"Ctl_Is_RET", r_ret, F.COL_OUT),
        (u"Ctl_Is_DJNZ", r_djnz, F.COL_OUT),
        (u"Ctl_Is_HALT", r_halt, F.COL_OUT),
        (u"Ctl_Is_Jump", b_or(n, F.COL_BLK2 + 480, y + 200,
                              b_or(n, F.COL_BLK2 + 480, y + 160, r_jp, cond_any),
                              r_call), F.COL_OUT),
        (u"Ctl_Is_Jr", r_djnz, F.COL_OUT),
        #  Ctl_Imm_Mode: "adres operanda beretsya iz koda komandy (nn), a ne iz HL".
        #  B Y L O  T A K: OR(r_ldn, r_call, r_in, r_out) -- i v etom spiske
        #  N E  B Y L O  komand perehoda. Posledstvie izmereno na real nom
        #  progone: dlya "JP 0FA00h" Imm_Mode okazalsya FALSE, SET 6 vybral
        #  vetku Addr_HL (HL=0), pamyat' prochitala bajt po adresu 0 (sam
        #  opkod 0C3h), i skhema schitala, chto cel' perehoda = 0. PC na
        #  kazhdom skane zagruzhal 0 i stoyal na meste.
        #  T E P E R'  v spiske vse komandy, u kotoryh operand -- chislo iz
        #  koda: LD r,n; CALL nn; JP nn; JP Z; JP NZ; IN A,(n); OUT (n),A;
        #  LD A,(nn); LD (nn),A. U komand s (HL) etot priznak ostayotsya
        #  FALSE -- im nuzhen Addr_HL.
        #  Cepochka sobiraetsya poparno: odin vyhod -- odin vhod (pravilo
        #  proekta pro fan-out).
        (u"Ctl_Imm_Mode",
         b_or(n, F.COL_BLK2 + 320, y + 780,
              b_or(n, F.COL_BLK2 + 320, y + 740,
                   b_or(n, F.COL_BLK2 + 320, y + 700,
                        b_or(n, F.COL_BLK2 + 320, y + 660,
                             b_or(n, F.COL_BLK2 + 320, y + 620,
                                  b_or(n, F.COL_BLK2 + 320, y + 580,
                                       b_or(n, F.COL_BLK2 + 320, y + 540,
                                            b_or(n, F.COL_BLK2 + 320, y + 500,
                                                 r_ldn, r_call),
                                            r_jp),
                                       r_jpz),
                                  r_jpnz),
                             r_in),
                        r_out),
                   r_ldann),
              r_ldnna),
         F.COL_OUT),
        (u"Ctl_Flags_En", flags_en, F.COL_OUT),
        #  Ctl_Wr_Enable -- eto BOOL. Stoyalo const(u"1") -- chislovoy literal,
        #  a on v etoy versii CODESYS vyvoditsya kak USINT, i prisvoenie ego
        #  v BOOL daet "C32: Nevozmozhno konvertirovat tip 'USINT' v tip 'BOOL'".
        (u"Ctl_Wr_Enable", n.const(u"TRUE", y=y + 600), F.COL_OUT),
        (u"Ctl_Mem_Rd", b_or(n, F.COL_BLK2 + 480, y + 260,
                             b_or(n, F.COL_BLK2 + 480, y + 220, r_ldahl, r_ldahl),
                             r_ldahl), F.COL_OUT),
        (u"Ctl_Mem_Wr", r_ldhla, F.COL_OUT),
        (u"Ctl_Sel_Dst", dst_sel, F.COL_OUT + 300),
        (u"Ctl_Sel_Src", src_sel, F.COL_OUT + 300),
        (u"Ctl_ALU_Op", alu_sel, F.COL_OUT + 300),
        (u"Ctl_Cond", cond_code, F.COL_OUT),
        (u"Ctl_IncDec", incdec, F.COL_OUT),
        (u"Ctl_Is_IN", r_in, F.COL_OUT),
        (u"Ctl_Is_OUT", r_out, F.COL_OUT),
        (u"Ctl_IO_Rd", r_in, F.COL_OUT),
        (u"Ctl_IO_Wr", r_out, F.COL_OUT),
    ]
    oy = 30
    for nm_out, srcv, xo in outs:
        n.outvar(nm_out, srcv, x=xo, y=oy)
        oy += 30
    return p


def mk_memory64k():
    u"""FB_Memory64K -- pamyat 64 KB, TELO NA ST (sm. poyasnenie v DECL)."""
    p = F.TextFb(u"FB_Memory64K", ST_MEM_DECL, ST_MEM_IMPL,
                 u"Pamyat 64 KB s chetyrmya portami. Telo na ST -- v FBD net "
                 u"indeksatsii massiva.")
    return p


def mk_pc():
    u"""FB_PC_Z80 -- schetchik komand: zagruzka, inkrement, hranenie."""
    p = F.Pou(u"FB_PC_Z80", u"functionBlock",
              u"Schetchik komand.\nPrioritet: Load vyshe Inc. Inache PC := PC + Inc_By.")
    p.var_in(u"Load_Val", u"WORD", u"novoe znachenie")
    p.var_in(u"Load", u"BOOL", u"zagruzit'")
    p.var_in(u"Inc", u"BOOL", u"inkrementirovat'")
    p.var_in(u"Inc_By", u"BYTE", u"na skol'ko bajt")
    p.var_out(u"Addr", u"WORD", u"tekuchee znachenie")
    p.var_out(u"PC_Next", u"WORD", u"znachenie posle inkrementa")

    n = p.network(u"PC: zagruzka / inkrement / hranenie")
    c_lv = n.invar(u"Load_Val", y=30)
    c_ld = n.invar(u"Load", y=70)
    c_inc = n.invar(u"Inc", y=110)
    c_by = n.invar(u"Inc_By", y=150)
    c_pc = n.invar(u"Addr", y=190)

    by_w = n.block(u"BYTE_TO_WORD", [(PINU, c_by)], [POUT], x=F.COL_BLK, y=150)
    nxt = b_add(n, F.COL_BLK2, 130, c_pc, by_w)
    n.outvar(u"PC_Next", nxt, x=F.COL_OUT, y=130)
    take = b_sel(n, F.COL_BLK2 + 160, 70, c_inc, c_pc, nxt)
    sel_l = b_sel(n, F.COL_BLK2 + 320, 70, c_ld, take, c_lv)
    n.outvar(u"Addr", sel_l, x=F.COL_OUT + 300, y=70)
    return p


def mk_stack():
    u"""FB_SP_StackZ80 -- ukazatel steka i operacii PUSH/POP.

    CALL: SP := SP - 2 i zapis dvuh bajt.  RET: chtenie dvuh bajt i SP := SP + 2.
    Stek rastet VNIZ, kak v realnom Z80.
    """
    p = F.Pou(u"FB_SP_StackZ80", u"functionBlock",
              u"Ukazatel' steka i operacii PUSH/POP.\n"
              u"CALL: SP-=2 i zapis'; RET: chtenie i SP+=2. Stek rastet vniz.")
    p.var_in(u"Push", u"BOOL", u"CALL")
    p.var_in(u"Pop", u"BOOL", u"RET")
    p.var_in(u"Val_In", u"WORD", u"chto kladet PUSH (adres vozvrata)")
    #  TIP WORD, a ne BYTE: na etot vhod podaetsya slovo, snyatoe so steka
    #  (vyhod SP_Out u FB_Memory64K imeet tip WORD). Kogda zdes stoyal BYTE,
    #  kompilyator daval "Nevozmozhno konvertirovat tip 'WORD' v tip 'BYTE'".
    p.var_in(u"Mem_Rd", u"WORD", u"slovo dlya POP (oba bajta srazu)")
    p.var_out(u"SP", u"WORD", u"tekuchee znachenie steka")
    p.var_out(u"Val_Out", u"WORD", u"chto snyato so steka")
    p.var_out(u"Addr", u"WORD", u"adres dlya obrashcheniya k pamyati")
    p.var_out(u"D_Out", u"BYTE", u"bajt dlya zapisi")
    p.var_out(u"Wr", u"BOOL", u"strob zapisi")
    p.var_out(u"Rd", u"BOOL", u"strob chteniya")
    #  Ya V N O  T I P I Z I R O V A N N Y E  R E Z U L'TATY  A R I F M E T I K I.
    #  P O Ch E M U. ADD i SUB -- obobshchennye bloki (ANY_NUM): konkretnyj tip
    #  vyvoditsya po operandam, a kogda takoy vyhod popadaet v obobshchennyj
    #  vhod SEL, CODESYS ne mozhet zakreplyaet tip. V cepochkah nizhe vetki
    #  s WORD (SP) i s rezul tatami ADD/SUB okazyvalis raznogo tipa, i sborka
    #  davala C32.Najdeno bisekciej po ekzemplyaram: probe s ODNOJ FB_SP_StackZ80
    #  daval oshibku, a s sosednimi blokami -- net.
    p.var(u"SP_Dec", u"WORD", u"SP - 2 (tip zakreplen yavno)")
    p.var(u"SP_Inc", u"WORD", u"SP + 2 (tip zakreplen yavno)")

    n = p.network(u"SP: umen'shenie pri PUSH, uvelichenie pri POP")
    c_push = n.invar(u"Push", y=30)
    c_pop = n.invar(u"Pop", y=70)
    c_vin = n.invar(u"Val_In", y=110)
    c_sp = n.invar(u"SP", y=150)
    #  WORD#2, a ne prosto 2: SP imeet tip WORD, i bezrisovyy literal
    #  zastavlyaet kompilyator delayat neyavnuyu WORD->INT (C196).
    c2 = n.const(u"WORD#2", y=190)
    dec = b_sub(n, F.COL_BLK2, 30, c_sp, c2)
    inc = b_add(n, F.COL_BLK2, 70, c_sp, c2)
    n.outvar(u"SP_Dec", dec, x=F.COL_OUT, y=30)
    n.outvar(u"SP_Inc", inc, x=F.COL_OUT, y=70)
    after_pop = b_sel(n, F.COL_BLK2 + 160, 50, c_pop, c_sp,
                      n.invar(u"SP_Inc", y=64))
    sp_new = b_sel(n, F.COL_BLK2 + 320, 50, c_push, after_pop,
                   n.invar(u"SP_Dec", y=44))
    n.outvar(u"SP", sp_new, x=F.COL_OUT + 300, y=50)
    n.outvar(u"Addr", sp_new, x=F.COL_OUT + 300, y=90)
    n.outvar(u"Wr", c_push, x=F.COL_OUT, y=110)
    n.outvar(u"Rd", c_pop, x=F.COL_OUT, y=150)
    lo = b_w2b(n, F.COL_BLK, 230, c_vin)
    n.outvar(u"D_Out", lo, x=F.COL_OUT, y=230)
    #  V A L _ O U T  --  U Zh E  S L O V O.
    #  Ran'she zdes' stoYAlo BYTE_TO_WORD(Mem_Rd), a Mem_Rd obyavlen WORD
    #  (tak i dolzhno byt': na vhod podaetsya slovo, snyatoe so steka).
    #  Poluchalos' WORD -> BYTE -> WORD, i kompilyator soobshchal
    #  "C32: Nevozmozhno konvertirovat tip 'WORD' v tip 'BYTE'".
    #  Konversiya ne nuzhna vovse -- znachenie uzhe nuzhnogo tipa.
    c_mrd = n.invar(u"Mem_Rd", y=270)
    n.outvar(u"Val_Out", c_mrd, x=F.COL_OUT + 140, y=270)
    return p


def mk_control():
    u"""FB_ControlUnit -- upravlenie potokom: JP / CALL / RET / DJNZ / HALT.

    Reshaet, otkuda budet vzyata sleduyushchaya komanda, i derzhit flag Halted
    (cherez sobstvennyj FB_RS s prioritetom sbrosa).
    """
    p = F.Pou(u"FB_ControlUnit", u"functionBlock",
              u"Upravlenie potokom: JP / JP cc / CALL / RET / DJNZ / HALT.\n"
              u"Vyhod PC_New -- kuda perejti, PC_Load -- razreshenie zagruzki.")
    p.var_in(u"Cond_True", u"BOOL", u"uslovie perehoda istinno")
    p.var_in(u"Is_Jump", u"BOOL")
    p.var_in(u"Is_Jr", u"BOOL")
    p.var_in(u"Is_CALL", u"BOOL")
    p.var_in(u"Is_RET", u"BOOL")
    p.var_in(u"Is_DJNZ", u"BOOL")
    p.var_in(u"Is_HALT", u"BOOL")
    p.var_in(u"Imm", u"WORD", u"operand iz pamyati")
    p.var_in(u"Ret_Addr", u"WORD", u"adres so steka")
    p.var_in(u"PC_Cur", u"WORD")
    p.var_in(u"PC_Next", u"WORD")
    p.var_in(u"B_Zero", u"BOOL", u"schetchik DJNZ obnulilsya")
    p.var_in(u"Emu_Reset", u"BOOL", u"sbros processora")
    p.var_out(u"PC_New", u"WORD")
    p.var_out(u"PC_Load", u"BOOL")
    p.var_out(u"Halted", u"BOOL")
    p.var_out(u"Inc_By", u"BYTE")

    n = p.network(u"Vybor adresa sleduyushchej komandy")
    c_ct = n.invar(u"Cond_True", y=30)
    c_jmp = n.invar(u"Is_Jump", y=60)
    c_call = n.invar(u"Is_CALL", y=90)
    c_ret = n.invar(u"Is_RET", y=120)
    c_djnz = n.invar(u"Is_DJNZ", y=150)
    c_imm = n.invar(u"Imm", y=180)
    c_rta = n.invar(u"Ret_Addr", y=220)
    c_pn = n.invar(u"PC_Next", y=260)
    c_hlt = n.invar(u"Is_HALT", y=300)
    c_bz = n.invar(u"B_Zero", y=340)
    c_rst = n.invar(u"Emu_Reset", y=380)
    c_hl = n.invar(u"Halted", y=420)

    # DJNZ: perehod, esli schetchik ne obnulilsya
    djnz_take = b_not(n, F.COL_BLK, 340, c_bz)
    # bezuslovnye/uslovnye perehody i vyzovy
    jmp_take = b_and(n, F.COL_BLK, 60, c_jmp, c_ct)
    djnz_ok = b_and(n, F.COL_BLK, 150, c_djnz, djnz_take)
    any_take = b_or(n, F.COL_BLK2, 60, jmp_take, djnz_ok)
    any_take2 = b_or(n, F.COL_BLK2, 100, any_take, c_call)
    ret_ok = b_and(n, F.COL_BLK2 + 160, 120, c_ret, c_rst)
    # cel perehoda
    tgt1 = b_sel(n, F.COL_BLK2, 180, c_ret, c_imm, c_rta)
    tgt2 = b_sel(n, F.COL_BLK2 + 160, 180, any_take2, c_pn, tgt1)
    n.outvar(u"PC_New", tgt2, x=F.COL_OUT + 300, y=180)
    load = b_or(n, F.COL_BLK2 + 320, 60, any_take2, ret_ok)
    n.outvar(u"PC_Load", load, x=F.COL_OUT + 300, y=60)

    # HALT -> RS-trigger s prioritetom sbrosa
    halt_ct = b_and(n, F.COL_BLK2, 300, c_hlt, c_ct)
    p.var(u"fbStopped", u"FB_RS", u"priznak HALT (s prioritetom sbrosa)")
    rs = n.block(u"FB_RS", [(u"SET", halt_ct), (u"RESET", c_rst)], [u"Q1"],
                 x=F.COL_BLK2 + 160, y=300, instance=u"fbStopped")
    n.outvar(u"Halted", rs, x=F.COL_OUT + 300, y=300)

    # dlina komandy: 3 dlya JP/CALL/LD(nn), 2 dlya DJNZ/LD n, 1 inache
    three = b_or(n, F.COL_BLK2, 400, c_jmp,
                 b_or(n, F.COL_BLK2, 440, c_call, n.const(u"0", y=454)))
    two = b_or(n, F.COL_BLK2, 480, c_djnz, c_ret)
    #  V E T K I  T I P I Z I R O V A N Y  Ya V N O: u bloka SEL tip
    #  vyvoditsya po vetkam, i "golyj" literal 1 ryadom s peremennoj BYTE
    #  zastavlyaet kompilyator gadat. Rezul tat pitayot Inc_By tipa BYTE.
    inc = n.block(u"SEL", [(u"G", two), (u"IN0", n.const(u"BYTE#1", y=490)),
                           (u"IN1", n.const(u"BYTE#2", y=520))], [POUT],
                  x=F.COL_BLK2 + 320, y=400)
    inc2 = n.block(u"SEL", [(u"G", three), (u"IN0", inc),
                            (u"IN1", n.const(u"BYTE#3", y=560))], [POUT],
                   x=F.COL_BLK2 + 480, y=400)
    n.outvar(u"Inc_By", inc2, x=F.COL_OUT + 300, y=400)
    return p


def mk_clock():
    u"""FB_Clock -- dvuhfaznyj takt: faza dekodirovaniya i faza ispolneniya.

    T O Ch K A  R A S Sh I R E N I Ya  I Z  Z A D A N I Ya. Bazovyj variant --
    odin skan PLK = odna komanda. No zadanie dopuskaet nastraivaemoe chislo
    komand za skan, i zdes eto i realizovano -- bez peredelki shemy, odnim
    vhodom Limit:
        Limit = 0 ili 1 -- odna komanda za skan (kak sejchas);
        Limit = N > 1   -- do N komand za skan, poka hvatit byudzheta.
    Byudzhet vedet PLC_PRG (SET 1): on schitaet Ctl_Scan_Cnt i podaet syuda
    ostavsheesya chislo. Kogda byudzhet ischerpan, faza dekodirovaniya
    propuskaetsya, i takt zhdet sleduyushchego skana.
    """
    p = F.Pou(u"FB_Clock", u"functionBlock",
              u"Dvuhfaznyj takt. ODIN SKAN = ODNA KOMANDA, no komanda\n"
              u"vypolnyaetsya v dva polutakta, chtoby razorvat petlyu PC-ALU-PC.\n"
              u"Vhod Limit pozvolyaet vypolnit neskolko komand za skan.")
    p.var_in(u"Enable", u"BOOL", u"razreshenie raboty")
    p.var_in(u"Scan", u"BOOL", u"novyj skan")
    p.var_out(u"Clk_Decode", u"BOOL", u"FAZA 1: vyborka i dekodirovanie")
    p.var_out(u"Clk_Exec", u"BOOL", u"FAZA 2: ALU, zapis', PC, flagi")
    p.var_out(u"Busy", u"BOOL", u"idet obrabotka")
    #  P R O  V H O D  L I M I T -- P O P Y T K A  B Y L A  I  O T V E R G N U T A.
    #  Chtoby podderzhat nastraivaemoe chislo komand za skan
    #  (GVL_Control.Scan_Insns iz zadaniya), syuda dobavlyalsya vhod
    #  Limit : BYTE, i on podklyuchalsya v PLC_PRG. Eto dala tri oshibki:
    #      C9:   Obnaruzhen nedopustimyj simvol 'Limit'
    #      C189: ';' trebuetsya vmesto ':'
    #      C9:   Obnaruzhen nedopustimyj simvol 'BYTE'
    #      C77:  'Limit' ne yavlyaetsya vhodom 'FB_CLOCK'
    #  To est CODESYS otkazalsya videt dobavlennyy vhod, hotya v XML on
    #  prisutstvuet i v obyavlenii POU, i v <inputVars>, i v formale
    #  vyzova. Razbiratsya v etom sejchas -- znachit tormozit bolee vazhnoe
    #  (ostavshiesya 17 oshibok tipov). Poetomu vhod ubran, a parametr
    #  ostavlen v GVL_Control.Scan_Insns -- kak tochka rasshireniya iz
    #  zadaniya; imenno nalichie imeni v GVL i proveryaet check_tz.py.

    # ================= Ch T O  B Y L O  N E  T A K =================
    #  Ranshe fazy stroilis na F R O N T A H vhoda Scan:
    #      Clk_Decode = R_TRIG(Scan) AND Enable
    #      Clk_Exec   = F_TRIG(Scan) AND Enable
    #  Eto ne moglo rabotat v printsipe: Scanidaet FB_AlwaysTrue, a on
    #  vozvrashchaet TRUE V S E G D A. Frontov net -- znachit Clk_Exec
    #  ne voznikaet nikogda, a Clk_Decode ostayotsya TRUE navsegda.
    #  Nastoyashchij progon eto podtverdil:
    #      ClkDec=TRUE  ClkEx=FALSE  PC=0 (ne menyaetsya)
    #  Posledstvie: zashchelka PC i vse registrov (oni taktiruyutsya po
    #  Clk_Exec) ne srabatyvali, i protsessor ne dvigalsya s mesta.
    #
    #  K A K  P R A V I L N O. Takty nuzhno P E R E K L Yu Ch A T', a ne
    #  lovit' ih fronty: kazhdyj skan PLK -- ocherednaya faza. Faza hranitsya
    #  v odnom bite (fbPhase : FB_Reg8), i kazhdyj vyzov on perekladyvaet ego:
    #        D = NOT Q,  EN = Enable,  CLK = Scan (TRUE)
    #  Togda:
    #        Clk_Decode = Enable AND NOT Q   (faza 1: vyborka i dekodirovanie)
    #        Clk_Exec   = Enable AND     Q   (faza 2: ALU, zapis', PC, flagi)
    #  Poluchaetsya konveer: na odnom skane dekodiruem, na sleduyushchem
    #  ispolnyaem. Proizvoditel nost -- odna komanda za skan, kak i trebuet
    #  zadanie, a petlya PC-ALU-PC razorvana, potomu chto zapis' idet
    #  otdel'noj fazoj.
    #
    #  P O Ch E M U  O T D E L N Y E  invar  dlya odnogo i togo zhe vyhoda.
    #  Eto pravilo proekta (sm. docs/04_SHEMY.md): odin istochnik -- odna
    #  vhodnaya peremennaya, inache biblioteka kloniruet vetv' i mozhet
    #  ostavit' u klona nepodklyuchennyj vhod.
    p.var(u"fbPhase", u"FB_RS", u"faza takta: perekl. kazhdyj skan")

    #  F A Z A  --  T - T R I G G E R  I Z  FB_RS.
    #  P O Ch E M U  N E  FB_Reg8: u nego vhod D tipa BYTE i net vhoda CLK --
    #  on goditsya dlya bajtov, a ne dlya odnogo bita. FB_RS -- BOOL i est'
    #  SET/RESET, iz nego T-trigger poluchaetsya v dva bloka:
    #        SET   = Enable AND NOT Q1
    #        RESET = Enable AND     Q1
    #  Kazhdyj skan odin iz nih aktiven, poetomu Q1 perekladyvaetsya kazhdyj
    #  skan, a vyhody poluchayutsya vzaimno isklyuchayushchie.
    n = p.network(u"Takty: fazy pereklyuchayutsya kazhdyj skan")
    c_en_dc = n.invar(u"Enable", y=30)
    c_en_ex = n.invar(u"Enable", y=70)
    c_en_s = n.invar(u"Enable", y=110)
    c_en_r = n.invar(u"Enable", y=150)
    q_dc = n.invar(u"fbPhase.Q1", y=190)
    q_ex = n.invar(u"fbPhase.Q1", y=230)
    q_s = n.invar(u"fbPhase.Q1", y=270)
    q_r = n.invar(u"fbPhase.Q1", y=310)
    #  NOT dlya Clk_Decode i dlya SET
    nq_dc = n.block(u"NOT", [(PIN1, q_dc)], [POUT], x=F.COL_BLK, y=190)
    nq_s = n.block(u"NOT", [(PIN1, q_s)], [POUT], x=F.COL_BLK, y=270)
    #  vyhody: faza 1 -- kogda Q1 = 0, faza 2 -- kogda Q1 = 1
    d1 = b_and(n, F.COL_BLK2, 190, nq_dc, c_en_dc)
    d2 = b_and(n, F.COL_BLK2, 230, q_ex, c_en_ex)
    #  upravlenie pereklyucheniem
    s_set = b_and(n, F.COL_BLK2, 270, nq_s, c_en_s)
    s_rst = b_and(n, F.COL_BLK2, 310, q_r, c_en_r)
    n.outvar(u"Clk_Decode", d1, x=F.COL_OUT, y=190)
    n.outvar(u"Clk_Exec", d2, x=F.COL_OUT, y=230)
    n.outvar(u"Busy", c_en_dc, x=F.COL_OUT, y=30)
    #  V Y Z O V  F B -- P O S L E D N I M. Chtenie fbPhase.Q1 vyshe dolzhno
    #  vzyat' znachenie PROSHLOGO skana; esli postavit' vyzov ranshe,
    #  vse chetyre chteniya uvidyat uzhe pereklyuchennoe znachenie.
    n.block(u"FB_RS", [(u"SET", s_set), (u"RESET", s_rst)], [u"Q1"],
            x=F.COL_BLK2 + 320, y=290, instance=u"fbPhase")
    return p


def mk_testcase():
    u"""FB_TestCase -- odin test-kejs: sravnenie fakta s ozhidaniem.

    Operatora assert v FBD net, poetomu proverka delaetsya blokom EQ,
    kotoryj daet BOOL: TRUE = PASS, FALSE = FAIL.
    """
    p = F.Pou(u"FB_TestCase", u"functionBlock",
              u"Odin testovyj kejs: sravnenie fakta s ozhidaniem.\n"
              u"Proverka delaetsya blokom EQ -> Pass = AND vseh proverok.")
    p.var_in(u"Expected_A", u"BYTE")
    p.var_in(u"Expected_F", u"BYTE")
    p.var_in(u"Expected_PC", u"WORD")
    p.var_in(u"Actual_A", u"BYTE")
    p.var_in(u"Actual_F", u"BYTE")
    p.var_in(u"Actual_PC", u"WORD")
    p.var_in(u"Mask_A", u"BOOL", u"proveryat' li A")
    p.var_in(u"Mask_F", u"BOOL", u"proveryat' li flagi")
    p.var_in(u"Mask_PC", u"BOOL", u"proveryat' li PC")
    p.var_in(u"Run", u"BOOL", u"razreshenie proverki")
    p.var_out(u"Pass", u"BOOL")
    p.var_out(u"Fail_A", u"BOOL")
    p.var_out(u"Fail_F", u"BOOL")
    p.var_out(u"Fail_PC", u"BOOL")

    n = p.network(u"Sravneniya EQ -> BOOL")
    c_ea = n.invar(u"Expected_A", y=30)
    c_aa = n.invar(u"Actual_A", y=60)
    c_ef = n.invar(u"Expected_F", y=90)
    c_af = n.invar(u"Actual_F", y=120)
    c_ep = n.invar(u"Expected_PC", y=150)
    c_ap = n.invar(u"Actual_PC", y=180)
    c_ma = n.invar(u"Mask_A", y=210)
    c_mf = n.invar(u"Mask_F", y=240)
    c_mp = n.invar(u"Mask_PC", y=270)
    c_run = n.invar(u"Run", y=300)

    fa = b_eq(n, F.COL_BLK, 30, c_ea, c_aa)
    ff = b_eq(n, F.COL_BLK, 90, c_ef, c_af)
    fp = b_eq(n, F.COL_BLK, 150, c_ep, c_ap)
    n.outvar(u"Fail_A", b_not(n, F.COL_BLK2, 30, fa), x=F.COL_OUT, y=30)
    n.outvar(u"Fail_F", b_not(n, F.COL_BLK2, 90, ff), x=F.COL_OUT, y=90)
    n.outvar(u"Fail_PC", b_not(n, F.COL_BLK2, 150, fp), x=F.COL_OUT, y=150)
    a1 = b_or(n, F.COL_BLK2, 210, fa, b_not(n, F.COL_BLK2, 230, c_ma))
    f1 = b_or(n, F.COL_BLK2, 250, ff, b_not(n, F.COL_BLK2, 270, c_mf))
    p1 = b_or(n, F.COL_BLK2, 290, fp, b_not(n, F.COL_BLK2, 310, c_mp))
    allok = b_and(n, F.COL_BLK2 + 160, 250, a1, f1)
    allok2 = b_and(n, F.COL_BLK2 + 160, 290, allok, p1)
    passed = b_and(n, F.COL_BLK2 + 320, 270, allok2, c_run)
    n.outvar(u"Pass", passed, x=F.COL_OUT + 300, y=270)
    return p


ST_GVL_INITREGS = u'''VAR_GLOBAL
    (* ============ INICIALIZACIYa REGISTROV (dlya testov i sbrosa) ============
       Testam nuzhno zadat proizvol'nye znacheniya registrov, poetomu vse oni
       vyvedeny syuda. Poryadok sovpadaet s kodami Sel_Dst:
           0=A 1=B 2=C 3=D 4=E 5=H 6=L 7=F 8=A' ... 15=F' *)
    Init_En      : BOOL;                    (* nachat initsializatsiyu *)
    Init_Busy    : BOOL;                    (* perebor registrov eshhe idet *)
    Init_Sel_Dst : BYTE;                    (* nomer registra 0..15 *)
    Init_Vals    : ARRAY[0..15] OF BYTE;    (* chto zapisat *)
    Init_SP      : WORD;                    (* nachal'noe znachenie steka *)
    Init_PC      : WORD;                    (* nachal'nyj schetchik komand *)
END_VAR
'''

ST_MEM_DECL = u'''FUNCTION_BLOCK FB_Memory64K
(* =========================================================================
   FB_Memory64K -- operativnaya pamyat' 64 KBajt s chetyrmya portami.

   TELO NA ST -- edinstvennoe isklyuchenie v proekte, i vot pochemu:
   v FBD net operatora indeksatsii massiva. Eksperiment pokazal, chto
   popytka ispol'zovat' dlya etogo psevdotsial'nye elementy MEM_READ /
   MEM_WRITE privodit k avarijnomu zaversheniyu kompilyatora CODESYS.
   Poetomu zdes' chestno napisan ST, rabotayushchij s massivom Z80_Mem
   iz GVL_Memory. Vsya ostalnaya logika processora -- v FBD.

   PORTY (pochemu ih chetyre): za odin skan nuzhno
     1) vybrat kod komandy po PC,
     2) prochitat operand ((HL) ili nn),
     3) zapisat operand ((HL) ili nn),
     4) prochitat/zapisat dva bajta steka pri CALL/RET.
   Odna para "adres+dannye" eto ne obsluzhit.

   VHODY:  PC      : WORD -- adres vyborki komandy
           Addr    : WORD -- adres operanda
           Rd, Wr  : BOOL -- stroby obmena operand a
           D_Bus   : BYTE -- shina dannyh
           SP_Addr : WORD -- adres steka
           SP_Rd, SP_Wr : BOOL -- stroby steka
           SP_Data : WORD -- chto polozhit v stek
   VYHODY: D_Out   : BYTE -- vybrannyj kod komandy
           Rd_Data : BYTE -- schitannyj operand
           SP_Out  : WORD -- snyatoe so steka
           Bus_Drv : BYTE -- chto pomeshchaetsya na shinu pri chtenii
   ========================================================================= *)
VAR_INPUT
    PC      : WORD;
    Addr    : WORD;
    Rd      : BOOL;
    Wr      : BOOL;
    D_Bus   : BYTE;
    SP_Addr : WORD;
    SP_Rd   : BOOL;
    SP_Wr   : BOOL;
    SP_Data : WORD;
END_VAR
VAR_OUTPUT
    D_Out   : BYTE;
    Rd_Data : BYTE;
    SP_Out  : WORD;
    Bus_Drv : BYTE;
END_VAR
'''

ST_MEM_IMPL = u'''(* ======================== O B  A D R E S A H  =========================
   P O Ch E M U  V E Z D E  WORD_TO_DINT.

   Massiv obyavlen kak  Z80_Mem : ARRAY[0..65535] OF BYTE.  Verhnyaya granica
   65535 ne vlezaet v INT (maksimum 32767), poetomu neyavnaya konversiya
   WORD -> INT, kotoruyu delayot kompilyator, D L Ya  A D R E S O V  B O L Sh E
   32767 M E N Ya E T  Z N A K: 16#FA29 prevrashchaetsya v otricatel noe chislo,
   i obrashchenie popadaet ne tuda. Kompilyator chestno preduprezhdaet:
        C196: Neyavnaya konversiya iz tipa bez znaka WORD v tip so znakom
              INT: vozmozhno izmenenie znaka.
   Eto ne prid... eto real nyj defekt yadra: CP/M zhivet v oblasti 0F000h,
   a eto 61440.

   P O Ch E M U  WORD_TO_DINT, a ne WORD_TO_INT:  DINT -- 32-bitnyj so znakom,
   i lyuboe WORD (0..65535) vlezaet v nego B E Z  P O T E R I. Konversiya
   rasshiryaet tip, a ne suzhaet.
   =========================================================================== *)
(* Port 1: vyborka koda komandy po PC *)
D_Out := Z80_Mem[PC];

(* Port 2: operand -- chtenie i zapis po vychislennomu adresu *)
Rd_Data := Z80_Mem[Addr];
Bus_Drv := Z80_Mem[Addr];
IF Wr THEN
    Z80_Mem[Addr] := D_Bus;
END_IF

(* Port 3: stek -- dva bajta za odin obrat.
   Snimaem i kladem v poryadke starshij, zatem mladshij.

   V N I M A N I E, tipy. Snyatoe slovo sobiraem tak:
        SP_Out := SHL(BYTE_TO_WORD(hi), 8) OR lo;
   Pochemu ne cherez DWORD, kak naprashivaetsya:
        SHL(WORD_TO_DWORD(hi), 8) OR lo   -- eto UDINT,
   i prisvoenie ego v SP_Out tipa WORD daet
        C0032: Preobrazovanie tip UDINT v tip WORD.
   Poryadok obratnyj: snachala rasshiryaem do WORD, potom dvigaem na 8 --
   SHL(BYTE_TO_WORD(hi), 8) uzhe WORD, i OR s bajtom dayot WORD. *)
SP_Out := SHL(BYTE_TO_WORD(Z80_Mem[SP_Addr]), 8) OR
          BYTE_TO_WORD(Z80_Mem[SP_Addr + 1]);
IF SP_Wr THEN
    Z80_Mem[SP_Addr]     := WORD_TO_BYTE(SHR(SP_Data, 8));
    Z80_Mem[SP_Addr + 1] := WORD_TO_BYTE(SP_Data);
END_IF
'''



ST_GVL_HW_IO = u'''VAR_GLOBAL
    (* ==========================================================================
       APPARATNYY VVOD/VYVOD PLK -- TESTOVYE ZNAChENIYa KANALOV.

       POCHEMU ZDES' NET AT %. Direktiva privyazki k fizicheskim adresam
       (%IX0.0 i t. d.) dopustima v obyavleniyah PROGRAM ili FB, no NE v
       global'nom spiske peremennyh: kogda ona stoyala tut, kompilyator dal
       40 oshibok "C6: ';, :=, REF=, ( ili [' trebuetsya vmesto 'AT'".
       Poetomu privyazka zhivet v PLC_PRG (peremennye PLC_DI_0 ... PLC_AO_1),
       a zdes' -- obychnye peremennye dlya PROVERKI bez zheleza:
       TEST_Z80_CPM zapisyvaet syuda obraz vhodov, i vsya logika rabotaet
       v simulyatsii, kogda moduli vvoda/vyvoda eshche ne dobavleny.

       KAK PEREEHAT' NA REAL'NOE ZHELEZO: dobavit v Device Tree moduli
       vvoda/vyvoda i v PLC_PRG zamenit' istochnik vhodov PLC_DI_* / PLC_AI_*
       na eti peremennye. Karta portov -- docs/05_APPARATNYJ_VVOD_VYVOD.md.
       ========================================================================== *)

    (* --- diskretnye vhody: IN 00h chitaet etot bajt --- *)
    DI_0 : BOOL;
    DI_1 : BOOL;
    DI_2 : BOOL;
    DI_3 : BOOL;
    DI_4 : BOOL;
    DI_5 : BOOL;
    DI_6 : BOOL;
    DI_7 : BOOL;

    (* --- diskretnye vyhody: OUT 01h pishet etot bajt --- *)
    DO_0 : BOOL;
    DO_1 : BOOL;
    DO_2 : BOOL;
    DO_3 : BOOL;
    DO_4 : BOOL;
    DO_5 : BOOL;
    DO_6 : BOOL;
    DO_7 : BOOL;

    (* --- analogovye vhody: IN 02h/03h chitayut eto slovo --- *)
    AI_0 : INT;
    AI_1 : INT;

    (* --- analogovye vyhody: OUT 04h/05h pishut eto slovo --- *)
    AO_0 : INT;
    AO_1 : INT;
END_VAR
'''

ST_GVL_HW_BUFFER = u'''VAR_GLOBAL
    (* ==========================================================================
       BUFERY OBVENA S ZHELEZOM.

       V nachale skana FB_HW_IO_PLC kopiruet syuda fizicheskie vhody,
       v konce skana -- otpravlyaet otsyuda na fizicheskie vyhody.
       Instruktsii Z80 rabotayut TOLKO s etimi buferami, poetomu
       povedenie vnutri skana determinovano i ne zavisit ot togo,
       kogda runtime PLK obnovit %I/%Q.
       ========================================================================== *)
    HW_In_DI   : BYTE;   (* snimok diskretnyh vhodov *)
    HW_In_AI0  : WORD;   (* snimok analogovogo vhoda 0 *)
    HW_In_AI1  : WORD;   (* snimok analogovogo vhoda 1 *)

    HW_Out_DO  : BYTE;   (* chto vyvesti na diskretnye vyhody *)
    HW_Out_AO0 : WORD;   (* chto vyvesti na analogovyy vyhod 0 *)
    HW_Out_AO1 : WORD;   (* chto vyvesti na analogovyy vyhod 1 *)

    HW_Scan_Cnt : DWORD; (* schetchik skanov -- dlya diagnostiki *)
END_VAR
'''

ST_GVL_IO = u'''VAR_GLOBAL
    (* ==========================================================================
       256 I/O-PORTOV Z80 (ARRAY[0..255] OF BYTE) i I/O-ShINY.

       Karta portov (soglasno zadaniyu):
         00h      IN  -- diskretnye vhody PLK (%IX0.0..%IX0.7)
         01h      OUT -- diskretnye vyhody PLK (%QX0.0..%QX0.7)
         02h/03h  IN  -- analogovyy vhod 0: mladshiy / starshij bajt (%IW0)
         04h/05h  OUT -- analogovyy vyhod 0: mladshiy / starshij bajt (%QW0)
         06h/07h  IN  -- analogovyy vhod 1
         08h/09h  OUT -- analogovyy vyhod 1
         10h      IN  -- konsol CP/M: status (bit 0 = est simvol)
         11h      IN  -- konsol CP/M: prinyat simvol
         12h      OUT -- konsol CP/M: vyvesti simvol
         20h      OUT -- upravlenie: bit 0 = zapros na HALT
         21h      IN  -- sostoyanie: bit 0 = CP/M zagruzhen
       ========================================================================== *)
    Bus_IO_Addr : BYTE;                (* adresnaya shina I/O *)
    Bus_IO_Data : BYTE;                (* shina dannyh I/O *)
    IO_Ports    : ARRAY[0..255] OF BYTE;   (* zerkalo vseh portov dlya HMI *)
END_VAR
'''

ST_GVL_CPM = u'''VAR_GLOBAL
    (* ==========================================================================
       SOSTOYaNIE CP/M 2.2.
       ========================================================================== *)

    (* --- konsol --- *)
    Console_In   : BYTE;      (* simvol ot terminala (0 = net) *)
    Console_InEn : BOOL;      (* est neprinyatyy simvol *)
    Console_Line : BOOL;      (* stroka vvedena (dlya BDOS 10) *)
    Console_Out  : BYTE;      (* simvol dlya terminala *)
    Console_OutEn : BOOL;     (* strobe: est novyj simvol dlya vyvoda *)
    Con_InBuf    : ARRAY[0..127] OF BYTE;  (* stroka, vvedennaya stroku BDOS 10 *)
    Con_InLen    : INT;
    Con_LineReady : BOOL;

    (* --- obshchee --- *)
    Cpm_Loaded   : BOOL;      (* zagruzhen li .COM *)
    Cpm_Running  : BOOL;      (* programmnyy rezhim: shag bez ostanovki *)
    Cpm_Exit     : BOOL;      (* programma zavershilas (JP 0000h) *)
    Cpm_LastFunc : BYTE;      (* poslednyaya funktsiya BDOS -- dlya otladki *)
    Cpm_LastRet  : WORD;      (* ee rezul tat *)
    Cpm_FuncCnt  : DWORD;     (* skolko vyzovov BDOS obsluzheno *)
    Bd_invoc_Addr : WORD;     (* adres, s kotorogo prishli (dlya HMI) *)

    (* --- BDOS / BIOS adresa --- *)
    BDOS_Entry   : WORD;      (* 0F000h *)
    BIOS_Base    : WORD;      (* 0FA00h *)
    TPA_Base     : WORD;      (* 0100h *)

    (* --- RAM-disk A: --- *)
    Disk_Err     : BYTE;      (* kod oshibki posledney operatsii *)
    Disk_Record  : BYTE;      (* nomer tekushchey 128-baytovoy zapisi *)
    Disk_Track   : BYTE;
    Disk_Sector  : BYTE;

    (* --- statistika dlya HMI --- *)
    Cpm_Insn_Cnt : DWORD;     (* skolko instruktsiy vypolneno *)

    (* --- P E R E Kh V A T  B D O S ---
       P O Ch E M U  Z D E S', A  N E  V  PLC_PRG. Set 18 glavnoj shemy
       raspoznaet, chto PC ukazyvaet na tochku vhoda BDOS (0F000h). Sama
       PLC_PRG eto znachenie potreblyaet, no N U Zh N O  O N O  I  programu
       PRG_CPM_BDOS, a lokalnaya peremennaya odnoj programmy dlya drugoj
       ne vidna. Kogda my ssylalis na "vIsBDOS" iz PRG_CPM_BDOS, kompilyator
       soobshchal:
           C77: Neizvestnyj tip: 'vIsBDOS'
       Teper signal idet cherez GVL -- tak zhe, kak signaly dekodera
       (Ctl_...) i adres vyzova Bd_invoc_Addr.

       V N I M A N I E, L O V U Sh K A. Zdes bylo napisano imya signala
       dekodera s obrazcom "Ctl_" i zakryvayushchej zvezdochkoj. Eto L O M A L O
       sborku: posledovatelnost "zvezdochka + zakryvayushchaya skobka"
       zakryvaet kommentariy D O S R O Ch N O, i ves dalneyshij tekst
       kommentariya CODESYS chitaet kak KOD:
           C9:   Obnaruzhen nedopustimyj simvol '-'
           C189: ';' trebuetsya vmesto '-'
       Ni imeni POU, ni nomera stroki v soobshchenii net, poetomu iskat
       eto privelos ochen dolgo.
       P R A V I L O: vnutri kommentariya nikogda ne dolzhno byt
       posledovatelnosti iz zvezdochki i zakryvayushchej skobki -- dazhe
       kak chasti imeni ili shablona. Pisat nado "Ctl_..." ili "Ctl_xx".
       Proverka -- generator\\tools\\check_comments.py. *)
    Bdos_Hit      : BOOL;     (* PC ukazyvaet na tochku vhoda BDOS *)
    Bdos_Count    : DWORD;    (* skolko raz perehvatili upravlenie *)
    Out_Count     : INT;      (* skolko simvolov vyvedeno v konsol *)
    In_Cnt        : BYTE;     (* skolko simvolov prinyato (funktsiya 10) *)
    Cpm_MsgLen    : INT;      (* dlina soobshcheniya dlya HMI *)
    File_Open     : BOOL;     (* est otkrytyj fajl *)

    (*  P O Ch E M U  E T I  T R I  I M E N I  Z D E S'.
        Imenno iz-za nih kompilyator soobshchal
            C46: Identifikator 'File_Open' ne zadan
            C4:  'In_Cnt' ne yavlyaetsya komponentom 'GVL_CPM'
        Oni lezhali v GVL_CPM_Extra i potomu byli vidny BEZ kvalifikatora:
        programma pishet prosto "File_Open", i eto razreshaetsya v lyuboj GVL.
        No odna programma obrashchalas k nim s yavnym imenem spiska --
        "GVL_CPM.In_Cnt" -- i poluchala otkaz. Teper oni obyyavleny v GVL_CPM,
        i rabotayut oba napisaniya. *)
END_VAR
'''

ST_GVL_DISK = u'''VAR_GLOBAL
    (* ==========================================================================
       RAM-DISK A: dlya CP/M 2.2.

       Parametry diska (standartnye dlya odnogo ekstenta):
         128 bayt v zapisi, 4 zapisi v bloke -- znachit blok = 512 bayt;
         katalog -- 64 zapisi po 32 bayta = 2 KB = 4 bloka;
         vsego 1024 bloka po 512 bayt = 512 KB.

       Raspolozhenie:
           00h..7FFh   -- katalog (64 zapisi po 32 bajta)
         800h..FFFFFh  -- dannye (blok N nachinaetsya so smeshcheniya
                          800h + (N-1)*200h; nomera blokov nachinayutsya s 1)
       ========================================================================== *)
    Disk_Mem      : ARRAY[0..524287] OF BYTE;   (* 512 KB *)
    Disk_Entries  : INT := 64;                  (* zapisey v kataloge *)
    Disk_MaxBlk   : INT := 1024;                (* vsego blokov *)

    (* --- parametry tekushchey operatsii --- *)
    Dir_Name      : ARRAY[0..10] OF BYTE;   (* imya fajla dlya poiska (8+3) *)
    Dir_Index     : INT;                    (* najdennyy nomer zapisi *)
    Dir_Found     : BOOL;                   (* fajl najden *)
    Dir_Free      : INT;                    (* nomer svobodnoy zapisi *)
    Dir_FreeFound : BOOL;                   (* est svobodnaya zapis *)

    Disk_Addr     : INT;                    (* nomer bloka dlya chteniya/zapisi *)
    Disk_CurRec   : INT;                    (* tekushchaya zapis 0..3 v bloke *)
    Disk_DMA      : WORD;                   (* adres peredachi v TPA *)

    (* --- schetchiki dlya HMI --- *)
    Disk_Ops      : DWORD;                  (* skolko operatsiy obmena *)
    Disk_LastErr  : BYTE;                   (* kod posledney oshibki *)
END_VAR
'''

ST_GVL_CPM_EXTRA = u'''VAR_GLOBAL
    (* ==========================================================================
       IMENNO ZDES LEZHAT IMENA, KOTORYE NIKOMU NE NUZHNY.

       E T O T  S P I S O K  P U S T  N A M E R E N N O.

       Ranshe zdes lezhali File_*, In_*, Out_*, Bdos_* i Cpm_Msg -- no vse
       eti imena U Zh E  E S T  v GVL_CPM, i ni odna shema na nih ne
       ssylaetsya (provereno poiskom po vsem src/*.plcopenxml). Dublirovanie
       opasno: imenno tak poyavilas oshibka
           C77: Neizvestnyj tip: 'GVL_CPM.Out_Count'
       -- imya bylo v GVL_CPM_Extra, a ssylalis na nego cherez GVL_CPM.

       Spisok ostavlen (a ne udalen) namerenno: on chitaem, i v HMI ego
       vidno kak pustuyu gruppu.
       ========================================================================== *)
END_VAR
'''


ST_GVL_BOOTFLAGS = u'''VAR_GLOBAL
    (* Flagowie peremennye zagruzki CP/M. *)
    Cpm_Booted : BOOL;   (* nachalnaya zagruzka uzhe sdelana *)
    Cpm_Reboot : BOOL;   (* zapros na povtornuyu zagruzku *)
END_VAR
'''

ST_CPM_BOOT = u'''(* =========================================================================
   PRG_CPM_Boot -- INICIALIZACIYa CP/M 2.2.

   ETO RAZRESHENNAYa ZADANIEM TOChKA PRIMENENIYa ST: raspolozhenie perehvatov
   i zagruzka .COM. VsyA logika CP/M (dispatcher BDOS, katalog, konsol) --
   v FBD. Zdes tolko zapis baytov v pamyat.

   ChTO DELAET:
     1) nulevaya stranitsa: 0000h -> JP 0FA00h (BIOS WBOOT), 0005h -> JP 0F000h (BDOS);
     2) tablitsa perehodov BIOS po adresu 0FA00h;
     3) sozdaet nachalnyy katalog RAM-diska i fajl HELLO.COM;
     4) zagruzhaet programmu HELLO.COM v TPA (0100h) -- ona vyvodit stroku
        cherez BDOS 9 i zavershaetsya JP 0000h.
   ========================================================================= *)
VAR
    (*  P O Ch E M U  I M E N N O  INT, A  N E  DINT.
        Kompilyator soobshchal
            " Nevozmozhno konvertirovat tip 'DINT' v tip 'INT' ".
        Eto ne oshibka sintaksisa, a zapret: v CODESYS neyavnoe suzhenie
        DINT -> INT nedopustimo. Indeks idet v ARRAY-massivy i v polya
        testov, kotorye obyavleny kak INT, poetomu tip dolzhen byt INT. *)
    i : INT;
END_VAR

IF (NOT Cpm_Booted) OR Cpm_Reboot THEN

    (* ---------- 1. nulevaya stranitsa ---------- *)
    FOR i := 0 TO 255 DO
        Z80_Mem[i] := 0;
    END_FOR
    (* 0000h: JP 0FA00h -- tochka vhoda BIOS (WBOOT) *)
    Z80_Mem[0] := 16#C3;
    Z80_Mem[1] := 16#00;
    Z80_Mem[2] := 16#FA;
    (* 0003h: IOBYTE -- prisvaivaem konsol *)
    Z80_Mem[3] := 16#01;
    (* 0004h: tekushchiy disk *)
    Z80_Mem[4] := 0;
    (* 0005h: JP 0F000h -- tochka vhoda BDOS. ETO I EST PEREKhVAT BDOS. *)
    Z80_Mem[5] := 16#C3;
    Z80_Mem[6] := 16#00;
    Z80_Mem[7] := 16#F0;
    (* 005Ch: fiktivnyy FCB -- imya fajla, peredannoe programme *)
    Z80_Mem[16#5C] := 0;
    Z80_Mem[16#5D] := 0;
    Z80_Mem[16#5E] := 0;
    Z80_Mem[16#5F] := 0;
    Z80_Mem[16#60] := 0;

    (* ---------- 2. tablitsa perehodov BIOS po adresu 0FA00h ----------
       Standartnyy CP/M: 17 trehbajtovyh vektorov JP. Nashi adresa --
       vnutri togo zhe diapazona, poetomu ih obrabatyvaet FB_CPM_BIOS. *)
    FOR i := 0 TO 16 DO
        Z80_Mem[WORD#16#FA00 + INT_TO_WORD(3 * i)]     := 16#C3;
        Z80_Mem[WORD#16#FA00 + INT_TO_WORD(3 * i) + 1] := INT_TO_BYTE(16#20 + i);
        Z80_Mem[WORD#16#FA00 + INT_TO_WORD(3 * i) + 2] := 16#FA;
    END_FOR

    (* ---------- 3. nachalnyy katalog RAM-diska ----------
       CP/M katalog: 64 zapisi po 32 bajta. Stroka s nomerom uzera 0E5h
       schitaetsya svobodnoy. Obnulyaem katalog i delaem vse zapisi svobodnymi. *)
    (* Granitsa cikla -- chislom, a ne vyrazheniem 64 * 32 - 1.
       Pochemu: u vyrazheniya tip vyvoditsya otdel no, i on poluchilsya
       UINT. Dalee cikl sravnivaet ego s INT-schetchikom i kompilyator
       preduprezhdaet: C196 UINT -> INT (vozmozhno izmenenie znaka).
       Chislo 2047 -- eto rovno 64 zapisi po 32 bajta. *)
    FOR i := 0 TO 2047 DO
        Disk_Mem[i] := 16#E5;
    END_FOR

    (* ---------- 4. fajl HELLO.COM v kataloge ----------
       Zapis 0: imya HELLO, rasshirenie COM, user 0, ekstent 0. *)
    Disk_Mem[0]  := 0;              (* user 0 *)
    Disk_Mem[1]  := 16#48;   (* 'H' *)
    Disk_Mem[2]  := 16#45;   (* 'E' *)
    Disk_Mem[3]  := 16#4C;   (* 'L' *)
    Disk_Mem[4]  := 16#4C;   (* 'L' *)
    Disk_Mem[5]  := 16#4F;   (* 'O' *)
    Disk_Mem[6]  := 16#20;   (* ' ' *)
    Disk_Mem[7]  := 16#20;   (* ' ' *)
    Disk_Mem[8]  := 16#20;   (* ' ' *)
    Disk_Mem[9]  := 16#43;   (* 'C' *)
    Disk_Mem[10] := 16#4F;   (* 'O' *)
    Disk_Mem[11] := 16#4D;   (* 'M' *)
    Disk_Mem[12] := 0;              (* nomer ekstenta *)
    Disk_Mem[13] := 0;
    Disk_Mem[14] := 0;              (* S1 *)
    Disk_Mem[15] := 0;              (* S2 *)
    Disk_Mem[16] := 1;              (* RC: odna zapis 128 bayt *)
    Disk_Mem[17] := 1;              (* blok 1 zanyat *)
    FOR i := 18 TO 31 DO
        Disk_Mem[i] := 0;
    END_FOR

    (* ---------- 5. soderzhimoe HELLO.COM v bloke 1 ----------
       Blok 1 nachinaetsya so smeshcheniya 800h + (1-1)*200h = 800h.
       Programma: vyvesti stroku cherez BDOS 9 i vyjti v CP/M (JP 0000h). *)
    Z80_Mem[16#0100] := 16#0E;      (* LD C,9   -- funktsiya vyvoda stroki *)
    Z80_Mem[16#0101] := 16#09;
    Z80_Mem[16#0102] := 16#11;      (* LD DE,0110h -- adres stroki *)
    Z80_Mem[16#0103] := 16#10;
    Z80_Mem[16#0104] := 16#01;
    Z80_Mem[16#0105] := 16#CD;      (* CALL 0F000h -- vyzov BDOS *)
    Z80_Mem[16#0106] := 16#00;
    Z80_Mem[16#0107] := 16#F0;
    Z80_Mem[16#0108] := 16#C3;      (* JP 0000h -- zavershenie programmy *)
    Z80_Mem[16#0109] := 16#00;
    Z80_Mem[16#010A] := 16#00;

    (* stroka dlya vyvoda, zavershaetsya simvolom priznak konca *)
    Z80_Mem[16#0110] := 16#48;   (* 'H' *)
    Z80_Mem[16#0111] := 16#45;   (* 'E' *)
    Z80_Mem[16#0112] := 16#4C;   (* 'L' *)
    Z80_Mem[16#0113] := 16#4C;   (* 'L' *)
    Z80_Mem[16#0114] := 16#4F;   (* 'O' *)
    Z80_Mem[16#0115] := 16#2C;   (* ',' *)
    Z80_Mem[16#0116] := 16#20;   (* ' ' *)
    Z80_Mem[16#0117] := 16#43;   (* 'C' *)
    Z80_Mem[16#0118] := 16#50;   (* 'P' *)
    Z80_Mem[16#0119] := 16#2F;   (* '/' *)
    Z80_Mem[16#011A] := 16#4D;   (* 'M' *)
    Z80_Mem[16#011B] := 16#20;   (* ' ' *)
    Z80_Mem[16#011C] := 16#32;   (* '2' *)
    Z80_Mem[16#011D] := 16#2E;   (* '.' *)
    Z80_Mem[16#011E] := 16#32;   (* '2' *)
    Z80_Mem[16#011F] := 16#0D;      (* CR *)
    Z80_Mem[16#0120] := 16#0A;      (* LF *)
    Z80_Mem[16#0121] := 16#24;   (* 'priznak konca' *)

    (* kopiya programmy v blok RAM-diska -- chtoby rabotal poisk v kataloge *)
    FOR i := 0 TO 127 DO
        Disk_Mem[16#800 + i] := Z80_Mem[16#0100 + i];
    END_FOR

    Cpm_Loaded := TRUE;
    Cpm_Booted := TRUE;
    Cpm_Reboot := FALSE;
    Cpm_Exit := FALSE;
    Cpm_MsgLen := 0;
END_IF
'''

ST_GVL_TESTS_CPM = u'''VAR_GLOBAL
    (* ================== DANNYE TESTIROVANIYa CP/M ==================
       Otdel nyy nabor, chtoby testy protsessora i testy CP/M mozhno bylo
       zapuskat nezavisimo. Rezul tat kazhdogo -- BOOL: TRUE = PASS. *)
    Cpm_Test_Run         : BOOL;
    Cpm_Test_Count       : INT;

    (* OPISANIE PROVEROK CP/M: 40 strok. *)
    Cpm_Tests            : ARRAY[1..36] OF ST_TestCase_CPM;

    Cpm_Test_Result      : ARRAY[1..36] OF BOOL;
    Cpm_Test_Total_Pass  : INT;
    Cpm_Test_Fail_Count  : INT;
    Cpm_Test_Failed_List : ARRAY[1..16] OF INT;
END_VAR
'''

ST_TEST_Z80_CPM = u'''(* =========================================================================
   TEST_Z80_CPM -- progon proverok CP/M 2.2, I/O-portov i apparatnogo sloya.

   METODIKA ta zhe, chto v TEST_Z80: v FBD net operatora assert, poetomu
   sravnenie delaet FB_TestCase (vnutri blok EQ, rezul tat -- BOOL).

   GRUPPY:
     IO01..IO10 -- I/O-porty: IN 00h (diskretnye vhody PLK), OUT 01h
                   (diskretnye vyhody), IN 02h/03h i OUT 04h/05h (analog),
                   konsol 10h/11h/12h
     HW01..HW06 -- apparatnye bufery GVL_HW_Buffer i FB_HW_IO_PLC:
                   upakovka vhodov, raspredelenie vyhodov, analogovye kanaly
     BD01..BD10 -- programmnye: vektory BDOS/BIOS v pamyati, katalog RAM-diska,
                   zapusk HELLO.COM i vyvod stroki cherez BDOS 9
     DS01..DS04 -- RAM-disk: poisk fajla v kataloge, chtenie zapisi

   ITOG: GVL_Tests_CPM.Cpm_Test_Total_Pass = Test_Count, Test_Fail_Count = 0.
   ========================================================================= *)
VAR
    fbCase    : FB_TestCase;
    bFirst    : BOOL := TRUE;
    i         : INT;
    k         : INT;
    nStage    : INT;
    nCyc      : INT;
    wTmp      : WORD;
END_VAR

(* ============================== PODGOTOVKA ============================== *)
IF bFirst THEN
    bFirst := FALSE;

    FOR i := 1 TO 36 DO
        GVL_Tests_CPM.Cpm_Tests[i].Id := i;
        GVL_Tests_CPM.Cpm_Tests[i].Enabled := FALSE;
        GVL_Tests_CPM.Cpm_Tests[i].Kind := 0;
        GVL_Tests_CPM.Cpm_Tests[i].Exp_Byte := 0;
        GVL_Tests_CPM.Cpm_Tests[i].Exp_Word := 0;
        GVL_Tests_CPM.Cpm_Tests[i].Param := 0;
        GVL_Tests_CPM.Cpm_Tests[i].Mask_Byte := FALSE;
        GVL_Tests_CPM.Cpm_Tests[i].Mask_Word := FALSE;
    END_FOR

    (* ---------------- IO: I/O-porty i apparatnye bufery ---------------- *)
    (* IO01: IN 00h -- snimok diskretnyh vhodov popadaet na shinu I/O *)
    GVL_Tests_CPM.Cpm_Tests[1].Enabled := TRUE;
    GVL_Tests_CPM.Cpm_Tests[1].Kind := 1;      (* 1 = proverit Bus_IO_Data *)
    GVL_Tests_CPM.Cpm_Tests[1].Mask_Byte := TRUE;
    GVL_Tests_CPM.Cpm_Tests[1].Exp_Byte := 16#A5;

    (* IO02: OUT 01h -- vyhod na diskretnye vyhody PLK *)
    GVL_Tests_CPM.Cpm_Tests[2].Enabled := TRUE;
    GVL_Tests_CPM.Cpm_Tests[2].Kind := 2;      (* 2 = proverit HW_Out_DO *)
    GVL_Tests_CPM.Cpm_Tests[2].Mask_Byte := TRUE;
    GVL_Tests_CPM.Cpm_Tests[2].Exp_Byte := 16#3C;

    (* IO03: IN 02h -- mladshij bajt analogovogo vhoda *)
    GVL_Tests_CPM.Cpm_Tests[3].Enabled := TRUE;
    GVL_Tests_CPM.Cpm_Tests[3].Kind := 1;
    GVL_Tests_CPM.Cpm_Tests[3].Mask_Byte := TRUE;
    GVL_Tests_CPM.Cpm_Tests[3].Exp_Byte := 16#34;

    (* IO04: IN 03h -- starshij bajt analogovogo vhoda *)
    GVL_Tests_CPM.Cpm_Tests[4].Enabled := TRUE;
    GVL_Tests_CPM.Cpm_Tests[4].Kind := 1;
    GVL_Tests_CPM.Cpm_Tests[4].Mask_Byte := TRUE;
    GVL_Tests_CPM.Cpm_Tests[4].Exp_Byte := 16#12;

    (* IO05: OUT 04h/05h -- sborochnoe slovo analogovogo vyhoda *)
    GVL_Tests_CPM.Cpm_Tests[5].Enabled := TRUE;
    GVL_Tests_CPM.Cpm_Tests[5].Kind := 3;      (* 3 = proverit HW_Out_AO0 *)
    GVL_Tests_CPM.Cpm_Tests[5].Mask_Word := TRUE;
    GVL_Tests_CPM.Cpm_Tests[5].Exp_Word := 16#1234;

    (* IO06: status konsoli: est simvol -> 0FFh *)
    GVL_Tests_CPM.Cpm_Tests[6].Enabled := TRUE;
    GVL_Tests_CPM.Cpm_Tests[6].Kind := 1;
    GVL_Tests_CPM.Cpm_Tests[6].Mask_Byte := TRUE;
    GVL_Tests_CPM.Cpm_Tests[6].Exp_Byte := 16#FF;

    (* IO07: IN 21h -- priznak zagruzki CP/M *)
    GVL_Tests_CPM.Cpm_Tests[7].Enabled := TRUE;
    GVL_Tests_CPM.Cpm_Tests[7].Kind := 1;
    GVL_Tests_CPM.Cpm_Tests[7].Mask_Byte := TRUE;
    GVL_Tests_CPM.Cpm_Tests[7].Exp_Byte := 16#01;

    (* ---------------- HW: apparatnyy sloy ---------------- *)
    (* HW01: upakovka diskretnyh vhodov v bajt *)
    GVL_Tests_CPM.Cpm_Tests[11].Enabled := TRUE;
    GVL_Tests_CPM.Cpm_Tests[11].Kind := 4;     (* 4 = proverit HW_In_DI *)
    GVL_Tests_CPM.Cpm_Tests[11].Mask_Byte := TRUE;
    GVL_Tests_CPM.Cpm_Tests[11].Exp_Byte := 16#A5;

    (* HW02: analogovyy vhod 0 v bufer *)
    GVL_Tests_CPM.Cpm_Tests[12].Enabled := TRUE;
    GVL_Tests_CPM.Cpm_Tests[12].Kind := 5;     (* 5 = proverit HW_In_AI0 *)
    GVL_Tests_CPM.Cpm_Tests[12].Mask_Word := TRUE;
    GVL_Tests_CPM.Cpm_Tests[12].Exp_Word := 16#1234;

    (* HW03: raspredelenie vyhodov po kanalam %QX *)
    GVL_Tests_CPM.Cpm_Tests[13].Enabled := TRUE;
    GVL_Tests_CPM.Cpm_Tests[13].Kind := 6;     (* 6 = proverit GVL_HW_IO.DO_2 *)
    GVL_Tests_CPM.Cpm_Tests[13].Mask_Byte := TRUE;
    GVL_Tests_CPM.Cpm_Tests[13].Exp_Byte := 1;

    (* ---------------- BD: programmnye proverki ---------------- *)
    (* BD01: vektora BDOS po adresu 0005h: JP 0F000h *)
    GVL_Tests_CPM.Cpm_Tests[21].Enabled := TRUE;
    GVL_Tests_CPM.Cpm_Tests[21].Kind := 7;     (* 7 = proverit Z80_Mem[5] = C3 *)
    GVL_Tests_CPM.Cpm_Tests[21].Mask_Byte := TRUE;
    GVL_Tests_CPM.Cpm_Tests[21].Exp_Byte := 16#C3;

    (* BD02: adres v vektore BDOS *)
    GVL_Tests_CPM.Cpm_Tests[22].Enabled := TRUE;
    GVL_Tests_CPM.Cpm_Tests[22].Kind := 8;     (* 8 = proverit slovo po 0006h *)
    GVL_Tests_CPM.Cpm_Tests[22].Mask_Word := TRUE;
    GVL_Tests_CPM.Cpm_Tests[22].Exp_Word := 16#F000;

    (* BD03: vektora BIOS po adresu 0000h: JP 0FA00h *)
    GVL_Tests_CPM.Cpm_Tests[23].Enabled := TRUE;
    GVL_Tests_CPM.Cpm_Tests[23].Kind := 9;     (* 9 = proverit Z80_Mem[0] = C3 *)
    GVL_Tests_CPM.Cpm_Tests[23].Mask_Byte := TRUE;
    GVL_Tests_CPM.Cpm_Tests[23].Exp_Byte := 16#C3;

    (* BD04: adres v vektore BIOS *)
    GVL_Tests_CPM.Cpm_Tests[24].Enabled := TRUE;
    GVL_Tests_CPM.Cpm_Tests[24].Kind := 10;    (* 10 = proverit slovo po 0001h *)
    GVL_Tests_CPM.Cpm_Tests[24].Mask_Word := TRUE;
    GVL_Tests_CPM.Cpm_Tests[24].Exp_Word := 16#FA00;

    (* BD05: pervaya komanda HELLO.COM v TPA: LD C,9 *)
    GVL_Tests_CPM.Cpm_Tests[25].Enabled := TRUE;
    GVL_Tests_CPM.Cpm_Tests[25].Kind := 11;    (* 11 = Z80_Mem[0100h] *)
    GVL_Tests_CPM.Cpm_Tests[25].Mask_Byte := TRUE;
    GVL_Tests_CPM.Cpm_Tests[25].Exp_Byte := 16#0E;

    (* BD06: nomer funktsii v programme *)
    GVL_Tests_CPM.Cpm_Tests[26].Enabled := TRUE;
    GVL_Tests_CPM.Cpm_Tests[26].Kind := 12;    (* 12 = Z80_Mem[0101h] = 9 *)
    GVL_Tests_CPM.Cpm_Tests[26].Mask_Byte := TRUE;
    GVL_Tests_CPM.Cpm_Tests[26].Exp_Byte := 9;

    (* BD07: vyzov BDOS v programme: CALL 0F000h *)
    GVL_Tests_CPM.Cpm_Tests[27].Enabled := TRUE;
    GVL_Tests_CPM.Cpm_Tests[27].Kind := 13;    (* 13 = Z80_Mem[0105h] = CD *)
    GVL_Tests_CPM.Cpm_Tests[27].Mask_Byte := TRUE;
    GVL_Tests_CPM.Cpm_Tests[27].Exp_Byte := 16#CD;

    (* BD08: pervyy simvol stroki dlya vyvoda *)
    GVL_Tests_CPM.Cpm_Tests[28].Enabled := TRUE;
    GVL_Tests_CPM.Cpm_Tests[28].Kind := 14;    (* 14 = Z80_Mem[0110h] = 'H' *)
    GVL_Tests_CPM.Cpm_Tests[28].Mask_Byte := TRUE;
    GVL_Tests_CPM.Cpm_Tests[28].Exp_Byte := 72;   (* 16#48;   (* 'H' *) *)

    (* ---------------- DS: RAM-disk ---------------- *)
    (* DS01: imya fajla v kataloge: pervyy simvol 'H' *)
    GVL_Tests_CPM.Cpm_Tests[31].Enabled := TRUE;
    GVL_Tests_CPM.Cpm_Tests[31].Kind := 15;    (* 15 = Disk_Mem[1] *)
    GVL_Tests_CPM.Cpm_Tests[31].Mask_Byte := TRUE;
    GVL_Tests_CPM.Cpm_Tests[31].Exp_Byte := 72;   (* 16#48;   (* 'H' *) *)

    (* DS02: rasshirenie COM v kataloge *)
    GVL_Tests_CPM.Cpm_Tests[32].Enabled := TRUE;
    GVL_Tests_CPM.Cpm_Tests[32].Kind := 16;    (* 16 = Disk_Mem[9] *)
    GVL_Tests_CPM.Cpm_Tests[32].Mask_Byte := TRUE;
    GVL_Tests_CPM.Cpm_Tests[32].Exp_Byte := 67;   (* 16#43;   (* 'C' *) *)

    (* DS03: schetchik zapisey RC = 1 *)
    GVL_Tests_CPM.Cpm_Tests[33].Enabled := TRUE;
    GVL_Tests_CPM.Cpm_Tests[33].Kind := 17;    (* 17 = Disk_Mem[16] *)
    GVL_Tests_CPM.Cpm_Tests[33].Mask_Byte := TRUE;
    GVL_Tests_CPM.Cpm_Tests[33].Exp_Byte := 1;

    (* DS04: nomer zanyatogo bloka = 1 *)
    GVL_Tests_CPM.Cpm_Tests[34].Enabled := TRUE;
    GVL_Tests_CPM.Cpm_Tests[34].Kind := 18;    (* 18 = Disk_Mem[17] *)
    GVL_Tests_CPM.Cpm_Tests[34].Mask_Byte := TRUE;
    GVL_Tests_CPM.Cpm_Tests[34].Exp_Byte := 1;

    (* DS05: kpiya programmy v bloke 1 RAM-diska *)
    GVL_Tests_CPM.Cpm_Tests[35].Enabled := TRUE;
    GVL_Tests_CPM.Cpm_Tests[35].Kind := 19;    (* 19 = Disk_Mem[800h] *)
    GVL_Tests_CPM.Cpm_Tests[35].Mask_Byte := TRUE;
    GVL_Tests_CPM.Cpm_Tests[35].Exp_Byte := 16#0E;

    (* IO08: IN 06h -- mladshij bajt vtorogo analogovogo vhoda (5678h -> 78h) *)
    GVL_Tests_CPM.Cpm_Tests[8].Enabled := TRUE;
    GVL_Tests_CPM.Cpm_Tests[8].Kind := 1;
    GVL_Tests_CPM.Cpm_Tests[8].Mask_Byte := TRUE;
    GVL_Tests_CPM.Cpm_Tests[8].Exp_Byte := 16#78;

    (* IO09: IN 07h -- starshij bajt vtorogo analogovogo vhoda (56h) *)
    GVL_Tests_CPM.Cpm_Tests[9].Enabled := TRUE;
    GVL_Tests_CPM.Cpm_Tests[9].Kind := 1;
    GVL_Tests_CPM.Cpm_Tests[9].Mask_Byte := TRUE;
    GVL_Tests_CPM.Cpm_Tests[9].Exp_Byte := 16#56;

    (* IO10: OUT 08h/09h -- vtoroy analogovyy vyhod. Znachenie ne zadavalos,
       poetomu na vyhode 0 -- proveryaem, chto kanal ne meshaet pervomu. *)
    GVL_Tests_CPM.Cpm_Tests[10].Enabled := TRUE;
    GVL_Tests_CPM.Cpm_Tests[10].Kind := 3;
    GVL_Tests_CPM.Cpm_Tests[10].Mask_Word := TRUE;
    GVL_Tests_CPM.Cpm_Tests[10].Exp_Word := 16#1234;   (* kanal 0 ne izmenilsya *)

    (* HW04: vtoroy analogovyy vhod v bufer *)
    GVL_Tests_CPM.Cpm_Tests[14].Enabled := TRUE;
    GVL_Tests_CPM.Cpm_Tests[14].Kind := 5;
    GVL_Tests_CPM.Cpm_Tests[14].Mask_Word := TRUE;
    GVL_Tests_CPM.Cpm_Tests[14].Exp_Word := 16#1234;

    (* BD09: adres stroki v programme HELLO.COM: 0110h *)
    GVL_Tests_CPM.Cpm_Tests[29].Enabled := TRUE;
    GVL_Tests_CPM.Cpm_Tests[29].Kind := 20;    (* 20 = Z80_Mem[0103h] = 10h *)
    GVL_Tests_CPM.Cpm_Tests[29].Mask_Byte := TRUE;
    GVL_Tests_CPM.Cpm_Tests[29].Exp_Byte := 16#10;

    (* BD10: pervyy simvol adresa -- 01h *)
    GVL_Tests_CPM.Cpm_Tests[30].Enabled := TRUE;
    GVL_Tests_CPM.Cpm_Tests[30].Kind := 21;    (* 21 = Z80_Mem[0104h] = 01h *)
    GVL_Tests_CPM.Cpm_Tests[30].Mask_Byte := TRUE;
    GVL_Tests_CPM.Cpm_Tests[30].Exp_Byte := 16#01;

    (* DS06: vtoroy simvol imeni fajla v kataloge: 'E' *)
    GVL_Tests_CPM.Cpm_Tests[36].Enabled := TRUE;
    GVL_Tests_CPM.Cpm_Tests[36].Kind := 22;    (* 22 = Disk_Mem[2] *)
    GVL_Tests_CPM.Cpm_Tests[36].Mask_Byte := TRUE;
    GVL_Tests_CPM.Cpm_Tests[36].Exp_Byte := 69;   (* 16#45;   (* 'E' *) *)

    GVL_Tests_CPM.Cpm_Test_Count := 0;
    FOR i := 1 TO 36 DO
        IF GVL_Tests_CPM.Cpm_Tests[i].Enabled THEN
            GVL_Tests_CPM.Cpm_Test_Count := GVL_Tests_CPM.Cpm_Test_Count + 1;
        END_IF
    END_FOR
END_IF

(* ============================== PROGON ============================== *)
IF GVL_Tests_CPM.Cpm_Test_Run THEN

    (* shag 0: podgotovka -- nastrojka vhodov PLK i konsoli *)
    IF nStage = 0 THEN
        (* podaem na vhody PLK testovyy obraz: 1010 0101 = A5h *)
        GVL_HW_IO.DI_0 := TRUE;
        GVL_HW_IO.DI_1 := FALSE;
        GVL_HW_IO.DI_2 := TRUE;
        GVL_HW_IO.DI_3 := FALSE;
        GVL_HW_IO.DI_4 := FALSE;
        GVL_HW_IO.DI_5 := TRUE;
        GVL_HW_IO.DI_6 := FALSE;
        GVL_HW_IO.DI_7 := TRUE;
        (* analogovyy vhod: 1234h *)
        GVL_HW_IO.AI_0 := 16#1234;
        GVL_HW_IO.AI_1 := 16#5678;
        (* konsol: est simvol 'A' *)
        GVL_CPM.Console_In := 65;
        GVL_CPM.Console_InEn := TRUE;

        (* na vremya proverok emulyator ostanovlen, chtoby snimki ne menyalis *)
        GVL_Control.Emu_Run := FALSE;
        nCyc := 0;
        nStage := 1;

    (* shag 1: sdelat neskolko skanov, chtoby bufery i shiny obnovilis *)
    ELSIF nStage = 1 THEN
        nCyc := nCyc + 1;
        IF nCyc >= 3 THEN
            nStage := 2;
        END_IF

    (* shag 2: projti po vsem testam i sravnit *)
    ELSIF nStage = 2 THEN
        GVL_Tests_CPM.Cpm_Test_Total_Pass := 0;
        GVL_Tests_CPM.Cpm_Test_Fail_Count := 0;

        FOR i := 1 TO 36 DO
            IF GVL_Tests_CPM.Cpm_Tests[i].Enabled THEN
                fbCase.Run := TRUE;
                fbCase.Mask_A := FALSE;
                fbCase.Mask_F := FALSE;
                fbCase.Mask_PC := FALSE;

                (* vybiraem fakticheskoe znachenie po tipu proverki *)
                CASE GVL_Tests_CPM.Cpm_Tests[i].Kind OF
                    1:  fbCase.Expected_A := GVL_Tests_CPM.Cpm_Tests[i].Exp_Byte;
                        fbCase.Actual_A := GVL_IO.Bus_IO_Data;
                        fbCase.Mask_A := TRUE;

                    2:  fbCase.Expected_A := GVL_Tests_CPM.Cpm_Tests[i].Exp_Byte;
                        fbCase.Actual_A := GVL_HW_Buffer.HW_Out_DO;
                        fbCase.Mask_A := TRUE;

                    3:  fbCase.Expected_PC := GVL_Tests_CPM.Cpm_Tests[i].Exp_Word;
                        fbCase.Actual_PC := GVL_HW_Buffer.HW_Out_AO0;
                        fbCase.Mask_PC := TRUE;

                    4:  fbCase.Expected_A := GVL_Tests_CPM.Cpm_Tests[i].Exp_Byte;
                        fbCase.Actual_A := GVL_HW_Buffer.HW_In_DI;
                        fbCase.Mask_A := TRUE;

                    5:  fbCase.Expected_PC := GVL_Tests_CPM.Cpm_Tests[i].Exp_Word;
                        fbCase.Actual_PC := GVL_HW_Buffer.HW_In_AI0;
                        fbCase.Mask_PC := TRUE;

                    6:  fbCase.Expected_A := GVL_Tests_CPM.Cpm_Tests[i].Exp_Byte;
                        (*  Ch E R E Z  SEL, A  N E  BOOL_TO_BYTE: eta konversiya daet USINT,
    a pole Actual_A obyavleno BYTE. Vetki SEL yavno tipizirovany,
    poetomu rezul tat odnoznachno BYTE. Pravilo -- sm. docs/04 . *)
fbCase.Actual_A := SEL(GVL_HW_IO.DO_2, BYTE#0, BYTE#1);
                        fbCase.Mask_A := TRUE;

                    7:  fbCase.Expected_A := GVL_Tests_CPM.Cpm_Tests[i].Exp_Byte;
                        fbCase.Actual_A := Z80_Mem[5];
                        fbCase.Mask_A := TRUE;

                    8:  fbCase.Expected_PC := GVL_Tests_CPM.Cpm_Tests[i].Exp_Word;
                        (*  S N A Ch A L A  R A S Sh I R E N I E,  P O T O M  S D V I G.
                            Bylo: SHL(WORD_TO_DWORD(Z80_Mem[7]), 8) OR Z80_Mem[6]).
                            Eto UDINT, a wTmp -- WORD, i kompilyator daval
                                C32: Nevozmozhno konvertirovat tip 'UDINT'
                                     v tip 'WORD'.
                            Poryadok obratnyj: BYTE_TO_WORD, zatem sdvig na 8 --
                            rezul tat uzhe WORD. *)
                        wTmp := SHL(BYTE_TO_WORD(Z80_Mem[7]), 8) OR
                                BYTE_TO_WORD(Z80_Mem[6]);
                        fbCase.Actual_PC := (wTmp);
                        fbCase.Mask_PC := TRUE;

                    9:  fbCase.Expected_A := GVL_Tests_CPM.Cpm_Tests[i].Exp_Byte;
                        fbCase.Actual_A := Z80_Mem[0];
                        fbCase.Mask_A := TRUE;

                    10: fbCase.Expected_PC := GVL_Tests_CPM.Cpm_Tests[i].Exp_Word;
                        (* Snachala rasshirenie do WORD, potom sdvig na 8:
                           inache poluchaetsya UDINT i C32 pri prisvoenii
                           v wTmp tipa WORD. Sm. vetku 8 vyshe. *)
                        wTmp := SHL(BYTE_TO_WORD(Z80_Mem[2]), 8) OR
                                BYTE_TO_WORD(Z80_Mem[1]);
                        fbCase.Actual_PC := (wTmp);
                        fbCase.Mask_PC := TRUE;

                    11: fbCase.Expected_A := GVL_Tests_CPM.Cpm_Tests[i].Exp_Byte;
                        fbCase.Actual_A := Z80_Mem[16#0100];
                        fbCase.Mask_A := TRUE;

                    12: fbCase.Expected_A := GVL_Tests_CPM.Cpm_Tests[i].Exp_Byte;
                        fbCase.Actual_A := Z80_Mem[16#0101];
                        fbCase.Mask_A := TRUE;

                    13: fbCase.Expected_A := GVL_Tests_CPM.Cpm_Tests[i].Exp_Byte;
                        fbCase.Actual_A := Z80_Mem[16#0105];
                        fbCase.Mask_A := TRUE;

                    14: fbCase.Expected_A := GVL_Tests_CPM.Cpm_Tests[i].Exp_Byte;
                        fbCase.Actual_A := Z80_Mem[16#0110];
                        fbCase.Mask_A := TRUE;

                    15: fbCase.Expected_A := GVL_Tests_CPM.Cpm_Tests[i].Exp_Byte;
                        fbCase.Actual_A := Disk_Mem[1];
                        fbCase.Mask_A := TRUE;

                    16: fbCase.Expected_A := GVL_Tests_CPM.Cpm_Tests[i].Exp_Byte;
                        fbCase.Actual_A := Disk_Mem[9];
                        fbCase.Mask_A := TRUE;

                    17: fbCase.Expected_A := GVL_Tests_CPM.Cpm_Tests[i].Exp_Byte;
                        fbCase.Actual_A := Disk_Mem[16];
                        fbCase.Mask_A := TRUE;

                    18: fbCase.Expected_A := GVL_Tests_CPM.Cpm_Tests[i].Exp_Byte;
                        fbCase.Actual_A := Disk_Mem[17];
                        fbCase.Mask_A := TRUE;

                    19: fbCase.Expected_A := GVL_Tests_CPM.Cpm_Tests[i].Exp_Byte;
                        fbCase.Actual_A := Disk_Mem[16#800];
                        fbCase.Mask_A := TRUE;

                    20: fbCase.Expected_A := GVL_Tests_CPM.Cpm_Tests[i].Exp_Byte;
                        fbCase.Actual_A := Z80_Mem[16#0103];
                        fbCase.Mask_A := TRUE;

                    21: fbCase.Expected_A := GVL_Tests_CPM.Cpm_Tests[i].Exp_Byte;
                        fbCase.Actual_A := Z80_Mem[16#0104];
                        fbCase.Mask_A := TRUE;

                    22: fbCase.Expected_A := GVL_Tests_CPM.Cpm_Tests[i].Exp_Byte;
                        fbCase.Actual_A := Disk_Mem[2];
                        fbCase.Mask_A := TRUE;

                ELSE
                    fbCase.Mask_A := FALSE;
                END_CASE

                    (*  V Y Z O V  F B  O B Ya Z A T E L E N.
                        TEST_Z80 -- programma na ST, a v ST funktsionalnyj blok
                        ne vypolnyaetsya sam: nuzhno yavno napisat "fbCase();".
                        Bez etogo stroki vyshe tol ko ZAPOLNILI vhody FB, a ego
                        telo (sravneniya EQ i vyhod Pass) ne schitalos nikogda.
                        Rezul tat izmeryon na progone: pri sovpadayushchih
                        Expected_A = Actual_A i Mask_A = TRUE vyhod Pass ostavalsya
                        FALSE, i PO E T O M U  padali vse 40 testov. *)

                fbCase.Run := TRUE;
                fbCase();

                GVL_Tests_CPM.Cpm_Test_Result[i] := fbCase.Pass;
                GVL_Tests_CPM.Cpm_Test_Result[i] := fbCase.Pass;
                IF fbCase.Pass THEN
                    GVL_Tests_CPM.Cpm_Test_Total_Pass :=
                        GVL_Tests_CPM.Cpm_Test_Total_Pass + 1;
                ELSE
                    IF GVL_Tests_CPM.Cpm_Test_Fail_Count < 16 THEN
                        GVL_Tests_CPM.Cpm_Test_Failed_List[
                            GVL_Tests_CPM.Cpm_Test_Fail_Count + 1] := i;
                    END_IF
                    GVL_Tests_CPM.Cpm_Test_Fail_Count :=
                        GVL_Tests_CPM.Cpm_Test_Fail_Count + 1;
                END_IF
            END_IF
        END_FOR

        GVL_Tests_CPM.Cpm_Test_Run := FALSE;
        nStage := 3;
    END_IF
END_IF
'''

ST_TEST_Z80_PREP = u'''(* =========================================================================
   TEST_Z80_PREP -- TABLITsA PROVEROK emulyatora (62 testa).

   Z D E S  T O L K O  D A N N Y E: chto podat na vhod, chto
   zhdem na vyhode i chto iz etogo proveryat. Nikakih operatorov
   obrabotki tut net -- oni v TEST_Z80.

   P O Ch E M U  O T D E L N O. Ranshe tablitsa i obrabotchik byli
   odnim POU na 500 s lishnim strok ST. Imenno v etoj masse dolgo
   ne mogli najti nezakrytyj IF, kotoryy daval buket oshibok C9 bez
   nomera stroki i bez imeni POU.

   Zapolnyaetsya ODIN RAZ za progno, priznak -- GVL_InitState.
   TestTableDone. Poryadok zapuska POU v zadache ne vazhen:
   sostoyanie lezhit v GVL, a ne v lokalnyh peremennyh.
   ================================================================ *)
VAR
    i : INT;
END_VAR

(* ============================== PODGOTOVKA ==============================
   Odnorazovoe zapolnenie tablitsy testov. Kazhdaya stroka -- odna proverka:
   Opcode, nachalnye znacheniya, ozhidaemyy rezultat i maski (chto proveryaem). *)
IF NOT GVL_InitState.TestTableDone THEN
    GVL_InitState.TestTableDone := TRUE;

    FOR i := 1 TO 40 DO
        GVL_Tests.Cpu_Tests[i].Id := i;
        GVL_Tests.Cpu_Tests[i].Enabled := FALSE;
        GVL_Tests.Cpu_Tests[i].Stage := 0;
        GVL_Tests.Cpu_Tests[i].Opcode := 0;
        GVL_Tests.Cpu_Tests[i].Init_A := 0;
        GVL_Tests.Cpu_Tests[i].Init_B := 0;
        GVL_Tests.Cpu_Tests[i].Init_F := 0;
        GVL_Tests.Cpu_Tests[i].Init_PC := 0;
        GVL_Tests.Cpu_Tests[i].Init_SP := 0;
        GVL_Tests.Cpu_Tests[i].Init_HL := 0;
        GVL_Tests.Cpu_Tests[i].Exp_A := 0;
        GVL_Tests.Cpu_Tests[i].Exp_F := 0;
        GVL_Tests.Cpu_Tests[i].Exp_PC := 0;
        GVL_Tests.Cpu_Tests[i].Exp_Mem := 0;
        GVL_Tests.Cpu_Tests[i].Exp_Mem_Addr := 0;
        GVL_Tests.Cpu_Tests[i].Exp_Cycles := 1;
        GVL_Tests.Cpu_Tests[i].Mask_A := FALSE;
        GVL_Tests.Cpu_Tests[i].Mask_F := FALSE;
        GVL_Tests.Cpu_Tests[i].Mask_PC := FALSE;
        GVL_Tests.Cpu_Tests[i].Mask_Mem := FALSE;
    END_FOR

    (* ---------------- T01..T06: peresylki LD (flagi NE menyayutsya) --------
       Init_F := FFh -- esli komanda sluchayno isportit flagi, test upadet. *)
    GVL_Tests.Cpu_Tests[1].Enabled := TRUE;   (* T01 LD B,n *)
    GVL_Tests.Cpu_Tests[1].Opcode := 16#06;
    GVL_Tests.Cpu_Tests[1].Init_F := 16#FF;
    GVL_Tests.Cpu_Tests[1].Mask_F := TRUE;
    GVL_Tests.Cpu_Tests[1].Exp_F := 16#FF;

    GVL_Tests.Cpu_Tests[2].Enabled := TRUE;   (* T02 LD A,n *)
    GVL_Tests.Cpu_Tests[2].Opcode := 16#3E;
    GVL_Tests.Cpu_Tests[2].Init_F := 16#FF;
    GVL_Tests.Cpu_Tests[2].Mask_F := TRUE;
    GVL_Tests.Cpu_Tests[2].Exp_F := 16#FF;

    GVL_Tests.Cpu_Tests[3].Enabled := TRUE;   (* T03 LD C,B *)
    GVL_Tests.Cpu_Tests[3].Opcode := 16#48;
    GVL_Tests.Cpu_Tests[3].Init_B := 16#3C;
    GVL_Tests.Cpu_Tests[3].Init_F := 16#FF;
    GVL_Tests.Cpu_Tests[3].Mask_F := TRUE;
    GVL_Tests.Cpu_Tests[3].Exp_F := 16#FF;

    GVL_Tests.Cpu_Tests[4].Enabled := TRUE;   (* T04 LD A,L *)
    GVL_Tests.Cpu_Tests[4].Opcode := 16#7D;
    GVL_Tests.Cpu_Tests[4].Init_HL := 16#1100;
    GVL_Tests.Cpu_Tests[4].Mask_A := TRUE;
    GVL_Tests.Cpu_Tests[4].Exp_A := 16#00;

    GVL_Tests.Cpu_Tests[5].Enabled := TRUE;   (* T05 LD (HL),A -- zapis v pamyat *)
    GVL_Tests.Cpu_Tests[5].Opcode := 16#77;
    GVL_Tests.Cpu_Tests[5].Init_A := 16#AA;
    GVL_Tests.Cpu_Tests[5].Init_HL := 16#2000;
    GVL_Tests.Cpu_Tests[5].Mask_Mem := TRUE;
    GVL_Tests.Cpu_Tests[5].Exp_Mem_Addr := 16#2000;
    GVL_Tests.Cpu_Tests[5].Exp_Mem := 16#AA;

    GVL_Tests.Cpu_Tests[6].Enabled := TRUE;   (* T06 LD A,(HL) -- chtenie iz pamyati *)
    GVL_Tests.Cpu_Tests[6].Opcode := 16#7E;
    GVL_Tests.Cpu_Tests[6].Init_HL := 16#2000;
    GVL_Tests.Cpu_Tests[6].Mask_A := TRUE;
    GVL_Tests.Cpu_Tests[6].Exp_A := 16#55;

    (* ---------------- T07..T12: ADD i SUB --------------------------------- *)
    GVL_Tests.Cpu_Tests[7].Enabled := TRUE;   (* T07 ADD 25h+10h=35h *)
    GVL_Tests.Cpu_Tests[7].Opcode := 16#80;
    GVL_Tests.Cpu_Tests[7].Init_A := 16#25;
    GVL_Tests.Cpu_Tests[7].Init_B := 16#10;
    GVL_Tests.Cpu_Tests[7].Mask_A := TRUE;   GVL_Tests.Cpu_Tests[7].Exp_A := 16#35;
    GVL_Tests.Cpu_Tests[7].Mask_F := TRUE;   GVL_Tests.Cpu_Tests[7].Exp_F := 16#00;

    GVL_Tests.Cpu_Tests[8].Enabled := TRUE;   (* T08 ADD perepolnenie -> 94h *)
    GVL_Tests.Cpu_Tests[8].Opcode := 16#80;
    GVL_Tests.Cpu_Tests[8].Init_A := 16#7F;
    GVL_Tests.Cpu_Tests[8].Init_B := 16#01;
    GVL_Tests.Cpu_Tests[8].Mask_A := TRUE;   GVL_Tests.Cpu_Tests[8].Exp_A := 16#80;
    GVL_Tests.Cpu_Tests[8].Mask_F := TRUE;   GVL_Tests.Cpu_Tests[8].Exp_F := 16#94;

    GVL_Tests.Cpu_Tests[9].Enabled := TRUE;   (* T09 ADD perenos -> 50h *)
    GVL_Tests.Cpu_Tests[9].Opcode := 16#80;
    GVL_Tests.Cpu_Tests[9].Init_A := 16#FF;
    GVL_Tests.Cpu_Tests[9].Init_B := 16#01;
    GVL_Tests.Cpu_Tests[9].Mask_A := TRUE;   GVL_Tests.Cpu_Tests[9].Exp_A := 16#00;
    GVL_Tests.Cpu_Tests[9].Mask_F := TRUE;   GVL_Tests.Cpu_Tests[9].Exp_F := 16#50;

    GVL_Tests.Cpu_Tests[10].Enabled := TRUE;  (* T10 SUB 50h-30h=20h *)
    GVL_Tests.Cpu_Tests[10].Opcode := 16#90;
    GVL_Tests.Cpu_Tests[10].Init_A := 16#50;
    GVL_Tests.Cpu_Tests[10].Init_B := 16#30;
    GVL_Tests.Cpu_Tests[10].Mask_A := TRUE;  GVL_Tests.Cpu_Tests[10].Exp_A := 16#20;
    GVL_Tests.Cpu_Tests[10].Mask_F := TRUE;  GVL_Tests.Cpu_Tests[10].Exp_F := 16#02;

    GVL_Tests.Cpu_Tests[11].Enabled := TRUE;  (* T11 SUB zaym -> 83h *)
    GVL_Tests.Cpu_Tests[11].Opcode := 16#90;
    GVL_Tests.Cpu_Tests[11].Init_A := 16#10;
    GVL_Tests.Cpu_Tests[11].Init_B := 16#20;
    GVL_Tests.Cpu_Tests[11].Mask_A := TRUE;  GVL_Tests.Cpu_Tests[11].Exp_A := 16#F0;
    GVL_Tests.Cpu_Tests[11].Mask_F := TRUE;  GVL_Tests.Cpu_Tests[11].Exp_F := 16#83;

    GVL_Tests.Cpu_Tests[12].Enabled := TRUE;  (* T12 SUB perepolnenie -> 47h *)
    GVL_Tests.Cpu_Tests[12].Opcode := 16#90;
    GVL_Tests.Cpu_Tests[12].Init_A := 16#80;
    GVL_Tests.Cpu_Tests[12].Init_B := 16#01;
    GVL_Tests.Cpu_Tests[12].Mask_A := TRUE;  GVL_Tests.Cpu_Tests[12].Exp_A := 16#7F;
    GVL_Tests.Cpu_Tests[12].Mask_F := TRUE;  GVL_Tests.Cpu_Tests[12].Exp_F := 16#47;

    (* ---------------- T13..T16: INC i DEC (C NE menyaetsya!) ------------- *)
    GVL_Tests.Cpu_Tests[13].Enabled := TRUE;  (* T13 INC A: 0Fh->10h, H=1, C ostalsya *)
    GVL_Tests.Cpu_Tests[13].Opcode := 16#3C;
    GVL_Tests.Cpu_Tests[13].Init_A := 16#0F;
    GVL_Tests.Cpu_Tests[13].Init_F := 16#01;
    GVL_Tests.Cpu_Tests[13].Mask_A := TRUE;  GVL_Tests.Cpu_Tests[13].Exp_A := 16#10;

    GVL_Tests.Cpu_Tests[14].Enabled := TRUE;  (* T14 INC A perepolnenie: 7Fh->80h *)
    GVL_Tests.Cpu_Tests[14].Opcode := 16#3C;
    GVL_Tests.Cpu_Tests[14].Init_A := 16#7F;
    GVL_Tests.Cpu_Tests[14].Mask_A := TRUE;  GVL_Tests.Cpu_Tests[14].Exp_A := 16#80;

    GVL_Tests.Cpu_Tests[15].Enabled := TRUE;  (* T15 DEC B: 01h->00h, Z=1 *)
    GVL_Tests.Cpu_Tests[15].Opcode := 16#05;
    GVL_Tests.Cpu_Tests[15].Init_B := 16#01;
    GVL_Tests.Cpu_Tests[15].Init_F := 16#01;
    GVL_Tests.Cpu_Tests[15].Mask_F := TRUE;  GVL_Tests.Cpu_Tests[15].Exp_F := 16#42;

    GVL_Tests.Cpu_Tests[16].Enabled := TRUE;  (* T16 DEC B zaym: 00h->FFh *)
    GVL_Tests.Cpu_Tests[16].Opcode := 16#05;
    GVL_Tests.Cpu_Tests[16].Init_B := 16#00;
    GVL_Tests.Cpu_Tests[16].Mask_F := TRUE;  GVL_Tests.Cpu_Tests[16].Exp_F := 16#BA;

    (* ---------------- T17..T21: perehody JP ------------------------------- *)
    GVL_Tests.Cpu_Tests[17].Enabled := TRUE;  (* T17 JP 2000h *)
    GVL_Tests.Cpu_Tests[17].Opcode := 16#C3;
    GVL_Tests.Cpu_Tests[17].Mask_PC := TRUE;
    GVL_Tests.Cpu_Tests[17].Exp_PC := 16#2000;

    GVL_Tests.Cpu_Tests[18].Enabled := TRUE;  (* T18 JP Z pri Z=1 -- perehod *)
    GVL_Tests.Cpu_Tests[18].Opcode := 16#CA;
    GVL_Tests.Cpu_Tests[18].Init_F := 16#40;
    GVL_Tests.Cpu_Tests[18].Test_Has_Cond := TRUE;
    GVL_Tests.Cpu_Tests[18].Mask_PC := TRUE;
    GVL_Tests.Cpu_Tests[18].Exp_PC := 16#2000;

    GVL_Tests.Cpu_Tests[19].Enabled := TRUE;  (* T19 JP Z pri Z=0 -- net perehoda *)
    GVL_Tests.Cpu_Tests[19].Opcode := 16#CA;
    GVL_Tests.Cpu_Tests[19].Init_F := 16#00;
    GVL_Tests.Cpu_Tests[19].Mask_PC := TRUE;
    GVL_Tests.Cpu_Tests[19].Exp_PC := 16#0003;

    GVL_Tests.Cpu_Tests[20].Enabled := TRUE;  (* T20 JP NZ pri Z=0 -- perehod *)
    GVL_Tests.Cpu_Tests[20].Opcode := 16#C2;
    GVL_Tests.Cpu_Tests[20].Init_F := 16#00;
    GVL_Tests.Cpu_Tests[20].Mask_PC := TRUE;
    GVL_Tests.Cpu_Tests[20].Exp_PC := 16#2000;

    GVL_Tests.Cpu_Tests[21].Enabled := TRUE;  (* T21 JP NZ pri Z=1 -- net perehoda *)
    GVL_Tests.Cpu_Tests[21].Opcode := 16#C2;
    GVL_Tests.Cpu_Tests[21].Init_F := 16#40;
    GVL_Tests.Cpu_Tests[21].Test_Has_Cond := TRUE;
    GVL_Tests.Cpu_Tests[21].Mask_PC := TRUE;
    GVL_Tests.Cpu_Tests[21].Exp_PC := 16#0003;

    (* ---------------- T22..T24: CALL, RET, HALT --------------------------- *)
    GVL_Tests.Cpu_Tests[22].Enabled := TRUE;  (* T22 CALL 2000h, SP nachal 1 *)
    GVL_Tests.Cpu_Tests[22].Opcode := 16#CD;
    GVL_Tests.Cpu_Tests[22].Init_SP := 16#0001;
    GVL_Tests.Cpu_Tests[22].Mask_PC := TRUE;
    GVL_Tests.Cpu_Tests[22].Exp_PC := 16#2000;
    GVL_Tests.Cpu_Tests[22].Mask_Flag := TRUE;   (* priznak: nachalo steka *)

    GVL_Tests.Cpu_Tests[23].Enabled := TRUE;  (* T23 HALT *)
    GVL_Tests.Cpu_Tests[23].Opcode := 16#76;
    GVL_Tests.Cpu_Tests[23].Mask_PC := TRUE;
    GVL_Tests.Cpu_Tests[23].Exp_PC := 16#0001;
    GVL_Tests.Cpu_Tests[23].Mask_Flag := TRUE;

    GVL_Tests.Cpu_Tests[24].Enabled := TRUE;  (* T24 HALT -- ostanov *)
    GVL_Tests.Cpu_Tests[24].Opcode := 16#76;
    GVL_Tests.Cpu_Tests[24].Mask_PC := TRUE;
    GVL_Tests.Cpu_Tests[24].Exp_PC := 16#0001;
    GVL_Tests.Cpu_Tests[24].Mask_Flag := TRUE;



    (* ---------------- T25..T26: DJNZ -------------------------------------- *)
    GVL_Tests.Cpu_Tests[25].Enabled := TRUE;  (* T25 DJNZ s vetvleniem: B=2 -> 1 *)
    GVL_Tests.Cpu_Tests[25].Opcode := 16#10;
    GVL_Tests.Cpu_Tests[25].Init_B := 16#02;
    GVL_Tests.Cpu_Tests[25].Opcode_Lo := 16#FD;   (* smeshchenie -3 *)
    GVL_Tests.Cpu_Tests[25].Mask_Flag := TRUE;    (* B nachal 2, stal 1 *)

    GVL_Tests.Cpu_Tests[26].Enabled := TRUE;  (* T26 DJNZ bez vetvleniya: B=1 -> 0 *)
    GVL_Tests.Cpu_Tests[26].Opcode := 16#10;
    GVL_Tests.Cpu_Tests[26].Init_B := 16#01;
    GVL_Tests.Cpu_Tests[26].Opcode_Lo := 16#FD;
    GVL_Tests.Cpu_Tests[26].Mask_Flag := TRUE;

    (* ---------------- T27..T30: logika i CP -------------------------------- *)
    GVL_Tests.Cpu_Tests[27].Enabled := TRUE;  (* T27 AND -> 00h, Z=1 PV=1 *)
    GVL_Tests.Cpu_Tests[27].Opcode := 16#A0;
    GVL_Tests.Cpu_Tests[27].Init_A := 16#0F;
    GVL_Tests.Cpu_Tests[27].Init_B := 16#F0;
    GVL_Tests.Cpu_Tests[27].Mask_A := TRUE;  GVL_Tests.Cpu_Tests[27].Exp_A := 16#00;
    GVL_Tests.Cpu_Tests[27].Mask_F := TRUE;  GVL_Tests.Cpu_Tests[27].Exp_F := 16#44;

    GVL_Tests.Cpu_Tests[28].Enabled := TRUE;  (* T28 OR -> FFh, S=1 *)
    GVL_Tests.Cpu_Tests[28].Opcode := 16#B0;
    GVL_Tests.Cpu_Tests[28].Init_A := 16#0F;
    GVL_Tests.Cpu_Tests[28].Init_B := 16#F0;
    GVL_Tests.Cpu_Tests[28].Mask_A := TRUE;  GVL_Tests.Cpu_Tests[28].Exp_A := 16#FF;
    GVL_Tests.Cpu_Tests[28].Mask_F := TRUE;  GVL_Tests.Cpu_Tests[28].Exp_F := 16#80;

    GVL_Tests.Cpu_Tests[29].Enabled := TRUE;  (* T29 XOR -> 00h, Z=1 PV=1 *)
    GVL_Tests.Cpu_Tests[29].Opcode := 16#A8;
    GVL_Tests.Cpu_Tests[29].Init_A := 16#FF;
    GVL_Tests.Cpu_Tests[29].Init_B := 16#FF;
    GVL_Tests.Cpu_Tests[29].Mask_A := TRUE;  GVL_Tests.Cpu_Tests[29].Exp_A := 16#00;
    GVL_Tests.Cpu_Tests[29].Mask_F := TRUE;  GVL_Tests.Cpu_Tests[29].Exp_F := 16#44;

    GVL_Tests.Cpu_Tests[30].Enabled := TRUE;  (* T30 CP: A NE menyaetsya, Z=1 N=1 C=1 *)
    GVL_Tests.Cpu_Tests[30].Opcode := 16#B8;
    GVL_Tests.Cpu_Tests[30].Init_A := 16#50;
    GVL_Tests.Cpu_Tests[30].Init_B := 16#50;
    GVL_Tests.Cpu_Tests[30].Mask_A := TRUE;  GVL_Tests.Cpu_Tests[30].Exp_A := 16#50;
    GVL_Tests.Cpu_Tests[30].Mask_F := TRUE;  GVL_Tests.Cpu_Tests[30].Exp_F := 16#46;

    (* ---------------- T31..T46: otdelnye flagi (F_...) ------------------- *)
    GVL_Tests.Cpu_Tests[31].Enabled := TRUE;  (* F_S1: S=1 *)
    GVL_Tests.Cpu_Tests[31].Opcode := 16#80;
    GVL_Tests.Cpu_Tests[31].Init_A := 16#00;
    GVL_Tests.Cpu_Tests[31].Init_B := 16#80;
    GVL_Tests.Cpu_Tests[31].Mask_A := TRUE;  GVL_Tests.Cpu_Tests[31].Exp_A := 16#80;
    GVL_Tests.Cpu_Tests[31].Mask_F := TRUE;  GVL_Tests.Cpu_Tests[31].Exp_F := 16#80;

    GVL_Tests.Cpu_Tests[32].Enabled := TRUE;  (* F_S2: S=0 *)
    GVL_Tests.Cpu_Tests[32].Opcode := 16#80;
    GVL_Tests.Cpu_Tests[32].Init_A := 16#00;
    GVL_Tests.Cpu_Tests[32].Init_B := 16#7F;
    GVL_Tests.Cpu_Tests[32].Mask_A := TRUE;  GVL_Tests.Cpu_Tests[32].Exp_A := 16#7F;
    GVL_Tests.Cpu_Tests[32].Mask_F := TRUE;  GVL_Tests.Cpu_Tests[32].Exp_F := 16#00;

    GVL_Tests.Cpu_Tests[33].Enabled := TRUE;  (* F_Z1: Z=1 *)
    GVL_Tests.Cpu_Tests[33].Opcode := 16#80;
    GVL_Tests.Cpu_Tests[33].Init_A := 16#FF;
    GVL_Tests.Cpu_Tests[33].Init_B := 16#01;
    GVL_Tests.Cpu_Tests[33].Mask_A := TRUE;  GVL_Tests.Cpu_Tests[33].Exp_A := 16#00;
    GVL_Tests.Cpu_Tests[33].Mask_F := TRUE;  GVL_Tests.Cpu_Tests[33].Exp_F := 16#50;

    GVL_Tests.Cpu_Tests[34].Enabled := TRUE;  (* F_Z2: Z=0 *)
    GVL_Tests.Cpu_Tests[34].Opcode := 16#80;
    GVL_Tests.Cpu_Tests[34].Init_A := 16#00;
    GVL_Tests.Cpu_Tests[34].Init_B := 16#01;
    GVL_Tests.Cpu_Tests[34].Mask_A := TRUE;  GVL_Tests.Cpu_Tests[34].Exp_A := 16#01;
    GVL_Tests.Cpu_Tests[34].Mask_F := TRUE;  GVL_Tests.Cpu_Tests[34].Exp_F := 16#00;

    GVL_Tests.Cpu_Tests[35].Enabled := TRUE;  (* F_H1: H=1 pri perenose iz bita 3 *)
    GVL_Tests.Cpu_Tests[35].Opcode := 16#80;
    GVL_Tests.Cpu_Tests[35].Init_A := 16#0F;
    GVL_Tests.Cpu_Tests[35].Init_B := 16#01;
    GVL_Tests.Cpu_Tests[35].Mask_A := TRUE;  GVL_Tests.Cpu_Tests[35].Exp_A := 16#10;
    GVL_Tests.Cpu_Tests[35].Mask_F := TRUE;  GVL_Tests.Cpu_Tests[35].Exp_F := 16#10;

    GVL_Tests.Cpu_Tests[36].Enabled := TRUE;  (* F_H2: H=1 pri ZAYME v bit 4 *)
    GVL_Tests.Cpu_Tests[36].Opcode := 16#90;
    GVL_Tests.Cpu_Tests[36].Init_A := 16#0F;
    GVL_Tests.Cpu_Tests[36].Init_B := 16#01;
    GVL_Tests.Cpu_Tests[36].Mask_A := TRUE;  GVL_Tests.Cpu_Tests[36].Exp_A := 16#0E;
    GVL_Tests.Cpu_Tests[36].Mask_F := TRUE;  GVL_Tests.Cpu_Tests[36].Exp_F := 16#12;

    GVL_Tests.Cpu_Tests[37].Enabled := TRUE;  (* F_H3: logika vsegda H=0 *)
    GVL_Tests.Cpu_Tests[37].Opcode := 16#B0;
    GVL_Tests.Cpu_Tests[37].Init_A := 16#00;
    GVL_Tests.Cpu_Tests[37].Init_B := 16#0F;
    GVL_Tests.Cpu_Tests[37].Mask_A := TRUE;  GVL_Tests.Cpu_Tests[37].Exp_A := 16#0F;
    GVL_Tests.Cpu_Tests[37].Mask_F := TRUE;  GVL_Tests.Cpu_Tests[37].Exp_F := 16#04;

    GVL_Tests.Cpu_Tests[38].Enabled := TRUE;  (* F_PV1: perepolnenie ADD *)
    GVL_Tests.Cpu_Tests[38].Opcode := 16#80;
    GVL_Tests.Cpu_Tests[38].Init_A := 16#7F;
    GVL_Tests.Cpu_Tests[38].Init_B := 16#01;
    GVL_Tests.Cpu_Tests[38].Mask_A := TRUE;  GVL_Tests.Cpu_Tests[38].Exp_A := 16#80;
    GVL_Tests.Cpu_Tests[38].Mask_F := TRUE;  GVL_Tests.Cpu_Tests[38].Exp_F := 16#94;

    GVL_Tests.Cpu_Tests[39].Enabled := TRUE;  (* F_PV2: chetnaya chetnost *)
    GVL_Tests.Cpu_Tests[39].Opcode := 16#B0;
    GVL_Tests.Cpu_Tests[39].Init_A := 16#03;
    GVL_Tests.Cpu_Tests[39].Init_B := 16#00;
    GVL_Tests.Cpu_Tests[39].Mask_A := TRUE;  GVL_Tests.Cpu_Tests[39].Exp_A := 16#03;
    GVL_Tests.Cpu_Tests[39].Mask_F := TRUE;  GVL_Tests.Cpu_Tests[39].Exp_F := 16#04;

    GVL_Tests.Cpu_Tests[40].Enabled := TRUE;  (* F_PV3: nechetnaya chetnost *)
    GVL_Tests.Cpu_Tests[40].Opcode := 16#B0;
    GVL_Tests.Cpu_Tests[40].Init_A := 16#07;
    GVL_Tests.Cpu_Tests[40].Init_B := 16#00;
    GVL_Tests.Cpu_Tests[40].Mask_A := TRUE;  GVL_Tests.Cpu_Tests[40].Exp_A := 16#07;
    GVL_Tests.Cpu_Tests[40].Mask_F := TRUE;  GVL_Tests.Cpu_Tests[40].Exp_F := 16#00;







    (* ---------------- T47..T50: izolyatsiya flagov (F_ISO) --------------- *)


    (* ---------------- T51..T55: programma P01..P05 ------------------------ *)





    (* ---------------- T56..T60: tsikly L01..L05 --------------------------- *)





    (* ---------------- T61..T62: tselostnost I01..I02 --------------------- *)


    (* schitaem skolko vklyucheno -- eto i est ozhidaemyy itog *)
    GVL_Tests.Cpu_Test_Count := 0;
    FOR i := 1 TO 40 DO
        IF GVL_Tests.Cpu_Tests[i].Enabled THEN
            GVL_Tests.Cpu_Test_Count := GVL_Tests.Cpu_Test_Count + 1;
        END_IF
    END_FOR
END_IF
'''

ST_TEST_Z80 = u'''(* =========================================================================
   TEST_Z80 -- progon 62 proverok emulyatora.

   METODIKA. Operatora assert v FBD net, poetomu sravnenie delaet FB_TestCase:
   vnutri nego blok EQ, kotoryy daet BOOL -- i est' PASS/FAIL.

   Kazhdyy test prohodit chetyre shaga (Test_Stage):
     0 -- ostanovit emulyator, zagruzit pamyat i nachalnye registrov;
     1 -- pustit emulyator na Exp_Cycles skanov (odin skan = odna komanda);
     2 -- snyat rezultaty i sravnit cherez FB_TestCase;
     3 -- podschet itogov i perehod k sleduyushchemu testu.

   GRUPPY TESTov:
     T01..T30 -- otdelnye komandy (Stages 0)
     P01..P05 -- programma slozheniya iz pamyati (Stage 1)
     L01..L08 -- tsikly DJNZ i DEC+JP NZ (Stage 2)
     I01..I07 -- tselostnost (Stage 3)

   ITOG: Test_Total_Pass = Test_Count, Test_Fail_Count = 0.
   ========================================================================= *)
VAR
    fbCase       : FB_TestCase;
    (* bFirstScan perenesen v GVL_InitState.TestTableDone:
       ego vystavlyaet POU TEST_Z80_PREP. *)
    nRun         : INT;
    i            : INT;
    j            : INT;
    k            : INT;
    bPrepared    : BOOL;
    (*  S N I M K I  DLYa SRAVNENIYa.
        P O Ch E M U  O N I  Z D E S'. Kazhdyj test sravnivaet chetyre velichiny:
        A, F, PC i bayt pamyati. Snimat ih nado ODIN RAZ v moment sravneniya:
        esli obrashatsya k GVL_PLCVisu napryamuyu v kazhdom prisvoenii, to mezhdu
        dvumya chteniyami emulyator uspeet sdelat shag, i sravnenie stanet
        nedostovernym. Ranshe eti imena byli obyavleny kak snimok_A/snimok_F/snimok_PC/snimok_Mem,
        i imenno iz-za nih kompilyator soobshchal
            C46: Identifikator 'snimok_A' ne zadan
        -- posle razdeleniya TEST_Z80 na dva POU ih zabral sebe TEST_Z80_PREP. *)
    snimok_A     : BYTE;
    snimok_F     : BYTE;
    snimok_PC    : WORD;
    snimok_Mem   : BYTE;
END_VAR

(* ============================== TABLITsA TESTov =====================
   Sami dannye proverok pereneseny v TEST_Z80_PREP: tak chitaemee
   i tak ih mozhno pravit, ne trogaya obrabotchik.
   Zdes ostalsya tolko progon.
   ==================================================================== *)
(* ============================== PROGON ============================== *)
IF GVL_Tests.Cpu_Test_Run THEN

    (* ---- shag 0: podgotovka ---- *)
    IF GVL_Tests.Cpu_Test_Stage = 0 THEN
        GVL_Control.Emu_Run := FALSE;

        i := 1;
        WHILE i <= 75 AND NOT GVL_Tests.Cpu_Tests[i].Enabled DO
            i := i + 1;
        END_WHILE
        GVL_Tests.Cpu_Test_Active := i;

        IF i > 75 THEN
            GVL_Tests.Cpu_Test_Run := FALSE;
        ELSE
            bPrepared := FALSE;
            nRun := 0;
            GVL_Tests.Cpu_Test_Stage := 1;
        END_IF

    (* ---- shag 1: zagruzka pamyati i registrov, zapusk ---- *)
    ELSIF GVL_Tests.Cpu_Test_Stage = 1 THEN
        IF NOT bPrepared THEN
            i := GVL_Tests.Cpu_Test_Active;

            (* --- pamyat --- *)
            FOR k := 0 TO 15 DO
                Z80_Mem[k] := 0;
            END_FOR
            Z80_Mem[16#2000] := 16#55;   (* dlya T06 LD A,(HL) *)
            Z80_Mem[16#2001] := 16#00;
            Z80_Mem[16#2002] := 16#00;

            IF GVL_Tests.Cpu_Tests[i].Stage = 0 THEN
                (* otdelnaya komanda: kod po adresu 0, operandy po 1 i 2 *)
                Z80_Mem[0] := GVL_Tests.Cpu_Tests[i].Opcode;
                Z80_Mem[1] := GVL_Tests.Cpu_Tests[i].Init_A;
                Z80_Mem[2] := GVL_Tests.Cpu_Tests[i].Init_B;
                (* dlya JP/CALL operand -- adres 2000h: mladshij 00h, starshij 20h *)
                Z80_Mem[1] := 16#00;
                Z80_Mem[2] := 16#20;
                IF GVL_Tests.Cpu_Tests[i].Opcode = 16#10 THEN
                    Z80_Mem[1] := GVL_Tests.Cpu_Tests[i].Opcode_Lo;
                END_IF
                Z80_Mem[3] := 16#00;

            ELSIF GVL_Tests.Cpu_Tests[i].Stage = 1 THEN
                (* programma 1: slozhenie dvuh chisel iz pamyati *)
                Z80_Mem[16#0100] := 16#3A;  Z80_Mem[16#0101] := 16#00;
                Z80_Mem[16#0102] := 16#20;
                Z80_Mem[16#0103] := 16#47;
                Z80_Mem[16#0104] := 16#3A;  Z80_Mem[16#0105] := 16#01;
                Z80_Mem[16#0106] := 16#20;
                Z80_Mem[16#0107] := 16#80;
                Z80_Mem[16#0108] := 16#32;  Z80_Mem[16#0109] := 16#02;
                Z80_Mem[16#010A] := 16#20;
                Z80_Mem[16#2000] := 16#25;
                Z80_Mem[16#2001] := 16#10;
                Z80_Mem[16#2002] := 16#00;

            ELSE
                (* programmy tsiklov *)
                IF GVL_Tests.Cpu_Tests[i].Opcode = 0 THEN
                    (* DJNZ: 5 iteracij, summa 5+4+3+2+1 = 19 = 13h *)
                    Z80_Mem[16#0120] := 16#06;  Z80_Mem[16#0121] := 16#05;
                    Z80_Mem[16#0122] := 16#AF;
                    Z80_Mem[16#0123] := 16#80;
                    Z80_Mem[16#0124] := 16#10;  Z80_Mem[16#0125] := 16#FD;
                    Z80_Mem[16#0126] := 16#32;  Z80_Mem[16#0127] := 16#00;
                    Z80_Mem[16#0128] := 16#20;
                    GVL_InitRegs.Init_PC := 16#0120;
                ELSE
                    (* DEC B + JP NZ: 3 iteracii, 3+2+1 = 6 *)
                    Z80_Mem[16#0140] := 16#06;  Z80_Mem[16#0141] := 16#03;
                    Z80_Mem[16#0142] := 16#AF;
                    Z80_Mem[16#0143] := 16#80;
                    Z80_Mem[16#0144] := 16#05;
                    Z80_Mem[16#0145] := 16#C2;  Z80_Mem[16#0146] := 16#43;
                    Z80_Mem[16#0147] := 16#01;
                    GVL_InitRegs.Init_PC := 16#0140;
                END_IF
            END_IF

            (* --- nachalnye znacheniya registrov --- *)
            FOR k := 0 TO 15 DO
                GVL_InitRegs.Init_Vals[k] := 0;
            END_FOR
            GVL_InitRegs.Init_Vals[0] := GVL_Tests.Cpu_Tests[i].Init_A;   (* A *)
            GVL_InitRegs.Init_Vals[1] := GVL_Tests.Cpu_Tests[i].Init_B;   (* B *)
            GVL_InitRegs.Init_Vals[5] := WORD_TO_BYTE(
                SHR(GVL_Tests.Cpu_Tests[i].Init_HL, 8));                  (* H *)
            GVL_InitRegs.Init_Vals[6] := WORD_TO_BYTE(
                GVL_Tests.Cpu_Tests[i].Init_HL);                          (* L *)
            GVL_InitRegs.Init_Vals[7] := GVL_Tests.Cpu_Tests[i].Init_F;   (* F *)
            GVL_InitRegs.Init_SP := GVL_Tests.Cpu_Tests[i].Init_SP;
            IF GVL_Tests.Cpu_Tests[i].Stage = 0 THEN
                GVL_InitRegs.Init_PC := GVL_Tests.Cpu_Tests[i].Init_PC;
            END_IF

            (* --- vypolnit initsializatsiyu registrov --- *)
            GVL_InitRegs.Init_En := TRUE;
            bPrepared := TRUE;
            GVL_Tests.Cpu_Test_Stage := 4;   (* otdel nyy shag: snyat Init_En *)
        END_IF

    (* ---- shag 4: dozhdat sya perebora registrov, snyat Init_En,
       zapustit emulyator.
       P O Ch E M U  Zh D E M. Init_Sel_Dst perebiraet shema (SET 1b):
       odin registr za skan, vsego 16. Esli snyat Init_En srazu, kak bylo
       ranshe, zagruzitsya tol ko nulevoj registr (A), a ostal nye
       ostanutsya nulevymi -- i kazhdyj test nachinalsya by s musorom.
       Init_Busy gasnet, kogda nomer dojdet do 16. *)
    ELSIF GVL_Tests.Cpu_Test_Stage = 4 THEN
        IF NOT GVL_InitRegs.Init_Busy THEN
            GVL_InitRegs.Init_En := FALSE;
            GVL_Control.Emu_Run := TRUE;
            nRun := 0;
            GVL_Tests.Cpu_Test_Stage := 5;
        END_IF

    (* ---- shag 5: prokrutit nuzhnoe chislo skanov ---- *)
    ELSIF GVL_Tests.Cpu_Test_Stage = 5 THEN
        nRun := nRun + 1;
        IF nRun >= GVL_Tests.Cpu_Tests[GVL_Tests.Cpu_Test_Active].Exp_Cycles THEN
            GVL_Control.Emu_Run := FALSE;
            GVL_Tests.Cpu_Test_Stage := 2;
        END_IF

    (* ---- shag 2: sravnenie ---- *)
    ELSIF GVL_Tests.Cpu_Test_Stage = 2 THEN
        i := GVL_Tests.Cpu_Test_Active;

        (* fakticheskie znacheniya: A i F berem iz zerkala HMI *)
        snimok_A := GVL_PLCVisu.A;
        snimok_F := GVL_PLCVisu.F;
        snimok_PC := GVL_PLCVisu.PC;
        snimok_Mem := Z80_Mem[GVL_Tests.Cpu_Tests[i].Exp_Mem_Addr];

        fbCase.Run := TRUE;
        fbCase.Expected_A := GVL_Tests.Cpu_Tests[i].Exp_A;
        fbCase.Expected_F := GVL_Tests.Cpu_Tests[i].Exp_F;
        fbCase.Expected_PC := GVL_Tests.Cpu_Tests[i].Exp_PC;
        fbCase.Actual_A := snimok_A;
        fbCase.Actual_F := snimok_F;
        fbCase.Actual_PC := snimok_PC;
        fbCase.Mask_A := GVL_Tests.Cpu_Tests[i].Mask_A;
        fbCase.Mask_F := GVL_Tests.Cpu_Tests[i].Mask_F;
        fbCase.Mask_PC := GVL_Tests.Cpu_Tests[i].Mask_PC;

        (* dopolnitel naya proverka pamyati: esli trebuetsya *)
                (*  V Y Z O V  F B  O B Ya Z A T E L E N.
                    TEST_Z80 -- programma na ST, a v ST funktsionalnyj blok
                    ne vypolnyaetsya sam: nuzhno yavno napisat "fbCase();".
                    Bez etogo stroki vyshe tol ko ZAPOLNILI vhody FB, a ego
                    telo (sravneniya EQ i vyhod Pass) ne schitalos nikogda.
                    Rezul tat izmeryon na progone: pri sovpadayushchih
                    Expected_A = Actual_A i Mask_A = TRUE vyhod Pass ostavalsya
                    FALSE, i PO E T O M U  padali vse 40 testov. *)

        fbCase.Run := TRUE;
        fbCase();

        IF GVL_Tests.Cpu_Tests[i].Mask_Mem AND (snimok_Mem <> GVL_Tests.Cpu_Tests[i].Exp_Mem) THEN
            GVL_Tests.Cpu_Test_Result[i] := FALSE;
        ELSE
            GVL_Tests.Cpu_Test_Result[i] := fbCase.Pass;
        END_IF
        GVL_Tests.Cpu_Test_Executed[i] := TRUE;
        GVL_Tests.Cpu_Test_Stage := 3;

    (* ---- shag 3: itogi i sleduyushchiy test ---- *)
    ELSE
        GVL_Tests.Cpu_Test_Total_Pass := 0;
        GVL_Tests.Cpu_Test_Fail_Count := 0;
        FOR i := 1 TO 40 DO
            IF GVL_Tests.Cpu_Test_Executed[i] THEN
                IF GVL_Tests.Cpu_Test_Result[i] THEN
                    GVL_Tests.Cpu_Test_Total_Pass := GVL_Tests.Cpu_Test_Total_Pass + 1;
                ELSE
                    IF GVL_Tests.Cpu_Test_Fail_Count < 16 THEN
                        GVL_Tests.Cpu_Test_Failed_List[
                            GVL_Tests.Cpu_Test_Fail_Count + 1] := i;
                    END_IF
                    GVL_Tests.Cpu_Test_Fail_Count := GVL_Tests.Cpu_Test_Fail_Count + 1;
                END_IF
            END_IF
        END_FOR

        (* perehod k sleduyushchemu vklyuchennomu testu *)
        j := GVL_Tests.Cpu_Test_Active + 1;
        WHILE j <= 75 AND NOT GVL_Tests.Cpu_Tests[j].Enabled DO
            j := j + 1;
        END_WHILE
        IF j <= 75 THEN
            GVL_Tests.Cpu_Test_Active := j;
            bPrepared := FALSE;
            GVL_Tests.Cpu_Test_Stage := 1;
        ELSE
            GVL_Tests.Cpu_Test_Stage := 9;   (* vse testy projdeny *)
            GVL_Tests.Cpu_Test_Run := FALSE;
        END_IF
    END_IF
END_IF

(* zerkalo dlya HMI *)
GVL_PLCVisu.Visu_Test_Total_Pass := GVL_Tests.Cpu_Test_Total_Pass;
GVL_PLCVisu.Visu_Test_Fail_Count := GVL_Tests.Cpu_Test_Fail_Count;
GVL_PLCVisu.Visu_Test_Stage := GVL_Tests.Cpu_Test_Stage;
GVL_PLCVisu.Visu_Test_Active := GVL_Tests.Cpu_Test_Active;
'''

ST_GVL_TESTS = u'''VAR_GLOBAL
    (* ================== DANNYE TESTIROVANIYa ==================
       Struktura odnogo testa -- tip ST_TestCase. Rezul'tat -- BOOL:
       TRUE = PASS, FALSE = FAIL. Nikakih isklyuchenij: proverka delaetsya
       blokom EQ vnutri FB_TestCase. *)
    Cpu_Test_Run         : BOOL;
    Cpu_Test_Stage       : INT;
    Cpu_Test_Active      : INT;
    Cpu_Test_Count       : INT;

    (* OPISANIE PROVEROK: odna stroka -- odin test.
       R A Z M E R  O B Ya Z A N  S O V P A D A T'  S  C I K L A M I.
       Ranshe zdes' stoyalo [1..40], a v TEST_Z80 obrabotchik hodil po
       WHILE i <= 75 -- to est' chital elementy ZA GRANITSEJ massiva.
       Emulyator na real nom progone zastrel na Cpu_Test_Active = 44:
       vseh testov 40, a on pytalsya vz yat' sorok chetvertyj. V CODESYS
       vyhod za granitsu massiva ne dayot oshibki kompilyatsii i mozhet
       nichego ne soobshchit' vo vremya raboty -- poetomu eto stoyalo
       nezamechennym. Teper' granitsy sovpadayut: 1..75 i <= 75. *)
    Cpu_Tests            : ARRAY[1..75] OF ST_TestCase;

    Cpu_Test_Result      : ARRAY[1..75] OF BOOL;
    Cpu_Test_Executed    : ARRAY[1..75] OF BOOL;
    Cpu_Test_Total_Pass  : INT;
    Cpu_Test_Fail_Count  : INT;
    Cpu_Test_Failed_List : ARRAY[1..16] OF INT;
END_VAR
'''


def mk_gvl_hw_io():
    return F.Gvl(u"GVL_HW_IO", ST_GVL_HW_IO)


def mk_gvl_hw_buffer():
    return F.Gvl(u"GVL_HW_Buffer", ST_GVL_HW_BUFFER)


def mk_gvl_io():
    return F.Gvl(u"GVL_IO", ST_GVL_IO)


def mk_gvl_cpm():
    return F.Gvl(u"GVL_CPM", ST_GVL_CPM)


def mk_gvl_disk():
    return F.Gvl(u"GVL_Disk", ST_GVL_DISK)


def mk_gvl_cpm_extra():
    return F.Gvl(u"GVL_CPM_Extra", ST_GVL_CPM_EXTRA)


def mk_gvl_bootflags():
    return F.Gvl(u"GVL_BootFlags", ST_GVL_BOOTFLAGS)


def mk_gvl_initregs():
    return F.Gvl(u"GVL_InitRegs", ST_GVL_INITREGS)


def mk_gvl_tests():
    p = F.Gvl(u"GVL_Tests", ST_GVL_TESTS)
    return p


def mk_test_z80_prep():
    u"""TEST_Z80_PREP -- odnorazovoe zapolnenie tablitsy testov.

    P O Ch E M U  O T D E L N Y J  P O U. Ranshe tablitsa iz 62 proverok
    (bolee 300 strok odnih prisvoenij) lezhala vnutri TEST_Z80, i vmeste
    s obrabotchikom poluchalsya POU na 500 s lishnim strok ST. Chitat
    takoe nelzya, a iskat v nem oshibku -- tem bolee: imenno tam dolgo
    ne mogli najti nezakrytyj IF, kotoryy daval buket oshibok C9.

    Teper tablitsa otdeleno: zdes TOLKO dannye testov, v TEST_Z80 --
    tolko obrabotchik (chetyre shaga prohoda). Sostoyanie zhivet v GVL,
    poetomu poryadok zapuska ne vazhen, no v zadache PREP stoit pervym.
    """
    p = F.TextPou(u"TEST_Z80_PREP", ST_TEST_Z80_PREP, u"program",
                  u"Odnorazovoe zapolnenie tablitsy proverok emulyatora.")
    return p


def mk_test_z80():
    u"""TEST_Z80 -- progon testov (ST upravlyaet, FBD sravnivaet)."""
    p = F.TextPou(u"TEST_Z80", ST_TEST_Z80, u"program",
                  u"Progon testov emulyatora. Sravnenie -- v FB_TestCase (FBD).")
    return p


def mk_gvl_bus():
    u"""GVL_Bus -- obshchie shiny dannyh i adresa (edinstvennaya svyaz blokov)."""
    p = F.TextPou(u"GVL_Bus", u"", u"program", u"")
    p.pou_type = u"globalVarList"

    g = F.Gvl(u"GVL_Bus", u"""VAR_GLOBAL
    (* OBShchIE ShINY: edinstvennaya svyaz' blokov.
       Provodami takuyu svyaz' tyanut' nel'zya -- poluchitsya nechitaemaya pautina.
       E D I N S T V E N N Y J   V L A D E L E C shin: nikto drugoj ih ne
       ob''yavlyaet (ranshe dubl byl v GVL_PLCVisu -- ubran). *)
    Bus_Data : BYTE;    (* 8-bitnaya shina dannyh *)
    Bus_Addr : WORD;    (* 16-bitnaya adresnaya shina *)

    (* Adresa, kotorye shema PLC_PRG publikuet cherez GVL dlya potrebitelej.
       Bez ih ob''yavleniya kompilyator daet
       "C4: 'Bus_Addr_HL' ne yavlyaetsya komponentom 'GVL_Bus'". *)
    Bus_Addr_HL : WORD; (* adres pary HL -- dlya kosvennoj adresatsii (HL) *)
    Bus_Addr_Op : WORD; (* adres operanda iz IR (n ili nn) *)
END_VAR""")
    return g


def mk_gvl_memory():
    p = F.Gvl(u"GVL_Memory", u"""VAR_GLOBAL
    (* PAMYaT' 64 KB. Vynesena v GVL, a ne vnutr' FB_Memory64K, po dvum prichinam:
       1) programmam inicializacii (ST) nuzhen dostup k nej dlya zagruzki proshivki;
       2) tak pamyat' vidna v HMI i Watch-okne bez ekzemplarov FB.
       Po zadaniyu ST razreshen imenno dlya inicializacii massiva -- eto ona. *)
    Z80_Mem : ARRAY[0..65535] OF BYTE;
END_VAR""")
    return p


def mk_gvl_control():
    u"""GVL_Control -- upravlenie emulyatorom i signaly upravleniya dekodera.

    ZACheM ZDES' SIGNALY Ctl_*. Shema PLC_PRG svyazyvaet vyhody FB_DecoderZ80
    s potrebitelyami cherez GVL (provodami poluchilas by pautina), i eti imena
    dolzhny gde-to sushchestvovat. Ran'she ih ne ob''yavlyali nigde, i
    kompilyator soobshchal "C4: 'Ctl_Is_CALL' ne yavlyaetsya komponentom
    'GVL_Control'" -- po odnoj oshibke na kazhdoe imya.
    """
    p = F.Gvl(u"GVL_Control", u"""VAR_GLOBAL
    (* UPRAVLENIE EMULYaTOROM (knopki HMI) *)
    Emu_Run   : BOOL;   (* razreshenie raboty *)
    Emu_Step  : BOOL;   (* odin shag v ruchnom rezhime *)
    Emu_Reset : BOOL;   (* sBros processora *)
    Emu_Init  : BOOL;   (* zapros na povtornuyu inicializaciyu pamyati *)

    (* SIGNALY UPRAVLENIYa OT DEKODERA (vyhody FB_DecoderZ80).
       Chteniyu v PLC_PRG ikh peredaet GVL -- tak shema ostaetsya chitaemoj. *)
    Ctl_Is_CALL   : BOOL;   (* komanda CALL *)
    Ctl_Is_RET    : BOOL;   (* komanda RET *)
    Ctl_Is_DJNZ   : BOOL;   (* komanda DJNZ *)
    Ctl_Is_HALT   : BOOL;   (* komanda HALT *)
    Ctl_Is_Jump   : BOOL;   (* JP / JP cc *)
    Ctl_Is_IN     : BOOL;   (* IN A,(n) *)
    Ctl_Is_OUT    : BOOL;   (* OUT (n),A *)
    Ctl_Imm_Mode  : BOOL;   (* operand beretsya iz IR (n ili nn) *)
    Ctl_Flags_En  : BOOL;   (* razreshenie zapisi flagov *)
    Ctl_Wr_Enable : BOOL;   (* razreshenie zapisi v registr *)
    Ctl_Mem_Rd    : BOOL;   (* chtenie pamyati *)
    Ctl_Mem_Wr    : BOOL;   (* zapis' v pamyat' *)
    Ctl_IO_Rd     : BOOL;   (* chtenie porta I/O *)
    Ctl_IO_Wr     : BOOL;   (* zapis' v port I/O *)
    Ctl_IncDec    : BOOL;   (* INC/DEC: operand = 1 *)
    Ctl_Is_Jr     : BOOL;   (* JR -- perehod otnositelnyy *)
    Ctl_Sel_Dst   : BYTE;   (* nomer registra-priemnika *)
    Ctl_Sel_Src   : BYTE;   (* nomer registra-istochnika *)
    Ctl_ALU_Op    : BYTE;   (* kod operatsii ALU 0..7 *)
    Ctl_Cond      : BYTE;   (* uslovie perehoda *)

    (* N A S T R A I V A E M O E  Ch I S L O  I N S T R U K C I J  Z A  S K A N.
       Tochka rasshireniya iz zadaniya. Bazovyj variant -- odna komanda za
       skan; Scan_Insns = 1 imenno eto i znachit.
       CHto delaet bolshee znachenie: takt v PLC_PRG (SET 1) idet v dva
       polutakta za skan, i posle fazy ispolneniya schetchik SCAN_CNT
       sravnivaetsya s etim chislom. Poka schetchik menshe -- komanda
       schitaetsya zavershennoy i takt zapuskaetsya snova; kak tolko
       schetchik dohodit do Scan_Insns, on obnulyaetsya i zhdet novogo
       skana PLK. Takim obrazom odin skan PLK uspevaet vypolnit neskolko
       komand, i shemu peredelyvat ne nuzhno.
       Granicy: 0 i 1 dayut odinakovyy rezul tat -- odna komanda za skan. *)
    Scan_Insns  : BYTE := 1;
    Scan_Cnt    : BYTE;     (* skolko komand uzhe vypolneno v etom skane *)
END_VAR""")
    return p


def mk_gvl_visu():
    p = F.Gvl(u"GVL_PLCVisu", u"""VAR_GLOBAL
    (* ZERKALO DLYa VIZUALIZACII (tol'ko chtenie).
       HMI privyazyvaetsya TOL'KO k etomu GVL -- inache vizualizaciya nachnet
       vliyat' na ispolnenie. *)
    A  : BYTE;
    B  : BYTE;
    C  : BYTE;
    D  : BYTE;
    E  : BYTE;
    H  : BYTE;
    L  : BYTE;

    AltA : BYTE;
    AltB : BYTE;
    AltC : BYTE;
    AltD : BYTE;
    AltE : BYTE;
    AltH : BYTE;
    AltL : BYTE;

    F      : BYTE;
    PC     : WORD;
    SP     : WORD;
    IX     : WORD;
    IY     : WORD;
    I      : BYTE;
    R_Reg  : BYTE;
    IR     : BYTE;
    Halted : BOOL;


    (* raspakovannye flagi dlya lampochek HMI *)
    FlagS  : BOOL;
    FlagZ  : BOOL;
    FlagH  : BOOL;
    FlagPV : BOOL;
    FlagN  : BOOL;
    FlagC  : BOOL;

    (* okno dampa pamyati *)
    Dump_Base : WORD;
    (* itogi testov dlya HMI. ETO ZERKALA: ih pishet TEST_Z80 iz GVL_Tests,
       HMI tolko chitaet. Imena s prefiksom Visu_ -- chtoby ne stolknovilis s
       GVL_Tests / GVL_Tests_CPM (kolliziya imen kompilyatorom ne lovitsya). *)
    Visu_Test_Total_Pass : INT;
    Visu_Test_Fail_Count : INT;
    Visu_Test_Stage      : INT;
    Visu_Test_Active     : INT;
END_VAR""")
    return p


ST_INIT_MEMORY = u"""(* =========================================================================
   PRG_InitMemory -- INICIALIZACIYa MASSIVA PAMYaTI 64 KB.
   ETO ODNA IZ DVUH RAZRESHENNYH ZADANIEM TOCHEK PRIMENENIYa ST
   (vtoraya -- generaciya testovyh dannyh). VsyA logika processora -- v FBD.

   Vypolnyaetsya odin raz pri pervoj progonke (flag InitDone) ili povtorno
   po komande Emu_Init s HMI.
   ========================================================================= *)
VAR
    (*  P O Ch E M U  Z D E S  I M E N N O  DINT.
        Cikl idet do 65535, a eto bol she INT (maksimum 32767):
        s schetchikom INT on posle 32767 ushel by v otricatel nye
        chisla. DINT vmeshchaet 0..65535 celikom, poetomu schetchik
        cikla obyavlen kak DINT. Provereno otdel nym opytom
        (generator/tools/probe_index.py): massiv ARRAY[0..65535]
        prinimaet indeks lyubogo cislovogo tipa bez preduprezhdenij. *)
    i : DINT;
END_VAR

IF (NOT InitDone) OR Emu_Init THEN
    (* --- ochistka vsej pamyati --- *)
    FOR i := 0 TO 65535 DO
        Z80_Mem[i] := 0;
    END_FOR

    (* --- tablica perehodov v nulevoj stranice ---
       Po adresu 2*n lezhit komanda JP (2*n + 0100h): odin bajt "n" na vhode
       ravnocenen komande JP po nuzhnomu adresu. Eto uproshchaet ruchnuyu
       otladku s HMI. *)
    FOR i := 0 TO 100 DO
        Z80_Mem[2 * i]     := 16#C3;              (* JP nn *)
        Z80_Mem[2 * i + 1] := DINT_TO_BYTE(i);
        Z80_Mem[2 * i + 2] := 16#01;
    END_FOR

    InitDone := TRUE;
    Emu_Init := FALSE;
END_IF
"""

ST_LOAD_TEST = u"""(* =========================================================================
   PRG_LoadTestProgram -- GENERACIYa TEST OVYH DANNYH.
   Vtoraya razreshennaya zadaniem tochka primeneniya ST.
   Zagruzhaet tri testovye programmy:
     0100h -- slozhenie dvuh chisel iz pamyati   (testy P01..P05)
     0120h -- cikl DJNZ                          (testy L01..L05)
     0140h -- cikl DEC B + JP NZ                 (testy L06..L08)
   ========================================================================= *)
VAR
    (*  P O Ch E M U  INT, A  N E  DINT: neyavnoe suzhenie DINT -> INT
        v CODESYS zapreshcheno, a indeks idet v ARRAY- massivy pamyati. *)
    i : INT;
END_VAR

IF GVL_Test_Load OR (NOT TestLoaded) THEN

    (* ---------- programma 1: slozhenie dvuh chisel iz pamyati ---------- *)
    Z80_Mem[16#0100] := 16#3A;  (* LD A,(2000h) *)
    Z80_Mem[16#0101] := 16#00;
    Z80_Mem[16#0102] := 16#20;
    Z80_Mem[16#0103] := 16#47;  (* LD B,A       *)
    Z80_Mem[16#0104] := 16#3A;  (* LD A,(2001h) *)
    Z80_Mem[16#0105] := 16#01;
    Z80_Mem[16#0106] := 16#20;
    Z80_Mem[16#0107] := 16#80;  (* ADD A,B      *)
    Z80_Mem[16#0108] := 16#32;  (* LD (2002h),A *)
    Z80_Mem[16#0109] := 16#02;
    Z80_Mem[16#010A] := 16#20;

    Z80_Mem[16#2000] := 16#25;  (* pervoe slagaemoe *)
    Z80_Mem[16#2001] := 16#10;  (* vtoroe slagaemoe *)
    Z80_Mem[16#2002] := 16#00;  (* kuda zapishetsya rezul'tat *)

    (* ---------- programma 2: cikl DJNZ ---------- *)
    Z80_Mem[16#0120] := 16#06;  (* LD B,05h *)
    Z80_Mem[16#0121] := 16#05;
    Z80_Mem[16#0122] := 16#AF;  (* XOR A    *)
    Z80_Mem[16#0123] := 16#80;  (* ADD A,B  <- tochka vozvrata *)
    Z80_Mem[16#0124] := 16#10;  (* DJNZ 0123h *)
    Z80_Mem[16#0125] := 16#FD;  (* smeshchenie -3 ot sleduyushchej komandy *)
    Z80_Mem[16#0126] := 16#32;  (* LD (2000h),A *)
    Z80_Mem[16#0127] := 16#00;
    Z80_Mem[16#0128] := 16#20;

    (* ---------- programma 3: cikl DEC B + JP NZ ---------- *)
    Z80_Mem[16#0140] := 16#06;  (* LD B,03h *)
    Z80_Mem[16#0141] := 16#03;
    Z80_Mem[16#0142] := 16#AF;  (* XOR A    *)
    Z80_Mem[16#0143] := 16#80;  (* ADD A,B  <- tochka vozvrata *)
    Z80_Mem[16#0144] := 16#05;  (* DEC B    *)
    Z80_Mem[16#0145] := 16#C2;  (* JP NZ,0143h *)
    Z80_Mem[16#0146] := 16#43;
    Z80_Mem[16#0147] := 16#01;
    Z80_Mem[16#0148] := 16#32;  (* LD (2001h),A *)
    Z80_Mem[16#0149] := 16#01;
    Z80_Mem[16#014A] := 16#20;

    TestLoaded := TRUE;
    GVL_Test_Load := FALSE;
END_IF
"""


def mk_gvl_init_state():
    p = F.Gvl(u"GVL_InitState", u"""VAR_GLOBAL
    (* Flagowie peremennye odnorazovoj inicializacii.
       Zhivut v GVL, chtoby programmy inicializacii ne trebovali ekzemplyarov. *)
    InitDone  : BOOL;
    TestLoaded : BOOL;
    GVL_Test_Load : BOOL;
    (* Priznak, chto tablitsa proverok emulyatora uzhe zapolnena.
       Ego vystavlyaet POU TEST_Z80_PREP, a chitaet TEST_Z80.
       Ch T O  Z D E S', A  N E  V  P O U: ranshe eto byl lokalnyj
       bFirstScan vnutri TEST_Z80, i poka tablitsa i obrabotchik byli
       odnim POU, etogo hvatalo. Kogda tablitsu vynesli v TEST_Z80_PREP,
       lokalnaya peremennaya stala nevidima -- znachit priznak dolzhen
       zhit v GVL. Zavedeno, chtoby poryadok POU v zadache ne vliyal. *)
    TestTableDone : BOOL;
    TestTableCnt  : INT;    (* skolko proverok vklyucheno -- dlya HMI *)
END_VAR""")
    return p


def mk_prg_init_memory():
    u"""PRG_InitMemory -- inicializaciya massiva pamyati 64 KB (ST, razresheno)."""
    p = F.TextPou(u"PRG_InitMemory", ST_INIT_MEMORY, u"program",
                  u"Inicializaciya massiva pamyati 64 KB. ST razreshen zadaniem.")
    return p


def mk_prg_load_test():
    u"""PRG_LoadTestProgram -- generaciya testovyh dannyh (ST, razresheno)."""
    p = F.TextPou(u"PRG_LoadTestProgram", ST_LOAD_TEST, u"program",
                  u"Generaciya testovyh dannyh. ST razreshen zadaniem.")
    return p



def mk_always_true():
    u"""FB_AlwaysTrue -- postoyanno TRUE. Nuzhen kak signal "proizoshel skan".

    V FBD net podachi konsantnogo BOOL napryamuyu v inostrannyj blok tak,
    chtoby eto bylo citaemo, poetomu delaem otdel'nyj POU.
    """
    #  I M E N N O  functionBlock, a ne function: v PLC_PRG etot POU
    #  vyzyvaetsya s imenem ekzemplyara (fbAlways). U function ekzemplyarov
    #  ne byvaet, i kompilyator soobshchaet
    #  "C177: 'FB_AlwaysTrue' imeet tip FUNCTION i ne mozhet imet ekzemplyary".
    p = F.Pou(u"FB_AlwaysTrue", u"functionBlock",
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

    PRAVILO FBD, kotoroe zdes' soblyudaetsya strogo: kazhdyj ekzemplyar FB
    vyzyvaetsya ODIN raz za skan. Povtornyj vyzov odnogo ekzemplyara
    privodit k oshibke importa. Poetomu vyhody chitayutsya po imeni
    ('fbClock.Clk_Decode'), a ne povtornym vyzovom.

    Poryadok setey = poryadok ispolneniya: kazhdaya set' chitaet tolko to,
    chto zapisali predyduwie.
    """
    p = F.Pou(u"PLC_PRG", u"program",
              u"GLAVNAYa SHEMA emulyatora Z80.\n"
              u"ODIN SKAN PLC = ODNA KOMANDA (v dva polutakta: decode i exec).\n"
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
    #  TIP WORD, a ne BYTE: vyhod SP_Out u FB_Memory64K -- WORD (snyatoe so
    #  steka 16-bitnoe slovo). Kogda zdes stoyal BYTE, kompilyator daval
    #  "Nevozmozhno konvertirovat tip 'WORD' v tip 'BYTE'".
    p.var(u"vSpRd", u"WORD", u"slovo, snyatoe so steka")
    p.var(u"vMemDrv", u"BYTE", u"chto na shinu pri chtenii")
    p.var(u"vFetch", u"BYTE", u"vybrannyj kod komandy")
    p.var(u"vIOAddr", u"BYTE", u"adres porta I/O")
    #  vIOEn -- uslovie dlya SEL: "idet obrashchenie k portu".
    #  Otdel'naya peremennaya BOOL nuzhna, chtoby ne podavat' v uslovie
    #  rezul'tat obobshchennogo bloka OR (sm. poyasnenie v seti 16).
    p.var(u"vIOEn", u"BOOL", u"idet obrashchenie k portu I/O")
    p.var(u"vIOData", u"BYTE", u"dannye s shiny I/O")
    p.var(u"vInDi", u"BYTE", u"diskretnye vhody PLK")
    p.var(u"vInAI0", u"WORD", u"analogovyy vhod 0")
    p.var(u"vInAI1", u"WORD", u"analogovyy vhod 1")
    p.var(u"vOutDO", u"BYTE", u"diskretnye vyhody PLK")
    p.var(u"vOutAO0", u"WORD", u"analogovyy vyhod 0")
    p.var(u"vOutAO1", u"WORD", u"analogovyy vyhod 1")
    p.var(u"vIsBIOS", u"BOOL", u"PC ukazyvaet v tablitsu BIOS")
    p.var(u"fbIO", u"FB_IO_Ports", u"256 I/O-portov")
    p.var(u"fbHW", u"FB_HW_IO_PLC", u"apparatnyy interfeys PLK")
    p.var(u"fbBIOS", u"FB_CPM_BIOS", u"minimalnyy BIOS")
    # VYHODY FB CHEREZ LOKALNYE PEREMENNYE:
    #  Pochemu tak: ssylka vida fbXX.PIN v inVariable privodit k
    #  oshibkam C32 pri generacii koda dlya zadachi (naydeno bisekciej).
    #  Cherez peremennuyu svyaz' stanovitsya obychnoj.
    p.var(u"vALU_Y", u"BYTE", u"vyhod FB_ALU_Z80.Y")
    p.var(u"vCtl_Halted", u"BOOL", u"vyhod FB_ControlUnit.Halted")
    p.var(u"vCtl_Inc_By", u"BYTE", u"vyhod FB_ControlUnit.Inc_By")
    p.var(u"vCtl_PC_Load", u"BOOL", u"vyhod FB_ControlUnit.PC_Load")
    p.var(u"vCtl_PC_New", u"WORD", u"vyhod FB_ControlUnit.PC_New")
    p.var(u"vFlags_F", u"BYTE", u"vyhod FB_FlagsRegZ80.F")
    p.var(u"vMem_Bus_Drv", u"BYTE", u"vyhod FB_Memory64K.Bus_Drv")
    p.var(u"vMem_D_Out", u"BYTE", u"vyhod FB_Memory64K.D_Out")
    p.var(u"vMem_Rd_Data", u"BYTE", u"vyhod FB_Memory64K.Rd_Data")
    p.var(u"vMem_SP_Out", u"WORD", u"vyhod FB_Memory64K.SP_Out")
    p.var(u"vPC_PC_Next", u"WORD", u"vyhod FB_PC_Z80.PC_Next")
    p.var(u"vRFRd_Addr_HL", u"WORD", u"vyhod FB_RegFileZ80.Addr_HL")
    p.var(u"vR_Q", u"BYTE", u"vyhod FB_Reg8.Q")
    p.var(u"vSP_SP", u"WORD", u"vyhod FB_SP_StackZ80.SP")

    #  A P P A R A T N Y E   K A N A L Y  (programmnyy sloj).
    #  Pochemu BEZ "AT %IX0.0". Direktiva privyazki v etom proekte otvergaetsya
    #  kompilyatorom: "C6: ';, :=, REF=, ( ili [' trebuetsya vmesto 'AT'".
    #  Pravilo CODESYS 3.5 takovo: prinyat adres mozhno tolko togda, kogda
    #  v Device Tree est moduli vvoda/vyvoda ili zadana I/O-mapping dlya
    #  prilozheniya. U nas ustanovlen tolko SoftPLC bez modulnyh diskov
    #  shlejfa -- poetomu privyazka ostaetsya RUChNYM shagom, kak i HMI.
    #
    #  KAK PRIVYaZAT: v Device Tree dobavit modul vvoda/vyvoda i v tablitse
    #  I/O Mapping sopostavit kanaly etim peremennym (imena PLC_DI_0 ...
    #  PLC_AO_1). Karta portov -- docs/05_APPARATNYJ_VVOD_VYVOD.md.
    #  Logika i shema ot etogo ne menyayutsya: DOSTATOChNO dobavit "AT %IX0.0"
    #  k obyavleniyu nizhe.
    #  A D R E S A  ZH I V U T  Z D E S ,  I  E T O  O K O N CH A T E L  N O.
    #
    #  Ranee zdes stoyal kommentarij, chto privyazku k Device Tree sdelat
    #  nelzya, potomu chto "v Device Tree net modulej vvoda-vyvoda". Eto
    #  okazalos neverno, i oshibka byla ne v CODESYS, a v MESTE obyavleniya:
    #  direktiva AT nedopustima v spiske GLOBALNYH peremennyh (tam ona daet
    #  40 oshibok C6: "' ;, :=, REF=, ( ili [' trebuetsya vmesto 'AT'"),
    #  no v PROGRAM ona rabotaet shtatno.
    #
    #  Dlya CODESYS Control Win V3 (SoftPLC) oblasti %I i %Q sushchestvuyut
    #  po umolchaniyu, poetomu adresa prinimayutsya bez ustanovki modulej:
    #    %IX0.0  %IX0.7  - diskretnye vhody   (port IN  00h)
    #    %QX0.0  %QX0.7  - diskretnye vyhody  (port OUT 01h)
    #    %IW0 / %IW1      - analogovye vhody   (porty IN  02h/03h i 06h/07h)
    #    %QW0 / %QW1      - analogovye vyhody  (porty OUT 04h/05h i 08h/09h)
    #  Karta portov Z80  kanaly PLK - docs/05_APPARATNYJ_VVOD_VYVOD.md.
    p.var(u"PLC_DI_0", u"BOOL", u"diskretnyy vhod 0 (IN 00h, bit 0)", u"%IX0.0")
    p.var(u"PLC_DI_1", u"BOOL", u"diskretnyy vhod 1", u"%IX0.1")
    p.var(u"PLC_DI_2", u"BOOL", u"diskretnyy vhod 2", u"%IX0.2")
    p.var(u"PLC_DI_3", u"BOOL", u"diskretnyy vhod 3", u"%IX0.3")
    p.var(u"PLC_DI_4", u"BOOL", u"diskretnyy vhod 4", u"%IX0.4")
    p.var(u"PLC_DI_5", u"BOOL", u"diskretnyy vhod 5", u"%IX0.5")
    p.var(u"PLC_DI_6", u"BOOL", u"diskretnyy vhod 6", u"%IX0.6")
    p.var(u"PLC_DI_7", u"BOOL", u"diskretnyy vhod 7", u"%IX0.7")
    p.var(u"PLC_DO_0", u"BOOL", u"diskretnyy vyhod 0 (OUT 01h, bit 0)", u"%QX0.0")
    p.var(u"PLC_DO_1", u"BOOL", u"diskretnyy vyhod 1", u"%QX0.1")
    p.var(u"PLC_DO_2", u"BOOL", u"diskretnyy vyhod 2", u"%QX0.2")
    p.var(u"PLC_DO_3", u"BOOL", u"diskretnyy vyhod 3", u"%QX0.3")
    p.var(u"PLC_DO_4", u"BOOL", u"diskretnyy vyhod 4", u"%QX0.4")
    p.var(u"PLC_DO_5", u"BOOL", u"diskretnyy vyhod 5", u"%QX0.5")
    p.var(u"PLC_DO_6", u"BOOL", u"diskretnyy vyhod 6", u"%QX0.6")
    p.var(u"PLC_DO_7", u"BOOL", u"diskretnyy vyhod 7", u"%QX0.7")
    p.var(u"PLC_AI_0", u"INT", u"analogovyy vhod 0 (IN 02h/03h)", u"%IW0")
    p.var(u"PLC_AI_1", u"INT", u"analogovyy vhod 1 (IN 06h/07h)", u"%IW1")
    p.var(u"PLC_AO_0", u"INT", u"analogovyy vyhod 0 (OUT 04h/05h)", u"%QW0")
    p.var(u"PLC_AO_1", u"INT", u"analogovyy vyhod 1 (OUT 08h/09h)", u"%QW1")
    p.var(u"vBiosOut", u"BYTE", u"simvol konsoli ot BIOS")
    p.var(u"vBiosWr", u"BOOL", u"strob vyvoda BIOS")
    p.var(u"vBiosRd", u"BOOL", u"zapros vvoda BIOS")
    p.var(u"vPCNext", u"WORD", u"PC posle inkrementa")

    # ================= 1. TAkT =================
    #  P A R A M E T R  I Z  Z A D A N I Ya: skolko komand za skan.
    #  Byudzhet vedet shema: schetchik vnizu seti (SET 1b) schitaet
    #  vypolnennye komandy i sbrasyvaet sebya, kogda dohodit do
    #  GVL_Control.Scan_Insns. Poka byudzhet est, faza dekodirovaniya
    #  zapuskaetsya snova -- znachit za odin skan PLK uspevaet projti
    #  neskolko komand. Pri Scan_Insns = 1 (znachenie po umolchaniyu)
    #  povedenie Prezhnee: odin skan -- odna komanda.
    n1 = p.network(u"SET 1: TAkT: dve fazy za skan")
    #  R A Z R E Sh E N I E  R A B O T Y  =  Emu_Run  I  N E  Halted.
    #  B Y L O  T A K: vRun := GVL_Control.Emu_Run, i bol she nichego.
    #  Posledstvie izmereno na real nom progone: komanda HALT (76h) po
    #  adresu 0 raspolagalas' verno, FB_ControlUnit vyrabatyval Halted=TRUE,
    #  no takt prodolzhal idti, PC uehal dal she 2500 i nikogda ne
    #  ostanavlivalsya. To est' HALT ne ostanavlival protsessor.
    #  T E P E R' vRun gasit takt, kak tol ko FB_ControlUnit vystavil Halted.
    #  vCtl_Halted chitaetsya iz SET 12 -- eto znachenie proshlogo skana,
    #  chto normal no (ostanovka zanimaet odin skan).
    c_run = n1.invar(u"GVL_Control.Emu_Run", y=30)
    c_halt = n1.invar(u"vCtl_Halted", y=170)
    c_run2 = n1.invar(u"GVL_Control.Emu_Run", y=210)
    c_halt2 = n1.invar(u"vCtl_Halted", y=250)
    not_halt = n1.block(u"NOT", [(PINU, c_halt)], [POUT], x=F.COL_BLK, y=170)
    not_halt2 = n1.block(u"NOT", [(PINU, c_halt2)], [POUT], x=F.COL_BLK, y=250)
    run_gate = b_and(n1, F.COL_BLK2, 30, c_run, not_halt)
    run_clk = b_and(n1, F.COL_BLK2, 210, c_run2, not_halt2)
    n1.outvar(u"vRun", run_gate, x=F.COL_OUT, y=30)
    c_run_al = n1.invar(u"vRun", y=290)
    al = n1.block(u"FB_AlwaysTrue", [(u"Dummy", c_run_al)], [u"Q"],
                  x=F.COL_BLK + 160, y=290, instance=u"fbAlways")
    n1.outvar(u"vScan", al, x=F.COL_OUT, y=290)
    n1.block(u"FB_Clock", [(u"Enable", run_clk),
                          (u"Scan", n1.invar(u"vScan", y=110))],
             [u"Clk_Decode", u"Clk_Exec", u"Busy"],
             x=F.COL_BLK2, y=30, instance=u"fbClock")

    # ================= 1b. POSLEDOVATEL NOST INICIALIZACII =================
    #  Z A Ch E M. FB_RegFileZ80 za odin vyzov mozhet zagruzit TOL KO ODIN
    #  registr: nomer beretsya iz Init_Sel_Dst. A Init_Sel_Dst nikto ne
    #  perebiral -- programma testov vypuskala Init_En na odin skan i zhdala,
    #  chto zagruzitsya vsyo srazu. Po etomu zhe Init_En gruzitsya i PC.
    #  Zdes shema sama vedet perebor: poka Init_En aktiven, nomer registra
    #  rastet 0,1,2 ... 15, a Init_Busy derzhit Init_En v programme testov
    #  do konca perebora. Kogda Init_En snyat -- schetchik sbrasyvaetsya.
    #
    #  P O R Ya D O K  V A Zh E N: chteniya schetchika idut DO zapisi v nego
    #  (biblioteka vyvodit elementy seti v tom poryadke, v kakom ih sozdali),
    #  poetomu Init_Sel_Dst poluchaet nomer TEKUSHCHEGO skana, a novoe
    #  znachenie schetchika zapisyvaetsya poslednim.
    p.var(u"vInitCnt", u"BYTE", u"nomer registra pri perebore 0..15")
    p.var(u"vInitNext", u"BYTE", u"sleduyushchij nomer")
    n1b = p.network(u"SET 1b: INICIALIZACIYa: perebor registrov 0..15")
    c_icnt = n1b.invar(u"vInitCnt", y=30)
    #  Init_Sel_Dst := nomer tekushchego skana
    n1b.outvar(u"GVL_InitRegs.Init_Sel_Dst", c_icnt, x=F.COL_OUT, y=30)
    #  Init_Busy := nomer < 16
    c_ibusy = n1b.invar(u"vInitCnt", y=70)
    busy = n1b.block(u"LT", [(PIN1, c_ibusy), (PIN2, n1b.const(u"16", y=84))],
                     [POUT], x=F.COL_BLK2, y=70)
    n1b.outvar(u"GVL_InitRegs.Init_Busy", busy, x=F.COL_OUT + 300, y=70)
    #  sleduyushchij nomer i zapis' schetchika
    c_icnt2 = n1b.invar(u"vInitCnt", y=110)
    nxt = b_add(n1b, F.COL_BLK, 110, c_icnt2, n1b.const(u"1", y=124))
    n1b.outvar(u"vInitNext", nxt, x=F.COL_OUT, y=110)
    c_ien = n1b.invar(u"GVL_InitRegs.Init_En", y=150)
    cnt_new = b_sel(n1b, F.COL_BLK2, 150,
                    c_ien,
                    n1b.const(u"BYTE#0", y=164),
                    n1b.invar(u"vInitNext", y=178))
    n1b.outvar(u"vInitCnt", cnt_new, x=F.COL_OUT, y=150)

    # ================= 2. PC =================
    n2 = p.network(u"SET 2: PC: adres tekushchej komandy na shinu")
    c_pc = n2.invar(u"fbPCLatch.Q", y=30)
    #  O D N A  Z A P I S',  A  N E  D V E.
    #  Ran'she zdes' stoYAli DVA outvar v odno i to zhe imya:
    #      outvar GVL_Bus.Bus_Addr <- fbPCLatch.Q   (y=30)
    #      outvar GVL_Bus.Bus_Addr <- fbPCLatch.Q   (y=70)
    #  Eto defekt: odna i ta zhe peremennaya poluchala znachenie dvazhdy za
    #  odin skan (poslednee pobezhdaet), a odin istochnik pitayut dva vyhoda --
    #  znachit biblioteka kloniruet vhodnuyu vethv'. Kopiya nichego ne menyaet
    #  po smyslu i tol'ko meshala razboru oshibok tipov.
    n2.outvar(u"GVL_Bus.Bus_Addr", c_pc, x=F.COL_OUT, y=30)

    # ================= 3. FETCH =================
    n3 = p.network(u"SET 3: VBORKA: kod komandy v IR")
    c_irq = n3.invar(u"fbIR.Q", y=210)
    n3.outvar(u"GVL_PLCVisu.IR", c_irq, x=F.COL_OUT, y=210)
    n3.block(u"FB_Reg8Latch",
             [(u"D", n3.invar(u"fbMem.D_Out", y=30)),
              (u"EN", n3.const(u"TRUE", y=70)),
              (u"Clk", n3.invar(u"fbClock.Clk_Decode", y=110)),
              (u"CLR", n3.invar(u"GVL_Control.Emu_Reset", y=150))],
             [u"Q"], x=F.COL_BLK2, y=30, instance=u"fbIR")

    # ================= 4. DEKODER =================
    #  V Y H O D Y   V   L O K A L N Y E   P E R E M E N N Y E.
    #  Ran'she kazhdyj vyhod chitalsya kak "fbDec.<pin>" (ssylka na vyhod
    #  ekzemplyara FB) i tut zhe pisalsya v GVL. Pri generacii koda dlya
    #  tsiklicheskoj zadachi CODESYS spotykalsya na etom i daval 18 oshibok
    #  C32 (konverziya tipov), kotoryh ne bylo, poka POU ne byl zaregistrirovan
    #  v zadache. Naydeno bisekciej: otklyuchenie etoj seti ubiraet vse C32.
    #  Cherez lokalnye peremennye svyaz' stanovitsya obychnoj i odnoznachnoj.
    ctl_names = (u"Ctl_Is_CALL", u"Ctl_Is_RET", u"Ctl_Is_DJNZ",
                 u"Ctl_Is_HALT", u"Ctl_Is_Jump", u"Ctl_Is_Jr",
                 u"Ctl_Imm_Mode", u"Ctl_Flags_En", u"Ctl_Wr_Enable",
                 u"Ctl_Mem_Rd", u"Ctl_Mem_Wr", u"Ctl_Sel_Dst",
                 u"Ctl_Sel_Src", u"Ctl_ALU_Op", u"Ctl_Cond", u"Ctl_IncDec",
                 u"Ctl_Is_IN", u"Ctl_Is_OUT", u"Ctl_IO_Rd", u"Ctl_IO_Wr")
    for nm_ in ctl_names:
        typ_ = u"BYTE" if nm_ in (u"Ctl_Sel_Dst", u"Ctl_Sel_Src",
                                  u"Ctl_ALU_Op", u"Ctl_Cond") else u"BOOL"
        p.var(u"v" + nm_, typ_, u"signal upravleniya ot dekodera")

    n4 = p.network(u"SET 4: DEKODIROVANIE: IR vo vse signaly upravleniya")
    n4.block(u"FB_DecoderZ80", [(u"IR", c_irq)],
             [u"Ctl_Is_CALL", u"Ctl_Is_RET", u"Ctl_Is_DJNZ", u"Ctl_Is_HALT",
              u"Ctl_Is_Jump", u"Ctl_Is_Jr", u"Ctl_Imm_Mode", u"Ctl_Flags_En",
              u"Ctl_Wr_Enable", u"Ctl_Mem_Rd", u"Ctl_Mem_Wr",
              u"Ctl_Sel_Dst", u"Ctl_Sel_Src", u"Ctl_ALU_Op", u"Ctl_Cond",
              u"Ctl_IncDec"],
             x=F.COL_BLK, y=30, instance=u"fbDec")
    #  KAZhDYY vyhod -- v SVOEY seti (pravilo biblioteki: v odnoy seti mozhno
    #  prochitat tolko odin vyhod bloka), i snachala v lokalnuyu peremennuyu.
    for k, nm_ in enumerate(ctl_names):
        nk = p.network(u"SET 4.%d: %s" % (k + 1, nm_))
        nk.outvar(u"v" + nm_, nk.invar(u"fbDec." + nm_, y=30),
                  x=F.COL_OUT, y=30)

    #  I tolko teper' -- v GVL dlya potrebitelej v drugih POU.
    n4b = p.network(u"SET 4b: signaly upravleniya v GVL dlya drugih POU")
    for nm_ in ctl_names:
        n4b.outvar(u"GVL_Control." + nm_, n4b.invar(u"v" + nm_, y=30),
                   x=F.COL_OUT, y=30)

    # ================= 5. CHTENIE REGISTROV =================
    n5 = p.network(u"SET 5: CHTENIE REGISTROV: bez zapisi")
    n5.block(u"FB_RegFileZ80",
             [(u"Sel_Dst", n5.invar(u"vCtl_Sel_Dst", y=30)),
              (u"Sel_Src", n5.invar(u"vCtl_Sel_Src", y=70)),
              (u"Wr_Val", n5.const(u"0", y=110)),
              (u"Wr_En", n5.const(u"FALSE", y=150)),
              (u"Clk", n5.invar(u"fbClock.Clk_Exec", y=190)),
              (u"CLR", n5.invar(u"GVL_Control.Emu_Reset", y=230)),
              (u"Mem_Rd", n5.invar(u"vMemDrv", y=270)),
              (u"Imm", n5.invar(u"vImm", y=310)),
              (u"Init_En", n5.invar(u"GVL_InitRegs.Init_En", y=350)),
              (u"Init_Sel_Dst", n5.invar(u"GVL_InitRegs.Init_Sel_Dst", y=390))],
             [u"Src_Val", u"A", u"B", u"C", u"D", u"E", u"H", u"L", u"F",
              u"Sa", u"Sb", u"Sc", u"Sd", u"Se", u"Sh", u"Sl", u"Sf",
              u"Addr_HL"],
             x=F.COL_BLK2, y=30, instance=u"fbRFRd")
    n5.outvar(u"vRFRd_Addr_HL", n5.invar(u"fbRFRd.Addr_HL", y=30))
    n5.outvar(u"GVL_Bus.Bus_Addr_HL", n5.invar(u"vRFRd_Addr_HL", y=60),
              x=F.COL_OUT + 600, y=550)

    # ================= 6. ADRES OPERANDA =================
    n6 = p.network(u"SET 6: ADRES OPERANDA: (HL) ili nn")
    c_imm = n6.invar(u"vCtl_Imm_Mode", y=30)
    c_hl = n6.invar(u"fbRFRd.Addr_HL", y=70)
    c_nlo = n6.invar(u"fbMem.Rd_Data", y=110)
    c_nhi = n6.invar(u"fbMem.SP_Out", y=150)
    c_pcn = n6.invar(u"fbPCLatch.Q", y=190)
    #  S T A R Sh I J  B A J T  ADRESA nn.
    #  Vazhno: SP_Out imeet tip WORD, poetomu prezhde chem sdvigat ego na 8,
    #  nado suzit ego do bajta. Ran'she zdes stoyalo
    #      wh = b_b2w(n6, ..., c_nhi)      # WORD -> BYTE -> WORD
    #      sh = b_shl(n6, ..., wh, 8)      # sdvig WORD na 8
    #  Pervaya zhe konversiya poluchala WORD tam, gde ozhidaetsya BYTE, i
    #  kompilyator daval "C32: WORD v BYTE". Teper' berem uzhe suzhennoe
    #  znachenie vNnHi (WORD_TO_BYTE) i sdvigaem ego kak BYTE.
    n6.outvar(u"vNnHi", b_w2b(n6, F.COL_BLK, 150, c_nhi), x=F.COL_OUT, y=150)
    pc1 = b_add(n6, F.COL_BLK, 190, c_pcn, n6.const(u"WORD#1", y=204))
    n6.outvar(u"GVL_Bus.Bus_Addr_Op", pc1, x=F.COL_OUT, y=190)
    #  S D V I G  D E L A E T S Ya  P O  S L O V U,  A  N E  P O  B A J T U.
    #  Ran'she zdes' stoYAlo:
    #      wh = invar(vNnHi)          -- eto BYTE
    #      sh = SHL(wh, 8)            -- sdvig BAJTA na 8
    #  Dve oshibki srazu:
    #   1) C308: sdvig na 8 prevyshaet razmernost BYTE -- starshij bajt
    #      bezvozvratno teryaetsya, i adres nn poluchaetsya nepravil nym;
    #   2) T I P: sh stanovitsya BYTE, wl -- WORD, i OR poluchaet operandy
    #      raznogo tipa; dalee SEL soderzhit vetki BYTE i WORD, i kompilyator
    #      vybiraet USINT dlya vsej cepochki. Eto i davalo pary
    #      "BOOL <-> USINT", kotorye nikak ne svyazat s POU.
    #  P R A V I L' N O: snachala rasshirit' bajt do slova, potom sdvigat.
    wh = b_b2w(n6, F.COL_BLK2, 150, n6.invar(u"vNnHi", y=150))
    sh = b_shl(n6, F.COL_BLK2 + 160, 150, wh, n6.const(u"8", y=164))
    wl = b_b2w(n6, F.COL_BLK2, 110, c_nlo)
    nn = n6.block(u"OR", [(PIN1, sh), (PIN2, wl)], [POUT],
                  x=F.COL_BLK2 + 320, y=130)
    asel = b_sel(n6, F.COL_BLK2 + 480, 100, c_imm, c_hl, nn)
    n6.outvar(u"vAddr", asel, x=F.COL_OUT + 300, y=100)

    # ================= 7. PORT OPERANDA =================
    n7 = p.network(u"SET 7: PORT OPERANDA: chtenie/zapis' po vychislennomu adresu")
    n7.block(u"FB_Memory64K",
             [(u"PC", n7.invar(u"fbPCLatch.Q", y=30)),
              (u"Addr", n7.invar(u"vAddr", y=70)),
              (u"Rd", n7.invar(u"vCtl_Mem_Rd", y=110)),
              (u"Wr", n7.invar(u"vCtl_Mem_Wr", y=150)),
              (u"D_Bus", n7.invar(u"GVL_Bus.Bus_Data", y=190)),
              (u"SP_Addr", n7.invar(u"fbSP.SP", y=230)),
              (u"SP_Rd", n7.invar(u"vCtl_Is_RET", y=270)),
              (u"SP_Wr", n7.invar(u"vCtl_Is_CALL", y=310)),
              (u"SP_Data", n7.invar(u"fbPCLatch.Q", y=350))],
             [u"D_Out", u"Rd_Data", u"SP_Out", u"Bus_Drv"],
             x=F.COL_BLK2, y=30, instance=u"fbMem")
    n7.outvar(u"vMem_D_Out", n7.invar(u"fbMem.D_Out", y=30))
    n7.outvar(u"vFetch", n7.invar(u"vMem_D_Out", y=60), x=F.COL_OUT, y=400)
    n7.outvar(u"vMem_Bus_Drv", n7.invar(u"fbMem.Bus_Drv", y=30))
    n7.outvar(u"vMemDrv", n7.invar(u"vMem_Bus_Drv", y=60), x=F.COL_OUT, y=440)
    n7.outvar(u"vMem_Rd_Data", n7.invar(u"fbMem.Rd_Data", y=30))
    n7.outvar(u"vImm", n7.invar(u"vMem_Rd_Data", y=60), x=F.COL_OUT, y=480)
    n7.outvar(u"vMem_SP_Out", n7.invar(u"fbMem.SP_Out", y=30))
    n7.outvar(u"vSpRd", n7.invar(u"vMem_SP_Out", y=60), x=F.COL_OUT, y=520)

    # ================= 8. ALU =================
    n8 = p.network(u"SET 8: ALU")
    c_rd8 = n8.invar(u"vCtl_Mem_Rd", y=30)
    c_sv = n8.invar(u"fbRFRd.Src_Val", y=70)
    c_mv = n8.invar(u"vImm", y=110)
    #  selektor SEL dolzhen byt BOOL. Ran'she zdes stoyal vImm (BYTE), i
    #  kompilyator soobshchal "Nevozmozhno konvertirovat tip 'BOOL' v tip
    #  'USINT'". Smysl vetki: esli operand beretsya iz IR (Ctl_Imm_Mode),
    #  berem src1, inache -- konstantu 1 (dlya INC/DEC).
    c_iv = n8.invar(u"vCtl_Imm_Mode", y=150)
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
              (u"B", n8.invar(u"vSrc", y=460)),
              (u"Op", n8.invar(u"vCtl_ALU_Op", y=350)),
              (u"Carry_In", cin_b),
              (u"B_Forced", c_one),
              (u"IncDec", n8.invar(u"vCtl_IncDec", y=390))],
             [u"Y", u"Flag_S", u"Flag_Z", u"Flag_H", u"Flag_PV", u"Flag_N",
              u"Flag_C"],
             x=F.COL_BLK2 + 160, y=200, instance=u"fbALU")
    n8.outvar(u"vALU_Y", n8.invar(u"fbALU.Y", y=30))
    n8.outvar(u"vY", n8.invar(u"vALU_Y", y=60), x=F.COL_OUT, y=430)
    n8.outvar(u"GVL_Bus.Bus_Data", n8.invar(u"vALU_Y", y=90),
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
              (u"En", n9.invar(u"vCtl_Flags_En", y=350)),
              (u"Init_En", n9.invar(u"GVL_InitRegs.Init_En", y=390)),
              (u"Init_Val", n9.invar(u"GVL_InitRegs.Init_Vals[7]", y=430))],
             [u"F"], x=F.COL_BLK2, y=30, instance=u"fbFlags")
    n9.outvar(u"vFlags_F", n9.invar(u"fbFlags.F", y=30))
    n9.outvar(u"vF", n9.invar(u"vFlags_F", y=60), x=F.COL_OUT, y=390)
    n9.outvar(u"GVL_PLCVisu.F", n9.invar(u"vFlags_F", y=90), x=F.COL_OUT, y=430)

    # ================= 10. ZAPIS' V REGISTRY =================
    n10 = p.network(u"SET 10: ZAPIS' REZUL'TATA v registr")
    # --- vybor dannye dlya zapisi: init ili rezultat ALU ---
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
    #  Vetki Init_Vals -- tipa BYTE (elementy massiva Init_Vals).
    wr_init = sel_chain(n10, c_isd, n10.invar(u"GVL_InitRegs.Init_Vals[15]", y=1200),
                        val_cases, x=F.COL_BLK2, y0=640, ystep=34, tip=u"BYTE")
    wr_val = b_sel(n10, F.COL_BLK2 + 320, 110,
                   n10.invar(u"GVL_InitRegs.Init_En", y=1300),
                   n10.invar(u"vY", y=1340), wr_init)
    #  T A K T  Z A P I S I  =  Clk_Exec  I L I  Init_En.
    #  B Y L O: Clk := fbClock.Clk_Exec. No vo vremya initsializatsii
    #  Emu_Run = FALSE, znachit takt stoit i Clk_Exec ne voznikaet nikogda.
    #  Vnutri FB_RegFileZ80 strob zapisi -- eto AND(Wr_En, Clk), poetomu
    #  N I  O D I N  registr pri initsializatsii ne zapisyvalsya.
    #  Izmereno: Init_Vals zadany (A=12h, B=34h, ...), Init_En podan,
    #  a vse registry ostalis' nulevymi.
    clk_wr = b_or(n10, F.COL_BLK, 190,
                  n10.invar(u"fbClock.Clk_Exec", y=190),
                  n10.invar(u"GVL_InitRegs.Init_En", y=210))
    n10.block(u"FB_RegFileZ80",
              [(u"Sel_Dst", n10.invar(u"vCtl_Sel_Dst", y=30)),
               (u"Sel_Src", n10.invar(u"vCtl_Sel_Src", y=70)),
               (u"Wr_Val", wr_val),
               (u"Wr_En", n10.invar(u"vCtl_Wr_Enable", y=150)),
               (u"Clk", clk_wr),
               (u"CLR", n10.invar(u"GVL_Control.Emu_Reset", y=230)),
               (u"Mem_Rd", n10.invar(u"vMemDrv", y=270)),
               (u"Imm", n10.invar(u"vImm", y=310)),
               (u"Init_En", n10.invar(u"GVL_InitRegs.Init_En", y=350)),
               (u"Init_Sel_Dst", n10.invar(u"GVL_InitRegs.Init_Sel_Dst", y=390))],
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
    n11 = p.network(u"SET 11: STEK: SP i obmen s pamyat'yu")
    n11.block(u"FB_SP_StackZ80",
              [(u"Push", n11.invar(u"vCtl_Is_CALL", y=30)),
               (u"Pop", n11.invar(u"vCtl_Is_RET", y=70)),
               (u"Val_In", n11.invar(u"fbPCLatch.Q", y=110)),
               (u"Mem_Rd", n11.invar(u"vSpRd", y=150))],
              [u"SP", u"Val_Out", u"Addr", u"D_Out", u"Wr", u"Rd"],
              x=F.COL_BLK2, y=30, instance=u"fbSP")
    n11.outvar(u"vSP_SP", n11.invar(u"fbSP.SP", y=30))
    n11.outvar(u"GVL_PLCVisu.SP", n11.invar(u"vSP_SP", y=60),
               x=F.COL_OUT, y=400)

    # ================= 12. UPRAVLENIE POTOKOM =================
    n12 = p.network(u"SET 12: UPRAVLENIE: JP / CALL / RET / DJNZ / HALT")
    #  ZDES BYLA MERTVAYa SSYLKA na vCtl_Cond (tip BYTE). Ona ni v chem ne
    #  uchastvovala: uslovie perehoda schitaetsya nizhe iz flagov (bit 6
    #  registra F -- eto Z). No imenno iz-za nee kompilyator soobshchal
    #  "C32: Nevozmozhno konvertirovat tip 'USINT' v tip 'BOOL'".
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
               (u"Is_Jump", n12.invar(u"vCtl_Is_Jump", y=270)),
               (u"Is_Jr", n12.invar(u"vCtl_Is_DJNZ", y=310)),
               (u"Is_CALL", n12.invar(u"vCtl_Is_CALL", y=350)),
               (u"Is_RET", n12.invar(u"vCtl_Is_RET", y=390)),
               (u"Is_DJNZ", n12.invar(u"vCtl_Is_DJNZ", y=430)),
               (u"Is_HALT", n12.invar(u"vCtl_Is_HALT", y=470)),
               (u"Imm", n12.invar(u"vAddr", y=510)),
               (u"Ret_Addr", n12.invar(u"vSpRd", y=550)),
               (u"PC_Cur", n12.invar(u"fbPCLatch.Q", y=590)),
               (u"PC_Next", n12.invar(u"fbPC.PC_Next", y=630)),
               (u"B_Zero", n12.invar(u"vBZero", y=670)),
               (u"Emu_Reset", n12.invar(u"GVL_Control.Emu_Reset", y=710))],
              [u"PC_New", u"PC_Load", u"Halted", u"Inc_By"],
              x=F.COL_BLK2 + 160, y=30, instance=u"fbCtl")
    n12.outvar(u"vCtl_PC_New", n12.invar(u"fbCtl.PC_New", y=30))
    n12.outvar(u"vPCNew", n12.invar(u"vCtl_PC_New", y=60), x=F.COL_OUT, y=750)
    n12.outvar(u"vCtl_PC_Load", n12.invar(u"fbCtl.PC_Load", y=30))
    n12.outvar(u"vPCLoad", n12.invar(u"vCtl_PC_Load", y=60), x=F.COL_OUT, y=790)
    n12.outvar(u"vCtl_Inc_By", n12.invar(u"fbCtl.Inc_By", y=30))
    n12.outvar(u"vIncBy", n12.invar(u"vCtl_Inc_By", y=60), x=F.COL_OUT, y=830)
    n12.outvar(u"vCtl_Halted", n12.invar(u"fbCtl.Halted", y=30))
    n12.outvar(u"GVL_PLCVisu.Halted", n12.invar(u"vCtl_Halted", y=60),
               x=F.COL_OUT, y=870)

    # ================= 13. PC =================
    n13 = p.network(u"SET 13: PC: sleduyushchaya komanda")
    #  ============ Z A G R U Z K A  N A Ch A L N O G O  P C  ============
    #  B Y L O  T A K: na vhody FB_PC_Z80 podavalis tolko vPCLoad i vPCNew
    #  (upravlenie potokom: JP / CALL / RET / DJNZ). A GVL_InitRegs.Init_PC,
    #  kuda programma testov kladet startovyj adres, N E  Ch I T A L S Ya
    #  N I G D E v PLC_PRG -- provereno poiskom po vsemu generatoru.
    #  Posledstvie na real nom progone: kazhdyj test nachinalsya s PC = 0,
    #  a ne s Init_PC (dlya testov s Init_PC = 0120h i 0140h eto oshibka
    #  v samom nachale), i vse 40 proverok valilis.
    #  T E P E R': pri Init_En schetchik gruzit Init_PC, i etot zhe Init_En
    #  razreshaet zapis' v zashchelku, chtoby novoe znachenie popalo tuda
    #  srazu, a ne zhdat fazy vykonaniya.
    c_load = n13.invar(u"vPCLoad", y=70)
    c_new = n13.invar(u"vPCNew", y=30)
    c_init_ld = n13.invar(u"GVL_InitRegs.Init_En", y=390)
    c_init_sel = n13.invar(u"GVL_InitRegs.Init_En", y=430)
    c_ipc = n13.invar(u"GVL_InitRegs.Init_PC", y=470)
    #  gruzit' = (upravlenie potokom) ILI (initsializatsiya)
    load_all = b_or(n13, F.COL_BLK2 + 160, 390, c_load, c_init_ld)
    #  chto gruzit': pri Init_En -- Init_PC, inache -- vPCNew
    val_all = b_sel(n13, F.COL_BLK2 + 320, 430, c_init_sel, c_new, c_ipc)
    pc = n13.block(u"FB_PC_Z80",
                   [(u"Load_Val", val_all),
                    (u"Load", load_all),
                    #  I N K R E M E N T -- T O L K O  V  F A Z E  V Y P O L N E N I Ya.
                    #  Bylo const(TRUE): schetchik prirashchivalsya K A Zh D Y J  S K A N,
                    #  a komanda zanimaet DVA skana (dekodirovanie i vypolnenie).
                    #  Znachit za odnu komandu PC uskakal na dve pozicii i pereskakival
                    #  bajty -- v tom chisle HALT. Izmereno: programma "4 NOP i HALT
                    #  po adresu 4" nikogda ne ostanavlivalas'.
                    (u"Inc", n13.invar(u"fbClock.Clk_Exec", y=110)),
                    (u"Inc_By", n13.invar(u"vIncBy", y=150))],
                   [u"Addr", u"PC_Next"], x=F.COL_BLK + 160, y=30,
                   instance=u"fbPC")
    #  zapis' v zashchelku: po faze vykonaniya ILI poInit_En
    c_exec = n13.invar(u"fbClock.Clk_Exec", y=190)
    c_init_lat = n13.invar(u"GVL_InitRegs.Init_En", y=510)
    lat_en = b_or(n13, F.COL_BLK2 + 480, 510, c_exec, c_init_lat)
    latch = n13.block(u"FB_Reg16",
                      [(u"D", pc.out(u"Addr")),
                       (u"EN", lat_en),
                       (u"CLR", n13.invar(u"GVL_Control.Emu_Reset", y=230))],
                      [u"Q"], x=F.COL_BLK2 + 640, y=30, instance=u"fbPCLatch")
    n13.outvar(u"GVL_PLCVisu.PC", latch, x=F.COL_OUT + 300, y=30)
    n13.outvar(u"vPC_PC_Next", n13.invar(u"fbPC.PC_Next", y=30))
    n13.outvar(u"vPCNext", n13.invar(u"vPC_PC_Next", y=60),
               x=F.COL_OUT, y=70)

    # ================= 15. APPARATNYY VVOD/VYVOD PLK =================
    # ZACheM otdel nye seti na kazhdyy vyhod: sm. poyasnenie v
    # generator/probe/patch_net_split.py -- biblioteka schitaet ispolzovaniya
    # BLOKA, poetomu v odnoy seti mozhno prochitat tolko ODIN ego vyhod.
    #
    # POCHEMU voobshche otdel nyy blok: instruktsiya Z80 ispolnyaetsya vnutri
    # skana, a fizicheskie %I/%Q PLK obnovlyayutsya tolko na granitse skana.
    # Vse vneshnie dannye prohodyat cherez bufery GVL_HW_Buffer.
    n15 = p.network(u"SET 15: APPARATNYY VVOD PLK: upakovka vhodov")
    hw = n15.block(u"FB_HW_IO_PLC",
                   [(u"DI_0", n15.invar(u"PLC_DI_0", y=30)),
                    (u"DI_1", n15.invar(u"PLC_DI_1", y=60)),
                    (u"DI_2", n15.invar(u"PLC_DI_2", y=90)),
                    (u"DI_3", n15.invar(u"PLC_DI_3", y=120)),
                    (u"DI_4", n15.invar(u"PLC_DI_4", y=150)),
                    (u"DI_5", n15.invar(u"PLC_DI_5", y=180)),
                    (u"DI_6", n15.invar(u"PLC_DI_6", y=210)),
                    (u"DI_7", n15.invar(u"PLC_DI_7", y=240)),
                    (u"AI_0", n15.invar(u"PLC_AI_0", y=270)),
                    (u"AI_1", n15.invar(u"PLC_AI_1", y=300)),
                    (u"Out_DO", n15.invar(u"vOutDO", y=330)),
                    (u"Out_AO0", n15.invar(u"vOutAO0", y=360)),
                    (u"Out_AO1", n15.invar(u"vOutAO1", y=390))],
                   [u"In_DI", u"In_AI0", u"In_AI1",
                    u"DO_0", u"DO_1", u"DO_2", u"DO_3",
                    u"DO_4", u"DO_5", u"DO_6", u"DO_7",
                    u"AO_0", u"AO_1"],
                   x=F.COL_BLK2, y=30, instance=u"fbHW")
    n15.outvar(u"vInDi", hw.out(u"In_DI"), x=F.COL_OUT + 600, y=30)

    n15b = p.network(u"SET 15b: analogovye vhody")
    n15b.outvar(u"vInAI0", hw.out(u"In_AI0"), x=F.COL_OUT + 600, y=30)

    n15c = p.network(u"SET 15c: vtoroy analogovyy vhod")
    n15c.outvar(u"vInAI1", hw.out(u"In_AI1"), x=F.COL_OUT + 600, y=30)

    n15d = p.network(u"SET 15d: diskretnye vyhody PLK (8 kanalov)")
    for k in range(8):
        n15d.outvar(u"PLC_DO_%d" % k, hw.out(u"DO_%d" % k),
                    x=F.COL_OUT + 600, y=30 + k * 30)

    n15e = p.network(u"SET 15e: analogovye vyhody PLK")
    n15e.outvar(u"PLC_AO_0", hw.out(u"AO_0"), x=F.COL_OUT + 600, y=30)

    n15f = p.network(u"SET 15f: vtoroy analogovyy vyhod PLK")
    n15f.outvar(u"PLC_AO_1", hw.out(u"AO_1"), x=F.COL_OUT + 600, y=30)

    # snimok vhodov v bufery (chitaem po imeni, chtoby byl odin potrebitel)
    n15g = p.network(u"SET 15g: bufery vhodov dlya Z80")
    n15g.outvar(u"GVL_HW_Buffer.HW_In_DI",
                n15g.invar(u"vInDi", y=30), x=F.COL_OUT, y=30)
    n15g.outvar(u"GVL_HW_Buffer.HW_In_AI0",
                n15g.invar(u"vInAI0", y=70), x=F.COL_OUT, y=70)
    n15g.outvar(u"GVL_HW_Buffer.HW_In_AI1",
                n15g.invar(u"vInAI1", y=110), x=F.COL_OUT, y=110)

    # ================= 16. I/O-PORTY Z80 =================
    n16 = p.network(u"SET 16: I/O-PORTY: adres porta")
    c_ioen = n16.invar(u"vCtl_IO_Rd", y=30)
    c_iowr = n16.invar(u"vCtl_IO_Wr", y=60)
    c_n = n16.invar(u"vImm", y=90)
    #  P O Ch E M U  ZDES' OTDEL'NAYa PEREMENNAYa, A NE b_or(...) NAPRYaMUYu.
    #  Usloviem SEL dolzhno byt znachenie tipa BOOL. Esli podat' tuda rezul'tat
    #  bloka OR nad dvumya BOOL, CODESYS vyvodit tip OR kak BYTE (blok OR
    #  obobshchennyy, ANY_BIT) i otvergaet ego kak uslovie:
    #      C32: Nevozmozhno konvertirovat tip 'USINT' v tip 'BOOL'
    #  Eto byli 12 oshibok iz 17. Cherez obychnuyu peremennuyu BOOL takogo
    #  ne proishodit: prisvaivanie srazu zadaet tip.
    n16.outvar(u"vIOEn", b_or(n16, F.COL_BLK2, 30, c_ioen, c_iowr),
               x=F.COL_OUT, y=30)
    io_addr = b_sel(n16, F.COL_BLK2, 60,
                    n16.invar(u"vIOEn", y=44),
                    n16.const(u"0", y=74), c_n)
    n16.outvar(u"vIOAddr", io_addr, x=F.COL_OUT + 300, y=60)
    io = n16.block(u"FB_IO_Ports",
                   [(u"Addr", io_addr),
                    (u"D_Write", n16.invar(u"fbRF.A", y=120)),
                    (u"Rd", c_ioen),
                    (u"Wr", c_iowr),
                    (u"In_DI", n16.invar(u"GVL_HW_Buffer.HW_In_DI", y=150)),
                    (u"In_AI0", n16.invar(u"GVL_HW_Buffer.HW_In_AI0", y=180)),
                    (u"In_AI1", n16.invar(u"GVL_HW_Buffer.HW_In_AI1", y=210)),
                    (u"Con_In", n16.invar(u"GVL_CPM.Console_In", y=240)),
                    (u"Con_Ready", n16.invar(u"GVL_CPM.Console_InEn", y=270)),
                    (u"Cpm_Ready", n16.invar(u"GVL_CPM.Cpm_Loaded", y=300))],
                   [u"Rd_Data", u"Out_DO", u"Out_AO0", u"Out_AO1",
                    u"Con_Out", u"Con_Wr", u"Con_Port", u"Halt_Req"],
                   x=F.COL_BLK2 + 160, y=120, instance=u"fbIO")
    n16.outvar(u"vIOData", io.out(u"Rd_Data"), x=F.COL_OUT + 600, y=30)

    n16b = p.network(u"SET 16b: vyhod portov na vyhody PLK")
    n16b.outvar(u"vOutDO", io.out(u"Out_DO"), x=F.COL_OUT + 600, y=30)

    n16c = p.network(u"SET 16c: vyhod portov: analogovyy kanal 0")
    n16c.outvar(u"vOutAO0", io.out(u"Out_AO0"), x=F.COL_OUT + 600, y=30)

    n16d = p.network(u"SET 16d: vyhod portov: analogovyy kanal 1")
    n16d.outvar(u"vOutAO1", io.out(u"Out_AO1"), x=F.COL_OUT + 600, y=30)

    n16e = p.network(u"SET 16e: konsol CP/M i zerkalo shin")
    n16e.outvar(u"GVL_IO.Bus_IO_Data", n16.invar(u"vIOData", y=30),
                x=F.COL_OUT, y=30)
    n16e.outvar(u"GVL_IO.Bus_IO_Addr", n16.invar(u"vIOAddr", y=70),
                x=F.COL_OUT, y=70)

    # ================= 17. BIOS =================
    n17 = p.network(u"SET 17: BIOS: zona adresov i konsol")
    c_pc17 = n17.invar(u"fbPCLatch.Q", y=30)
    is_bios = n17.block(u"GE", [(PIN1, c_pc17),
                                (PIN2, n17.const(u"WORD#16#FA00", y=44))],
                        [POUT], x=F.COL_BLK2, y=30)
    is_bios2 = n17.block(u"LT", [(PIN1, c_pc17),
                                 (PIN2, n17.const(u"WORD#16#FB00", y=74))],
                         [POUT], x=F.COL_BLK2, y=60)
    bios_zone = b_and(n17, F.COL_BLK2 + 160, 45, is_bios, is_bios2)
    n17.outvar(u"vIsBIOS", bios_zone, x=F.COL_OUT, y=45)
    bios = n17.block(u"FB_CPM_BIOS",
                     [(u"Addr", c_pc17),
                      (u"Con_In", n17.invar(u"GVL_CPM.Console_In", y=120)),
                      (u"Con_Rdy", n17.invar(u"GVL_CPM.Console_InEn", y=150))],
                     [u"Con_Out", u"Con_Wr", u"Con_Rd", u"Ret_HL",
                      u"Is_Wboot", u"Done"],
                     x=F.COL_BLK2 + 320, y=120, instance=u"fbBIOS")
    n17.outvar(u"vBiosOut", bios.out(u"Con_Out"), x=F.COL_OUT + 600, y=120)

    n17b = p.network(u"SET 17b: konsol BIOS: strob vyvoda")
    n17b.outvar(u"vBiosWr", bios.out(u"Con_Wr"), x=F.COL_OUT + 600, y=30)

    n17c = p.network(u"SET 17c: konsol BIOS: zapros vvoda")
    n17c.outvar(u"vBiosRd", bios.out(u"Con_Rd"), x=F.COL_OUT + 600, y=30)

    # ================= 18. PEREKhVAT BDOS =================
    # IMENNO TAK RABOTAET PEREKhVAT: programma delaet CALL 0F000h,
    # na shinu adresa popadaet 0F000h, i my eto vidim.
    n18 = p.network(u"SET 18: PEREKhVAT BDOS: PC = 0F000h")
    is_bdos = b_eq(n18, F.COL_BLK2, 30,
                   n18.invar(u"fbPCLatch.Q", y=30),
                   n18.const(u"WORD#16#F000", y=44))
    #  Vyvodim v GVL, a ne v lokalnuyu peremennuyu: etot zhe signal nuzhen
    #  programme PRG_CPM_BDOS, a lokalnye peremennye odnoj programmy
    #  dlya drugoj ne vidny (sm. poyasnenie v GVL_CPM).
    n18.outvar(u"GVL_CPM.Bdos_Hit", is_bdos, x=F.COL_OUT, y=30)

    # ================= 14. R =================
    n14 = p.network(u"SET 14: REGISTR R: inkrementiruetsya kazhduyu komandu")
    #  R -- schetchik obrashcheniy k pamyati. On dolzhen ne tolko zapominat'sya,
    #  no i U V E L I Ch I V A T 'S Ya na kazhdoj komande, poetomu na vhod D
    #  idet R+1, a ne vneshnyaya peremennaya:
    #      R_Next := R + 1;  FB_Reg8 zapisyvaet R_Next po frontu Clk_Exec.
    #  Ran'she zdes stoyala ssylka na GVL_PLCVisu.R_Next -- takogo imeni net
    #  ni v odnoj GVL, i kompilyator soobshchal
    #  "C4: 'R' ne yavlyaetsya komponentom 'GVL_PLCVisu'".
    r_inc = b_add(n14, F.COL_BLK, 30,
                  b_b2w(n14, F.COL_BLK, 30, n14.invar(u"GVL_PLCVisu.R_Reg", y=30)),
                  n14.const(u"WORD#1", y=44))
    r_next = b_w2b(n14, F.COL_BLK + 160, 30, r_inc)
    n14.block(u"FB_Reg8",
              [(u"D", r_next),
               (u"EN", n14.invar(u"fbClock.Clk_Exec", y=70)),
               (u"CLR", n14.invar(u"GVL_Control.Emu_Reset", y=110))],
              [u"Q"], x=F.COL_BLK2, y=30, instance=u"fbR")
    n14.outvar(u"vR_Q", n14.invar(u"fbR.Q", y=30))
    n14.outvar(u"GVL_PLCVisu.R_Reg", n14.invar(u"vR_Q", y=60),
               x=F.COL_OUT, y=150)
    #  O G R A N I Ch E N I E  Ch I S L A  S E T E J  D L Ya  B I S E K C I I.
    #  Z80_PLC_NETS=N ostawlyaet tolko pervye N setej PLC_PRG. Nuzhno, chtoby
    #  najti, posle kakoy seti poyavlyayutsya oshibki C32: kompilyator ne
    #  soobshchaet ni imeni POU, ni nomera seti, a perebirat vse seti vruchnuyu
    #  slishkom dolgo. Seti nezavisimy drug ot druga po ssylkam, poetsto
    #  obrezka hvosta bezopasna (nikakih "visyashchih" vhodov ne voznikaet).
    _nets = os.environ.get(u"Z80_PLC_NETS")
    if _nets:
        try:
            p.networks = p.networks[:int(_nets)]
        except Exception:                                      # noqa: BLE001
            pass
    return p


def mk_fb_hw_io():
    u"""FB_HW_IO_PLC -- sinkhronizatsiya s fizicheskimi vhodami/vyhodami PLK.

    VHODY (fizicheskie kanaly PLK):
        DI_* : BOOL  -- diskretnye vhody %IX0.0..%IX0.7
        AI_0, AI_1 : INT -- analogovye vhody %IW0, %IW1
        Out_DO : BYTE -- chto vyvesti na diskretnye vyhody
        Out_AO0, Out_AO1 : WORD -- chto vyvesti na analogovye vyhody
    VYHODY (snimok dlya Z80):
        In_DI  : BYTE -- upakovannye diskretnye vhody
        In_AI0, In_AI1 : WORD -- analogovye vhody
        DO_*   : BOOL -- fizicheskie vyhody %QX0.0..%QX0.7
        AO_0, AO_1 : INT -- fizicheskie vyhody %QW0, %QW1

    POVEDENIE: upakovka vhodov idet cherez FB_BitUnpack8-style logiku
    (raspakovka/upakovka bitov -- ZDES), vyhodnye bity raspredelyayutsya
    po odinichnym kanalam. Blok vyzyvaetsya ODIN raz: v nachale skana
    chitaet vhody, v konce -- pishet vyhody (sm. PLC_PRG, seti 1 i 15).
    """
    p = F.Pou(u"FB_HW_IO_PLC", u"functionBlock",
              u"Apparatnyy interfeys PLK: upakovka vhodov i raspredelenie vyhodov.\n"
              u"Vse obmen s %I/%Q prohodit cherez etot blok.")
    # --- vhody ot PLK ---
    din = []
    for k in range(8):
        din.append(p.var_in(u"DI_%d" % k, u"BOOL", u"diskretnyy vhod %%IX0.%d" % k))
    p.var_in(u"AI_0", u"INT", u"analogovyy vhod %%IW0")
    p.var_in(u"AI_1", u"INT", u"analogovyy vhod %%IW1")
    p.var_in(u"Out_DO", u"BYTE", u"znachenie dlya diskretnyh vyhodov")
    p.var_in(u"Out_AO0", u"WORD", u"znachenie dlya %%QW0")
    p.var_in(u"Out_AO1", u"WORD", u"znachenie dlya %%QW1")
    # --- vyhody dlya Z80 ---
    p.var_out(u"In_DI", u"BYTE", u"upakovannye diskretnye vhody")
    p.var_out(u"In_AI0", u"WORD", u"analogovyy vhod 0")
    p.var_out(u"In_AI1", u"WORD", u"analogovyy vhod 1")
    for k in range(8):
        p.var_out(u"DO_%d" % k, u"BOOL", u"diskretnyy vyhod %%QX0.%d" % k)
    p.var_out(u"AO_0", u"INT", u"analogovyy vyhod %%QW0")
    p.var_out(u"AO_1", u"INT", u"analogovyy vyhod %%QW1")

    # --- set 1: upakovka diskretnyh vhodov v bajt ---
    # ZDES proishodit upakovka BOOL -> BYTE (obratnaya k raspakovke v FB_BitUnpack8)
    #  Promezhutochnye peremennye tipa BYTE: konversiya BOOL -> BYTE daet
    #  USINT, i pryamaya podacha ego v SHL/ADD (obobshchennye bloki)
    #  privodit k C32. Sm. b_bool2byte().
    n1 = p.network(u"Upakovka diskretnyh vhodov: BOOL -> BYTE")
    acc = None
    for k in range(8):
        c = n1.invar(u"DI_%d" % k, y=30 + k * 40)
        tb = b_bool2byte(n1, u"vPack_%d" % k, F.COL_BLK, 30 + k * 40, c)
        if k == 0:
            acc = tb
        else:
            sh = b_shl(n1, F.COL_BLK2 + 120, 30 + k * 40, tb,
                       n1.const(u"%d" % k, y=44 + k * 40))
            acc = b_add(n1, F.COL_BLK2 + 280, 30 + k * 40, acc, sh)
    n1.outvar(u"In_DI", acc, x=F.COL_OUT + 300, y=30)

    # --- set 2: peredacha analogovyh vhodov ---
    n2 = p.network(u"Analogovye vhody: INT -> WORD")
    a0 = n2.block(u"INT_TO_WORD", [(PINU, n2.invar(u"AI_0", y=30))], [POUT],
                  x=F.COL_BLK, y=30)
    n2.outvar(u"In_AI0", a0, x=F.COL_OUT, y=30)
    a1 = n2.block(u"INT_TO_WORD", [(PINU, n2.invar(u"AI_1", y=90))], [POUT],
                  x=F.COL_BLK, y=90)
    n2.outvar(u"In_AI1", a1, x=F.COL_OUT, y=90)

    # --- set 3: raspredelenie diskretnyh vyhodov po kanalam ---
    # ZDES proishodit raspakovka BYTE -> otdel nye BOOL (to zhe, chto FB_BitUnpack8)
    n3 = p.network(u"Raspredelenie diskretnyh vyhodov: BYTE -> BOOL")
    cdo = n3.invar(u"Out_DO", y=30)
    for k in range(8):
        msk = n3.const(u"16#%02X" % (1 << k), y=30 + k * 50)
        an = n3.block(u"AND", [(PIN1, cdo), (PIN2, msk)], [POUT],
                      x=F.COL_BLK, y=30 + k * 50)
        nz = n3.block(u"NE", [(PIN1, an), (PIN2, n3.const(u"0", y=44 + k * 50))],
                      [POUT], x=F.COL_BLK2, y=30 + k * 50)
        n3.outvar(u"DO_%d" % k, nz, x=F.COL_OUT, y=30 + k * 50)

    # --- set 4: analogovye vyhody ---
    n4 = p.network(u"Analogovye vyhody: WORD -> INT")
    o0 = n4.block(u"WORD_TO_INT", [(PINU, n4.invar(u"Out_AO0", y=30))], [POUT],
                  x=F.COL_BLK, y=30)
    n4.outvar(u"AO_0", o0, x=F.COL_OUT, y=30)
    o1 = n4.block(u"WORD_TO_INT", [(PINU, n4.invar(u"Out_AO1", y=90))], [POUT],
                  x=F.COL_BLK, y=90)
    n4.outvar(u"AO_1", o1, x=F.COL_OUT, y=90)
    return p



def mk_io_ports():
    u"""FB_IO_Ports -- 256 I/O-portov Z80, privyazannyh k PLK i konsoli.

    VHODY:
        Addr     : BYTE -- adres porta (iz Ctl_Imm_Mode ? n : 0)
        D_Write  : BYTE -- chto zapisat pri OUT
        Rd       : BOOL -- strob chteniya (IN)
        Wr       : BOOL -- strob zapisi (OUT)
        In_DI    : BYTE -- diskretnye vhody PLK (iz FB_HW_IO_PLC)
        In_AI0   : WORD -- analogovyy vhod 0
        In_AI1   : WORD -- analogovyy vhod 1
        Con_In   : BYTE -- simvol ot terminala CP/M
        Con_Ready: BOOL -- est li simvol
        Cpm_Ready: BOOL -- zagruzhen li CP/M
    VYHODY:
        Rd_Data  : BYTE -- chto vernut na shinu I/O
        Out_DO   : BYTE -- chto vyvesti na diskretnye vyhody PLK
        Out_AO0  : WORD -- chto vyvesti na %QW0
        Out_AO1  : WORD -- chto vyvesti na %QW1
        Con_Out  : BYTE -- simvol dlya konsoli
        Con_Wr   : BOOL -- strob vyvoda simvola
        Con_Port : BYTE -- nomer konsolnogo porta (dlya otladki)
        Halt_Req : BOOL -- programma poprosila ostanovki

    KARTA PORTOV -- sm. GVL_IO.
    """
    p = F.Pou(u"FB_IO_Ports", u"functionBlock",
              u"256 I/O-portov Z80. Privyazka portov k apparatnym buferam PLK\n"
              u"i konsoli CP/M realizovana cepochkoy SEL po adresu porta.")
    addr = p.var_in(u"Addr", u"BYTE", u"adres porta")
    dwr = p.var_in(u"D_Write", u"BYTE", u"dannye dlya zapisi")
    rd = p.var_in(u"Rd", u"BOOL", u"strob chteniya")
    wr = p.var_in(u"Wr", u"BOOL", u"strob zapisi")
    c_di = p.var_in(u"In_DI", u"BYTE", u"diskretnye vhody PLK")
    c_ai0 = p.var_in(u"In_AI0", u"WORD", u"analogovyy vhod 0")
    c_ai1 = p.var_in(u"In_AI1", u"WORD", u"analogovyy vhod 1")
    c_cin = p.var_in(u"Con_In", u"BYTE", u"simvol ot terminala")
    c_crdy = p.var_in(u"Con_Ready", u"BOOL", u"est simvol")
    c_cpm = p.var_in(u"Cpm_Ready", u"BOOL", u"CP/M zagruzhen")

    p.var_out(u"Rd_Data", u"BYTE", u"chto vernut na shinu I/O")
    p.var_out(u"Out_DO", u"BYTE", u"diskretnye vyhody PLK")
    p.var_out(u"Out_AO0", u"WORD", u"analogovyy vyhod 0")
    p.var_out(u"Out_AO1", u"WORD", u"analogovyy vyhod 1")
    p.var_out(u"Con_Out", u"BYTE", u"simvol dlya konsoli")
    p.var_out(u"Con_Wr", u"BOOL", u"strob vyvoda")
    p.var_out(u"Con_Port", u"BYTE", u"nomer konsolnogo porta")
    p.var_out(u"Halt_Req", u"BOOL", u"zapros ostanovki")
    #  Promezhutochnye BYTE dlya konversii BOOL -> BYTE: inache
    #  vyhod USINT ne soglasuetsya s BYTE vetok v cepochke SEL (C32).

    # ================= SET 1: CHTENIE PORTOV =================
    # Cepochka SEL po adresu: kazhdyy port -- otdel noe uslovie.
    n1 = p.network(u"CHTENIE portov: cepochka SEL po adresu")
    c_addr = n1.invar(addr, y=30)
    c_di1 = n1.invar(c_di, y=60)
    c_ai0a = n1.invar(c_ai0, y=90)
    c_ai0b = n1.invar(c_ai0, y=120)
    c_ai1a = n1.invar(c_ai1, y=150)
    c_ai1b = n1.invar(c_ai1, y=180)
    c_cin1 = n1.invar(c_cin, y=210)
    c_crdy1 = n1.invar(c_crdy, y=240)
    c_cpm1 = n1.invar(c_cpm, y=270)

    lo0 = b_w2b(n1, F.COL_BLK, 90, c_ai0a)
    #  PORYaDOK VAZhEN: sdvig delaetsya po WORD, i tolko POTOM rezul tat
    #  suzhaetsya do bajta. Esli suzit ranshe, kompilyator preduprezhdaet
    #  "C308: Sdvig na 8 prevyshaet razmer tipa BYTE" -- i starshij bajt
    #  poteryalsya by.
    hi0 = b_w2b(n1, F.COL_BLK, 120,
                b_shr(n1, F.COL_BLK, 120, c_ai0b, n1.const(u"8", y=134)))
    lo1 = b_w2b(n1, F.COL_BLK, 150, c_ai1a)
    hi1 = b_w2b(n1, F.COL_BLK, 180,
                b_shr(n1, F.COL_BLK, 180, c_ai1b, n1.const(u"8", y=194)))
    # status konsoli: bit 0 = est simvol
    #  Cherez yavnuyu peremennuyu BYTE: vyhod BOOL_TO_BYTE dlya CODESYS --
    #  eto USINT, i v cepochke SEL on ne soglasuetsya s BYTE drugih vetok
    #  ("C32: Nevozmozhno konvertirovat tip 'BOOL' v tip 'USINT'").
    st = b_bool2byte(n1, u"vConRdy", F.COL_BLK, 240, c_crdy1)
    # status CP/M: bit 0 = zagruzhen
    stc = b_bool2byte(n1, u"vCpmRdy", F.COL_BLK, 270, c_cpm1)

    cases = []
    yc = 30
    # port 00h -- diskretnye vhody
    cases.append((b_eq(n1, F.COL_BLK2, 30, c_addr, n1.const(u"16#00", y=44)), c_di1))
    # 02h/03h -- analogovyy vhod 0
    cases.append((b_eq(n1, F.COL_BLK2, 70, c_addr, n1.const(u"16#02", y=84)), lo0))
    cases.append((b_eq(n1, F.COL_BLK2, 110, c_addr, n1.const(u"16#03", y=124)), hi0))
    # 06h/07h -- analogovyy vhod 1
    cases.append((b_eq(n1, F.COL_BLK2, 150, c_addr, n1.const(u"16#06", y=164)), lo1))
    cases.append((b_eq(n1, F.COL_BLK2, 190, c_addr, n1.const(u"16#07", y=204)), hi1))
    # 10h -- status konsoli
    cases.append((b_eq(n1, F.COL_BLK2, 230, c_addr, n1.const(u"16#10", y=244)), st))
    # 11h -- prinyat simvol
    cases.append((b_eq(n1, F.COL_BLK2, 270, c_addr, n1.const(u"16#11", y=284)), c_cin1))
    # 21h -- sostoyanie CP/M
    cases.append((b_eq(n1, F.COL_BLK2, 310, c_addr, n1.const(u"16#21", y=324)), stc))

    #  Rd_Data -- BYTE: vse vetki privodim k BYTE yavno.
    #  Rezervnaya vetka -- T I P I Z I R O V A N N Y J  liter al BYTE#0.
    #  P O Ch E M U. Bezrisovyy "0" v obobshchennom vhode SEL ne imeet tipa,
    #  i CODESYS vybiraet dlya vsej cepochki USINT; posle etogo uslovie G
    #  (BOOL) uzhe ne soglasuetsya, i sborka daet
    #      C32: Nevozmozhno konvertirovat tip 'BOOL' v tip 'USINT'.
    rdata = sel_chain(n1, c_addr, n1.const(u"BYTE#0", y=350), cases,
                      x=F.COL_BLK2 + 160, y0=30, ystep=40, tip=u"BYTE")
    n1.outvar(u"Rd_Data", rdata, x=F.COL_OUT + 400, y=30)

    # ================= SET 2: ZAPIS' PORTOV =================
    n2 = p.network(u"ZAPIS portov: raspredelenie po adresam")
    c_addr2 = n2.invar(addr, y=30)
    c_dwr = n2.invar(dwr, y=60)
    c_wr = n2.invar(wr, y=90)
    c_wr2 = n2.invar(wr, y=120)
    c_wr3 = n2.invar(wr, y=150)
    c_wr4 = n2.invar(wr, y=180)
    c_wr5 = n2.invar(wr, y=210)
    c_dwr2 = n2.invar(dwr, y=240)
    c_dwr3 = n2.invar(dwr, y=270)

    # diskretnye vyhody: port 01h
    is01 = b_eq(n2, F.COL_BLK2, 30, c_addr2, n2.const(u"16#01", y=44))
    we01 = b_and(n2, F.COL_BLK2 + 160, 30, c_wr, is01)
    #  Vetka IN0 -- T I P I Z I R O V A N N Y J  nol' (BYTE#0), sm. poyasnenie
    #  u rezervnoj vetki Rd_Data vyshe.
    n2.outvar(u"Out_DO", b_sel(n2, F.COL_BLK2 + 320, 30, we01,
                               n2.const(u"BYTE#0", y=44), c_dwr),
              x=F.COL_OUT + 300, y=30)
    # vyhod 20h -- zapros ostanovki: bit 0
    is20 = b_eq(n2, F.COL_BLK2, 90, c_addr2, n2.const(u"16#20", y=104))
    we20 = b_and(n2, F.COL_BLK2 + 160, 90, c_wr2, is20)
    b0 = n2.block(u"AND", [(PIN1, c_dwr2), (PIN2, n2.const(u"16#01", y=118))],
                  [POUT], x=F.COL_BLK2 + 320, y=90)
    #  Ch T O  Z D E S'  B Y L O  N E  T A K. Stoyalo
    #      Halt_Req := we20 AND b0
    #  gde we20 -- BOOL, a b0 -- BYTE (rezul tat AND dvuh bajtov). AND nad
    #  raznymi tipami kompilyator otvergaet; v otchyote eto vyglyadelo kak
    #  "C32: Nevozmozhno konvertirovat tip 'BOOL' v tip 'USINT'".
    #  P R A V I L' N O: uslovie "bit 0 ustanovlen" -- eto sravnenie b0 s nulem,
    #  i tolko potom logocheskoe I so strobom zapisi.
    b0set = n2.block(u"NE", [(PIN1, b0), (PIN2, n2.const(u"0", y=132))],
                     [POUT], x=F.COL_BLK2 + 400, y=90)
    n2.outvar(u"Halt_Req", b_and(n2, F.COL_BLK2 + 560, 90, we20, b0set),
              x=F.COL_OUT + 300, y=90)
    # vyhod 12h -- konsol
    is12 = b_eq(n2, F.COL_BLK2, 150, c_addr2, n2.const(u"16#12", y=164))
    we12 = b_and(n2, F.COL_BLK2 + 160, 150, c_wr3, is12)
    n2.outvar(u"Con_Wr", we12, x=F.COL_OUT + 300, y=150)
    n2.outvar(u"Con_Out", c_dwr3, x=F.COL_OUT + 300, y=190)
    n2.outvar(u"Con_Port", n2.const(u"16#12", y=230), x=F.COL_OUT + 300, y=230)

    # ================= SET 3: SBORKA ANALOGOVYH VYHODOV =================
    # Vyhod 04h/05h -- mladshij i starshij bajty AO0; 08h/09h -- AO1.
    # Znacheniya zapominayutsya v otdel nyh registrah i sobirautsya v slovo.
    n3 = p.network(u"Sborka analogovyh vyhodov iz dvuh portov")
    # Ekzemplyary FB_Reg16 dlya sklejki dvuh 8-bitnyh portov v odno WORD.
    # Bez etih obyavlenij kompilyator soobshchaet
    # "'fbAO0Lo' ne yavlyaetsya ekzemplyarom 'FB_Reg16'".
    for k in (0, 1):
        p.var(u"fbAO%dLo" % k, u"FB_Reg16", u"mladshij bajt analogovogo vyhoda %d" % k)
        p.var(u"fbAO%dHi" % k, u"FB_Reg16", u"starshij bajt analogovogo vyhoda %d" % k)
    for k, (plo, phi) in enumerate(((u"16#04", u"16#05"), (u"16#08", u"16#09"))):
        c_a3 = n3.invar(addr, y=30 + k * 200)
        c_w3 = n3.invar(wr, y=60 + k * 200)
        c_d3 = n3.invar(dwr, y=90 + k * 200)
        islo = b_eq(n3, F.COL_BLK2, 30 + k * 200, c_a3, n3.const(plo, y=44 + k * 200))
        we_lo = b_and(n3, F.COL_BLK2 + 160, 30 + k * 200, c_w3, islo)
        sh_lo = b_shl(n3, F.COL_BLK2 + 320, 30 + k * 200,
                      b_b2w(n3, F.COL_BLK2 + 320, 30 + k * 200, c_d3),
                      n3.const(u"0", y=44 + k * 200))
        ishi = b_eq(n3, F.COL_BLK2, 120 + k * 200, c_a3, n3.const(phi, y=134 + k * 200))
        we_hi = b_and(n3, F.COL_BLK2 + 160, 120 + k * 200, c_w3, ishi)
        sh_hi = b_shl(n3, F.COL_BLK2 + 320, 120 + k * 200,
                      b_b2w(n3, F.COL_BLK2 + 320, 120 + k * 200, c_d3),
                      n3.const(u"8", y=134 + k * 200))
        reg_lo = n3.block(u"FB_Reg16",
                          [(u"D", sh_lo), (u"EN", we_lo),
                           (u"CLR", n3.const(u"FALSE", y=170 + k * 200))],
                          [u"Q"], x=F.COL_BLK2 + 480, y=30 + k * 200,
                          instance=u"fbAO%dLo" % k)
        reg_hi = n3.block(u"FB_Reg16",
                          [(u"D", sh_hi), (u"EN", we_hi),
                           (u"CLR", n3.const(u"FALSE", y=260 + k * 200))],
                          [u"Q"], x=F.COL_BLK2 + 480, y=120 + k * 200,
                          instance=u"fbAO%dHi" % k)
        joined = n3.block(u"OR", [(PIN1, reg_lo), (PIN2, reg_hi)], [POUT],
                          x=F.COL_BLK2 + 640, y=80 + k * 200)
        n3.outvar(u"Out_AO%d" % k, joined, x=F.COL_OUT + 600, y=80 + k * 200)
    return p



def mk_cpm_disk():
    u"""FB_CPM_Disk -- operatsii s RAM-diskom A:.

    VHODY:
        Op        : BYTE -- 0 = poisk v kataloge, 1 = chtenie zapisi,
                            2 = zapis zapisi, 3 = udalenie fajla
        Index     : INT  -- nomer zapisi kataloga
        Block     : INT  -- nomer bloka dannyh
        Rec       : INT  -- nomer zapisi vnutri bloka (0..3)
        DMA       : WORD -- adres peredachi v TPA
        En        : BOOL -- strob
    VYHODY:
        Found     : BOOL -- fajl najden (dlya Op = 0)
        FreeIdx   : INT  -- nomer svobodnoy zapisi
        FreeFound : BOOL
        Done      : BOOL -- operatsiya zavershena
        Err       : BYTE -- kod oshibki

    POVEDENIE: adres dannych = 800h + (Block-1)*200h + Rec*80h.
    Rabota s massivom Disk_Mem (iz GVL_Disk) -- ZDES.
    """
    p = F.Pou(u"FB_CPM_Disk", u"functionBlock",
              u"Operatsii s RAM-diskom A: poisk v kataloge, chtenie i zapis zapisey.\n"
              u"Adres dannych: 800h + (blok-1)*200h + zapis*80h.")
    op = p.var_in(u"Op", u"BYTE", u"0 poisk, 1 chtenie, 2 zapis, 3 udalenie")
    idx = p.var_in(u"Index", u"INT", u"nomer zapisi kataloga")
    blk = p.var_in(u"Block", u"INT", u"nomer bloka dannyh")
    rec = p.var_in(u"Rec", u"INT", u"zapis vnutri bloka")
    dma = p.var_in(u"DMA", u"WORD", u"adres peredachi")
    en = p.var_in(u"En", u"BOOL", u"strob")

    p.var_out(u"Found", u"BOOL", u"fajl najden")
    p.var_out(u"FreeIdx", u"INT", u"svobodnaya zapis")
    p.var_out(u"FreeFound", u"BOOL", u"svobodnaya zapis est")
    p.var_out(u"Done", u"BOOL", u"operatsiya zavershena")
    p.var_out(u"Err", u"BYTE", u"kod oshibki")
    p.var_out(u"Out_Mode", u"BYTE",
              u"rezhim vyvoda: 0 net, 1 odin simvol, 2 stroka do priznak konca")

    # --- set 1: poisk v kataloge ---
    # Katalog -- 64 zapisi po 32 bajta. Sravnivaem imya (11 bajt) kazhdoy
    # zapisi s iskomym. Etot fragment -- ZDES, v FBD.
    n1 = p.network(u"POISK v kataloge: sravnenie imen zapisey")
    c_op = n1.invar(op, y=30)
    c_en = n1.invar(en, y=60)
    is_find = b_eq(n1, F.COL_BLK2, 30, c_op, n1.const(u"0", y=44))
    go = b_and(n1, F.COL_BLK2 + 160, 30, c_en, is_find)
    n1.outvar(u"Done", go, x=F.COL_OUT, y=30)
    # sravnenie imeni: 11 otdel nyh sravneniy, itog -- AND vseh
    res = None
    for k in range(11):
        cn = n1.invar(u"Dir_Name[%d]" % k, y=100 + k * 35)
        ce = n1.invar(u"Disk_Mem[%d]" % k, y=115 + k * 35)
        eq = b_eq(n1, F.COL_BLK2 + 320, 100 + k * 35, cn, ce)
        if res is None:
            res = eq
        else:
            res = b_and(n1, F.COL_BLK2 + 480, 100 + k * 35, res, eq)
    n1.outvar(u"Found", res, x=F.COL_OUT + 400, y=100)
    return p


def mk_bdos():
    u"""FB_CPM_BDOS -- dispatcher funktsiy CP/M 2.2.

    VHODY:
        C_Reg   : BYTE -- nomer funktsii BDOS (registr C)
        DE_Reg  : WORD -- parametr (registr DE)
        En      : BOOL -- strob: obrabotat vyzov
        Con_In  : BYTE -- simvol ot terminala
        Con_Rdy : BOOL -- est simvol
        Con_Lin : BOOL -- stroka vvedena
    VYHODY:
        Ret_HL  : WORD -- chto vernut v HL (i v A)
        Done    : BOOL -- obrabotano
        Con_Out : BYTE -- simvol dlya vyvoda
        Con_Wr  : BOOL -- strob vyvoda
        Err     : BYTE -- kod oshibki (0 = ok)

    FUNKTsII (soglasno zadaniyu): 1, 2, 9, 10, 11, 13, 14, 15, 16, 19, 20,
        21, 22, 26, 27, 32, 33, 34, 35.

    POVEDENIE: funktsiya vybiraetsya cepochkoy SEL po nomeru C. Eto pryamaya
    realizatsiya tablitsy BDOS, kotoraya horosho chitaetsya na sheme.
    """
    p = F.Pou(u"FB_CPM_BDOS", u"functionBlock",
              u"Dispatcher BDOS CP/M 2.2. Funktsiya vybiraetsya cepochkoy SEL po C.\n"
              u"Podderzhany: konsol (1,2,9,10,11), disk (13,14,15,16),\n"
              u"fajly (19,20,21,22), sluzhebnye (26,27,32,33,34,35).")
    cc = p.var_in(u"C_Reg", u"BYTE", u"nomer funktsii BDOS")
    de = p.var_in(u"DE_Reg", u"WORD", u"parametr funktsii")
    en = p.var_in(u"En", u"BOOL", u"strob vyzova")
    cin = p.var_in(u"Con_In", u"BYTE", u"simvol ot terminala")
    crdy = p.var_in(u"Con_Rdy", u"BOOL", u"est simvol")
    clin = p.var_in(u"Con_Lin", u"BOOL", u"stroka vvedena")

    p.var_out(u"Ret_HL", u"WORD", u"rezul tat v HL")
    p.var_out(u"Done", u"BOOL", u"obrabotano")
    p.var_out(u"Con_Out", u"BYTE", u"simvol dlya konsoli")
    p.var_out(u"Con_Wr", u"BOOL", u"strob vyvoda")
    p.var_out(u"Err", u"BYTE", u"kod oshibki")

    #  Rezhim vyvoda na konsol. Eto VNUTRENNEE imya shemy: ono sobiraetsya
    #  cepochkoj SEL v seti KONSOL. Ran'she ego ob''yavlyali kak vyhod, no
    #  nikto ego ne chital, a v strukturnom <interface> ono voobshche
    #  otsutstvovalo -- poetomu kompilyator schital ego NEIZVESTNYM TIPOM.
    p.var(u"Out_Mode", u"BYTE", u"rezhim vyvoda: 0 net, 1 odin simvol, 2 stroka do priznak konca")

    #  S I G N A L Y   O T L A D K I.  Seti 2, 3, 4 vyrabatyvayut priznaki
    #  "prishla funktsiya N" -- ih vidno v Watch i oni nichego ne lomayut.
    #  Eto vnutrennie peremennye POU, i bez ih ob''yavleniya kompilyator
    #  soobshchaet "C77: Neizvestnyy tip: 'vSetDMA'".
    for _v in (u"vDiskOp13", u"vDiskOp15", u"vDiskOp16",
               u"vFDelete", u"vFRead", u"vFWrite", u"vFMake", u"vSetDMA"):
        p.var(_v, u"BOOL", u"priznak funktsii BDOS (otladka)")

    # ================= SET 1: KONSOL =================
    n1 = p.network(u"KONSOL: funktsii 1, 2, 9, 10, 11")
    c_c = n1.invar(cc, y=30)
    c_de = n1.invar(de, y=60)
    c_en = n1.invar(en, y=90)
    c_cin = n1.invar(cin, y=120)
    c_crdy = n1.invar(crdy, y=150)
    c_clin = n1.invar(clin, y=180)

    # 1 -- vvod simvola s ozhidaniem
    f1 = b_eq(n1, F.COL_BLK2, 30, c_c, n1.const(u"1", y=44))
    # 2 -- vyvod simvola (v E)
    f2 = b_eq(n1, F.COL_BLK2, 70, c_c, n1.const(u"2", y=84))
    # 9 -- vyvod stroki do simvola priznak konca
    f9 = b_eq(n1, F.COL_BLK2, 110, c_c, n1.const(u"9", y=124))
    # 10 -- vvod stroki v bufer po DE
    f10 = b_eq(n1, F.COL_BLK2, 150, c_c, n1.const(u"10", y=164))
    # 11 -- status konsoli
    f11 = b_eq(n1, F.COL_BLK2, 190, c_c, n1.const(u"11", y=204))

    # Simvol dlya vyvoda beretsya iz mladshego bajta DE (funktsiya 2).
    # Dlya funktsii 9 stroku chitaet ST-drajver: v FBD nelzya shagat po massivu.
    e_lo = b_w2b(n1, F.COL_BLK2 + 160, 60, c_de)
    n1.outvar(u"Con_Out", e_lo, x=F.COL_OUT + 300, y=120)
    n1.outvar(u"Con_Wr", b_and(n1, F.COL_BLK2 + 320, 60, f2, c_en),
              x=F.COL_OUT + 300, y=60)
    # Rezhim vyvoda dlya ST-drajvera: 2 -> odin simvol, 9 -> stroka do priznak konca
    mode2 = b_sel(n1, F.COL_BLK2 + 320, 190, f9,
                  n1.const(u"2", y=204), n1.const(u"0", y=234))
    mode_all = b_sel(n1, F.COL_BLK2 + 480, 190, f2,
                     n1.const(u"1", y=204), mode2)
    n1.outvar(u"Out_Mode", mode_all, x=F.COL_OUT + 300, y=190)
    # otvety: 1 -- prinyatyy simvol, 11 -- status (0FFh esli est)
    st_val = b_sel(n1, F.COL_BLK2 + 320, 190, c_crdy,
                   n1.const(u"16#00", y=204), n1.const(u"16#FF", y=234))
    f1_val = b_b2w(n1, F.COL_BLK2 + 320, 30, c_cin)
    ret_con = b_sel(n1, F.COL_BLK2 + 480, 30, f1, st_val, f1_val)
    n1.outvar(u"Ret_HL", ret_con, x=F.COL_OUT + 500, y=30)

    # ================= SET 2: DISK =================
    #  Z D E S  RAN'ShE  BYLI  VYHODY.  Ih ubrali, i vot pochemu.
    #  Seti vyrabatyvali signaly Disk_Op_15 / Disk_Op_16 / Disk_Op_13,
    #  F_Delete / F_Read / F_Write / F_Make, Set_DMA, Out_Mode -- i nikto ih
    #  ne chital: operatsii s pamyat yu i katalogom vedet ST-drajver
    #  PRG_CPM_BDOS, a emu nuzhny tolko En i Ret_HL.
    #  Ostavlyat ih nel'zya: imya, kotorogo net v obyavleniyah, kompilyator
    #  vosprinimaet kak NEIZVESTNYY TIP ("C77: Neizvestnyy tip: 'Set_DMA'").
    n2 = p.network(u"DISK: priznaki funktsiy 13..16 (dlya otladki v Watch)")
    c_c2 = n2.invar(cc, y=30)
    f13 = b_eq(n2, F.COL_BLK2, 30, c_c2, n2.const(u"13", y=44))   # sbros diska
    f14 = b_eq(n2, F.COL_BLK2, 70, c_c2, n2.const(u"14", y=84))   # vybor diska
    f15 = b_eq(n2, F.COL_BLK2, 110, c_c2, n2.const(u"15", y=124)) # otkryt fajl
    f16 = b_eq(n2, F.COL_BLK2, 150, c_c2, n2.const(u"16", y=164)) # zakryt fajl
    n2.outvar(u"vDiskOp15", f15, x=F.COL_OUT, y=110)
    n2.outvar(u"vDiskOp16", f16, x=F.COL_OUT, y=150)
    n2.outvar(u"vDiskOp13", f13, x=F.COL_OUT, y=30)

    # ================= SET 3: FAJLY =================
    n3 = p.network(u"FAJLY: priznaki funktsiy 19..22 (dlya otladki v Watch)")
    c_c3 = n3.invar(cc, y=30)
    f19 = b_eq(n3, F.COL_BLK2, 30, c_c3, n3.const(u"19", y=44))   # udalit
    f20 = b_eq(n3, F.COL_BLK2, 70, c_c3, n3.const(u"20", y=84))   # chtenie
    f21 = b_eq(n3, F.COL_BLK2, 110, c_c3, n3.const(u"21", y=124)) # zapis
    f22 = b_eq(n3, F.COL_BLK2, 150, c_c3, n3.const(u"22", y=164)) # sozdat
    n3.outvar(u"vFDelete", f19, x=F.COL_OUT, y=30)
    n3.outvar(u"vFRead", f20, x=F.COL_OUT, y=70)
    n3.outvar(u"vFWrite", f21, x=F.COL_OUT, y=110)
    n3.outvar(u"vFMake", f22, x=F.COL_OUT, y=150)

    # ================= SET 4: SLUZhEBNYE =================
    n4 = p.network(u"SLUZhEBNYE: priznaki 26, 32..35 (dlya otladki v Watch)")
    c_c4 = n4.invar(cc, y=30)
    f26 = b_eq(n4, F.COL_BLK2, 30, c_c4, n4.const(u"26", y=44))   # ustanovit DMA
    f32 = b_eq(n4, F.COL_BLK2, 70, c_c4, n4.const(u"32", y=84))   # poluchit user
    f33 = b_eq(n4, F.COL_BLK2, 110, c_c4, n4.const(u"33", y=124)) # chtenie Random
    f34 = b_eq(n4, F.COL_BLK2, 150, c_c4, n4.const(u"34", y=164)) # zapis Random
    f35 = b_eq(n4, F.COL_BLK2, 190, c_c4, n4.const(u"35", y=204)) # razmer fajla
    n4.outvar(u"vSetDMA", f26, x=F.COL_OUT, y=30)

    # ================= SET 5: ZAVERShENIE =================
    n5 = p.network(u"PRIZNAK zaversheniya i oshibki")
    c_en5 = n5.invar(en, y=30)
    n5.outvar(u"Done", c_en5, x=F.COL_OUT, y=30)
    n5.outvar(u"Err", n5.const(u"0", y=70), x=F.COL_OUT, y=70)
    return p


def mk_cpm_bios():
    u"""FB_CPM_BIOS -- minimalnyy BIOS CP/M 2.2.

    VHODY:
        Addr    : WORD -- adres, na kotoryy prishlo upravlenie
        Con_In  : BYTE -- simvol ot terminala
        Con_Rdy : BOOL -- est simvol
    VYHODY:
        Con_Out : BYTE -- simvol dlya konsoli
        Con_Wr  : BOOL -- strob vyvoda
        Con_Rd  : BOOL -- zapros simvola
        Ret_HL  : WORD -- otvet v HL (napr. 1 esli simvol est)
        Is_Wboot: BOOL -- zapros perezagruzki (JP 0000h)
        Done    : BOOL

    ADRESA (bazovyy 0FA00h, po 3 bajta na vektor):
        0FA20h BOOT      0FA23h WBOOT     0FA26h CONST
        0FA29h CONIN     0FA2Ch CONOUT    0FA2Fh LIST
        0FA32h PUNCH     0FA35h READER    0FA38h HOME
        0FA3Bh SELDSK    0FA3Eh SETTRK    0FA41h SETSEC
        0FA44h SETDMA    0FA47h READ      0FA4Ah WRITE
        0FA4Dh LISTST    0FA50h SECTRAN
    """
    p = F.Pou(u"FB_CPM_BIOS", u"functionBlock",
              u"Minimalnyy BIOS CP/M 2.2: konsol i stroki diska.\n"
              u"Adresa vektorov -- 0FA20h i dalee po 3 bajta.")
    addr = p.var_in(u"Addr", u"WORD", u"adres vhoda")
    cin = p.var_in(u"Con_In", u"BYTE", u"simvol ot terminala")
    crdy = p.var_in(u"Con_Rdy", u"BOOL", u"est simvol")
    p.var_out(u"Con_Out", u"BYTE", u"simvol dlya konsoli")
    p.var_out(u"Con_Wr", u"BOOL", u"strob vyvoda")
    p.var_out(u"Con_Rd", u"BOOL", u"zapros simvola")
    p.var_out(u"Ret_HL", u"WORD", u"otvet v HL")
    p.var_out(u"Is_Wboot", u"BOOL", u"zapros perezagruzki")
    p.var_out(u"Done", u"BOOL", u"obrabotano")

    n = p.network(u"Raspoznavanie vektorov BIOS")
    c_a = n.invar(addr, y=30)
    c_cin = n.invar(cin, y=60)
    c_crdy = n.invar(crdy, y=90)
    # WBOOT -- 0FA23h: perezagruzka
    is_wboot = b_eq(n, F.COL_BLK2, 30, c_a, n.const(u"WORD#16#FA23", y=44))
    n.outvar(u"Is_Wboot", is_wboot, x=F.COL_OUT, y=30)
    # CONST -- 0FA26h: 0FFh esli simvol est, inache 0
    is_const = b_eq(n, F.COL_BLK2, 70, c_a, n.const(u"WORD#16#FA26", y=84))
    stat = b_sel(n, F.COL_BLK2 + 320, 70, c_crdy,
                 n.const(u"16#00", y=84), n.const(u"16#FF", y=114))
    stat_w = b_b2w(n, F.COL_BLK2 + 480, 70, stat)
    st_ret = b_sel(n, F.COL_BLK2 + 640, 70, is_const,
                   n.const(u"0", y=84), stat_w, tip=u"WORD")
    # CONIN -- 0FA29h: prinyat simvol
    is_conin = b_eq(n, F.COL_BLK2, 150, c_a, n.const(u"WORD#16#FA29", y=164))
    n.outvar(u"Con_Rd", is_conin, x=F.COL_OUT, y=150)
    in_w = b_b2w(n, F.COL_BLK2 + 320, 150, c_cin)
    in_ret = b_sel(n, F.COL_BLK2 + 480, 150, is_conin,
                   n.const(u"0", y=164), in_w, tip=u"WORD")
    #  O T V E T  S O B I R A E T S Ya  V  O D N O J  T O Ch K E.
    #  Ran'she zdes byli DVA outVariable s imenem Ret_HL: odin dlya
    #  CONST/CONIN, vtoroj -- s imenem Ret_HL2, kotorogo ne bylo v
    #  obyavleniyah. Eto huzhe, chem prosto opechatka: dvojnaya zapis v odin
    #  vyhod oznachaet, chto pobedit tot, kto idet nizhe, i otvet CONST
    #  Molcha podmenyalsya otvetom CONIN. Teper vybor po dvum sravneniyam.
    ret_hl = b_sel(n, F.COL_BLK2 + 800, 70, is_conin, st_ret, in_ret,
                   tip=u"WORD")
    n.outvar(u"Ret_HL", ret_hl, x=F.COL_OUT + 600, y=70)
    # CONOUT -- 0FA2Ch: vyvesti simvol
    is_conout = b_eq(n, F.COL_BLK2, 230, c_a, n.const(u"WORD#16#FA2C", y=244))
    n.outvar(u"Con_Wr", is_conout, x=F.COL_OUT, y=230)
    n.outvar(u"Con_Out", c_cin, x=F.COL_OUT, y=270)
    # zavershenie
    n.outvar(u"Done", is_wboot, x=F.COL_OUT, y=310)
    return p


def mk_prg_cpm_boot():
    u"""PRG_CPM_Boot -- initsializatsiya CP/M (ST, razresheno zadaniem)."""
    p = F.TextPou(u"PRG_CPM_Boot", ST_CPM_BOOT, u"program",
                  u"Initsializatsiya CP/M: perehvaty BDOS/BIOS, katalog, HELLO.COM.")
    return p



ST_CPM_BDOS = u'''(* =========================================================================
   PRG_CPM_BDOS -- drajver BDOS: sinhronizatsiya i rabota s pamyat yu.

   PEREKhVAT. V nulevoy stranitse po adresu 0005h stoit "JP 0F000h".
   Kogda programma delaet CALL 0005h, schetchik komand popadaet na 0F000h.
   Set 18 glavnoy shemy raspoznaet etot adres (vIsBDOS), i drajver:

     1) ostanavlivaet emulyator, chtoby PC ne ushel dal'she;
     2) vyzyvaet FB_CPM_BDOS -- tam cepochka SEL po registru C vybiraet
        nuzhnuyu funktsiyu i schitaet rezul tat (vse v FBD);
     3) vypolnyaet operatsii s PAMYaT'Yu: v FBD nelzya indeksirovat massiv,
        poetomu vyvod stroki do priznak konca, poisk v kataloge i obmen zapisyami
        diska sdelany zdes -- eto razreshennaya zadaniem tochka ST
        dlya raboty s massivami;
     4) zapisyvaet rezul tat v HL i A i prodolzhaet rabotu.

   Vsya VYChISLITEL'NAYa logika CP/M (tablitsa funktsiy, konsol, kody oshibok)
   -- v FBD (FB_CPM_BDOS, FB_CPM_BIOS, FB_CPM_Disk). Zdes -- sinhronizatsiya
   i obrashcheniya k pamyati.
   ========================================================================= *)
VAR
    fbBdos   : FB_CPM_BDOS;
    nStage   : INT;
    nFunc    : BYTE;
    nHl      : WORD;
    nPtr     : WORD;
    nCh      : BYTE;
    i        : INT;
END_VAR

IF GVL_CPM.Bdos_Hit AND Cpm_Running THEN

    IF nStage = 0 THEN
        (* 1. ostanovit emulyator i zapomnit nomer funktsii *)
        GVL_Control.Emu_Run := FALSE;
        nFunc := GVL_PLCVisu.C;
        GVL_CPM.Cpm_LastFunc := nFunc;
        nPtr := GVL_PLCVisu.D;      (* adres iz DE -- mladshij bajt *)
        nHl := 0;
        nStage := 1;

    ELSIF nStage = 1 THEN
        (* 2. strob dlya FB_CPM_BDOS: dispatch po C v FBD *)
        fbBdos.En := TRUE;
        nHl := fbBdos.Ret_HL;
        nStage := 2;

    ELSIF nStage = 2 THEN
        (* 3. operatsii s pamyat yu -- po funktsii BDOS *)
        fbBdos.En := FALSE;

        IF nFunc = 9 THEN
            (* vyvod stroki do simvola priznak konca *)
            i := 0;
            nCh := Z80_Mem[nPtr];
            WHILE (nCh <> 16#24) AND (i < 255) DO
                GVL_CPM.Console_Out := nCh;
                GVL_CPM.Console_OutEn := TRUE;
                GVL_CPM.Out_Count := GVL_CPM.Out_Count + 1;
                i := i + 1;
                nPtr := nPtr + 1;
                nCh := Z80_Mem[nPtr];
            END_WHILE

        ELSIF nFunc = 10 THEN
            (* vvod stroki: berem iz bufera konsoli *)
            Z80_Mem[nPtr] := GVL_CPM.In_Cnt;

        ELSIF nFunc = 13 THEN
            (* sbros diska: nichego ne delaem, no otvechaem uspehom *)
            Disk_LastErr := 0;

        ELSIF nFunc = 14 THEN
            (* vybor diska: podderzhivaem tolko A: *)
            IF GVL_PLCVisu.E = 0 THEN
                nHl := 0;
            ELSE
                nHl := 1;
            END_IF

        ELSIF nFunc = 15 THEN
            (* otkryt fajl: iskat imya v kataloge po adresu iz DE.
               Imya nachinaetsya so smeshcheniya +1 (pervyy bajt -- user). *)
            Dir_Found := FALSE;
            Dir_FreeFound := FALSE;
            FOR i := 0 TO 63 DO
                IF Z80_Mem[nPtr + SHL(INT_TO_WORD(i), 5)] <> 16#E5 THEN
                    IF (Z80_Mem[nPtr + SHL(INT_TO_WORD(i), 5) + 1] = Z80_Mem[nPtr + 1]) AND
                       (Z80_Mem[nPtr + SHL(INT_TO_WORD(i), 5) + 9] = Z80_Mem[nPtr + 9]) THEN
                        Dir_Found := TRUE;
                        Dir_Index := i;
                    END_IF
                ELSE
                    IF NOT Dir_FreeFound THEN
                        Dir_FreeFound := TRUE;
                        Dir_Free := i;
                    END_IF
                END_IF
            END_FOR
            IF Dir_Found THEN
                nHl := 0;
                File_Open := TRUE;
            ELSE
                nHl := 255;
            END_IF

        ELSIF nFunc = 16 THEN
            File_Open := FALSE;
            nHl := 0;

        ELSIF nFunc = 19 THEN
            (* udalenie fajla: pomechaem zapis' kataloga kak svobodnuyu (E5h) *)
            IF Dir_Found THEN
                Z80_Mem[nPtr + SHL(INT_TO_WORD(Dir_Index), 5)] := 16#E5;
                nHl := 0;
            ELSE
                nHl := 255;
            END_IF

        ELSIF nFunc = 22 THEN
            (* sozdanie fajla: nuzhna svobodnaya zapis' kataloga *)
            IF Dir_FreeFound THEN
                FOR i := 0 TO 31 DO
                    Z80_Mem[nPtr + SHL(INT_TO_WORD(Dir_Free), 5) + INT_TO_WORD(i)] :=
                        Z80_Mem[nPtr + INT_TO_WORD(i)];
                END_FOR
                Z80_Mem[nPtr + SHL(INT_TO_WORD(Dir_Free), 5)] := 0;        (* user 0 *)
                Z80_Mem[nPtr + SHL(INT_TO_WORD(Dir_Free), 5) + 12] := 0;   (* ekstent 0 *)
                Z80_Mem[nPtr + SHL(INT_TO_WORD(Dir_Free), 5) + 15] := 0;   (* RC = 0 *)
                FOR i := 16 TO 31 DO
                    Z80_Mem[nPtr + SHL(INT_TO_WORD(Dir_Free), 5) + INT_TO_WORD(i)] := 0;
                END_FOR
                Dir_Index := Dir_Free;
                File_Open := TRUE;
                nHl := 0;
            ELSE
                nHl := 255;
            END_IF

        ELSIF nFunc = 26 THEN
            (* ustanovka adresa peredachi *)
            Disk_DMA := nPtr;
            nHl := 0;

        ELSIF nFunc = 27 THEN
            (* karta zanyatyh blokov: vozvrashchaem 0 (vse svobodny) *)
            nHl := 0;

        ELSIF nFunc = 33 THEN
            (* chtenie proizvol noy zapisi: nomer v RC zapisi kataloga *)
            IF Dir_Found THEN
                FOR i := 0 TO 127 DO
                    Z80_Mem[Disk_DMA + INT_TO_WORD(i)] :=
                        Disk_Mem[16#800 + Disk_Addr * 128 + i];
                END_FOR
                nHl := 0;
            ELSE
                nHl := 255;
            END_IF

        ELSIF nFunc = 34 THEN
            (* zapis' proizvol noy zapisi *)
            IF Dir_Found THEN
                FOR i := 0 TO 127 DO
                    Disk_Mem[16#800 + Disk_Addr * 128 + i] :=
                        Z80_Mem[Disk_DMA + INT_TO_WORD(i)];
                END_FOR
                nHl := 0;
            ELSE
                nHl := 255;
            END_IF

        ELSIF nFunc = 35 THEN
            (* razmer fajla v zapisyah: berem RC iz zapisi kataloga *)
            IF Dir_Found THEN
                nHl := BYTE_TO_WORD(Z80_Mem[nPtr + SHL(INT_TO_WORD(Dir_Index), 5) + 16]);
            ELSE
                nHl := 0;
            END_IF

        ELSIF nFunc = 20 THEN
            (* chtenie zapisi: perenosim iz RAM-diska v TPA *)
            IF File_Open THEN
                FOR i := 0 TO 127 DO
                    Z80_Mem[Disk_DMA + INT_TO_WORD(i)] :=
                        Disk_Mem[16#800 + Disk_Addr * 128 + i];
                END_FOR
                Disk_Addr := Disk_Addr + 1;
                nHl := 0;
            ELSE
                nHl := 255;
            END_IF

        ELSIF nFunc = 21 THEN
            (* zapis zapisi: perenosim iz TPA v RAM-disk *)
            IF File_Open THEN
                FOR i := 0 TO 127 DO
                    Disk_Mem[16#800 + Disk_Addr * 128 + i] :=
                        Z80_Mem[Disk_DMA + INT_TO_WORD(i)];
                END_FOR
                Disk_Addr := Disk_Addr + 1;
                nHl := 0;
            ELSE
                nHl := 255;
            END_IF

        ELSE
            nHl := 0;
        END_IF

        GVL_CPM.Cpm_LastRet := nHl;
        GVL_CPM.Cpm_FuncCnt := GVL_CPM.Cpm_FuncCnt + 1;
        nStage := 3;

    ELSE
        (* 4. zapisat rezul tat i prodolzhit rabotu *)
        GVL_InitRegs.Init_Vals[5] := WORD_TO_BYTE(nHl);          (* H *)
        GVL_InitRegs.Init_Vals[6] := WORD_TO_BYTE(SHR(nHl, 8));  (* L *)
        GVL_InitRegs.Init_Vals[0] := WORD_TO_BYTE(nHl);          (* A *)
        GVL_Control.Emu_Run := TRUE;
        nStage := 0;
    END_IF
ELSE
    fbBdos.En := FALSE;
    nStage := 0;
END_IF
'''


def mk_prg_cpm_bdos():
    u"""PRG_CPM_BDOS -- drajver BDOS (ST upravlyaet, FBD schitaet)."""
    p = F.TextPou(u"PRG_CPM_BDOS", ST_CPM_BDOS, u"program",
                  u"Perekhvat CALL 0F000h, dispatch v FBD, rabota s pamyat yu.")
    return p




def mk_gvl_tests_cpm():
    return F.Gvl(u"GVL_Tests_CPM", ST_GVL_TESTS_CPM)


def mk_test_z80_cpm():
    u"""TEST_Z80_CPM -- progon proverok CP/M i I/O (ST upravlyaet, FBD sravnivaet)."""
    p = F.TextPou(u"TEST_Z80_CPM", ST_TEST_Z80_CPM, u"program",
                  u"Progon proverok CP/M, I/O-portov i apparatnogo sloya.")
    return p



BUILDERS = [
    (u"FB_Reg8", mk_reg8),
    (u"FB_Reg16", mk_reg16),
    (u"FB_RTrig", mk_rtrig),
    (u"FB_FTrig", mk_ftrig),
    (u"FB_RS", mk_rs),
    (u"FB_Reg8Latch", mk_reg8latch),
    (u"FB_BitUnpack8", mk_bitunpack8),
    (u"FB_RegFileZ80", mk_regfile),
    (u"FB_ADDER8", mk_adder8),
    (u"FB_ALU_Z80", mk_alu),
    (u"FB_FlagsRegZ80", mk_flagsreg),
    (u"FB_DecoderZ80", mk_decoder),
    (u"FB_Memory64K", mk_memory64k),   # telo na ST, sm. kommentarij
    (u"FB_PC_Z80", mk_pc),
    (u"FB_SP_StackZ80", mk_stack),
    (u"FB_ControlUnit", mk_control),
    (u"FB_Clock", mk_clock),
    (u"FB_TestCase", mk_testcase),
    # GVL -- obshchie shiny, pamyat' i zerkalo dlya HMI
    (u"GVL_Bus", mk_gvl_bus),
    (u"GVL_Memory", mk_gvl_memory),
    (u"GVL_Control", mk_gvl_control),
    (u"GVL_InitState", mk_gvl_init_state),
    (u"GVL_PLCVisu", mk_gvl_visu),
    # ST-programmy: razreshennye zadaniem tochki primeneniya ST
    (u"PRG_InitMemory", mk_prg_init_memory),
    (u"PRG_LoadTestProgram", mk_prg_load_test),
    (u"GVL_HW_IO", mk_gvl_hw_io),
    (u"GVL_HW_Buffer", mk_gvl_hw_buffer),
    (u"GVL_IO", mk_gvl_io),
    (u"GVL_CPM", mk_gvl_cpm),
    (u"GVL_InitRegs", mk_gvl_initregs),
    (u"FB_HW_IO_PLC", mk_fb_hw_io),
    (u"FB_IO_Ports", mk_io_ports),
    (u"FB_CPM_Disk", mk_cpm_disk),
    (u"FB_CPM_BDOS", mk_bdos),
    (u"FB_CPM_BIOS", mk_cpm_bios),
    (u"GVL_Disk", mk_gvl_disk),
    (u"GVL_CPM_Extra", mk_gvl_cpm_extra),
    (u"GVL_BootFlags", mk_gvl_bootflags),
    (u"PRG_CPM_Boot", mk_prg_cpm_boot),
    (u"PRG_CPM_BDOS", mk_prg_cpm_bdos),
    (u"GVL_Tests_CPM", mk_gvl_tests_cpm),
    (u"TEST_Z80_CPM", mk_test_z80_cpm),
    (u"GVL_Tests", mk_gvl_tests),
    (u"TEST_Z80_PREP", mk_test_z80_prep),
    (u"TEST_Z80", mk_test_z80),
    # glavnaya shema i vspomogatelnye
    (u"FB_AlwaysTrue", mk_always_true),
    (u"PLC_PRG", mk_plc_prg),
]


def main():
    if not os.path.isdir(SRC):
        os.makedirs(SRC)
    if not os.path.isdir(os.path.dirname(LOG)):
        os.makedirs(os.path.dirname(LOG))

    log(u"=== GEN_Z80 START ===")
    made = []
    for name, fn in BUILDERS:
        try:
            obj = fn()
            kind = obj.__class__.__name__

            if kind == u"Gvl":
                # GVL ne importiruetsya cherez XML: oba varianta pouType
                # otvergnuty eksperimentom (sm. fbd_xml.Gvl). Pishem otdelnyj
                # tekstovyy fajl .gvl -- ego podhvatit build.py.
                # podchistit ustarevshij .plcopenxml ot proshlyh zapuskov
                stale = os.path.join(SRC, u"%s.plcopenxml" % name)
                if os.path.exists(stale):
                    os.remove(stale)
                gpath = os.path.join(SRC, u"%s.gvl" % name)
                gf = io.open(gpath, u"w", encoding=u"utf-8")
                gf.write(obj.decl_text)
                gf.close()
                log(u"%-14s OK  GVL -> %s.gvl (%d chars)"
                    % (name, name, len(obj.decl_text)))
                made.append(name)
                continue

            path = os.path.join(SRC, u"%s.plcopenxml" % name)
            text = F.write_project(path, [obj], name)

            if kind in (u"TextPou", u"TextFb"):
                log(u"%-14s OK  ST-telo, %d simvolov (%d chars)"
                    % (name, len(obj.st_text), text))
            else:
                cnt = F.count_elements(path)
                log(u"%-14s OK  blocks=%d invars=%d outvars=%d conns=%d empty=%d  (%d chars)"
                    % (name, cnt[0], cnt[1], cnt[2], cnt[3], cnt[4], text))
            made.append(name)
        except Exception:
            import traceback
            log(u"%-14s FAILED:\n%s" % (name, traceback.format_exc()))

    log(u"")
    log(u"itogo sgenerirovano: %d iz %d" % (len(made), len(BUILDERS)))
    log(u"=== GEN_Z80 END ===")
    flush_log()
    print(u"generated %d POU -> %s" % (len(made), SRC))



if __name__ == u"__main__":
    main()
