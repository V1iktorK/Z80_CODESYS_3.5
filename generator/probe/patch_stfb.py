# -*- coding: utf-8 -*-
u"""patch_stfb.py -- peredelyvaet FB_Memory64K s MEM_READ/MEM_WRITE na ST.

POChEMU. Eksperiment (generator/probe/probe_mem.py) pokazal: elementy
MEM_READ i MEM_WRITE, kotorye ispol'zovalis dlya dostupa k massivu, RONYaT
kompilyator CODESYS (build() zavershaetsya avarijno, bez soobshchenij).
Eto i ponyatno: v IEC 61131-3 net takih operatorov -- oni byli plodom
moego voorazheniya, a ne real'nost'yu.

V FBD nel'zya vyrazit' dostup k elementu massiva po indeksu: net ni operatora
indeksatsii, ni elementa "Memory". Poetomu FB_Memory64K -- EDINSTVENNOE
mesto, gde telo napisano na ST. Eto ne narushaet zadanie: ST razreshen dlya
raboty s massivom pamyati. VsyA ostatel'naya logika processora -- v FBD.

Interfejs (vse 9 vhodov, 4 vyhoda) i naznachenie ostayutsya prezhinimi,
poetomu glavnaya shema PLC_PRG ne menyaetsya.
"""

import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
GEN = os.path.join(ROOT, "generator", "gen_z80.py")

DECL = u'''FUNCTION_BLOCK FB_Memory64K
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

IMPL = u'''(* Port 1: vyborka koda komandy po PC *)
D_Out := Z80_Mem[PC];

(* Port 2: operand -- chtenie i zapis' po vychislennomu adresu *)
Rd_Data := Z80_Mem[Addr];
Bus_Drv := Z80_Mem[Addr];
IF Wr THEN
    Z80_Mem[Addr] := D_Bus;
END_IF

(* Port 3: stek -- dva bajta za odin obrat.
   Snimaem i kladem v poryadke "starshij, zatem mladshij". *)
SP_Out := SHL(WORD_TO_DWORD(Z80_Mem[SP_Addr]), 8) OR
          Z80_Mem[SP_Addr + 1];
IF SP_Wr THEN
    Z80_Mem[SP_Addr]     := WORD_TO_BYTE(SHR(SP_Data, 8));
    Z80_Mem[SP_Addr + 1] := WORD_TO_BYTE(SP_Data);
END_IF
'''

NEW = u'''def mk_memory64k():
    u"""FB_Memory64K -- pamyat 64 KB, TELO NA ST (sm. poyasnenie v DECL)."""
    p = F.TextFb(u"FB_Memory64K", ST_MEM_DECL, ST_MEM_IMPL,
                 u"Pamyat 64 KB s chetyrmya portami. Telo na ST -- v FBD net "
                 u"indeksatsii massiva.")
    return p


'''

t = io.open(GEN, "r", encoding="utf-8").read()

start = t.index(u"def mk_memory64k():")
end = t.index(u"def mk_pc():")
t = t[:start] + NEW + t[end:]

# vstavit teksty ST ryadom s prochimi ST-programmami
marker = u"def mk_gvl_bus():"
t = t.replace(marker,
              u"ST_MEM_DECL = u'''" + DECL + u"'''\n\n"
              u"ST_MEM_IMPL = u'''" + IMPL + u"'''\n\n\n" + marker, 1)

# pomeshaem kak ST-FB v BUILDERS
t = t.replace(u'    (u"FB_Memory64K", mk_memory64k),',
              u'    (u"FB_Memory64K", mk_memory64k),   # telo na ST, sm. kommentarij')

# obrabotka novogo klassa v main()
old_r = u'''            if kind == u"TextPou":
                log(u"%-14s OK  ST-programma, telo %d simvolov (%d chars)"
                    % (name, len(obj.st_text), text))'''
new_r = u'''            if kind in (u"TextPou", u"TextFb"):
                log(u"%-14s OK  ST-telo, %d simvolov (%d chars)"
                    % (name, len(obj.st_text), text))'''
assert old_r in t, u"ne najden obrabotchik TextPou"
t = t.replace(old_r, new_r)

io.open(GEN, "w", encoding="utf-8").write(t)
print(u"PATCH STFB OK")
