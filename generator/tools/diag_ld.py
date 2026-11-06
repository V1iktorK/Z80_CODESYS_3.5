# -*- coding: utf-8 -*-
u"""O D N A  K O M A N D A: LD B,2Ah.

Z A Ch E M. Testy provaleny, i nuzhno ponyat, vypolnyaetsya li voobshche
komanda peresylki. Stavim:
    Z80_Mem[0] = 06h  (LD B,n)
    Z80_Mem[1] = 2Ah  (n)
    Init_PC = 0, B = 0
Puskaem na paru sekund i chitaem B. Ozhidaem B = 2Ah, PC = 2.

ZAPUSK: generator\run_sim.ps1 -Script tools\diag_ld.py
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
OUT = os.path.join(LOG, u"diag_ld.txt")

LINES = []


def log(m):
    LINES.append((u"%s" % (m,)))


def main():
    log(u"=== LD B,2Ah ===")
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
            return u"?%s" % (u"%s" % exc)[:26]

    def wr(pairs):
        for n, v in pairs:
            try:
                onl.set_prepared_value(n, v)
            except Exception as exc:                           # noqa: BLE001
                log(u"  set %s OSHIBKA: %s" % (n, exc))
        onl.write_prepared_values()

    def snap(t):
        log(u"  %-22s PC=%-9s IR=%-9s A=%-8s B=%-8s F=%-8s Halt=%s"
            % (t, rd(u"GVL_PLCVisu.PC"), rd(u"GVL_PLCVisu.IR"),
               rd(u"GVL_PLCVisu.A"), rd(u"GVL_PLCVisu.B"),
               rd(u"GVL_PLCVisu.F"), rd(u"GVL_PLCVisu.Halted")))

    time.sleep(2)
    wr([(u"GVL_Tests.Cpu_Test_Run", u"FALSE"),
        (u"GVL_Control.Emu_Run", u"FALSE"),
        (u"GVL_Control.Emu_Reset", u"TRUE")])
    time.sleep(1)
    wr([(u"GVL_Control.Emu_Reset", u"FALSE")])
    time.sleep(1)

    #  programma
    wr([(u"GVL_Memory.Z80_Mem[0]", u"BYTE#6"),
        (u"GVL_Memory.Z80_Mem[1]", u"BYTE#42"),
        (u"GVL_Memory.Z80_Mem[2]", u"BYTE#0"),
        (u"GVL_Memory.Z80_Mem[3]", u"BYTE#0"),
        (u"GVL_InitRegs.Init_PC", u"WORD#0")])
    for k in range(8):
        wr([(u"GVL_InitRegs.Init_Vals[%d]" % k, u"BYTE#0")])
    wr([(u"GVL_InitRegs.Init_Vals[1]", u"BYTE#0")])     # B = 0
    time.sleep(1)
    log(u"  Mem[0]=%s Mem[1]=%s" % (rd(u"GVL_Memory.Z80_Mem[0]"),
                                    rd(u"GVL_Memory.Z80_Mem[1]")))

    wr([(u"GVL_InitRegs.Init_En", u"TRUE")])
    time.sleep(1)
    snap(u"posle Init_En")
    wr([(u"GVL_InitRegs.Init_En", u"FALSE")])
    time.sleep(1)
    snap(u"posle snyatiya Init_En")

    wr([(u"GVL_Control.Emu_Run", u"TRUE")])
    for i in range(6):
        time.sleep(1)
        snap(u"pusk %d s" % (i + 1))
        wr([(u"GVL_Control.Emu_Run", u"FALSE")])
        time.sleep(0.5)
        snap(u"  pauza, Emu_Run=0")
        wr([(u"GVL_Control.Emu_Run", u"TRUE")])

    log(u"")
    log(u"--- O Zh I D A L O S' ---")
    log(u"  posle Init_En: B = 00h")
    log(u"  posle komandy: B = 2Ah, PC = 0002h, IR = 06h")

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
sys.stdout.write(u"diag_ld: %d strok\n" % len(LINES))
