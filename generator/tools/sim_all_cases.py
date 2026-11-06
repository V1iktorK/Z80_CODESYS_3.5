# -*- coding: utf-8 -*-
u"""SIM ALL CASES -- sravneniya po KAZhDOMU testu.

Lovim moment, kogda TEST_Z80 perehodit k sravneniyu (Stage = 2), i
zapisyvaem: nomer testa, chto zhdali i chto poluchili. Tak vidno, kakie
imenno velichiny rashodyatsya -- bez ugadyvaniya.

ZAPUSK: generator\run_diag.ps1 -Script "sim_all_cases.py" -OutName "simall" -TimeoutSec 500
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
OUT = os.path.join(LOG, u"sim_all_cases.txt")

L = []


def log(m):
    L.append(u"%s" % (m,))


def rd(oapp, expr, default=u"-"):
    try:
        return u"%s" % oapp.read_value(expr)
    except Exception:
        return default


def wr(oapp, expr, val):
    try:
        oapp.set_prepared_value(expr, u"%s" % val)
        oapp.write_prepared_values()
    except Exception as exc:
        log(u"  set %s OSHIBKA: %s" % (expr, exc))


def main():
    log(u"=== SIM ALL CASES ===")
    proj = scriptengine.projects.open(PROJ)
    app = proj.active_application
    app.build()
    dev = list(proj.find(u"Device"))[0]
    dev.set_simulation_mode(True)
    oapp = scriptengine.online.create_online_application(app)
    oapp.login(scriptengine.OnlineChangeOption.Try, False)
    oapp.start()
    time.sleep(1.2)

    #  imena testov
    log(u"")
    log(u"--- imena proverok ---")
    for i in range(1, 41):
        nm = rd(oapp, u"GVL_Tests.Cpu_Tests[%d].Name" % i)
        if nm and nm != u"-":
            log(u"  T%02d %s" % (i, nm))

    log(u"")
    log(u"--- progon ---")
    wr(oapp, u"GVL_Tests.Cpu_Test_Run", u"TRUE")
    seen = {}
    for k in range(4000):
        time.sleep(0.004)
        stage = rd(oapp, u"GVL_Tests.Cpu_Test_Stage")
        act = rd(oapp, u"GVL_Tests.Cpu_Test_Active")
        if stage == u"INT#2" and act != u"-":
            try:
                a = int(act.split(u"#")[-1])
            except Exception:
                a = -1
            if a not in seen:
                seen[a] = True
                ea = rd(oapp, u"TEST_Z80.fbCase.Expected_A")
                aa = rd(oapp, u"TEST_Z80.fbCase.Actual_A")
                ef = rd(oapp, u"TEST_Z80.fbCase.Expected_F")
                af = rd(oapp, u"TEST_Z80.fbCase.Actual_F")
                ep = rd(oapp, u"TEST_Z80.fbCase.Expected_PC")
                ap = rd(oapp, u"TEST_Z80.fbCase.Actual_PC")
                ma = rd(oapp, u"TEST_Z80.fbCase.Mask_A")
                mf = rd(oapp, u"TEST_Z80.fbCase.Mask_F")
                mp = rd(oapp, u"TEST_Z80.fbCase.Mask_PC")
                ps = rd(oapp, u"TEST_Z80.fbCase.Pass")
                log(u"  T%02d  A %s/%s m=%-5s  F %s/%s m=%-5s  PC %s/%s m=%-5s  pass=%s"
                    % (a, ea, aa, ma, ef, af, mf, ep, ap, mp, ps))
        if rd(oapp, u"GVL_Tests.Cpu_Test_Run") == u"FALSE" and k > 40:
            log(u"  progon zavershen")
            break

    log(u"")
    log(u"--- itog ---")
    log(u"  Pass = %s" % rd(oapp, u"GVL_Tests.Cpu_Test_Total_Pass"))
    log(u"  Fail = %s" % rd(oapp, u"GVL_Tests.Cpu_Test_Fail_Count"))

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
sys.stdout.write(u"sim_all_cases: %d strok\n" % len(L))
