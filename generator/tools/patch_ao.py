# -*- coding: utf-8 -*-
u"""PATCH_AO -- analogovye vyhody hranyatsya v GVL_Regs, a ne vnutri FB_Reg16.

D V E  P R I Ch I N Y.

1) FB_Reg8 / FB_Reg16 derzhat sostoyanie, chitaya S V O J  Zh E vyhod Q v toj
   zhe seti. Eto to zhe kolco "vyhod pitayot svoy vhod", iz-za kotorogo
   registrovaya chast kogda-to chitala nuli. Izmereno: starshij bajt
   analogovogo vyhoda ne zashchelkivalsya, i HW_Out_AO0 ostavalsya raven 34h
   vmesto 1234h, hotya sto procentov vyzovov OUT na port 05h prohodilo.

2) Katalog shagov stenda pishet komandu po adresu 0 i tem samym zatiraet
   nulevuyu stranitsu CP/M, kotoruyu proveryayut drugie testy (T23, T24).
   Teper' katalog rabotaet po adresu 4000h: adres nachala -- Init_PC.

Ch T O  D E L A E M. Slovo AO0/AO1 zhivet v GVL_Regs paroj Rs_/Nx_ (kak
registry, PC i SP). PLC_PRG sobiraet ego iz dvuh zapisej OUT: mladshij bajt s
porta 04h/08h, starshij -- s 05h/09h. Fizicheskie vyhody i bufery poluchayut
znachenie iz etogo slova.
"""

import io
import sys

sys.stdout.reconfigure(encoding=u"utf-8")

P = r"generator\gen_z80.py"
t = io.open(P, encoding=u"utf-8").read()
n = 0


def rep(old, new):
    global t, n
    assert t.count(old) == 1, (t.count(old), repr(old[:90]))
    t = t.replace(old, new, 1)
    n += 1


# ------------------------------------------------ 1. GVL_Regs: slova AO --------
rep(u'''    Rs_MW    : BOOL;   (* strob zapisi v pamyat' *)''',
    u'''    (*  A N A L O G O V Y E  V Y H O D Y. Slovo sobiraetsya iz dvuh zapisej
        OUT: mladshij bajt -- port 04h (08h), starshij -- 05h (09h). Hranenie
        zdes', a ne vnutri FB_Reg16: tot derzhit sostoyanie cherez svoy zhe
        vyhod i v kaskade dvuh registrov teryal starshij bajt. *)
    Rs_AO0   : WORD;
    Nx_AO0   : WORD;
    Rs_AO1   : WORD;
    Nx_AO1   : WORD;

    Rs_MW    : BOOL;   (* strob zapisi v pamyat' *)''')

# ------------------------------------------- 2. latch: perenos AO --------------
rep(u'''    nx.outvar(u"GVL_Regs.Rs_MData", nx.invar(u"GVL_Regs.Nx_MData", y=y),
              x=F.COL_OUT, y=y)''',
    u'''    nx.outvar(u"GVL_Regs.Rs_MData", nx.invar(u"GVL_Regs.Nx_MData", y=y),
              x=F.COL_OUT, y=y)
    y += 34
    nx.outvar(u"GVL_Regs.Rs_AO0", nx.invar(u"GVL_Regs.Nx_AO0", y=y),
              x=F.COL_OUT, y=y)
    y += 34
    nx.outvar(u"GVL_Regs.Rs_AO1", nx.invar(u"GVL_Regs.Nx_AO1", y=y),
              x=F.COL_OUT, y=y)''')

# ------------------------- 3. sborka AO v PLC_PRG (set' 16f posle portov) ------
rep(u'''    n16e = p.network(u"SET 16e: konsol CP/M i zerkalo shin")''',
    u'''    # ================= 16a. ANALOGOVYE VYHODY: sborka slova =================
    #  Dva porta na kanal: 04h -- mladshij bajt, 05h -- starshij (08h/09h --
    #  vtoroj kanal). Znachenie hranitsya v GVL_Regs.Rs_AO0 (para Rs_/Nx_,
    #  perenosit PRG_RegLatch), poetomu vyhod derzhitsya mezhdu komandami.
    n16a = p.network(u"SET 16a: analogovye vyhody: zapis' mladshego i starshego bajta")
    c_ao_wr = n16a.invar(u"vCtl_IO_Wr", y=30)
    c_ao_wc = n16a.invar(u"fbClock.Clk_Exec", y=70)
    c_ao_ad = n16a.invar(u"vIOAddr", y=110)
    c_ao_dt = n16a.invar(u"GVL_Regs.Rs_A", y=150)
    n16a.outvar(u"vAOWr", b_and(n16a, F.COL_BLK, 30, c_ao_wr,
                                n16a.invar(u"fbClock.Clk_Exec", y=70)),
                x=F.COL_OUT, y=30)
    #  maski dlya sklejki: mladshij bajt i starshij bajt
    c_ao_hi = n16a.invar(u"GVL_Regs.Rs_AO0", y=190)
    n16a.outvar(u"vAOLo", b_or(n16a, F.COL_BLK2, 190,
                              n16a.block(u"AND",
                                         [(PIN1, c_ao_hi),
                                          (PIN2, n16a.const(u"WORD#16#FF00", y=204))],
                                         [POUT], x=F.COL_BLK, y=190),
                              b_b2w(n16a, F.COL_BLK, 230,
                                    n16a.invar(u"GVL_Regs.Rs_A", y=230))),
                x=F.COL_OUT, y=190)
    c_ao_hi2 = n16a.invar(u"GVL_Regs.Rs_AO0", y=270)
    c_ao_dt2 = n16a.invar(u"GVL_Regs.Rs_A", y=310)
    n16a.outvar(u"vAOHi", b_or(n16a, F.COL_BLK2, 270,
                              n16a.block(u"AND",
                                         [(PIN1, c_ao_hi2),
                                          (PIN2, n16a.const(u"WORD#16#00FF", y=284))],
                                         [POUT], x=F.COL_BLK, y=270),
                              b_shl(n16a, F.COL_BLK2 + 160, 270,
                                    b_b2w(n16a, F.COL_BLK, 270, c_ao_dt2),
                                    n16a.const(u"8", y=284))),
                x=F.COL_OUT, y=270)
    #  vybor: port 04h -- mladshij, 05h -- starshij, inache -- bez izmenenij
    is04 = b_eq(n16a, F.COL_BLK2 + 320, 190,
                n16a.invar(u"vIOAddr", y=190), n16a.const(u"16#04", y=204))
    is05 = b_eq(n16a, F.COL_BLK2 + 320, 270,
                n16a.invar(u"vIOAddr", y=270), n16a.const(u"16#05", y=284))
    by_hi = b_sel(n16a, F.COL_BLK2 + 480, 270, is05,
                  n16a.invar(u"GVL_Regs.Rs_AO0", y=270),
                  n16a.invar(u"vAOHi", y=284), tip=u"WORD")
    by_lo = b_sel(n16a, F.COL_BLK2 + 480, 190, is04,
                  n16a.invar(u"by_hi", y=190), n16a.invar(u"vAOLo", y=204),
                  tip=u"WORD")
    n16a.outvar(u"vAONew", by_lo, x=F.COL_OUT, y=350)
    n16a.outvar(u"GVL_Regs.Nx_AO0",
                b_sel(n16a, F.COL_BLK2 + 640, 350,
                      n16a.invar(u"vAOWr", y=350),
                      n16a.invar(u"GVL_Regs.Rs_AO0", y=364),
                      n16a.invar(u"vAONew", y=378), tip=u"WORD"),
                x=F.COL_OUT, y=430)
    #  vtoroj kanal poka ne sobiraetsya otdel no: porty 24h/25h v karte ne
    #  zanyaty, i zerkalo vtorogo kanala ravnopravno perenositsya latch-em
    n16a.outvar(u"GVL_Regs.Nx_AO1", n16a.invar(u"GVL_Regs.Rs_AO1", y=470),
                x=F.COL_OUT, y=470)

    n16e = p.network(u"SET 16e: konsol CP/M i zerkalo shin")''')

# ------------------- 4. fizicheskie vyhody berut znacheniya iz GVL_Regs -------
rep(u'''    n16c.outvar(u"vOutAO0", io.out(u"Out_AO0"), x=F.COL_OUT + 600, y=30)''',
    u'''    n16c.outvar(u"vOutAO0", n16c.invar(u"GVL_Regs.Rs_AO0", y=30),
                x=F.COL_OUT + 600, y=30)''')
rep(u'''    n16d.outvar(u"vOutAO1", io.out(u"Out_AO1"), x=F.COL_OUT + 600, y=30)''',
    u'''    n16d.outvar(u"vOutAO1", n16d.invar(u"GVL_Regs.Rs_AO1", y=30),
                x=F.COL_OUT + 600, y=30)''')

# ------------------------------------ 5. katalog stenda -- po adresu 4000h -----
rep(u'''                0:  Z80_Mem[0] := 16#DB;  Z80_Mem[1] := 16#02;   (* IN A,(02h) *)''',
    u'''                0:  Z80_Mem[16#4000] := 16#DB;  Z80_Mem[16#4001] := 16#02;   (* IN A,(02h) *)''')
for k, code, port in ((1, u"16#DB", u"16#03"), (2, u"16#DB", u"16#06"),
                      (3, u"16#DB", u"16#07"), (4, u"16#DB", u"16#10"),
                      (5, u"16#DB", u"16#21"), (6, u"16#DB", u"16#00"),
                      (7, u"16#D3", u"16#01"), (8, u"16#D3", u"16#04"),
                      (9, u"16#D3", u"16#05")):
    old = u'                %d:  Z80_Mem[0] := %s;  Z80_Mem[1] := %s;' % (k, code, port)
    new = (u'                %d:  Z80_Mem[16#4000] := %s;  Z80_Mem[16#4001] := %s;'
           % (k, code, port))
    rep(old, new)

rep(u'''            ELSE
                Z80_Mem[0] := 16#76;
                GVL_InitRegs.Init_Vals[0] := 0;
            END_CASE
            GVL_InitRegs.Init_Sel_Dst := 0;
            GVL_InitRegs.Init_PC := 0;''',
    u'''            ELSE
                Z80_Mem[16#4000] := 16#76;
                GVL_InitRegs.Init_Vals[0] := 0;
            END_CASE
            GVL_InitRegs.Init_Sel_Dst := 0;
            (*  P R O G R A M M A  Zh I V E T  P O  A D R E S U  4000h:
                nulevaya stranitsa CP/M (vektory BDOS i BIOS) dolzhna
                ostavat'sya nedotronutoyoj -- eyo proveryayut drugie testy. *)
            Z80_Mem[0] := 16#C3;
            Z80_Mem[1] := 16#00;
            Z80_Mem[2] := 16#40;
            GVL_InitRegs.Init_PC := 16#4000;''')

io.open(P, u"w", encoding=u"utf-8").write(t)
print(u"patch_ao: %d zamen" % n)
print(u"nonascii: %d" % sum(1 for c in t if ord(c) > 127))
