# -*- coding: utf-8 -*-
u"""patch_net_split.py -- raspredelyaet vyhody mnogovyhodovyh FB po setyam.

PRAVILO, VYYaSNENNOE EKSPERIMENTOM (i ochen neochevidnoe):
    Biblioteka fbd_xml schitaet ispolzovaniya BLOKA, a ne otdel nogo vyvoda:
    v _expand_fanout kazhdaya ssylka na vyhod dobavlyaet +1 k schetchiku
    ispolzovaniy localId etogo bloka. Poetomu esli u bloka N vyhodov i v
    ODNOY seti prochitany >= 2 iz nih, eto vyglyadit kak fan-out, i popytka
    klonirovat vyzov FB zavershaetsya oshibkoy.

SLEDSTVIE: kazhdyy vyhod mnogovyhodovogo FB dolzhen byt prochitan
V OTDELNOY SETI. Odin vyhod -- odna set (ili odna peremennaya).

Eto zhe ogranichenie uzhe soblyudalos ranee: vtorye vyhody FB_Clock,
FB_PC_Z80, FB_ControlUnit i dr. byli razneseny po setyam. Zdes my privodim
k etomu zhe pravilu FB_HW_IO_PLC i FB_IO_Ports.
"""

import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
GEN = os.path.join(ROOT, "generator", "gen_z80.py")

t = io.open(GEN, "r", encoding="utf-8").read()

# --- zamena setey 15..18 na versiyu s razdeleniem po setyam ---------------------
start = t.index(u'    # ================= 15. APPARATNYY VVOD/VYVOD PLK =================')
end = t.index(u'    # ================= 14. R =================')

NETS = u'''    # ================= 15. APPARATNYY VVOD/VYVOD PLK =================
    # ZACheM otdel nye seti na kazhdyy vyhod: sm. poyasnenie v
    # generator/probe/patch_net_split.py -- biblioteka schitaet ispolzovaniya
    # BLOKA, poetomu v odnoy seti mozhno prochitat tolko ODIN ego vyhod.
    #
    # POCHEMU voobshche otdel nyy blok: instruktsiya Z80 ispolnyaetsya vnutri
    # skana, a fizicheskie %I/%Q PLK obnovlyayutsya tolko na granitse skana.
    # Vse vneshnie dannye prohodyat cherez bufery GVL_HW_Buffer.
    n15 = p.network(u"SET 15: APPARATNYY VVOD PLK: upakovka vhodov")
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
    n15.outvar(u"vInDi", hw.out(u"In_DI"), x=F.COL_OUT + 600, y=30)

    n15b = p.network(u"SET 15b: analogovye vhody")
    n15b.outvar(u"vInAI0", hw.out(u"In_AI0"), x=F.COL_OUT + 600, y=30)

    n15c = p.network(u"SET 15c: vtoroy analogovyy vhod")
    n15c.outvar(u"vInAI1", hw.out(u"In_AI1"), x=F.COL_OUT + 600, y=30)

    n15d = p.network(u"SET 15d: diskretnye vyhody PLK (13 kanalov)")
    for k in range(8):
        n15d.outvar(u"GVL_HW_IO.DO_%d" % k, hw.out(u"DO_%d" % k),
                    x=F.COL_OUT + 600, y=30 + k * 30)

    n15e = p.network(u"SET 15e: analogovye vyhody PLK")
    n15e.outvar(u"GVL_HW_IO.AO_0", hw.out(u"AO_0"), x=F.COL_OUT + 600, y=30)

    n15f = p.network(u"SET 15f: vtoroy analogovyy vyhod PLK")
    n15f.outvar(u"GVL_HW_IO.AO_1", hw.out(u"AO_1"), x=F.COL_OUT + 600, y=30)

    # snímok vhodov v bufery (chitaem po imeni, chtoby byl odin potrebitel)
    n15g = p.network(u"SET 15g: bufery vhodov dlya Z80")
    n15g.outvar(u"GVL_HW_Buffer.HW_In_DI",
                n15g.invar(u"vInDi", y=30), x=F.COL_OUT, y=30)
    n15g.outvar(u"GVL_HW_Buffer.HW_In_AI0",
                n15g.invar(u"vInAI0", y=70), x=F.COL_OUT, y=70)
    n15g.outvar(u"GVL_HW_Buffer.HW_In_AI1",
                n15g.invar(u"vInAI1", y=110), x=F.COL_OUT, y=110)

    # ================= 16. I/O-PORTY Z80 =================
    n16 = p.network(u"SET 16: I/O-PORTY: adres porta")
    c_ioen = n16.invar(u"GVL_Control.Ctl_IO_Rd", y=30)
    c_iowr = n16.invar(u"GVL_Control.Ctl_IO_Wr", y=60)
    c_n = n16.invar(u"vImm", y=90)
    io_addr = b_sel(n16, F.COL_BLK2, 60,
                    b_or(n16, F.COL_BLK2, 30, c_ioen, c_iowr),
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
                                (PIN2, n17.const(u"16#FA00", y=44))],
                        [POUT], x=F.COL_BLK2, y=30)
    is_bios2 = n17.block(u"LT", [(PIN1, c_pc17),
                                 (PIN2, n17.const(u"16#FB00", y=74))],
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
                   n18.const(u"16#F000", y=44))
    n18.outvar(u"vIsBDOS", is_bdos, x=F.COL_OUT, y=30)

'''

t = t[:start] + NETS + t[end:]

# dobavit nedostayushchie lokalnye peremennye
old_v = u'    p.var(u"fbBIOS", u"FB_CPM_BIOS", u"minimalnyy BIOS")'
new_v = u'''    p.var(u"fbBIOS", u"FB_CPM_BIOS", u"minimalnyy BIOS")
    p.var(u"vBiosOut", u"BYTE", u"simvol konsoli ot BIOS")
    p.var(u"vBiosWr", u"BOOL", u"strob vyvoda BIOS")
    p.var(u"vBiosRd", u"BOOL", u"zapros vvoda BIOS")'''
assert old_v in t, u"ne najdeny peremennye fbBIOS"
t = t.replace(old_v, new_v, 1)

io.open(GEN, "w", encoding="utf-8").write(t)
print(u"PATCH NET_SPLIT OK")
