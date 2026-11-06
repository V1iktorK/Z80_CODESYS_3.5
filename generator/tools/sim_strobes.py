# -*- coding: utf-8 -*-
u"""SIM STROBES -- dohodyat li strobы do registra flagov.

Z A Ch E M. Vyяснено: A i PC schitayutsya verno, a F zalip na 44h.
Znachit delo v strobah Init_En / Ctl_Flags_En. Merim ih v dinamike.

ZAPUSK: generator\run_diag.ps1 -Script "sim_strobes.py" -OutName "simstrobe" -TimeoutSec 400
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
OUT = os.path.join(LOG, u"sim_strobes.txt")

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
        except Exception:
            pass
    try:
        oapp.write_prepared_values()
    except Exception:
        pass


def main():
    log(u"=== SIM STROBES ===")
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
    log(u"--- 1. klyuchevye tochki shemy (spokojnoe sostoyanie) ---")
    for e in (u"GVL_InitRegs.Init_En", u"GVL_InitRegs.Init_Vals[7]",
              u"GVL_InitRegs.Init_Sel_Dst", u"GVL_InitRegs.Init_PC",
              u"GVL_Control.Ctl_Flags_En", u"GVL_Control.Ctl_ALU_Op",
              u"GVL_Control.Ctl_Sel_Dst", u"GVL_Control.Emu_Run",
              u"GVL_PLCVisu.F", u"GVL_PLCVisu.IR", u"GVL_PLCVisu.PC"):
        log(u"  %-32s = %s" % (e, rd(oapp, e)))

    log(u"")
    log(u"--- 2. puskaem testy i lovim perehody Init_En / Flags_En ---")
    wr(oapp, [(u"GVL_Tests.Cpu_Test_Run", u"TRUE")])
    prev = None
    hits = 0
    for k in range(500):
        time.sleep(0.04)
        init_en = rd(oapp, u"GVL_InitRegs.Init_En")
        fl_en = rd(oapp, u"GVL_Control.Ctl_Flags_En")
        cur = (init_en, fl_en)
        if cur != prev:
            log(u"  Init_En=%-6s Ctl_Flags_En=%-6s  F=%-9s IR=%-9s PC=%-11s"
                % (init_en, fl_en, rd(oapp, u"GVL_PLCVisu.F"),
                   rd(oapp, u"GVL_PLCVisu.IR"), rd(oapp, u"GVL_PLCVisu.PC")))
            prev = cur
            hits += 1
            if hits > 60:
                log(u"  (dovolno)")
                break
        if rd(oapp, u"GVL_Tests.Cpu_Test_Run") == u"FALSE" and k > 30:
            log(u"  testy zavershilis")
            break
    log(u"  perehodov zafiksirovano: %d" % hits)

    log(u"")
    log(u"--- 3. itog ---")
    for e in (u"GVL_Tests.Cpu_Test_Total_Pass", u"GVL_Tests.Cpu_Test_Fail_Count",
              u"GVL_PLCVisu.F"):
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
sys.stdout.write(u"sim_strobes: %d strok\n" % len(L))
