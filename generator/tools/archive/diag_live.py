# -*- coding: utf-8 -*-
u"""D I A G N O S T I K A  I S P O L N E N I Ya -- chto proishodit v emulyatore.

Z A Ch E M. Pervyj zhe nastoyashchij progon pokazal: testy ne prohodyat
(CPU 0/39, CPM 0/30). Znachit nuzhno smotret ne na itog, a na sam protsess:
dvizhetsya li PC, menyaetsya li IR, idet li schetchik testov.

Zdes my chitaem signaly po odnomu (read_value vozvrashchaet skalyar) i
pechataem tablicu po sekundam.

ZAPUSK: generator\run_sim.ps1 -Script tools\diag_live.py
"""
import io
import os
import sys
import time

import scriptengine

ROOT = os.environ.get(u"Z80_ROOT")
if not ROOT:
    ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUILD = os.path.join(ROOT, u"build")
LOG = os.path.join(ROOT, u"log")
PROJ = os.path.join(BUILD, u"Z80_EMU.project")
OUT = os.path.join(LOG, u"diag_live.txt")

#  chto chitaem i kak podpisyvaem
WATCH = [
    (u"PC",        u"GVL_PLCVisu.PC"),
    (u"IR",        u"GVL_PLCVisu.IR"),
    (u"A",         u"GVL_PLCVisu.A"),
    (u"F",         u"GVL_PLCVisu.F"),
    (u"SP",        u"GVL_PLCVisu.SP"),
    (u"HL",        u"GVL_PLCVisu.HL"),
    (u"Run",       u"GVL_Control.Emu_Run"),
    (u"Halted",    u"GVL_PLCVisu.Halted"),
    (u"T_Stage",   u"GVL_Tests.Cpu_Test_Stage"),
    (u"T_Active",  u"GVL_Tests.Cpu_Test_Active"),
    (u"T_Count",   u"GVL_Tests.Cpu_Test_Count"),
    (u"T_Pass",    u"GVL_Tests.Cpu_Test_Total_Pass"),
    (u"T_Fail",    u"GVL_Tests.Cpu_Test_Fail_Count"),
    (u"T_Run",     u"GVL_Tests.Cpu_Test_Run"),
    (u"Init_Done", u"GVL_InitState.InitDone"),
]

LINES = []


def log(m):
    LINES.append((u"%s" % (m,)))


def main():
    log(u"=== DIAGNOSTIKA ISPOLNENIYA ===")
    proj = scriptengine.projects.open(PROJ)
    app = proj.active_application
    try:
        app.build()
    except Exception as exc:                                   # noqa: BLE001
        log(u"build(): %s" % exc)

    dev = list(proj.find(u"Device"))[0]
    try:
        dev.set_simulation_mode(True)
        log(u"rezhim simulyatsii -- OK")
    except Exception as exc:                                   # noqa: BLE001
        log(u"simulyatsiya: %s" % exc)

    onl = scriptengine.online.create_online_application(app)
    onl.login(scriptengine.OnlineChangeOption.Try, True)
    log(u"login -- OK")
    onl.start()
    log(u"start -- OK")

    def read(name):
        try:
            return u"%s" % onl.read_value(name)
        except Exception as exc:                               # noqa: BLE001
            return u"?<%s>" % (u"%s" % exc)[:40]

    #  vyderzhka pered i posle vklyucheniya testov
    time.sleep(2)
    log(u"")
    log(u"--- do vklyucheniya testov ---")
    log(u"  " + u"  ".join([u"%s=%s" % (n, read(a)) for n, a in WATCH]))

    try:
        onl.set_prepared_value(u"GVL_Tests.Cpu_Test_Run", u"TRUE")
        onl.write_prepared_values()
        log(u"  Cpu_Test_Run := TRUE")
    except Exception as exc:                                   # noqa: BLE001
        log(u"  set Cpu_Test_Run OSHIBKA: %s" % exc)

    log(u"")
    log(u"--- tablica po sekundam ---")
    log(u"  " + u" ".join([u"%4s" % n for n, _ in WATCH]))
    prev = None
    for i in range(20):
        vals = [read(a) for _, a in WATCH]
        row = u" ".join([u"%4s" % (v if len(v) <= 4 else v[:4]) for v in vals])
        log(u"  " + row)
        if vals == prev:
            log(u"  (znacheniya ne menyayutsya -- ostanavlivaem)")
            break
        prev = vals
        time.sleep(1)

    #  polnyj vyvod posle
    log(u"")
    log(u"--- polnye znacheniya v konce ---")
    for n, a in WATCH:
        log(u"  %-10s %-28s = %s" % (n, a, read(a)))

    try:
        onl.stop()
        onl.logout()
    except Exception:                                          # noqa: BLE001
        pass
    try:
        proj.close()
    except Exception:                                          # noqa: BLE001
        pass
    log(u"=== KONEC ===")


try:
    main()
except Exception, exc:                                          # noqa: E999
    log(u"AVARIYA: " + (u"%s" % exc))
    import traceback
    log(traceback.format_exc())

if not os.path.isdir(LOG):
    os.makedirs(LOG)
f = open(OUT, u"w")
f.write(u"\n".join(LINES).encode(u"utf-8"))
f.close()
sys.stdout.write(u"diag_live: %d strok\n" % len(LINES))
