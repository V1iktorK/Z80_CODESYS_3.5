# -*- coding: utf-8 -*-
u"""M I N I M A L ' N Y J  O P Y T: NOP-y i HALT.

Z A Ch E M. Testy vse provaleny, i po nih ne ponyatno, gde imenno oshibka.
Stavim samuyu prostuyu programmu:
    Z80_Mem[0..3] = 00h  (NOP)
    Z80_Mem[4]    = 76h  (HALT)
    Init_PC = 0, Init_En na odin skan, zatem Emu_Run.
Ozhidaem: PC rastet 0 -> 1 -> 2 -> 3 -> 4, zatom Halted = TRUE.

Esli PC ne rastet -- oshibka v vyborke/takte.
Esli rastet po 3 -- ne tot Inc_By.
Esli rastet, no HALT ne srabatyvaet -- oshibka v FB_ControlUnit.

ZAPUSK: generator\run_sim.ps1 -Script tools\diag_nop.py
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
OUT = os.path.join(LOG, u"diag_nop.txt")

LINES = []


def log(m):
    LINES.append((u"%s" % (m,)))


def main():
    log(u"=== OPYT: NOP-y i HALT ===")
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
    log(u"onlajn -- OK")

    def rd(n):
        try:
            return u"%s" % onl.read_value(n)
        except Exception as exc:                               # noqa: BLE001
            return u"?%s" % (u"%s" % exc)[:30]

    def wr(pairs):
        for n, v in pairs:
            try:
                onl.set_prepared_value(n, v)
            except Exception as exc:                           # noqa: BLE001
                log(u"  set %s=%s OSHIBKA: %s" % (n, v, exc))
        onl.write_prepared_values()

    time.sleep(2)

    # 1. ostanovit' testy
    wr([(u"GVL_Tests.Cpu_Test_Run", u"FALSE"),
        (u"GVL_Tests_CPM.Cpm_Test_Run", u"FALSE"),
        (u"GVL_Control.Emu_Run", u"FALSE"),
        (u"GVL_Control.Emu_Reset", u"TRUE")])
    time.sleep(1)

    # 2. zapisat' programmu: 4 NOP i HALT
    if os.environ.get(u"Z80_HALT0"):
        prog = [(0, 0x76)]          # tolko HALT po adresu 0
    else:
        prog = [(0, 0x00), (1, 0x00), (2, 0x00), (3, 0x00), (4, 0x76)]
    pairs = []
    for addr, val in prog:
        pairs.append((u"GVL_Memory.Z80_Mem[%d]" % addr, u"BYTE#%d" % val))
    wr(pairs)
    log(u"  programma zapisana: 00 00 00 00 76")
    time.sleep(1)
    log(u"  Mem[0]=%s Mem[1]=%s Mem[4]=%s"
        % (rd(u"GVL_Memory.Z80_Mem[0]"), rd(u"GVL_Memory.Z80_Mem[1]"),
           rd(u"GVL_Memory.Z80_Mem[4]")))

    # 3. Init_PC := 0 i Init_En na odin skan
    wr([(u"GVL_InitRegs.Init_PC", u"WORD#0"),
        (u"GVL_InitRegs.Init_Vals[0]", u"BYTE#0"),
        (u"GVL_InitRegs.Init_Vals[1]", u"BYTE#0"),
        (u"GVL_InitRegs.Init_En", u"TRUE")])
    time.sleep(1)
    log(u"  posle Init_En: PC=%s  PCLat=%s  Init_En=%s"
        % (rd(u"GVL_PLCVisu.PC"), rd(u"PLC_PRG.fbPCLatch.Q"),
           rd(u"GVL_InitRegs.Init_En")))
    wr([(u"GVL_InitRegs.Init_En", u"FALSE")])
    time.sleep(1)
    log(u"  Init_En snYat: PC=%s  PCLat=%s"
        % (rd(u"GVL_PLCVisu.PC"), rd(u"PLC_PRG.fbPCLatch.Q")))

    # 4. sbros, zatem puskaem
    wr([(u"GVL_Control.Emu_Reset", u"FALSE")])
    time.sleep(1)
    wr([(u"GVL_Control.Emu_Run", u"TRUE")])

    log(u"")
    log(u"  %4s %6s %6s %6s %6s %6s %6s" % (u"t", u"PC", u"IR", u"A", u"F", u"Halt", u"PCNext"))
    for i in range(14):
        time.sleep(0.6)
        log(u"  %4d %6s %6s %6s %6s %6s %6s" % (
            i + 1, rd(u"GVL_PLCVisu.PC"), rd(u"GVL_PLCVisu.IR"),
            rd(u"GVL_PLCVisu.A"), rd(u"GVL_PLCVisu.F"),
            rd(u"GVL_PLCVisu.Halted"), rd(u"PLC_PRG.fbPC.PC_Next")))

    log(u"")
    log(u"--- itog ---")
    for n in (u"GVL_PLCVisu.PC", u"GVL_PLCVisu.IR", u"GVL_PLCVisu.Halted",
              u"PLC_PRG.fbPC.PC_Next", u"PLC_PRG.fbPCLatch.Q",
              u"PLC_PRG.vIncBy", u"PLC_PRG.vPCLoad", u"PLC_PRG.vPCNew",
              u"GVL_Control.Ctl_Is_HALT", u"PLC_PRG.vRun",
              u"PLC_PRG.fbCtl.Halted", u"PLC_PRG.vFetch"):
        log(u"  %-28s = %s" % (n, rd(n)))

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
sys.stdout.write(u"diag_nop: %d strok\n" % len(LINES))
