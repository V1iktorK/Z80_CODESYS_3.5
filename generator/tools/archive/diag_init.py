# -*- coding: utf-8 -*-
u"""P R O V E R K A  I N I C I A L I Z A C I I  R E G I S T R O V.

Z A Ch E M. Testy vse provaleny. Pervaya zhe proverka pokazala, chto Init_PC
voobshche ne chitalsya -- i eto uzhe ispravleno. Ostalsya vopros: a gruzyat li
Init_Vals v registrovuyu chast'? Esli net, to kazhdyj test nachinaetsya s
musorom v A/B/F, i provalennymi budut V S E 40 proverok srazu -- chto my i
vidim.

Zdes stavim zavedomo uznavaemye znacheniya i smotrim, poyavilis' li oni.
    Init_Vals[0]=12h (A), [1]=34h (B), [5]=AAh (H), [6]=BBh (L), [7]=C3h (F)
    Init_PC = 1234h

ZAPUSK: generator\run_sim.ps1 -Script tools\diag_init.py
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
OUT = os.path.join(LOG, u"diag_init.txt")

WATCH = [
    (u"A", u"GVL_PLCVisu.A"),
    (u"B", u"GVL_PLCVisu.B"),
    (u"H", u"GVL_PLCVisu.H"),
    (u"L", u"GVL_PLCVisu.L"),
    (u"F", u"GVL_PLCVisu.F"),
    (u"PC", u"GVL_PLCVisu.PC"),
    (u"IEn", u"GVL_InitRegs.Init_En"),
    (u"IBusy", u"GVL_InitRegs.Init_Busy"),
    (u"ISel", u"GVL_InitRegs.Init_Sel_Dst"),
    (u"ICnt", u"PLC_PRG.vInitCnt"),
    (u"WrEn", u"GVL_Control.Ctl_Wr_Enable"),
    (u"WrEnV", u"PLC_PRG.vCtl_Wr_Enable"),
    (u"ClkEx", u"PLC_PRG.fbClock.Clk_Exec"),
    (u"Clr", u"GVL_Control.Emu_Reset"),
]

LINES = []


def log(m):
    LINES.append((u"%s" % (m,)))


def main():
    log(u"=== PROVERKA INICIALIZACII REGISTROV ===")
    proj = scriptengine.projects.open(PROJ)
    app = proj.active_application
    app.build()
    dev = list(proj.find(u"Device"))[0]
    try:
        dev.set_simulation_mode(True)
    except Exception:                                          # noqa: BLE001
        pass
    onl = scriptengine.online.create_online_application(app)
    onl.login(scriptengine.OnlineChangeOption.Try, True)
    onl.start()

    def rd(n):
        try:
            return u"%s" % onl.read_value(n)
        except Exception as exc:                               # noqa: BLE001
            return u"?%s" % (u"%s" % exc)[:24]

    def wr(pairs):
        for n, v in pairs:
            try:
                onl.set_prepared_value(n, v)
            except Exception as exc:                           # noqa: BLE001
                log(u"  set %s OSHIBKA: %s" % (n, exc))
        onl.write_prepared_values()

    def snap(title):
        log(u"")
        log(u"  " + title)
        log(u"    " + u"  ".join([u"%s=%s" % (n, rd(a)) for n, a in WATCH]))

    time.sleep(2)
    wr([(u"GVL_Tests.Cpu_Test_Run", u"FALSE"),
        (u"GVL_Tests_CPM.Cpm_Test_Run", u"FALSE"),
        (u"GVL_Control.Emu_Run", u"FALSE"),
        (u"GVL_Control.Emu_Reset", u"TRUE")])
    time.sleep(1)
    #  V A Zh N O: snyat' Emu_Reset DO initsializacii, a ne posle.
    #  U registrov CLR imeet prioritet: poka on aktivен, strob zapisi
    #  AND(Wr_En, NOT CLR) nikogda ne srabatyvaet, i vse Init_Vals
    #  molcha otbrasyvayutsya.
    wr([(u"GVL_Control.Emu_Reset", u"FALSE")])
    time.sleep(1)
    snap(u"posle sbrosa")

    # 1. vystavlyaem Init_Vals i Init_PC
    wr([(u"GVL_InitRegs.Init_Vals[0]", u"BYTE#18"),   # 12h A
        (u"GVL_InitRegs.Init_Vals[1]", u"BYTE#52"),   # 34h B
        (u"GVL_InitRegs.Init_Vals[2]", u"BYTE#86"),   # 56h C
        (u"GVL_InitRegs.Init_Vals[3]", u"BYTE#120"),  # 78h D
        (u"GVL_InitRegs.Init_Vals[4]", u"BYTE#154"),  # 9Ah E
        (u"GVL_InitRegs.Init_Vals[5]", u"BYTE#170"),  # AAh H
        (u"GVL_InitRegs.Init_Vals[6]", u"BYTE#187"),  # BBh L
        (u"GVL_InitRegs.Init_Vals[7]", u"BYTE#195"),  # C3h F
        (u"GVL_InitRegs.Init_PC", u"WORD#4660")])     # 1234h
    time.sleep(1)
    log(u"")
    log(u"  Init_Vals zadany:")
    for k in range(8):
        log(u"    Init_Vals[%d] = %s" % (k, rd(u"GVL_InitRegs.Init_Vals[%d]" % k)))
    log(u"    Init_PC      = %s" % rd(u"GVL_InitRegs.Init_PC"))

    # 2. impul's Init_En
    wr([(u"GVL_InitRegs.Init_En", u"TRUE")])
    time.sleep(1)
    snap(u"pri Init_En = TRUE")

    wr([(u"GVL_InitRegs.Init_En", u"FALSE")])
    time.sleep(1)
    snap(u"posle snyatiya Init_En")

    time.sleep(2)
    snap(u"posle pauzy (Emu_Run = FALSE)")

    log(u"")
    log(u"--- O Zh I D A L O S' ---")
    log(u"  A=12h B=34h C=56h D=78h E=9Ah H=AAh L=BBh F=C3h  PC=1234h")

    onl.stop()
    onl.logout()
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
sys.stdout.write(u"diag_init: %d strok\n" % len(LINES))
