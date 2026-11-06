# -*- coding: utf-8 -*-
u"""patch_main.py -- dobavlyaet v gen_z80.py generator PLC_PRG i rasshireniya.

Chtoby ne pravit bolshoy fajl ruchnymi kusochnymi edit-ami, delaem eto skriptom:
  * FB_Memory64K rasshiryaetsya do 4 portov;
  * FB_RegFileZ80 poluchaet vyhod Addr_HL;
  * dobavlyaetsya FB_AlwaysTrue;
  * dobavlyaetsya mk_plc_prg (glavnaya shema);
  * BUILDERS popolnyaetsya.
"""

import io
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))          # generator/probe
ROOT = os.path.dirname(os.path.dirname(HERE))              # Z80_EMU
GEN = os.path.join(ROOT, "generator", "gen_z80.py")

t = io.open(GEN, "r", encoding="utf-8").read()

# ---------------------------------------------------------------------------
# 1. FB_Memory64K -> chetyre porta
# ---------------------------------------------------------------------------
start = t.index(u"def mk_memory64k():")
end = t.index(u"def mk_pc():")
NEW_MEM = u'''def mk_memory64k():
    u"""FB_Memory64K -- pamyat' 64 KB s ChETYR'M Ya PORTAMI.

    Pochemu chetyre porta, a ne odin: za odin skan protsessoru nuzhno
      * vybrat kod komandy po PC,
      * prochitat operand (neposredstvennoe znachenie ili adres nn),
      * prochitat/zapisat (HL) ili (nn),
      * prochitat/zapisat stek pri CALL/RET.
    Odna para "adres+dannye" eto ne obsluzhit za skan, poetomu porty
    razdelnye: u kazhdogo svoj adres i svoj vyhod dannyh.
    Pamyat Z80_Mem zhivet v GVL_Memory -- tak programmy initsializatsii (ST)
    i HMI imeyut k nej dostup.
    """
    p = F.Pou(u"FB_Memory64K", u"functionBlock",
              u"Operativnaya pamyat 64 KBajt s chetyrmya portami.\\n"
              u"Fetch po PC, operand (Rd/Wr) po vychislennomu adresu, stek -- otdelno.")
    p.var_in(u"PC", u"WORD", u"adres vyborki komandy")
    p.var_in(u"Addr", u"WORD", u"adres operanda ((HL) ili nn)")
    p.var_in(u"Rd", u"BOOL", u"chtenie operanda")
    p.var_in(u"Wr", u"BOOL", u"zapis operanda")
    p.var_in(u"D_Bus", u"BYTE", u"shina dannyh")
    p.var_in(u"SP_Addr", u"WORD", u"adres steka")
    p.var_in(u"SP_Rd", u"BOOL", u"chtenie dvuh bajtov steka")
    p.var_in(u"SP_Wr", u"BOOL", u"zapis dvuh bajtov steka")
    p.var_in(u"SP_Data", u"WORD", u"chto polozhit v stek")
    p.var_out(u"D_Out", u"BYTE", u"vybrannyj kod komandy")
    p.var_out(u"Rd_Data", u"BYTE", u"schitannyj operand")
    p.var_out(u"SP_Out", u"WORD", u"snyatoe so steka")
    p.var_out(u"Bus_Drv", u"BYTE", u"chto pomeshchaetsya na shinu pri chtenii")

    n = p.network(u"Port 1: vyborka komandy po PC")
    c_pc = n.invar(u"PC", y=30)
    fetch = n.block(u"MEM_READ", [(u"Addr", c_pc)], [POUT], x=F.COL_BLK, y=30)
    n.outvar(u"D_Out", fetch, x=F.COL_OUT, y=30)

    n2 = p.network(u"Port 2: operand -- chtenie i zapis")
    c_addr = n2.invar(u"Addr", y=30)
    c_wr = n2.invar(u"Wr", y=110)
    c_dbus = n2.invar(u"D_Bus", y=150)
    rd = n2.block(u"MEM_READ", [(u"Addr", c_addr)], [POUT], x=F.COL_BLK, y=30)
    n2.outvar(u"Rd_Data", rd, x=F.COL_OUT, y=30)
    n2.outvar(u"Bus_Drv", rd, x=F.COL_OUT, y=70)
    n2.block(u"MEM_WRITE", [(u"Addr", c_addr), (u"D", c_dbus), (u"En", c_wr)],
             [POUT], x=F.COL_BLK, y=110)

    n3 = p.network(u"Port 3: stek -- dva bajta za odin obrat")
    c_sp = n3.invar(u"SP_Addr", y=30)
    c_spw = n3.invar(u"SP_Wr", y=110)
    c_spd = n3.invar(u"SP_Data", y=150)
    hi_rd = n3.block(u"MEM_READ", [(u"Addr", c_sp)], [POUT], x=F.COL_BLK, y=30)
    one = n3.const(u"1", y=190)
    lo_addr = b_add(n3, F.COL_BLK, 70, c_sp, one)
    lo_rd = n3.block(u"MEM_READ", [(u"Addr", lo_addr)], [POUT], x=F.COL_BLK, y=70)
    lo_w = b_w2b(n3, F.COL_BLK, 150, c_spd)
    hi_w = b_shr(n3, F.COL_BLK2, 190, c_spd, n3.const(u"8", y=204))
    n3.block(u"MEM_WRITE", [(u"Addr", c_sp), (u"D", hi_w), (u"En", c_spw)],
             [POUT], x=F.COL_BLK2 + 160, y=110)
    n3.block(u"MEM_WRITE", [(u"Addr", lo_addr), (u"D", lo_w), (u"En", c_spw)],
             [POUT], x=F.COL_BLK2 + 160, y=150)
    w_hi = b_b2w(n3, F.COL_BLK2 + 160, 30, hi_rd)
    sh = b_shl(n3, F.COL_BLK2 + 320, 30, w_hi, n3.const(u"8", y=44))
    w_lo = b_b2w(n3, F.COL_BLK2 + 320, 70, lo_rd)
    joined = n3.block(u"OR", [(PIN1, sh), (PIN2, w_lo)], [POUT],
                      x=F.COL_BLK2 + 480, y=50)
    n3.outvar(u"SP_Out", joined, x=F.COL_OUT + 440, y=50)
    return p


'''
t = t[:start] + NEW_MEM + t[end:]

# ---------------------------------------------------------------------------
# 2. FB_RegFileZ80 -- dobavit vyhod Addr_HL
# ---------------------------------------------------------------------------
old = u'''    for v in (u"A", u"B", u"C", u"D", u"E", u"H", u"L", u"F",
              u"Sa", u"Sb", u"Sc", u"Sd", u"Se", u"Sh", u"Sl", u"Sf"):
        p.var_out(v, u"BYTE", u"registr")'''
new = u'''    for v in (u"A", u"B", u"C", u"D", u"E", u"H", u"L", u"F",
              u"Sa", u"Sb", u"Sc", u"Sd", u"Se", u"Sh", u"Sl", u"Sf"):
        p.var_out(v, u"BYTE", u"registr")
    p.var_out(u"Addr_HL", u"WORD", u"adres pary HL (dlya kosvennoj adresatsii)")'''
assert old in t, u"ne najden blok vyhodov RegFile"
t = t.replace(old, new)

# dobavit set' vychisleniya Addr_HL v konets mk_regfile (pered "return p")
old2 = u'''    v = sel_chain(nr, c_ss, cur[0], cases, x=F.COL_BLK2, y0=40, ystep=50)
    nr.outvar(u"Src_Val", v, x=F.COL_OUT, y=40)
    return p'''
new2 = u'''    v = sel_chain(nr, c_ss, cur[0], cases, x=F.COL_BLK2, y0=40, ystep=50)
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
    return p'''
assert old2 in t, u"ne najden hvost mk_regfile"
t = t.replace(old2, new2)

io.open(GEN, "w", encoding="utf-8").write(t)
print(u"PATCH OK: Memory64K rasshirena, RegFile poluchil Addr_HL")
