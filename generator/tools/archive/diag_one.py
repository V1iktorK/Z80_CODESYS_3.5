# -*- coding: utf-8 -*-
u"""R A Z B O R  O D N O G O  T E S T A: chto ozhidaetsya i chto poluchaetsya.

Chitaem opisanie testa #1 iz tablitsy (Cpu_Tests[1]) i potom vypolnyaem
T U  Zh E  podgotovku, chto i TEST_Z80, no vruchnuyu i s pechat yu vsego
sostoyaniya. Tak vidno, gde imenno rashozhdenie: v A, v F ili v PC.

ZAPUSK: generator\run_sim.ps1 -Script tools\diag_one.py
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
OUT = os.path.join(LOG, u"diag_one.txt")

FIELDS = [u"Opcode", u"Opcode_Lo", u"Init_A", u"Init_B", u"Init_F",
          u"Init_PC", u"Init_SP", u"Init_HL", u"Exp_A", u"Exp_F", u"Exp_PC",
          u"Exp_Cycles", u"Stage", u"Mask_A", u"Mask_F", u"Mask_PC",
          u"Mask_Mem", u"Enabled"]

LINES = []


def log(m):
    LINES.append((u"%s" % (m,)))


def main():
    log(u"=== RAZBOR ODNOGO TESTA ===")
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
        (u"GVL_Tests_CPM.Cpm_Test_Run", u"FALSE"),
        (u"GVL_Control.Emu_Run", u"FALSE"),
        (u"GVL_Control.Emu_Reset", u"TRUE")])
    time.sleep(1)

    log(u"")
    log(u"--- opisanie testa #1 ---")
    t1 = {}
    for f in FIELDS:
        v = rd(u"GVL_Tests.Cpu_Tests[1].%s" % f)
        t1[f] = v
        log(u"  %-12s = %s" % (f, v))

    log(u"")
    log(u"--- opisanie testa #2 (dlya sravneniya) ---")
    for f in (u"Opcode", u"Init_A", u"Init_B", u"Init_F", u"Init_PC",
              u"Exp_A", u"Exp_F", u"Exp_PC", u"Exp_Cycles", u"Stage"):
        log(u"  %-12s = %s" % (f, rd(u"GVL_Tests.Cpu_Tests[2].%s" % f)))

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
sys.stdout.write(u"diag_one: %d strok\n" % len(LINES))
