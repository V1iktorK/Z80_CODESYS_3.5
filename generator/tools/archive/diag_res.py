# -*- coding: utf-8 -*-
u"""P O K A Z A T '  R E Z U L ' T A T  K A Zh D O G O  T E S T A.

Z A Ch E M. Svodka "0 iz 40" ne govorit, chto imenno ne tak. Zdes posle
progona chitaem po kazhdomu testu: vypolnyalsya li on (Executed) i chem
zakonchilsya (Result), a dlya provalennyh -- chto ozhidali.

ZAPUSK: generator\run_sim.ps1 -Script tools\diag_res.py
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
OUT = os.path.join(LOG, u"diag_res.txt")

N = 40

LINES = []


def log(m):
    LINES.append((u"%s" % (m,)))


def main():
    log(u"=== REZULTATY PO KAZHDOMU TESTU ===")
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

    time.sleep(2)
    wr([(u"GVL_Tests.Cpu_Test_Run", u"FALSE"),
        (u"GVL_Control.Emu_Run", u"FALSE"),
        (u"GVL_Control.Emu_Reset", u"TRUE")])
    time.sleep(1)
    wr([(u"GVL_Control.Emu_Reset", u"FALSE"),
        (u"GVL_Tests.Cpu_Test_Run", u"TRUE")])

    #  zhdyom zaversheniya
    for i in range(60):
        time.sleep(1)
        run = rd(u"GVL_Tests.Cpu_Test_Run")
        if u"FALSE" in run:
            log(u"progon zavershen za %d s" % (i + 1))
            break

    log(u"")
    log(u"  itog: pass=%s fail=%s stage=%s"
        % (rd(u"GVL_Tests.Cpu_Test_Total_Pass"),
           rd(u"GVL_Tests.Cpu_Test_Fail_Count"),
           rd(u"GVL_Tests.Cpu_Test_Stage")))
    log(u"")
    log(u"  %3s %8s %7s %5s %6s %6s %6s %6s" % (
        u"#", u"Exec", u"Result", u"Op", u"ExpA", u"ExpF", u"ExpPC", u"Cyc"))
    passed = 0
    failed = 0
    notexec = 0
    for i in range(1, N + 1):
        ex = rd(u"GVL_Tests.Cpu_Test_Executed[%d]" % i)
        rs = rd(u"GVL_Tests.Cpu_Test_Result[%d]" % i)
        op = rd(u"GVL_Tests.Cpu_Tests[%d].Opcode" % i)
        ea = rd(u"GVL_Tests.Cpu_Tests[%d].Exp_A" % i)
        ef = rd(u"GVL_Tests.Cpu_Tests[%d].Exp_F" % i)
        ep = rd(u"GVL_Tests.Cpu_Tests[%d].Exp_PC" % i)
        cy = rd(u"GVL_Tests.Cpu_Tests[%d].Exp_Cycles" % i)
        if u"TRUE" in ex:
            if u"TRUE" in rs:
                passed += 1
            else:
                failed += 1
                log(u"  %3d %8s %7s %5s %6s %6s %6s %6s  <-- PROVAL"
                    % (i, ex, rs, op, ea, ef, ep, cy))
                continue
        else:
            notexec += 1
        log(u"  %3d %8s %7s %5s %6s %6s %6s %6s"
            % (i, ex, rs, op, ea, ef, ep, cy))

    log(u"")
    log(u"  projdeno %d, provaleno %d, ne vypolneno %d" % (passed, failed, notexec))

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
sys.stdout.write(u"diag_res: %d strok\n" % len(LINES))
