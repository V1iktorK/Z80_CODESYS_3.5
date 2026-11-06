# -*- coding: utf-8 -*-
u"""P O I S K  v i n o v n o g o  F B: kakoy blok daet oshibki C32.

Z A Ch E M. Kompilyator daet 8 par oshibok
    C32: Nevozmozhno konvertirovat tip 'BOOL'  v tip 'USINT'
    C32: Nevozmozhno konvertirovat tip 'USINT' v tip 'BOOL'
i ne ukazyvaet ni POU, ni nomer seti. Ustanovleno bisekciej po zadache:
s odnoj programmoy PRG_InitMemory oshibok NET, s odnoj PLC_PRG -- vse 17.
Znachit delo v bloke, kotoryy instanciruet PLC_PRG. Ih tam 18.

K A K  I Shch E M. Sozdaem proekt s temi zhe importami, chto i nastoyashchij,
no vmesto PLC_PRG -- kroshechnuyu programmu P_PROBE, kotoraya obstanovlyaet
TOLKO zadannye ekzemplyary FB. Eto zastavlyaet CODESYS skompilirovat
imenno ih vnutrennie seti. Dalee -- bisekciya po spisku.

ZAPUSK:  generator\run_probe_fb.cmd "FB_ALU_Z80,FB_IO_Ports"
Rezultat: log\probe_fb.txt (spisok FB i chislo oshibok)
"""
import io
import os
import sys

import scriptengine

ROOT = os.environ.get(u"Z80_ROOT")
if not ROOT:
    ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, u"src")
BUILD = os.path.join(ROOT, u"build")
LOG = os.path.join(ROOT, u"log")
MODE = os.environ.get(u"Z80_FBS") or u""
PT = scriptengine.PouType
DT = scriptengine.DutType

DEVICE_TYPE = 4096
DEVICE_ID = u"0000 0001"
DEVICE_VERSION = u"3.5.17.30"

GVL_ORDER = [u"GVL_Bus", u"GVL_Memory", u"GVL_Control", u"GVL_InitState",
             u"GVL_PLCVisu", u"GVL_Tests", u"GVL_InitRegs",
             u"GVL_HW_IO", u"GVL_HW_Buffer", u"GVL_IO", u"GVL_CPM",
             u"GVL_Disk", u"GVL_CPM_Extra", u"GVL_BootFlags", u"GVL_Tests_CPM"]

ALL_FBS = [u"FB_Reg8", u"FB_Reg16", u"FB_RTrig", u"FB_FTrig", u"FB_RS",
           u"FB_Reg8Latch", u"FB_BitUnpack8", u"FB_ADDER8", u"FB_RegFileZ80",
           u"FB_ALU_Z80", u"FB_FlagsRegZ80", u"FB_DecoderZ80", u"FB_Memory64K",
           u"FB_PC_Z80", u"FB_SP_StackZ80", u"FB_ControlUnit", u"FB_Clock",
           u"FB_TestCase", u"FB_AlwaysTrue", u"FB_HW_IO_PLC", u"FB_IO_Ports",
           u"FB_CPM_Disk", u"FB_CPM_BDOS", u"FB_CPM_BIOS"]

LINES = []


def log(m):
    LINES.append(u"%s" % (m,))


def main():
    log(u"=== PROBE FB: %r ===" % MODE)
    wanted = [x.strip() for x in MODE.split(u",") if x.strip()]
    log(u"probuem ekzemplyary: %s" % (wanted,))

    proj = scriptengine.projects.create(os.path.join(BUILD, u"probe_fb.project"))
    proj.add(name=u"Device", type=DEVICE_TYPE, id=DEVICE_ID,
             version=DEVICE_VERSION)
    app = proj.active_application

    for nm in (u"ST_TestCase", u"ST_TestCase_CPM"):
        app.create_dut(nm, type=DT.Structure)
    for nm in GVL_ORDER:
        gp = os.path.join(SRC, u"%s.gvl" % nm)
        if not os.path.exists(gp):
            continue
        txt = io.open(gp, encoding=u"utf-8").read()
        g = app.create_gvl(nm)
        g.textual_declaration.replace(txt)

    #  importiruem vse FB: sekciya ob yyavleniy vzaimozavisima
    for nm in ALL_FBS:
        path = os.path.join(SRC, u"%s.plcopenxml" % nm)
        if os.path.exists(path):
            app.import_xml(path)
    log(u"importirovano FB: %d" % len(ALL_FBS))

    #  programma-probnik: obyavlyaem i vyzyvaem nuzhnye ekzemplyary
    name = u"P_PROBE"
    app.create_pou(name, PT.Program, scriptengine.ImplementationLanguages.st,
                   None, None, None)
    p = None
    for cand in app.find(name):
        if hasattr(cand, u"textual_declaration"):
            p = cand
            break
    decl = [u"PROGRAM P_PROBE", u"VAR"]
    body = []
    for k, fb in enumerate(wanted):
        decl.append(u"\tfb_%d : %s;" % (k, fb))
        body.append(u"fb_%d();" % k)
    decl.append(u"END_VAR")
    p.textual_declaration.replace(u"\n".join(decl))
    p.textual_implementation.replace(u"\n".join(body) if body else u"(* net *);")
    log(u"P_PROBE: %d ekzemplyarov" % len(wanted))

    tc = app.create_task_configuration()
    task = tc.create_task(u"MainTask")
    try:
        task.priority = u"1"
        task.interval = u"T#10ms"
    except Exception:                                          # noqa: BLE001
        pass
    task.pous.add(name, name)

    try:
        app.build()
    except Exception as exc:                                   # noqa: BLE001
        log(u"build(): %s" % exc)
    try:
        app.generate_code()
    except Exception as exc:                                   # noqa: BLE001
        log(u"generate_code(): %s" % exc)

    #  P O P Y T K A  C H I T A T '  S O O B Shch E N I Ya  Ch E R E Z  A P I.
    #  Konsol nyj vyvod perehvatyvaetsya nenadezhno (dochernij process derzhit
    #  deskriptory), a soobshcheniya s nomerom seti reshili by zadachu srazu.
    #  Poetomu probuem neskolko API i pihem v log vse, chto udastsya.
    for label, fn in ((u"system.get_messages()", lambda: system.get_messages()),
                      (u"app.get_messages()", lambda: app.get_messages())):
        try:
            msgs = fn()
            log(u"%s -> %d soobshchenij" % (label, len(msgs)))
            for msg in list(msgs)[:40]:
                parts = []
                for attr in (u"severity", u"text", u"object", u"position",
                             u"pou", u"line", u"column", u"number"):
                    try:
                        parts.append(u"%s=%s" % (attr, getattr(msg, attr)))
                    except Exception:                          # noqa: BLE001
                        pass
                log(u"    %s" % (u" | ".join(parts) if parts else repr(msg)))
        except Exception as exc:                               # noqa: BLE001
            log(u"%s OSHIBKA: %s" % (label, exc))

    proj.save()
    proj.close()
    log(u"=== KONEC ===")


try:
    main()
except Exception, exc:                                          # noqa: E999
    log(u"AVARIYA: %s" % exc)
    import traceback
    log(traceback.format_exc())

if not os.path.isdir(LOG):
    os.makedirs(LOG)
f = open(os.path.join(LOG, u"probe_fb.txt"), u"w")
f.write(u"\n".join(LINES).encode(u"utf-8"))
f.close()
sys.stdout.write(u"probe_fb: %d strok\n" % len(LINES))
