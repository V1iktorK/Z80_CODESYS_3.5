# -*- coding: utf-8 -*-
u"""SIM TESTS --progon vstroennyh testov s podrobnym razborom.

Z A Ch E M. run_simulation.py pokazyvaet tolko itog (0 iz 40). Nuzhno
ponyat, K A K I E imenno proverki padayut i chto emulyator fakticheski
pokazyvaet. Poetomu zdes my:
  1) puskaem Cpu_Test_Run i zhdem okonchaniya;
  2) chitaem po kazhdomu testu: vypolnen li (Executed[i]) i rezul tat (Result[i]);
  3) chitaem sostoyanie registrov v moment sravneniya dlya pervogo testa.

ZAPUSK: generator\run_diag.ps1 -Script "sim_tests.py" -OutName "simtests" -TimeoutSec 400
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
OUT = os.path.join(LOG, u"sim_tests.txt")

L = []
NMAX = 40


def log(m):
    L.append(u"%s" % (m,))


def rd(oapp, expr, default=None):
    try:
        return u"%s" % oapp.read_value(expr)
    except Exception:
        return default


def num(oapp, expr):
    v = rd(oapp, expr)
    if v is None:
        return None
    try:
        return int(v.split(u"#")[-1], 0) if u"#" in v else int(v)
    except Exception:
        return None


def wr(oapp, pairs):
    for expr, val in pairs:
        try:
            oapp.set_prepared_value(expr, u"%s" % val)
        except Exception as exc:
            log(u"    set %s OSHIBKA: %s" % (expr, exc))
    try:
        oapp.write_prepared_values()
    except Exception as exc:
        log(u"    write OSHIBKA: %s" % exc)


def main():
    log(u"=== SIM TESTS ===")
    proj = scriptengine.projects.open(PROJ)
    app = proj.active_application
    app.build()
    dev = list(proj.find(u"Device"))[0]
    dev.set_simulation_mode(True)
    oapp = scriptengine.online.create_online_application(app)
    oapp.login(scriptengine.OnlineChangeOption.Try, False)
    oapp.start()
    time.sleep(1.2)
    log(u"onlajn zapushchen")

    log(u"")
    log(u"--- 1. sostoyanie do puska ---")
    for e in (u"GVL_Tests.Cpu_Test_Count", u"GVL_Tests.Cpu_Test_Run",
              u"GVL_Tests.Cpu_Test_Stage", u"GVL_Tests.Cpu_Test_Active"):
        log(u"  %-32s = %s" % (e, rd(oapp, e)))

    log(u"")
    log(u"--- 2. puskaem testy ---")
    wr(oapp, [(u"GVL_Tests.Cpu_Test_Run", u"TRUE")])
    prev = None
    stall = 0
    for k in range(90):
        time.sleep(0.5)
        run = rd(oapp, u"GVL_Tests.Cpu_Test_Run")
        stage = rd(oapp, u"GVL_Tests.Cpu_Test_Stage")
        act = rd(oapp, u"GVL_Tests.Cpu_Test_Active")
        ok = rd(oapp, u"GVL_Tests.Cpu_Test_Total_Pass")
        bad = rd(oapp, u"GVL_Tests.Cpu_Test_Fail_Count")
        cur = (run, stage, act, ok, bad)
        if k < 6 or k % 10 == 0 or cur != prev:
            log(u"  t=%5.1fs run=%-6s stage=%-4s active=%-4s pass=%-4s fail=%-4s"
                % (k * 0.5 + 0.5, run, stage, act, ok, bad))
        if cur == prev:
            stall += 1
        else:
            stall = 0
        prev = cur
        if run == u"FALSE" and k > 2:
            log(u"  testy zavershilis na shage %d" % k)
            break
        if stall > 30:
            log(u"  O S T A N O V: sostoyanie ne menyaetsya 15 sekund")
            break

    log(u"")
    log(u"--- 3. rezultaty po kazhdomu testu ---")
    rows = []
    for i in range(1, NMAX + 1):
        ex = rd(oapp, u"GVL_Tests.Cpu_Test_Executed[%d]" % i)
        rs = rd(oapp, u"GVL_Tests.Cpu_Test_Result[%d]" % i)
        if ex is None:
            continue
        rows.append((i, ex, rs))
    for i, ex, rs in rows:
        log(u"  test %2d: executed=%-6s result=%s" % (i, ex, rs))

    log(u"")
    log(u"--- 4. itog ---")
    for e in (u"GVL_Tests.Cpu_Test_Total_Pass", u"GVL_Tests.Cpu_Test_Fail_Count",
              u"GVL_Tests.Cpu_Test_Count"):
        log(u"  %-32s = %s" % (e, rd(oapp, e)))

    log(u"")
    log(u"--- 5. spisok provalennyh ---")
    for i in range(1, 17):
        v = rd(oapp, u"GVL_Tests.Cpu_Test_Failed_List[%d]" % i)
        if v is not None:
            log(u"  Failed_List[%2d] = %s" % (i, v))

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
sys.stdout.write(u"sim_tests: %d strok\n" % len(L))
