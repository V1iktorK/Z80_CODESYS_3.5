# -*- coding: utf-8 -*-
u"""SIM PROBE 2 -- poshagovoe povedenie na NOP-ah.

C H T O  P R O V E R Ya E M. Odin skan dolzhen vypolnyat ODNU komandu
(tak trebuet zadanie). Kladem v pamyat NOP-y (00h) i smotrim, na skolko
PC rastet za skan. Ozhidaem +1.

Dopolnitelno chitaem shinu adresa (GVL_Bus.Bus_Addr) i IR: tak vidno,
chto realno vybiraetsya iz pamyati.

V A Zh N O: GVL_PLCVisu -- eto ZERKALO dlya HMI, a ne sam registr.
Pisat v nego ne znachit izmenit PC. Poetomu PC my NE zadаem, a
prosto nablyudaem.

ZAPUSK: generator\run_diag.ps1 -Script "sim_probe2.py" -OutName "simprobe2"
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
OUT = os.path.join(LOG, u"sim_probe2.txt")

L = []


def log(m):
    L.append(u"%s" % (m,))


def rd(oapp, expr, default=u"?"):
    try:
        return u"%s" % oapp.read_value(expr)
    except Exception:
        return default


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


def snap(oapp, tag):
    log(u"  %-10s PC=%-12s BusAddr=%-12s IR=%-10s A=%-10s F=%-10s"
        % (tag,
           rd(oapp, u"GVL_PLCVisu.PC"), rd(oapp, u"GVL_Bus.Bus_Addr"),
           rd(oapp, u"GVL_PLCVisu.IR"), rd(oapp, u"GVL_PLCVisu.A"),
           rd(oapp, u"GVL_PLCVisu.F")))


def main():
    log(u"=== SIM PROBE 2: NOP-y ===")
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

    #  ostanovit emulyator i polozhit NOP-y s nulа
    wr(oapp, [(u"GVL_Control.Emu_Run", u"FALSE")])
    pairs = []
    for a in range(0, 32):
        pairs.append((u"GVL_Memory.Z80_Mem[%d]" % a, u"16#00"))
    wr(oapp, pairs)
    log(u"")
    log(u"--- pamyat 0000h..001Fh zapolnena NOP (00h) ---")
    for a in (0, 1, 2, 3):
        log(u"  Z80_Mem[%d] = %s" % (a, rd(oapp, u"GVL_Memory.Z80_Mem[%d]" % a)))
    snap(oapp, u"do puska")

    log(u"")
    log(u"--- puskaem i nablyudaem ---")
    wr(oapp, [(u"GVL_Control.Emu_Run", u"TRUE")])
    for k in range(10):
        time.sleep(0.35)
        snap(oapp, u"skan %d" % (k + 1))

    log(u"")
    log(u"--- proverka drugogo koda: LD A,55h po adresu 0 ---")
    wr(oapp, [(u"GVL_Control.Emu_Run", u"FALSE"),
              (u"GVL_Control.Emu_Reset", u"TRUE")])
    time.sleep(0.4)
    wr(oapp, [(u"GVL_Control.Emu_Reset", u"FALSE")])
    wr(oapp, [(u"GVL_Memory.Z80_Mem[0]", u"16#3E"),
              (u"GVL_Memory.Z80_Mem[1]", u"16#55"),
              (u"GVL_Memory.Z80_Mem[2]", u"16#00")])
    snap(oapp, u"posle reset")
    wr(oapp, [(u"GVL_Control.Emu_Run", u"TRUE")])
    for k in range(6):
        time.sleep(0.35)
        snap(oapp, u"zap %d" % (k + 1))

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
sys.stdout.write(u"sim_probe2: %d strok\n" % len(L))
