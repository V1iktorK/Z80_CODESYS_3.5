# -*- coding: utf-8 -*-
u"""SIM PROBE -- chto realno delaet emulyator v simulyatsii.

Vhodim v onlajn (rezhim simulyatsii), kladem v pamyat korotkuyu programmu,
puskaem na neskolko skanov i chitaem sostoyanie.

V A Zh N O  P R O  A D R E S A. PRG_InitMemory zapolnyaet nulevuyu stranitsu
tablitsey perehodov: po adresu 0 lezhit "JP 0100h" (C3 00 01). Poetomu
programmu kladem s 0100h -- tak zhe, kak zagruzhaetsya .COM v CP/M.

V A Zh N O  P R O  T I P Y. set_prepared_value prinimaet S T R O K U,
a ne bool/int. Popytka peredat bool daet "expected str, got bool",
i znachenie molcha ne zapisyvaetsya.

Programma: 3E 55 3C 76 = LD A,55h ; INC A ; HALT
Ozhidaemyy rezul tat: A = 16#56, PC = 16#0104, Halted = TRUE.

ZAPUSK: generator\run_diag.ps1 -Script "sim_probe.py" -OutName "simprobe"
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
OUT = os.path.join(LOG, u"sim_probe.txt")

L = []


def log(m):
    L.append(u"%s" % (m,))


REGS = [(u"PC", u"GVL_PLCVisu.PC"), (u"A", u"GVL_PLCVisu.A"),
        (u"F", u"GVL_PLCVisu.F"), (u"IR", u"GVL_PLCVisu.IR"),
        (u"SP", u"GVL_PLCVisu.SP"), (u"Halt", u"GVL_PLCVisu.Halted")]


def show(oapp, tag):
    parts = []
    for nm, expr in REGS:
        try:
            parts.append(u"%s=%s" % (nm, oapp.read_value(expr)))
        except Exception:
            parts.append(u"%s=<ERR>" % nm)
    log(u"  %-12s %s" % (tag, u"  ".join(parts)))


def wr(oapp, pairs):
    for expr, val in pairs:
        try:
            oapp.set_prepared_value(expr, u"%s" % val)
        except Exception as exc:
            log(u"    set %s = %s OSHIBKA: %s" % (expr, val, exc))
    try:
        oapp.write_prepared_values()
    except Exception as exc:
        log(u"    write_prepared_values OSHIBKA: %s" % exc)


def main():
    log(u"=== SIM PROBE ===")
    if not os.path.exists(PROJ):
        log(u"net proekta")
        return
    proj = scriptengine.projects.open(PROJ)
    app = proj.active_application
    try:
        app.build()
    except Exception as exc:
        log(u"build: %s" % exc)
    dev = list(proj.find(u"Device"))[0]
    try:
        dev.set_simulation_mode(True)
        log(u"rezhim simulyatsii vklyuchen")
    except Exception as exc:
        log(u"set_simulation_mode: %s" % exc)

    oapp = scriptengine.online.create_online_application(app)
    oapp.login(scriptengine.OnlineChangeOption.Try, False)
    log(u"login OK")
    oapp.start()
    log(u"start OK, state=%s" % oapp.application_state)
    time.sleep(1.0)

    log(u"")
    log(u"--- 1. ostanov i zagruzka programmy v 0100h ---")
    wr(oapp, [(u"GVL_Control.Emu_Run", u"FALSE"),
              (u"GVL_Control.Emu_Reset", u"FALSE")])
    prog = [0x3E, 0x55, 0x3C, 0x76]
    pairs = []
    for k, b in enumerate(prog):
        pairs.append((u"GVL_Memory.Z80_Mem[%d]" % (0x100 + k), u"16#%02X" % b))
    pairs.append((u"GVL_PLCVisu.PC", u"16#0100"))
    wr(oapp, pairs)
    log(u"  programma: 3E 55 3C 76 (LD A,55h ; INC A ; HALT)")

    log(u"")
    log(u"--- 2. proverka, chto pamyat legla ---")
    for a in (0x100, 0x101, 0x102, 0x103):
        try:
            log(u"  Z80_Mem[%d] = %s" % (a, oapp.read_value(
                u"GVL_Memory.Z80_Mem[%d]" % a)))
        except Exception:
            log(u"  Z80_Mem[%d] <ERR>" % a)
    show(oapp, u"do puska")

    log(u"")
    log(u"--- 3. puskaem: Emu_Run := TRUE ---")
    wr(oapp, [(u"GVL_Control.Emu_Run", u"TRUE")])
    for k in range(8):
        time.sleep(0.5)
        show(oapp, u"skan %d" % (k + 1))

    log(u"")
    log(u"--- 4. itog ---")
    try:
        log(u"  A  = %s   (ozhidaetsya BYTE#86)" % oapp.read_value(u"GVL_PLCVisu.A"))
        log(u"  PC = %s   (ozhidaetsya WORD#260)" % oapp.read_value(u"GVL_PLCVisu.PC"))
    except Exception as exc:
        log(u"  chtenie: %s" % exc)

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
sys.stdout.write(u"sim_probe: %d strok\n" % len(L))
