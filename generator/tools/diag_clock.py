# -*- coding: utf-8 -*-
u"""D I A G N O S T I K A  T A K T A  I  P C.

Fakty iz pervogo prohoda: PC=0 i ne dvigaetsya, IR=0, Halted=TRUE.
Znachit nuzhno ponyat: idut li voobshche takty, i pochemu PC stoit.

Zdes: snimaem testy, delaem sbros, pereiniciliziruem pamyat, puskaem i
smotrim signaly vnutri PLC_PRG (imena ekzemplyarov FB chitayutsya kak
PLC_PRG.fbClock.Clk_Exec i t.d.).

ZAPUSK: generator\run_sim.ps1 -Script tools\diag_clock.py
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
OUT = os.path.join(LOG, u"diag_clock.txt")

WATCH = [
    (u"PC",      u"GVL_PLCVisu.PC"),
    (u"IR",      u"GVL_PLCVisu.IR"),
    (u"ClkEx",   u"PLC_PRG.fbClock.Clk_Exec"),
    (u"ImmM",    u"GVL_Control.Ctl_Imm_Mode"),
    (u"IsJmp",   u"GVL_Control.Ctl_Is_Jump"),
    (u"vAddr",   u"PLC_PRG.vAddr"),
    (u"RdData",  u"PLC_PRG.fbMem.Rd_Data"),
    (u"SP_Out",  u"PLC_PRG.fbMem.SP_Out"),
    (u"vNnHi",   u"PLC_PRG.vNnHi"),
    (u"vImm",    u"PLC_PRG.vImm"),
    (u"PCNew",   u"PLC_PRG.vPCNew"),
    (u"PCLoad",  u"PLC_PRG.vPCLoad"),
    (u"PCNext",  u"PLC_PRG.vPCNext"),
    (u"AddrHL",  u"PLC_PRG.fbRFRd.Addr_HL"),
    (u"vPCLat",  u"PLC_PRG.fbPCLatch.Q"),
]

LINES = []


def log(m):
    LINES.append((u"%s" % (m,)))


def main():
    log(u"=== DIAGNOSTIKA TAKTA ===")
    proj = scriptengine.projects.open(PROJ)
    app = proj.active_application
    try:
        app.build()
    except Exception as exc:                                   # noqa: BLE001
        log(u"build(): %s" % exc)

    dev = list(proj.find(u"Device"))[0]
    try:
        dev.set_simulation_mode(True)
    except Exception:                                          # noqa: BLE001
        pass

    onl = scriptengine.online.create_online_application(app)
    onl.login(scriptengine.OnlineChangeOption.Try, True)
    onl.start()
    log(u"onlajn -- OK")

    def read(name):
        try:
            return u"%s" % onl.read_value(name)
        except Exception as exc:                               # noqa: BLE001
            return u"?%s" % (u"%s" % exc)[:26]

    def write(pairs):
        for nm, v in pairs:
            try:
                onl.set_prepared_value(nm, v)
            except Exception as exc:                           # noqa: BLE001
                log(u"  set %s = %s OSHIBKA: %s" % (nm, v, exc))
        try:
            onl.write_prepared_values()
        except Exception as exc:                               # noqa: BLE001
            log(u"  write_prepared_values OSHIBKA: %s" % exc)

    time.sleep(2)

    #  1. snimaem testy i delaem polnyj sbros + pereinitsializaciyu
    log(u"")
    log(u"--- sbros i initsializaciya ---")
    write([(u"GVL_Tests.Cpu_Test_Run", u"FALSE"),
           (u"GVL_Tests_CPM.Cpm_Test_Run", u"FALSE"),
           (u"GVL_Control.Emu_Run", u"FALSE"),
           (u"GVL_Control.Emu_Reset", u"TRUE")])
    time.sleep(1)
    write([(u"GVL_Control.Emu_Init", u"TRUE")])
    time.sleep(1)
    write([(u"GVL_Control.Emu_Init", u"FALSE"),
           (u"GVL_Control.Emu_Reset", u"FALSE")])
    time.sleep(1)

    log(u"  posle sbrosa:")
    for n, a in WATCH:
        log(u"    %-8s %-28s = %s" % (n, a, read(a)))

    #  2. puskaem
    log(u"")
    log(u"--- puskaem Emu_Run ---")
    write([(u"GVL_Control.Emu_Run", u"TRUE")])

    log(u"")
    log(u"  " + u" ".join([u"%7s" % n for n, _ in WATCH]))
    rows = []
    for i in range(12):
        time.sleep(0.5)
        vals = [read(a) for _, a in WATCH]
        short = []
        for v in vals:
            short.append(v.replace(u"WORD#", u"").replace(u"BYTE#", u"")
                         .replace(u"BOOL#", u"")[:7])
        log(u"  " + u" ".join([u"%7s" % s for s in short]))
        rows.append(tuple(vals))

    log(u"")
    log(u"--- polnye znacheniya v konce ---")
    for n, a in WATCH:
        log(u"  %-8s %-30s = %s" % (n, a, read(a)))

    #  3. proverim, dvigaetsya li PC hot kuda-to
    pcs = set(r[0] for r in rows)
    log(u"")
    log(u"razlichnyh znachenij PC za progon: %d -- %s"
        % (len(pcs), u", ".join(sorted(pcs))[:120]))

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
sys.stdout.write(u"diag_clock: %d strok\n" % len(LINES))
