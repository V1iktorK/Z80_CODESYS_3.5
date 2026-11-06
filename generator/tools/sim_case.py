# -*- coding: utf-8 -*-
u"""SIM CASE -- chto imenno sravnivaet test i chto poluchaet.

Z A Ch E M. Itog "0 iz 40" nichego ne govorit o prichine. No ekzemplyar
FB_TestCase zhivet v programme TEST_Z80 i ego vhody dostupny po polnomu
puti: TEST_Z80.fbCase.Expected_A, .Actual_A, .Pass i t. d. Znachit mozhno
posmotret, CH T O imenno test sravnivaet i CH T O poluchil emulyator.

ZAPUSK: generator\run_diag.ps1 -Script "sim_case.py" -OutName "simcase" -TimeoutSec 400
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
OUT = os.path.join(LOG, u"sim_case.txt")

L = []


def log(m):
    L.append(u"%s" % (m,))


def rd(oapp, expr, default=u"-"):
    try:
        return u"%s" % oapp.read_value(expr)
    except Exception as exc:
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


FIELDS = [u"Expected_A", u"Actual_A", u"Expected_F", u"Actual_F",
          u"Expected_PC", u"Actual_PC", u"Mask_A", u"Mask_F", u"Mask_PC",
          u"Pass"]


def dump_case(oapp, tag):
    parts = []
    for f in FIELDS:
        parts.append(u"%s=%s" % (f, rd(oapp, u"TEST_Z80.fbCase." + f)))
    log(u"  %-8s %s" % (tag, u" ".join(parts)))


def main():
    log(u"=== SIM CASE ===")
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
    log(u"--- 1. dostupnost polej fbCase ---")
    for f in FIELDS:
        v = rd(oapp, u"TEST_Z80.fbCase." + f)
        log(u"  TEST_Z80.fbCase.%-12s = %s" % (f, v))

    log(u"")
    log(u"--- 2. puskaem testy i lovim moment sravneniya ---")
    wr(oapp, [(u"GVL_Tests.Cpu_Test_Run", u"TRUE")])
    seen = 0
    last_act = None
    for k in range(160):
        time.sleep(0.12)
        run = rd(oapp, u"GVL_Tests.Cpu_Test_Run")
        stage = rd(oapp, u"GVL_Tests.Cpu_Test_Stage")
        act = rd(oapp, u"GVL_Tests.Cpu_Test_Active")
        if act != last_act or stage in (u"INT#2", u"INT#3"):
            log(u"  [stage=%s active=%s] " % (stage, act))
            dump_case(oapp, u"case")
            seen += 1
            if seen > 40:
                break
        last_act = act
        if run == u"FALSE" and k > 5:
            log(u"  testy zavershilis")
            break

    log(u"")
    log(u"--- 3. itog ---")
    for e in (u"GVL_Tests.Cpu_Test_Total_Pass", u"GVL_Tests.Cpu_Test_Fail_Count"):
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
sys.stdout.write(u"sim_case: %d strok\n" % len(L))
