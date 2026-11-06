# -*- coding: utf-8 -*-
u"""patch_ioports.py -- dobavlyaet FB_IO_Ports (256 portov Z80).

FB_IO_Ports -- eto "CHIP PPI" emulyatora: on privyazyvaet adresa portov Z80
k apparatnym buferam PLK i konsoli CP/M.

Realizaciya -- cepochka SEL po adresu porta (tot zhe priem, chto v
FB_RegFileZ80 dlya vyborny registrov). Cepochka daet dva rezul tata:
    Rd_Data -- chto vernut na shinu pri IN
    Wr_Do   -- zapisat li znachenie iz shiny v etot port

POCHEMU cepochka SEL, a ne MUX: kazhdyy adres -- otdel noe uslovie
sravneniya, znacheniya peredayutsya pryamymi ssylkami. Poetomu net
fan-out i CODESYS ne vybrasyvaet POU (sm. docs/04_SHEMY.md).
"""

import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
GEN = os.path.join(ROOT, "generator", "gen_z80.py")

FN = u'''def mk_io_ports():
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
              u"256 I/O-portov Z80. Privyazka portov k apparatnym buferam PLK\\n"
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
    hi0 = b_shr(n1, F.COL_BLK, 120, c_ai0b, n1.const(u"8", y=134))
    lo1 = b_w2b(n1, F.COL_BLK, 150, c_ai1a)
    hi1 = b_shr(n1, F.COL_BLK, 180, c_ai1b, n1.const(u"8", y=194))
    # status konsoli: bit 0 = est simvol
    st = n1.block(u"BOOL_TO_BYTE", [(PINU, c_crdy1)], [POUT],
                  x=F.COL_BLK, y=240)
    # status CP/M: bit 0 = zagruzhen
    stc = n1.block(u"BOOL_TO_BYTE", [(PINU, c_cpm1)], [POUT],
                   x=F.COL_BLK, y=270)

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

    rdata = sel_chain(n1, c_addr, n1.const(u"0", y=350), cases,
                      x=F.COL_BLK2 + 160, y0=30, ystep=40)
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
    n2.outvar(u"Out_DO", b_sel(n2, F.COL_BLK2 + 320, 30, we01,
                               n2.const(u"0", y=44), c_dwr), x=F.COL_OUT + 300, y=30)
    # vyhod 20h -- zapros ostanovki: bit 0
    is20 = b_eq(n2, F.COL_BLK2, 90, c_addr2, n2.const(u"16#20", y=104))
    we20 = b_and(n2, F.COL_BLK2 + 160, 90, c_wr2, is20)
    b0 = n2.block(u"AND", [(PIN1, c_dwr2), (PIN2, n2.const(u"16#01", y=118))],
                  [POUT], x=F.COL_BLK2 + 320, y=90)
    n2.outvar(u"Halt_Req", b_and(n2, F.COL_BLK2 + 480, 90, we20, b0),
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


'''


t = io.open(GEN, "r", encoding="utf-8").read()
t = t.replace(u"\nBUILDERS = [", u"\n" + FN + u"\nBUILDERS = [", 1)
t = t.replace(u'    (u"FB_HW_IO_PLC", mk_fb_hw_io),',
              u'    (u"FB_HW_IO_PLC", mk_fb_hw_io),\n    (u"FB_IO_Ports", mk_io_ports),')
io.open(GEN, "w", encoding="utf-8").write(t)
print(u"PATCH IOPORTS OK")
