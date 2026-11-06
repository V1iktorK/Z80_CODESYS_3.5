# -*- coding: utf-8 -*-
u"""Sborka izolirovannogo proekta iz tests/iso.

ZAPUSKAT TOLKO cherez CODESYS. Rezultat -- log/iso.log.

ZADAChA. Ponyat, v chem istochnik oshibok C32: v FBD-shemah ili v
ST-programmah. Sobiraem proekt tolko iz nih i smotrim itog kompilyacii.
"""
import io
import os
import traceback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, u"src")
PROJ = os.path.join(ROOT, u"tests", u"iso.project")
LOG = os.path.join(ROOT, u"log", u"iso.log")
#  V A Zh N O: import idet NAPRYaMUYu iz src/, kak v build.py.
#  Pervaya versiya kopirovala fajly v tests/iso i importirovala kopii --
#  i oshibki C32 (36 shtuk) pri etom PROPADALI. Znachit raznica byla v
#  kopirovanii/puti, a ne v soderzhimom. Chtoby izolyaciya chto-to
#  dokazyvala, usloviya dolzhny sovpadat s boevoj sborkoj.
ISO = SRC
_f = None


def log(m):
    global _f
    if _f is None:
        if not os.path.isdir(os.path.dirname(LOG)):
            os.makedirs(os.path.dirname(LOG))
        _f = io.open(LOG, u"w", encoding=u"utf-8")
    _f.write(m + u"\n")
    _f.flush()


def main():
    import scriptengine
    for p in list(scriptengine.projects.all):
        try:
            p.close()
        except Exception:
            pass
    for junk in (PROJ, PROJ + u".~u"):
        if os.path.exists(junk):
            try:
                os.remove(junk)
            except Exception:
                pass

    proj = scriptengine.projects.create(PROJ)
    proj.add(name=u"Device", type=4096, id=u"0000 0001", version=u"3.5.17.30")
    app = proj.active_application
    log(u"proekt sozdan")

    gvls = sorted([f[:-4] for f in os.listdir(ISO) if f.endswith(u".gvl")])
    #  DUT sozdaem tak zhe, kak v build.py: oni ispolzuyutsya v TEST_* i v
    #  FB_TestCase, i bez nih kartina oshibok budet ne toj.
    DUTS = {
        u"ST_TestCase": u"""TYPE ST_TestCase :
STRUCT
    Id : INT; Stage : INT; Opcode : BYTE;
    Init_A : BYTE; Init_B : BYTE; Init_F : BYTE;
    Init_PC : WORD; Init_SP : WORD;
    Exp_A : BYTE; Exp_F : BYTE; Exp_PC : WORD; Exp_Cycles : INT;
    Mask_A : BOOL; Mask_F : BOOL; Mask_PC : BOOL; Enabled : BOOL;
END_STRUCT
END_TYPE
""",
        u"ST_TestCase_CPM": u"""TYPE ST_TestCase_CPM :
STRUCT
    Id : INT; Kind : INT; Param : INT;
    Exp_Byte : BYTE; Exp_Word : WORD;
    Mask_Byte : BOOL; Mask_Word : BOOL; Enabled : BOOL;
END_STRUCT
END_TYPE
""",
    }
    for dn, dtext in sorted(DUTS.items()):
        try:
            d = app.create_dut(dn, 1)
            d.textual_declaration.replace(dtext)
            log(u"DUT %s OK" % dn)
        except Exception:
            log(u"DUT %s OSHIBKA: %s" % (dn, traceback.format_exc()))

    for g in gvls:
        try:
            txt = io.open(os.path.join(ISO, g + u".gvl"), encoding=u"utf-8").read()
            obj = app.create_gvl(g)
            obj.textual_declaration.replace(txt)
            log(u"GVL %s OK" % g)
        except Exception:
            log(u"GVL %s OSHIBKA: %s" % (g, traceback.format_exc()))

    order = [u"FB_Reg8", u"FB_Reg16", u"FB_RTrig", u"FB_FTrig", u"FB_RS",
             u"FB_Reg8Latch", u"FB_BitUnpack8", u"FB_ADDER8", u"FB_RegFileZ80",
             u"FB_ALU_Z80", u"FB_FlagsRegZ80", u"FB_DecoderZ80", u"FB_Memory64K",
             u"FB_PC_Z80", u"FB_SP_StackZ80", u"FB_ControlUnit", u"FB_Clock",
             u"FB_TestCase", u"FB_AlwaysTrue", u"FB_HW_IO_PLC", u"FB_IO_Ports",
             u"FB_CPM_Disk", u"FB_CPM_BDOS", u"FB_CPM_BIOS",
             u"PRG_InitMemory", u"PRG_LoadTestProgram", u"PRG_CPM_Boot",
             u"PRG_CPM_BDOS", u"TEST_Z80", u"TEST_Z80_CPM"]
    have = set([f[:-12] for f in os.listdir(ISO) if f.endswith(u".plcopenxml")])
    for n in order:
        if n not in have:
            continue
        try:
            app.import_xml(os.path.join(ISO, n + u".plcopenxml"))
            log(u"import: %s" % n)
        except Exception:
            log(u"import %s OSHIBKA: %s" % (n, traceback.format_exc()))

    try:
        tc = app.create_task_configuration()
        task = tc.create_task(u"MainTask")
        task.priority = u"1"
        task.interval = u"T#10ms"
        for p in (u"PRG_InitMemory", u"PRG_CPM_Boot", u"TEST_Z80",
                  u"PRG_CPM_BDOS", u"TEST_Z80_CPM", u"PLC_PRG"):
            try:
                task.pous.add(p, p)
            except Exception:
                pass
    except Exception:
        log(u"zadacha: %s" % traceback.format_exc())

    try:
        app.build()
    except Exception:
        log(u"build: %s" % traceback.format_exc())
    try:
        app.generate_code()
        log(u"generate_code OK")
    except Exception:
        log(u"generate_code: %s" % traceback.format_exc())
    log(u"=== KONEC (smotrite vyvod CODESYS) ===")
    try:
        proj.save()
        proj.close()
    except Exception:
        pass


if __name__ == u"__main__":
    try:
        main()
    except Exception:
        log(u"FATAL:\n%s" % traceback.format_exc())
