# -*- coding: utf-8 -*-
u"""patch_prg_cpm2.py -- vstavlyaet v PLC_PRG seti 15..18 (I/O, apparatnyy
interfeys, BIOS, perehvat BDOS) i novye lokalnye peremennye.

Pervaya popytka ne srabotala, potomu chto marker soderzhal "--", a v fajle
uzhe stoit ":" (my zamenili dvojnye defisy, chtoby XML-komentarii byli
korrektny). Zdes markery vzyaty iz fakticheskogo teksta.
"""

import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
GEN = os.path.join(ROOT, "generator", "gen_z80.py")

t = io.open(GEN, "r", encoding="utf-8").read()

# ---- 1. lokalnye peremennye ----------------------------------------------------
old = u'    p.var(u"vFetch", u"BYTE", u"vybrannyj kod komandy")'
new = u'''    p.var(u"vFetch", u"BYTE", u"vybrannyj kod komandy")
    p.var(u"vIOAddr", u"BYTE", u"adres porta I/O")
    p.var(u"vIOData", u"BYTE", u"dannye s shiny I/O")
    p.var(u"vInDi", u"BYTE", u"diskretnye vhody PLK")
    p.var(u"vInAI0", u"WORD", u"analogovyy vhod 0")
    p.var(u"vInAI1", u"WORD", u"analogovyy vhod 1")
    p.var(u"vOutDO", u"BYTE", u"diskretnye vyhody PLK")
    p.var(u"vOutAO0", u"WORD", u"analogovyy vyhod 0")
    p.var(u"vOutAO1", u"WORD", u"analogovyy vyhod 1")
    p.var(u"vIsBDOS", u"BOOL", u"PC ukazyvaet na tochku vhoda BDOS")
    p.var(u"vIsBIOS", u"BOOL", u"PC ukazyvaet v tablitsu BIOS")
    p.var(u"fbIO", u"FB_IO_Ports", u"256 I/O-portov")
    p.var(u"fbHW", u"FB_HW_IO_PLC", u"apparatnyy interfeys PLK")
    p.var(u"fbBIOS", u"FB_CPM_BIOS", u"minimalnyy BIOS")'''
assert old in t, u"ne najdeny lokalnye peremennye"
t = t.replace(old, new, 1)

# ---- 2. seti 15..18 pered set yu 14 --------------------------------------------
anchor = u"    # ================= 14. R ================="
assert anchor in t, u"ne najden yakor seti 14"

NETS = u'''    # ================= 15. APPARATNYY VVOD/VYVOD PLK =================
    # ZACheM otdel naya set: instruktsiya Z80 ispolnyaetsya vnutri skana,
    # a fizicheskie %I/%Q PLK obnovlyayutsya tolko na granitse skana.
    # Poetomu vse vneshnie dannye prohodyat cherez bufery GVL_HW_Buffer:
    # vhody chitayutsya v nachale skana (eta set), vyhody pisutsya v konce.
    n15 = p.network(u"SET 15: APPARATNYY VVOD/VYVOD PLK")
    hw = n15.block(u"FB_HW_IO_PLC",
                   [(u"DI_0", n15.invar(u"GVL_HW_IO.DI_0", y=30)),
                    (u"DI_1", n15.invar(u"GVL_HW_IO.DI_1", y=60)),
                    (u"DI_2", n15.invar(u"GVL_HW_IO.DI_2", y=90)),
                    (u"DI_3", n15.invar(u"GVL_HW_IO.DI_3", y=120)),
                    (u"DI_4", n15.invar(u"GVL_HW_IO.DI_4", y=150)),
                    (u"DI_5", n15.invar(u"GVL_HW_IO.DI_5", y=180)),
                    (u"DI_6", n15.invar(u"GVL_HW_IO.DI_6", y=210)),
                    (u"DI_7", n15.invar(u"GVL_HW_IO.DI_7", y=240)),
                    (u"AI_0", n15.invar(u"GVL_HW_IO.AI_0", y=270)),
                    (u"AI_1", n15.invar(u"GVL_HW_IO.AI_1", y=300)),
                    (u"Out_DO", n15.invar(u"vOutDO", y=330)),
                    (u"Out_AO0", n15.invar(u"vOutAO0", y=360)),
                    (u"Out_AO1", n15.invar(u"vOutAO1", y=390))],
                   [u"In_DI", u"In_AI0", u"In_AI1",
                    u"DO_0", u"DO_1", u"DO_2", u"DO_3",
                    u"DO_4", u"DO_5", u"DO_6", u"DO_7",
                    u"AO_0", u"AO_1"],
                   x=F.COL_BLK2, y=30, instance=u"fbHW")
    n15.outvar(u"GVL_HW_Buffer.HW_In_DI", hw.out(u"In_DI"),
               x=F.COL_OUT + 600, y=30)
    n15.outvar(u"GVL_HW_Buffer.HW_In_AI0", hw.out(u"In_AI0"),
               x=F.COL_OUT + 600, y=70)
    n15.outvar(u"GVL_HW_Buffer.HW_In_AI1", hw.out(u"In_AI1"),
               x=F.COL_OUT + 600, y=110)
    for k in range(8):
        n15.outvar(u"GVL_HW_IO.DO_%d" % k, hw.out(u"DO_%d" % k),
                   x=F.COL_OUT + 600, y=150 + k * 30)
    n15.outvar(u"GVL_HW_IO.AO_0", hw.out(u"AO_0"), x=F.COL_OUT + 600, y=390)
    n15.outvar(u"GVL_HW_IO.AO_1", hw.out(u"AO_1"), x=F.COL_OUT + 600, y=420)

    # ================= 16. I/O-PORTY Z80 =================
    n16 = p.network(u"SET 16: I/O-PORTY: IN i OUT")
    c_ioen = n16.invar(u"GVL_Control.Ctl_IO_Rd", y=30)
    c_iowr = n16.invar(u"GVL_Control.Ctl_IO_Wr", y=60)
    c_n = n16.invar(u"vImm", y=90)
    io_addr = b_sel(n16, F.COL_BLK2, 60,
                    b_or(n16, F.COL_BLK2, 30, c_ioen, c_iowr),
                    n16.const(u"0", y=74), c_n)
    n16.outvar(u"vIOAddr", io_addr, x=F.COL_OUT + 300, y=60)
    n16.outvar(u"GVL_IO.Bus_IO_Addr", io_addr, x=F.COL_OUT + 300, y=90)
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
    n16.outvar(u"vIOData", io.out(u"Rd_Data"), x=F.COL_OUT + 600, y=120)
    n16.outvar(u"GVL_IO.Bus_IO_Data", io.out(u"Rd_Data"),
               x=F.COL_OUT + 600, y=160)
    n16.outvar(u"vOutDO", io.out(u"Out_DO"), x=F.COL_OUT + 600, y=200)
    n16.outvar(u"vOutAO0", io.out(u"Out_AO0"), x=F.COL_OUT + 600, y=240)
    n16.outvar(u"vOutAO1", io.out(u"Out_AO1"), x=F.COL_OUT + 600, y=280)

    # ================= 17. BIOS =================
    n17 = p.network(u"SET 17: BIOS: vektory i konsol")
    c_pc17 = n17.invar(u"fbPCLatch.Q", y=30)
    is_bios = n17.block(u"GE", [(PIN1, c_pc17),
                                (PIN2, n17.const(u"16#FA00", y=44))],
                        [POUT], x=F.COL_BLK2, y=30)
    is_bios2 = n17.block(u"LT", [(PIN1, c_pc17),
                                 (PIN2, n17.const(u"16#FB00", y=74))],
                         [POUT], x=F.COL_BLK2, y=60)
    bios_zone = b_and(n17, F.COL_BLK2 + 160, 45, is_bios, is_bios2)
    n17.outvar(u"vIsBIOS", bios_zone, x=F.COL_OUT, y=45)
    n17.block(u"FB_CPM_BIOS",
              [(u"Addr", c_pc17),
               (u"Con_In", n17.invar(u"GVL_CPM.Console_In", y=120)),
               (u"Con_Rdy", n17.invar(u"GVL_CPM.Console_InEn", y=150))],
              [u"Con_Out", u"Con_Wr", u"Con_Rd", u"Ret_HL", u"Is_Wboot", u"Done"],
              x=F.COL_BLK2 + 320, y=120, instance=u"fbBIOS")

    # ================= 18. PEREKhVAT BDOS =================
    # IMENNO TAK RABOTAET PEREKhVAT: programma delaet CALL 0F000h,
    # na shinu adresa popadaet 0F000h, i my eto vidim.
    n18 = p.network(u"SET 18: PEREKhVAT BDOS: PC = 0F000h")
    is_bdos = b_eq(n18, F.COL_BLK2, 30,
                   n18.invar(u"fbPCLatch.Q", y=30),
                   n18.const(u"16#F000", y=44))
    n18.outvar(u"vIsBDOS", is_bdos, x=F.COL_OUT, y=30)

'''

t = t.replace(anchor, NETS + anchor, 1)

io.open(GEN, "w", encoding="utf-8").write(t)
print(u"PATCH PRG_CPM2 OK")
