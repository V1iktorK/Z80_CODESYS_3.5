# -*- coding: utf-8 -*-
u"""patch_hw_io.py -- dobavlyaet apparatnyj interfeys PLK.

Chto dobavlyaetsya:
  * GVL_HW_IO   -- peremennye, privyazannye k fizicheskim vhodam/vyhodam PLK
                   cherez AT %IX / %QX / %IW / %QW (Device Tree CODESYS);
  * GVL_IO      -- 256 I/O-portov Z80 (ARRAY[0..255] OF BYTE) + shiny
                   Bus_IO_Addr i Bus_IO_Data;
  * FB_HW_IO_PLC -- sinkhronizatsiya: v nachale skana vhody kopiruyutsya
                   v bufer chteniya, v konce skana bufer zapisi uhodit
                   na fizicheskie vyhody. Eto isklyuchaet gonki mezhdu
                   skan-tsiklom PLK i ispolneniem instruktsiy Z80.

POCHEMU TAK. Instruktsiya Z80 ispolnyaetsya vnutri skana, a fizicheskie
vhody PLK obnovlyayutsya tolko na granitse skana. Esli chitat %IX napryamuyu
iz instruktsii, znachenie budet "plavat" posredi skana. Poetomu vse vneshnie
dannye prohodyat cherez bufery GVL_HW_IO_In / GVL_HW_IO_Out, a obmen s
"zhivymi" peremennymi %I/%Q proishodit strogo v nachale i v konce skana.
"""

import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
GEN = os.path.join(ROOT, "generator", "gen_z80.py")

GVL_HW_IO = u'''VAR_GLOBAL
    (* ==========================================================================
       APPARATNYY VVOD/VYVOD PLK.

       Eti peremennye privyazany k fizicheskim kanalam PLK cherez AT %...
       Privyazka deystvuet, kogda v Device Tree dobavleny moduli vvoda/vyvoda
       i nastroyeny ikh kanaly. Imena %IX0.0 i t. d. sootvetstvuyut
       raspolozheniyu moduley; pri drugom PLK ih nado perenastroit.

       V rezhime SIMULYaTsII CODESYS eti zhe peremennye rabotayut kak
       obychnye: ih mozhno menyat vruchnuyu v Watch-okne, poetomu vsya
       logika proveryaetsya bez zheleza.
       ========================================================================== *)

    (* --- diskretnye vhody: IN 00h chitaet etot bajt --- *)
    DI_0 : BOOL AT %IX0.0;
    DI_1 : BOOL AT %IX0.1;
    DI_2 : BOOL AT %IX0.2;
    DI_3 : BOOL AT %IX0.3;
    DI_4 : BOOL AT %IX0.4;
    DI_5 : BOOL AT %IX0.5;
    DI_6 : BOOL AT %IX0.6;
    DI_7 : BOOL AT %IX0.7;

    (* --- diskretnye vyhody: OUT 01h pishet etot bajt --- *)
    DO_0 : BOOL AT %QX0.0;
    DO_1 : BOOL AT %QX0.1;
    DO_2 : BOOL AT %QX0.2;
    DO_3 : BOOL AT %QX0.3;
    DO_4 : BOOL AT %QX0.4;
    DO_5 : BOOL AT %QX0.5;
    DO_6 : BOOL AT %QX0.6;
    DO_7 : BOOL AT %QX0.7;

    (* --- analogovye vhody: IN 02h/03h chitayut eto slovo --- *)
    AI_0 : INT AT %IW0;
    AI_1 : INT AT %IW1;

    (* --- analogovye vyhody: OUT 04h/05h pishut eto slovo --- *)
    AO_0 : INT AT %QW0;
    AO_1 : INT AT %QW1;
END_VAR
'''

GVL_HW_BUFFER = u'''VAR_GLOBAL
    (* ==========================================================================
       BUFERY OBVENA S ZHELEZOM.

       V nachale skana FB_HW_IO_PLC kopiruet syuda fizicheskie vhody,
       v konce skana -- otpravlyaet отсюда na fizicheskie vyhody.
       Instruktsii Z80 rabotayut TOLKO s etimi buferami, poetomu
       povedenie vnutri skana determinovano i ne zavisit ot togo,
       kogda runtime PLK obnovit %I/%Q.
       ========================================================================== *)
    HW_In_DI   : BYTE;   (* snímok diskretnyh vhodov *)
    HW_In_AI0  : WORD;   (* snímok analogovogo vhoda 0 *)
    HW_In_AI1  : WORD;   (* snímok analogovogo vhoda 1 *)

    HW_Out_DO  : BYTE;   (* chto vyvesti na diskretnye vyhody *)
    HW_Out_AO0 : WORD;   (* chto vyvesti na analogovyy vyhod 0 *)
    HW_Out_AO1 : WORD;   (* chto vyvesti na analogovyy vyhod 1 *)

    HW_Scan_Cnt : DWORD; (* schetchik skanov -- dlya diagnostiki *)
END_VAR
'''

GVL_IO = u'''VAR_GLOBAL
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

GVL_CPM = u'''VAR_GLOBAL
    (* ==========================================================================
       SOSTOYaNIE CP/M 2.2.
       ========================================================================== *)

    (* --- konsol --- *)
    Console_In   : BYTE;      (* simvol ot terminala (0 = net) *)
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
    Disk_DMA     : WORD;      (* adres peredachi *)

    (* --- statistika dlya HMI --- *)
    Cpm_Insn_Cnt : DWORD;     (* skolko instruktsiy vypolneno *)
END_VAR
'''

GVL_HWIO_IN = u'''VAR_GLOBAL
    (* ==========================================================================
       GVL_HW_IO_In / GVL_HW_IO_Out -- starye imena buferov, sokhraneny dlya
       sovmestimosti s tekstom zadaniya. Rabotayut kak obych nye peremennye.
       ========================================================================== *)
    HW_In_DI   : BYTE;
    HW_In_AI0  : WORD;
    HW_In_AI1  : WORD;
    HW_Out_DO  : BYTE;
    HW_Out_AO0 : WORD;
    HW_Out_AO1 : WORD;
    HW_Scan_Cnt : DWORD;
END_VAR
'''


def mk_fb_hw_io():
    return u'''def mk_fb_hw_io():
    u"""FB_HW_IO_PLC -- sinkhronizatsiya s fizicheskimi vhodami/vyhodami PLK.

    VHODY (fizicheskie kanaly PLK):
        DI_* : BOOL  -- diskretnye vhody %IX0.0..%IX0.7
        AI_0, AI_1 : INT -- analogovye vhody %IW0, %IW1
        Out_DO : BYTE -- chto vyvesti na diskretnye vyhody
        Out_AO0, Out_AO1 : WORD -- chto vyvesti na analogovye vyhody
    VYHODY (snímok dlya Z80):
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
              u"Apparatnyy interfeys PLK: upakovka vhodov i raspredelenie vyhodov.\\n"
              u"Vse obmen s %I/%Q prohodit cherez etot blok.")
    # --- vhody ot PLK ---
    din = []
    for k in range(8):
        din.append(p.var_in(u"DI_%d" % k, u"BOOL", u"diskretnyy vhod %IX0.%d" % k))
    p.var_in(u"AI_0", u"INT", u"analogovyy vhod %IW0")
    p.var_in(u"AI_1", u"INT", u"analogovyy vhod %IW1")
    p.var_in(u"Out_DO", u"BYTE", u"znachenie dlya diskretnyh vyhodov")
    p.var_in(u"Out_AO0", u"WORD", u"znachenie dlya %QW0")
    p.var_in(u"Out_AO1", u"WORD", u"znachenie dlya %QW1")
    # --- vyhody dlya Z80 ---
    p.var_out(u"In_DI", u"BYTE", u"upakovannye diskretnye vhody")
    p.var_out(u"In_AI0", u"WORD", u"analogovyy vhod 0")
    p.var_out(u"In_AI1", u"WORD", u"analogovyy vhod 1")
    for k in range(8):
        p.var_out(u"DO_%d" % k, u"BOOL", u"diskretnyy vyhod %QX0.%d" % k)
    p.var_out(u"AO_0", u"INT", u"analogovyy vyhod %QW0")
    p.var_out(u"AO_1", u"INT", u"analogovyy vyhod %QW1")

    # --- set 1: upakovka diskretnyh vhodov v bajt ---
    # ZDES proishodit upakovka BOOL -> BYTE (obratnaya k raspakovke v FB_BitUnpack8)
    n1 = p.network(u"Upakovka diskretnyh vhodov: BOOL -> BYTE")
    acc = None
    for k in range(8):
        c = n1.invar(u"DI_%d" % k, y=30 + k * 40)
        tb = n1.block(u"BOOL_TO_BYTE", [(PINU, c)], [POUT], x=F.COL_BLK, y=30 + k * 40)
        if k == 0:
            acc = tb
        else:
            sh = b_shl(n1, F.COL_BLK2, 30 + k * 40, tb,
                       n1.const(u"%d" % k, y=44 + k * 40))
            acc = b_add(n1, F.COL_BLK2 + 160, 30 + k * 40, acc, sh)
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


'''


# --- Zamenit ST-programmu inicializatsii: dobavit kartu portov ------------------
FN = mk_fb_hw_io()

t = io.open(GEN, "r", encoding="utf-8").read()

# 1. dobavit GVL i generator v nachalo (pered ST_TEST_Z80)
anchor = u"ST_TEST_Z80 = u'''"
assert anchor in t
gvls = (u"ST_GVL_HW_IO = u'''" + GVL_HW_IO + u"'''\n\n"
        u"ST_GVL_HW_BUFFER = u'''" + GVL_HW_BUFFER + u"'''\n\n"
        u"ST_GVL_IO = u'''" + GVL_IO + u"'''\n\n"
        u"ST_GVL_CPM = u'''" + GVL_CPM + u"'''\n\n")
t = t.replace(anchor, gvls + anchor, 1)

# 2. dobavit FB_HW_IO_PLC pered BUILDERS
t = t.replace(u"\nBUILDERS = [", u"\n" + FN + u"\nBUILDERS = [", 1)

# 3. dobavit generatory GVL
t = t.replace(u"def mk_gvl_initregs():",
              u"def mk_gvl_hw_io():\n    return F.Gvl(u\"GVL_HW_IO\", ST_GVL_HW_IO)\n\n\n"
              u"def mk_gvl_hw_buffer():\n    return F.Gvl(u\"GVL_HW_Buffer\", ST_GVL_HW_BUFFER)\n\n\n"
              u"def mk_gvl_io():\n    return F.Gvl(u\"GVL_IO\", ST_GVL_IO)\n\n\n"
              u"def mk_gvl_cpm():\n    return F.Gvl(u\"GVL_CPM\", ST_GVL_CPM)\n\n\n"
              u"def mk_gvl_initregs():", 1)

# 4. dobavit v BUILDERS
t = t.replace(u'    (u"GVL_InitRegs", mk_gvl_initregs),',
              u'    (u"GVL_HW_IO", mk_gvl_hw_io),\n'
              u'    (u"GVL_HW_Buffer", mk_gvl_hw_buffer),\n'
              u'    (u"GVL_IO", mk_gvl_io),\n'
              u'    (u"GVL_CPM", mk_gvl_cpm),\n'
              u'    (u"GVL_InitRegs", mk_gvl_initregs),\n'
              u'    (u"FB_HW_IO_PLC", mk_fb_hw_io),')

io.open(GEN, "w", encoding="utf-8").write(t)
print(u"PATCH HW_IO OK")
