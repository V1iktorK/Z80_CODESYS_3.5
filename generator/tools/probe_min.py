# -*- coding: utf-8 -*-
u"""M I N I M A L N Y J  V O S P R O I Z V O D Ya Shch I J  T E S T.

Z A Ch E M. V polnom proekte kompilyator daet 21 oshibku
    C9: Obnaruzhen nedopustimyj simvol '-'
i ni odna iz nashih shestidesyati shesti strok s tire ne podhodit: vse
tire -- vnutri kommentariev (* ... *), a ih kompilyator propuskaet.
Znachit delo ne v soderzhimom, a v K A K O J - T O  Ch A S T I  S B O R K I.

Ch T O  D E L A E M. Sobiraem po ocheredi vse menshie proekty i smotrim,
na kakom shage poyavlyaetsya oshibka. Rezhim zadayetsya peremennoj
okruzheniya Z80_PROBE:

    1 -- odna programma so skromnym obyavleniem, bez zadachi
    2 -- to zhe + konfiguratsiya zadach i registraciya v nej
    3 -- odna ST-programma s kommentarom-shapkoj
    4 -- odna FBD-shema (FB_Reg8), bez zadachi
    5 -- odna FBD-shema + zadacha
    6 -- vsya gruppa ST-programm
    7 -- vse GVL

Rezultat: log\probe_<rezhim>.txt
ZAPUSK: generator\run_probe_min.cmd   (peremennaya Z80_PROBE iz .cmd)
"""
import os
import sys

import scriptengine

ROOT = os.environ.get(u"Z80_ROOT")
if not ROOT:
    ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, u"src")
BUILD = os.path.join(ROOT, u"build")
LOG = os.path.join(ROOT, u"log")
MODE = int(os.environ.get(u"Z80_PROBE") or u"1")

PT = scriptengine.PouType
DT = scriptengine.DutType
DEVICE_TYPE = 4096
DEVICE_ID = u"0000 0001"
DEVICE_VERSION = u"3.5.17.30"

ST_NAMES = [u"PRG_InitMemory", u"PRG_LoadTestProgram", u"PRG_CPM_Boot",
            u"PRG_CPM_BDOS", u"TEST_Z80", u"TEST_Z80_CPM"]
GVL_NAMES = [u"GVL_Bus", u"GVL_Memory", u"GVL_Control", u"GVL_InitState",
             u"GVL_PLCVisu", u"GVL_Tests", u"GVL_InitRegs", u"GVL_HW_IO",
             u"GVL_HW_Buffer", u"GVL_IO", u"GVL_CPM", u"GVL_Disk",
             u"GVL_CPM_Extra", u"GVL_BootFlags", u"GVL_Tests_CPM"]

LOG_LINES = []


def log(msg):
    LOG_LINES.append(u"%s" % msg)


def new_project(name):
    proj = scriptengine.projects.create(os.path.join(BUILD, name + u".project"))
    dev = proj.add(name=u"Device", type=DEVICE_TYPE, id=DEVICE_ID, version=DEVICE_VERSION)
    app = proj.active_application
    log(u"proekt sozdan: %s" % name)
    return proj, app


def add_task(app, pous):
    tc = app.create_task_configuration()
    task = tc.create_task(u"MainTask")
    try:
        task.priority = u"1"
        task.interval = u"T#10ms"
    except Exception:                                          # noqa: BLE001
        pass
    for prg in pous:
        #  P R A V I L N Y J  S P O S O B: add(imya, imya).
        #  Variant task.pous[prg] = prg rabotaet tolko u spiska,
        #  poluchennogo iz sohr an ennogo proekta, a u svezhego --
        #  padaet s "object does not support item assignment".
        try:
            task.pous.add(prg, prg)
        except Exception as exc:                               # noqa: BLE001
            log(u"  ne udalos dobavit %s: %s" % (prg, exc))
    log(u"  v zadache: %s" % list(task.pous))
    return task


def compile_and_save(proj, name):
    app = proj.active_application
    try:
        app.build()
    except Exception as exc:                                   # noqa: BLE001
        log(u"  build(): %s" % exc)
    try:
        app.generate_code()
    except Exception as exc:                                   # noqa: BLE001
        log(u"  generate_code(): %s" % exc)
    proj.save()
    log(u"  sohranено: %s" % name)
    proj.close()


def import_one(app, name):
    path = os.path.join(SRC, name + u".plcopenxml")
    if not os.path.exists(path):
        log(u"  NET FAJLA %s" % path)
        return False
    app.import_xml(path)
    o = app.find(name) if hasattr(app, u"find") else None
    log(u"  importirovan: %s (%s)" % (name, u"est" if o is not None else u"NE NAJDEN"))
    return True


def create_gvl(app, name):
    path = os.path.join(SRC, name + u".gvl")
    if not os.path.exists(path):
        log(u"  NET FAJLA %s" % path)
        return
    txt = open(path).read().decode(u"utf-8")
    g = app.create_gvl(name)
    g.textual_declaration.replace(txt)
    log(u"  GVL %s -- %d simvolov" % (name, len(txt)))


def minimal_st(app, with_comment):
    u"""Samaya prostaya programma: odna peremennaya i odin operator."""
    name = u"P_MIN"
    app.create_pou(name, PT.Program,
                   scriptengine.ImplementationLanguages.st, None, None, None)
    #  V N I M A N I E: app.find() vozvrashchaet S P I S O K obektov,
    #  a ne odin obekt. Beryom pervyj, u kotorogo est tekst obyavleniya.
    p = None
    for cand in app.find(name):
        if hasattr(cand, u"textual_declaration"):
            p = cand
            break
    if p is None:
        log(u"  NE NAJDEN POU %s" % name)
        return name
    decl = u"PROGRAM P_MIN\n"
    if with_comment:
        decl += (u"(* Kommentariy-shapka.\n"
                 u"Vtoraya stroka -- s tire: vot tut -- tire. *)\n")
    decl += u"VAR\n\ti : INT;\nEND_VAR"
    p.textual_declaration.replace(decl)
    p.textual_implementation.replace(u"i := 1;\ni := i + 1;")
    log(u"  sozdan P_MIN (kommentar: %s)" % with_comment)
    return name


def main():
    log(u"=== PROBE MIN, rezhim %d ===" % MODE)
    if MODE == 1:
        proj, app = new_project(u"probe1")
        nm = minimal_st(app, False)
        compile_and_save(proj, u"probe1 (bez zadachi)")
    elif MODE == 2:
        proj, app = new_project(u"probe2")
        nm = minimal_st(app, False)
        add_task(app, [nm])
        compile_and_save(proj, u"probe2 (s zadachej)")
    elif MODE == 3:
        proj, app = new_project(u"probe3")
        nm = minimal_st(app, True)
        compile_and_save(proj, u"probe3 (kommentar s tire)")
    elif MODE == 4:
        proj, app = new_project(u"probe4")
        app.create_dut(u"ST_TestCase", type=DT.Structure)
        import_one(app, u"FB_Reg8")
        compile_and_save(proj, u"probe4 (FB_Reg8)")
    elif MODE == 5:
        proj, app = new_project(u"probe5")
        import_one(app, u"FB_Reg8")
        add_task(app, [u"FB_Reg8"])
        compile_and_save(proj, u"probe5 (FB_Reg8 v zadache)")
    elif MODE == 6:
        proj, app = new_project(u"probe6")
        for n in (u"ST_TestCase", u"ST_TestCase_CPM"):
            app.create_dut(n, type=DT.Structure)
        for n in ST_NAMES:
            import_one(app, n)
        compile_and_save(proj, u"probe6 (vse ST-programmy)")
    elif MODE == 10:
        #  V S E  P O U  (kak v polnoj sborke), no B E Z konfiguracii zadach.
        proj, app = new_project(u"probe10")
        for n in (u"ST_TestCase", u"ST_TestCase_CPM"):
            app.create_dut(n, type=DT.Structure)
        for n in GVL_NAMES:
            create_gvl(app, n)
        order = [u"FB_Reg8", u"FB_Reg16", u"FB_RTrig", u"FB_FTrig",
                 u"FB_RS", u"FB_Reg8Latch", u"FB_BitUnpack8", u"FB_ADDER8",
                 u"FB_RegFileZ80", u"FB_ALU_Z80", u"FB_FlagsRegZ80",
                 u"FB_DecoderZ80", u"FB_Memory64K", u"FB_PC_Z80",
                 u"FB_SP_StackZ80", u"FB_ControlUnit", u"FB_Clock",
                 u"FB_TestCase", u"FB_AlwaysTrue", u"FB_HW_IO_PLC",
                 u"FB_IO_Ports", u"FB_CPM_Disk", u"FB_CPM_BDOS",
                 u"FB_CPM_BIOS", u"PLC_PRG", u"PRG_InitMemory",
                 u"PRG_LoadTestProgram", u"PRG_CPM_Boot", u"PRG_CPM_BDOS",
                 u"TEST_Z80", u"TEST_Z80_CPM"]
        for n in order:
            import_one(app, n)
        compile_and_save(proj, u"probe10 (vse POU, bez zadach)")
    elif MODE == 13:
        #  O D N A  programma TEST_Z80 v zadache -- samyj korotkij sluchaj,
        #  na kotorom vosproizvodilis oshibki C9. Bez GVL i bez DUT:
        #  tak proverim, ne v nih li delo.
        proj, app = new_project(u"probe13")
        for n in (u"ST_TestCase", u"ST_TestCase_CPM"):
            app.create_dut(n, type=DT.Structure)
        for n in GVL_NAMES:
            create_gvl(app, n)
        for n in (u"FB_Reg8", u"FB_Reg16", u"FB_RTrig", u"FB_FTrig",
                  u"FB_RS", u"FB_Reg8Latch", u"FB_BitUnpack8", u"FB_ADDER8",
                  u"FB_RegFileZ80", u"FB_ALU_Z80", u"FB_FlagsRegZ80",
                  u"FB_DecoderZ80", u"FB_Memory64K", u"FB_PC_Z80",
                  u"FB_SP_StackZ80", u"FB_ControlUnit", u"FB_Clock",
                  u"FB_TestCase", u"FB_AlwaysTrue", u"FB_HW_IO_PLC",
                  u"FB_IO_Ports", u"FB_CPM_Disk", u"FB_CPM_BDOS",
                  u"FB_CPM_BIOS", u"PLC_PRG", u"PRG_InitMemory",
                  u"PRG_LoadTestProgram", u"PRG_CPM_Boot", u"PRG_CPM_BDOS",
                  u"TEST_Z80", u"TEST_Z80_CPM"):
            import_one(app, n)
        add_task(app, [u"TEST_Z80"])
        compile_and_save(proj, u"probe13 (TEST_Z80 odin)")
    elif MODE >= 20 and MODE <= 29:
        #  V S E  P O U, no v zadache -- R O V N O  O D N A programma.
        #  Tak najdem, kakaya imenno daet oshibki C9/C189.
        which = [u"PRG_InitMemory", u"PRG_LoadTestProgram", u"PRG_CPM_Boot",
                 u"PRG_CPM_BDOS", u"TEST_Z80", u"TEST_Z80_CPM", u"PLC_PRG"]
        proj, app = new_project(u"probe%d" % MODE)
        for n in (u"ST_TestCase", u"ST_TestCase_CPM"):
            app.create_dut(n, type=DT.Structure)
        for n in GVL_NAMES:
            create_gvl(app, n)
        for n in (u"FB_Reg8", u"FB_Reg16", u"FB_RTrig", u"FB_FTrig",
                  u"FB_RS", u"FB_Reg8Latch", u"FB_BitUnpack8", u"FB_ADDER8",
                  u"FB_RegFileZ80", u"FB_ALU_Z80", u"FB_FlagsRegZ80",
                  u"FB_DecoderZ80", u"FB_Memory64K", u"FB_PC_Z80",
                  u"FB_SP_StackZ80", u"FB_ControlUnit", u"FB_Clock",
                  u"FB_TestCase", u"FB_AlwaysTrue", u"FB_HW_IO_PLC",
                  u"FB_IO_Ports", u"FB_CPM_Disk", u"FB_CPM_BDOS",
                  u"FB_CPM_BIOS", u"PLC_PRG", u"PRG_InitMemory",
                  u"PRG_LoadTestProgram", u"PRG_CPM_Boot", u"PRG_CPM_BDOS",
                  u"TEST_Z80", u"TEST_Z80_CPM"):
            import_one(app, n)
        one = which[MODE - 20] if MODE - 20 < len(which) else None
        log(u"v zadache tolko: %s" % one)
        add_task(app, [one] if one else [])
        compile_and_save(proj, u"probe%d (%s)" % (MODE, one))
    elif MODE == 12:
        #  V S E  P O U  +  zadacha s PROGRAMMAMI (pravilnyj add).
        proj, app = new_project(u"probe12")
        for n in (u"ST_TestCase", u"ST_TestCase_CPM"):
            app.create_dut(n, type=DT.Structure)
        for n in GVL_NAMES:
            create_gvl(app, n)
        for n in (u"FB_Reg8", u"FB_Reg16", u"FB_RTrig", u"FB_FTrig",
                  u"FB_RS", u"FB_Reg8Latch", u"FB_BitUnpack8", u"FB_ADDER8",
                  u"FB_RegFileZ80", u"FB_ALU_Z80", u"FB_FlagsRegZ80",
                  u"FB_DecoderZ80", u"FB_Memory64K", u"FB_PC_Z80",
                  u"FB_SP_StackZ80", u"FB_ControlUnit", u"FB_Clock",
                  u"FB_TestCase", u"FB_AlwaysTrue", u"FB_HW_IO_PLC",
                  u"FB_IO_Ports", u"FB_CPM_Disk", u"FB_CPM_BDOS",
                  u"FB_CPM_BIOS", u"PLC_PRG", u"PRG_InitMemory",
                  u"PRG_LoadTestProgram", u"PRG_CPM_Boot", u"PRG_CPM_BDOS",
                  u"TEST_Z80", u"TEST_Z80_CPM"):
            import_one(app, n)
        add_task(app, [u"PRG_InitMemory", u"PRG_CPM_Boot", u"TEST_Z80",
                       u"PRG_CPM_BDOS", u"TEST_Z80_CPM", u"PLC_PRG"])
        compile_and_save(proj, u"probe12 (vse POU + zadacha)")
    elif MODE == 11:
        #  V S E  P O U  +  P U S T A Ya konfiguraciya zadach.
        proj, app = new_project(u"probe11")
        for n in (u"ST_TestCase", u"ST_TestCase_CPM"):
            app.create_dut(n, type=DT.Structure)
        for n in GVL_NAMES:
            create_gvl(app, n)
        for n in (u"FB_Reg8", u"FB_Reg16", u"FB_RTrig", u"FB_FTrig",
                  u"FB_RS", u"FB_Reg8Latch", u"FB_BitUnpack8", u"FB_ADDER8",
                  u"FB_RegFileZ80", u"FB_ALU_Z80", u"FB_FlagsRegZ80",
                  u"FB_DecoderZ80", u"FB_Memory64K", u"FB_PC_Z80",
                  u"FB_SP_StackZ80", u"FB_ControlUnit", u"FB_Clock",
                  u"FB_TestCase", u"FB_AlwaysTrue", u"FB_HW_IO_PLC",
                  u"FB_IO_Ports", u"FB_CPM_Disk", u"FB_CPM_BDOS",
                  u"FB_CPM_BIOS", u"PLC_PRG", u"PRG_InitMemory",
                  u"PRG_LoadTestProgram", u"PRG_CPM_Boot", u"PRG_CPM_BDOS",
                  u"TEST_Z80", u"TEST_Z80_CPM"):
            import_one(app, n)
        add_task(app, [])
        compile_and_save(proj, u"probe11 (vse POU, pustaya zadacha)")
    elif MODE == 7:
        proj, app = new_project(u"probe7")
        for n in GVL_NAMES:
            create_gvl(app, n)
        compile_and_save(proj, u"probe7 (vse GVL)")
    else:
        log(u"neizvestnyj rezhim")
    log(u"=== KONEC ===")


try:
    main()
except Exception, exc:                                          # noqa: E999
    log(u"AVARIYA: %s" % exc)
    import traceback
    log(traceback.format_exc())

if not os.path.isdir(LOG):
    os.makedirs(LOG)
f = open(os.path.join(LOG, u"probe_%d.txt" % MODE), u"w")
f.write(u"\n".join(LOG_LINES).encode(u"utf-8"))
f.close()
sys.stdout.write(u"probe %d: %d strok\n" % (MODE, len(LOG_LINES)))
