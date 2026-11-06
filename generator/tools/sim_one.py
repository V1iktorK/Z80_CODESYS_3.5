# -*- coding: utf-8 -*-
u"""SIM ONE -- progon ODNOGO testa s razborom signalov upravleniya.

Vklyuchaem tolko odin test (po nomeru iz peremennoj Z80_TEST), gonim i
chitaem: rezul tat, A/F/PC, a takzhe signaly dekodera i vyhod ALU.
Tak vidno, na kakom shage rezul tat ALU ne popadaet v registr.

ZAPUSK: generator\run_diag.ps1 -Script "sim_one.py" -OutName "simone" -TimeoutSec 300
"""
import io
import os
import sys
import time

import scriptengine

ROOT = os.environ.get(u"Z80_ROOT")
if not ROOT:
    ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROJ = os.path.join(ROOT, u"build", u"Z80_EMU.project")
LOG = os.path.join(ROOT, u"log")
NUM = os.environ.get(u"Z80_TEST") or u"13"
OUT = os.path.join(LOG, u"sim_one_%s.txt" % NUM)

L = []


def log(m):
    L.append(u"%s" % (m,))


def rd(oapp, expr, default=u"-"):
    try:
        return u"%s" % oapp.read_value(expr)
    except Exception:
        return default


def wr(oapp, pairs):
    for expr, val in pairs:
        try:
            oapp.set_prepared_value(expr, u"%s" % val)
        except Exception as exc:
            log(u"  set %s OSHIBKA: %s" % (expr, exc))
    try:
        oapp.write_prepared_values()
    except Exception as exc:
        log(u"  write OSHIBKA: %s" % exc)


def main():
    n = int(NUM)
    log(u"=== SIM ONE: test %d ===" % n)
    proj = scriptengine.projects.open(PROJ)
    app = proj.active_application
    app.build()
    dev = list(proj.find(u"Device"))[0]
    dev.set_simulation_mode(True)
    oapp = scriptengine.online.create_online_application(app)
    oapp.login(scriptengine.OnlineChangeOption.Try, False)
    oapp.start()
    time.sleep(1.2)

    log(u"")
    log(u"--- tablitsa testa po usloviyu ---")
    for f in (u"Enabled", u"Opcode", u"Init_A", u"Init_B", u"Init_F",
              u"Init_PC", u"Init_SP", u"Exp_A", u"Exp_F", u"Exp_PC",
              u"Mask_A", u"Mask_F", u"Mask_PC", u"Exp_Cycles"):
        log(u"  Cpu_Tests[%d].%-11s = %s" % (n, f, rd(oapp, u"GVL_Tests.Cpu_Tests[%d].%s" % (n, f))))

    #  ostavim tolko odin test
    log(u"")
    log(u"--- vyklyuchaem vse, krome %d ---" % n)
    pairs = []
    for i in range(1, 41):
        pairs.append((u"GVL_Tests.Cpu_Tests[%d].Enabled" % i,
                      u"TRUE" if i == n else u"FALSE"))
    wr(oapp, pairs)
    time.sleep(0.6)
    log(u"  Cpu_Test_Count = %s" % rd(oapp, u"GVL_Tests.Cpu_Test_Count"))

    log(u"")
    log(u"--- puskaem odin test ---")
    wr(oapp, [(u"GVL_Tests.Cpu_Test_Active", u"%d" % n),
              (u"GVL_Tests.Cpu_Test_Stage", u"0"),
              (u"GVL_Tests.Cpu_Test_Run", u"TRUE")])
    for k in range(120):
        time.sleep(0.08)
        st = rd(oapp, u"GVL_Tests.Cpu_Test_Stage")
        if st == u"INT#9" or st == u"INT#3":
            break
    log(u"  Stage = %s" % rd(oapp, u"GVL_Tests.Cpu_Test_Stage"))

    log(u"")
    log(u"--- rezul tat i sostoyanie ---")
    for e in (u"GVL_Tests.Cpu_Test_Result[%d]" % n,
              u"GVL_PLCVisu.A", u"GVL_PLCVisu.B", u"GVL_PLCVisu.C",
              u"GVL_PLCVisu.F", u"GVL_PLCVisu.PC", u"GVL_PLCVisu.IR",
              u"GVL_Control.Ctl_ALU_Op", u"GVL_Control.Ctl_Sel_Dst",
              u"GVL_Control.Ctl_Wr_Enable", u"GVL_Control.Ctl_IncDec",
              u"GVL_Control.Ctl_Flags_En", u"GVL_Control.Emu_Run",
              u"PLC_PRG.vY", u"PLC_PRG.vSrc", u"PLC_PRG.vIncBy",
              u"PLC_PRG.vCtl_Sel_Dst", u"PLC_PRG.vCtl_Wr_Enable",
              u"PLC_PRG.fbRF.A", u"PLC_PRG.fbRFRd.A",
              u"PLC_PRG.fbRF.Src_Val", u"PLC_PRG.fbRFRd.Src_Val",
              u"PLC_PRG.vInitWr", u"PLC_PRG.vWrEn", u"PLC_PRG.vClkWr",
              u"PLC_PRG.fbALU.Y",
              u"GVL_InitRegs.Init_Sel_Dst", u"GVL_InitRegs.Init_Busy",
              u"GVL_InitRegs.Init_En", u"GVL_InitRegs.Init_Vals[0]",
              u"GVL_InitRegs.Init_Vals[1]", u"PLC_PRG.vClkWr"):
        log(u"  %-34s = %s" % (e, rd(oapp, e)))

    try:
        oapp.stop()
        oapp.logout()
    except Exception:
        pass
    proj.close()
    log(u"=== KONEC ===")


try:
    main()
except Exception, exc:
    log(u"AVARIYA: %s" % exc)
    import traceback
    log(traceback.format_exc())

if not os.path.isdir(LOG):
    os.makedirs(LOG)
f = open(OUT, u"w")
f.write(u"\n".join(L).encode(u"utf-8"))
f.close()
sys.stdout.write(u"sim_one: %d strok\n" % len(L))
