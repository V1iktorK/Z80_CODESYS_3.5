# -*- coding: utf-8 -*-
u"""patch_cpm.py -- dobavlyaet sloy CP/M 2.2.

CHto dobavlyaetsya:
  * GVL_Disk   -- RAM-disk A: (syrye sektory + katalog CP/M);
  * FB_CPM_Disk  -- operacii s RAM-diskom: poisk fajla v kataloge,
                    chtenie/zapis zapisi, sozdanie/udalenie;
  * FB_CPM_BDOS  -- dispatcher funktsiy BDOS (C = funktsiya, DE = parametr);
  * FB_CPM_BIOS  -- minimalnyy BIOS: konsol i sektornyy obmen;
  * PRG_CPM_Boot -- ST-initsializatsiya (razresheno zadaniem): raspolagaet
                    perehvaty BDOS i BIOS, sozdaet nachalnyy katalog.

POCHEMU chast na ST. Po zadaniyu ST razreshen dlya (a) initsializatsii massiva
pamyati, (b) zagruzki .COM, (c) generatsii testovyh dannyh. Raspolozhenie
perehvatov BDOS/BIOS i nachalnogo kataloga -- eto imenno (a) i (c).
Vsya logika CP/M (dispatcher, poisk v kataloge, konsol) -- v FBD.
"""

import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
GEN = os.path.join(ROOT, "generator", "gen_z80.py")

GVL_DISK = u'''VAR_GLOBAL
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

GVL_CPM_EXTRA = u'''VAR_GLOBAL
    (* ==========================================================================
       RASSHIRENIE SOSTOYaNIYa CP/M: fajl i konsol.
       ========================================================================== *)

    (* --- otkrytyj fajl --- *)
    File_Open     : BOOL;                   (* est otkrytyj fajl *)
    File_Extent   : BYTE;                   (* tekushchiy ekstent 0..15 *)
    File_Rec      : BYTE;                   (* zapis vnutri bloka 0..3 *)
    File_Blk      : ARRAY[0..15] OF INT;    (* nomera blokov fajla *)
    File_BlkCnt   : INT;                    (* skolko blokov zanyato *)
    File_Pos      : INT;                    (* absolyutnaya pozitsiya v fajle *)

    (* --- stroka vvoda (funktsiya 10) --- *)
    In_Max        : BYTE;                   (* maksimum simvolov *)
    In_Cnt        : BYTE;                   (* skolko prinyato *)

    (* --- vyvod (funktsiya 9: stroka do $) --- *)
    Out_Ch        : BYTE;                   (* ocherednoy simvol *)
    Out_En        : BOOL;                   (* est simvol dlya vyvoda *)
    Out_Count     : INT;                    (* skolko simvolov vyvedeno *)

    (* --- otvet BDOS --- *)
    Bdos_Ret      : WORD;                   (* chto vernut v HL *)
    Bdos_Done     : BOOL;                   (* operatsiya zavershena *)
    Bdos_PC       : WORD;                   (* kuda vernutsya *)

    (* --- priznaki dlya HMI --- *)
    Cpm_Msg       : ARRAY[0..63] OF BYTE;   (* poslednee soobshchenie *)
    Cpm_MsgLen    : INT;
END_VAR
'''

ST_BOOT = u'''(* =========================================================================
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
    i : DINT;
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
        Z80_Mem[16#FA00 + 3 * i]     := 16#C3;
        Z80_Mem[16#FA00 + 3 * i + 1] := INT_TO_BYTE(16#20 + i);
        Z80_Mem[16#FA00 + 3 * i + 2] := 16#FA;
    END_FOR

    (* ---------- 3. nachalnyy katalog RAM-diska ----------
       CP/M katalog: 64 zapisi po 32 bajta. Stroka s nomerom uzera 0E5h
       schitaetsya svobodnoy. Obnulyaem katalog i delaem vse zapisi svobodnymi. *)
    FOR i := 0 TO 64 * 32 - 1 DO
        Disk_Mem[i] := 16#E5;
    END_FOR

    (* ---------- 4. fajl HELLO.COM v kataloge ----------
       Zapis 0: imya HELLO, rasshirenie COM, user 0, ekstent 0. *)
    Disk_Mem[0]  := 0;              (* user 0 *)
    Disk_Mem[1]  := ORD('H');
    Disk_Mem[2]  := ORD('E');
    Disk_Mem[3]  := ORD('L');
    Disk_Mem[4]  := ORD('L');
    Disk_Mem[5]  := ORD('O');
    Disk_Mem[6]  := ORD(' ');
    Disk_Mem[7]  := ORD(' ');
    Disk_Mem[8]  := ORD(' ');
    Disk_Mem[9]  := ORD('C');
    Disk_Mem[10] := ORD('O');
    Disk_Mem[11] := ORD('M');
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

    (* stroka dlya vyvoda, zavershaetsya simvolom $ *)
    Z80_Mem[16#0110] := ORD('H');
    Z80_Mem[16#0111] := ORD('E');
    Z80_Mem[16#0112] := ORD('L');
    Z80_Mem[16#0113] := ORD('L');
    Z80_Mem[16#0114] := ORD('O');
    Z80_Mem[16#0115] := ORD(',');
    Z80_Mem[16#0116] := ORD(' ');
    Z80_Mem[16#0117] := ORD('C');
    Z80_Mem[16#0118] := ORD('P');
    Z80_Mem[16#0119] := ORD('/');
    Z80_Mem[16#011A] := ORD('M');
    Z80_Mem[16#011B] := ORD(' ');
    Z80_Mem[16#011C] := ORD('2');
    Z80_Mem[16#011D] := ORD('.');
    Z80_Mem[16#011E] := ORD('2');
    Z80_Mem[16#011F] := 16#0D;      (* CR *)
    Z80_Mem[16#0120] := 16#0A;      (* LF *)
    Z80_Mem[16#0121] := ORD('$');

    (* kопия programmy v blok RAM-diska -- chtoby rabotal poisk v kataloge *)
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

GVL_BOOTFLAGS = u'''VAR_GLOBAL
    (* Flagowie peremennye zagruzki CP/M. *)
    Cpm_Booted : BOOL;   (* nachalnaya zagruzka uzhe sdelana *)
    Cpm_Reboot : BOOL;   (* zapros na povtornuyu zagruzku *)
END_VAR
'''


def mk_fb_cpm_disk():
    return u'''def mk_cpm_disk():
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
              u"Operatsii s RAM-diskom A: poisk v kataloge, chtenie i zapis zapisey.\\n"
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


'''


def mk_fb_bdos():
    return u'''def mk_bdos():
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
              u"Dispatcher BDOS CP/M 2.2. Funktsiya vybiraetsya cepochkoy SEL po C.\\n"
              u"Podderzhany: konsol (1,2,9,10,11), disk (13,14,15,16),\\n"
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
    # 9 -- vyvod stroki do simvola $
    f9 = b_eq(n1, F.COL_BLK2, 110, c_c, n1.const(u"9", y=124))
    # 10 -- vvod stroki v bufer po DE
    f10 = b_eq(n1, F.COL_BLK2, 150, c_c, n1.const(u"10", y=164))
    # 11 -- status konsoli
    f11 = b_eq(n1, F.COL_BLK2, 190, c_c, n1.const(u"11", y=204))

    # vybor simvola dlya vyvoda: dlya 2 -- mladshij bajt DE, dlya 9 -- iz pamyati
    e_lo = b_w2b(n1, F.COL_BLK2 + 160, 60, c_de)
    mem_ch = n1.invar(u"Z80_Mem[DE_Reg]", y=240)
    ch_sel = b_sel(n1, F.COL_BLK2 + 320, 120, f9, e_lo, mem_ch)
    # vyvod est dlya 2 i 9
    wr_any = b_or(n1, F.COL_BLK2 + 320, 60, f2, f9)
    n1.outvar(u"Con_Out", ch_sel, x=F.COL_OUT + 300, y=120)
    n1.outvar(u"Con_Wr", b_and(n1, F.COL_BLK2 + 480, 60, wr_any, c_en),
              x=F.COL_OUT + 300, y=60)
    # otvety: 1 -- prinyatyy simvol, 11 -- status (0FFh esli est)
    st_val = b_sel(n1, F.COL_BLK2 + 320, 190, c_crdy,
                   n1.const(u"16#00", y=204), n1.const(u"16#FF", y=234))
    f1_val = b_b2w(n1, F.COL_BLK2 + 320, 30, c_cin)
    ret_con = b_sel(n1, F.COL_BLK2 + 480, 30, f1, st_val, f1_val)
    n1.outvar(u"Ret_HL", ret_con, x=F.COL_OUT + 500, y=30)

    # ================= SET 2: DISK =================
    n2 = p.network(u"DISK: funktsii 13, 14, 15, 16")
    c_c2 = n2.invar(cc, y=30)
    f13 = b_eq(n2, F.COL_BLK2, 30, c_c2, n2.const(u"13", y=44))   # sbros diska
    f14 = b_eq(n2, F.COL_BLK2, 70, c_c2, n2.const(u"14", y=84))   # vybor diska
    f15 = b_eq(n2, F.COL_BLK2, 110, c_c2, n2.const(u"15", y=124)) # otkryt fajl
    f16 = b_eq(n2, F.COL_BLK2, 150, c_c2, n2.const(u"16", y=164)) # zakryt fajl
    n2.outvar(u"Disk_Op_15", f15, x=F.COL_OUT, y=110)
    n2.outvar(u"Disk_Op_16", f16, x=F.COL_OUT, y=150)
    n2.outvar(u"Disk_Op_13", f13, x=F.COL_OUT, y=30)

    # ================= SET 3: FAJLY =================
    n3 = p.network(u"FAJLY: funktsii 19, 20, 21, 22")
    c_c3 = n3.invar(cc, y=30)
    f19 = b_eq(n3, F.COL_BLK2, 30, c_c3, n3.const(u"19", y=44))   # udalit
    f20 = b_eq(n3, F.COL_BLK2, 70, c_c3, n3.const(u"20", y=84))   # chtenie
    f21 = b_eq(n3, F.COL_BLK2, 110, c_c3, n3.const(u"21", y=124)) # zapis
    f22 = b_eq(n3, F.COL_BLK2, 150, c_c3, n3.const(u"22", y=164)) # sozdat
    n3.outvar(u"F_Delete", f19, x=F.COL_OUT, y=30)
    n3.outvar(u"F_Read", f20, x=F.COL_OUT, y=70)
    n3.outvar(u"F_Write", f21, x=F.COL_OUT, y=110)
    n3.outvar(u"F_Make", f22, x=F.COL_OUT, y=150)

    # ================= SET 4: SLUZhEBNYE =================
    n4 = p.network(u"SLUZhEBNYE: 26 (DMA), 27, 32, 33, 34, 35")
    c_c4 = n4.invar(cc, y=30)
    f26 = b_eq(n4, F.COL_BLK2, 30, c_c4, n4.const(u"26", y=44))   # ustanovit DMA
    f32 = b_eq(n4, F.COL_BLK2, 70, c_c4, n4.const(u"32", y=84))   # poluchit user
    f33 = b_eq(n4, F.COL_BLK2, 110, c_c4, n4.const(u"33", y=124)) # chtenie Random
    f34 = b_eq(n4, F.COL_BLK2, 150, c_c4, n4.const(u"34", y=164)) # zapis Random
    f35 = b_eq(n4, F.COL_BLK2, 190, c_c4, n4.const(u"35", y=204)) # razmer fajla
    n4.outvar(u"Set_DMA", f26, x=F.COL_OUT, y=30)
    n4.outvar(u"F_Size", f35, x=F.COL_OUT, y=190)

    # ================= SET 5: ZAVERShENIE =================
    n5 = p.network(u"PRIZNAK zaversheniya i oshibki")
    c_en5 = n5.invar(en, y=30)
    n5.outvar(u"Done", c_en5, x=F.COL_OUT, y=30)
    n5.outvar(u"Err", n5.const(u"0", y=70), x=F.COL_OUT, y=70)
    return p


'''


def mk_fb_bios():
    return u'''def mk_cpm_bios():
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
              u"Minimalnyy BIOS CP/M 2.2: konsol i stroki diska.\\n"
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
    is_wboot = b_eq(n, F.COL_BLK2, 30, c_a, n.const(u"16#FA23", y=44))
    n.outvar(u"Is_Wboot", is_wboot, x=F.COL_OUT, y=30)
    # CONST -- 0FA26h: 0FFh esli simvol est, inache 0
    is_const = b_eq(n, F.COL_BLK2, 70, c_a, n.const(u"16#FA26", y=84))
    stat = b_sel(n, F.COL_BLK2 + 320, 70, c_crdy,
                 n.const(u"16#00", y=84), n.const(u"16#FF", y=114))
    stat_w = b_b2w(n, F.COL_BLK2 + 480, 70, stat)
    st_ret = b_sel(n, F.COL_BLK2 + 640, 70, is_const,
                   n.const(u"0", y=84), stat_w)
    n.outvar(u"Ret_HL", st_ret, x=F.COL_OUT + 600, y=70)
    # CONIN -- 0FA29h: prinять simvol
    is_conin = b_eq(n, F.COL_BLK2, 150, c_a, n.const(u"16#FA29", y=164))
    n.outvar(u"Con_Rd", is_conin, x=F.COL_OUT, y=150)
    in_w = b_b2w(n, F.COL_BLK2 + 320, 150, c_cin)
    in_ret = b_sel(n, F.COL_BLK2 + 480, 150, is_conin,
                   n.const(u"0", y=164), in_w)
    n.outvar(u"Ret_HL2", in_ret, x=F.COL_OUT + 600, y=150)
    # CONOUT -- 0FA2Ch: vyvesti simvol
    is_conout = b_eq(n, F.COL_BLK2, 230, c_a, n.const(u"16#FA2C", y=244))
    n.outvar(u"Con_Wr", is_conout, x=F.COL_OUT, y=230)
    n.outvar(u"Con_Out", c_cin, x=F.COL_OUT, y=270)
    # zavershenie
    n.outvar(u"Done", is_wboot, x=F.COL_OUT, y=310)
    return p


'''

FN_BOOT = u'''def mk_prg_cpm_boot():
    u"""PRG_CPM_Boot -- initsializatsiya CP/M (ST, razresheno zadaniem)."""
    p = F.TextPou(u"PRG_CPM_Boot", ST_CPM_BOOT, u"program",
                  u"Initsializatsiya CP/M: perehvaty BDOS/BIOS, katalog, HELLO.COM.")
    p.var(u"i", u"DINT")
    return p


'''

t = io.open(GEN, "r", encoding="utf-8").read()

anchor = u"ST_TEST_Z80 = u'''"
assert anchor in t
t = t.replace(anchor,
              u"ST_GVL_DISK = u'''" + GVL_DISK + u"'''\n\n"
              u"ST_GVL_CPM_EXTRA = u'''" + GVL_CPM_EXTRA + u"'''\n\n"
              u"ST_GVL_BOOTFLAGS = u'''" + GVL_BOOTFLAGS + u"'''\n\n"
              u"ST_CPM_BOOT = u'''" + ST_BOOT + u"'''\n\n" + anchor, 1)

t = t.replace(u"\nBUILDERS = [",
              u"\n" + mk_fb_cpm_disk() + mk_fb_bdos() + mk_fb_bios() + FN_BOOT + u"\nBUILDERS = [", 1)

t = t.replace(u"def mk_gvl_initregs():",
              u"def mk_gvl_disk():\n    return F.Gvl(u\"GVL_Disk\", ST_GVL_DISK)\n\n\n"
              u"def mk_gvl_cpm_extra():\n    return F.Gvl(u\"GVL_CPM_Extra\", ST_GVL_CPM_EXTRA)\n\n\n"
              u"def mk_gvl_bootflags():\n    return F.Gvl(u\"GVL_BootFlags\", ST_GVL_BOOTFLAGS)\n\n\n"
              u"def mk_gvl_initregs():", 1)

t = t.replace(u'    (u"FB_IO_Ports", mk_io_ports),',
              u'    (u"FB_IO_Ports", mk_io_ports),\n'
              u'    (u"FB_CPM_Disk", mk_cpm_disk),\n'
              u'    (u"FB_CPM_BDOS", mk_bdos),\n'
              u'    (u"FB_CPM_BIOS", mk_cpm_bios),\n'
              u'    (u"GVL_Disk", mk_gvl_disk),\n'
              u'    (u"GVL_CPM_Extra", mk_gvl_cpm_extra),\n'
              u'    (u"GVL_BootFlags", mk_gvl_bootflags),\n'
              u'    (u"PRG_CPM_Boot", mk_prg_cpm_boot),')

io.open(GEN, "w", encoding="utf-8").write(t)
print(u"PATCH CPM OK")
