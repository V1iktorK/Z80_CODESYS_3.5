# -*- coding: utf-8 -*-
u"""K A K  V K L Yu Ch I T '  S I M U L Ya Ts I Yu  I Z  S K R I P T A.

Chto uzhe izvestno (opyt run_simulation.py):
  * proekt otkryvaetsya, build() prohodit;
  * online.create_online_application(app) sozdaet obekt;
  * login() padaet: "Nekorrektnaya konfiguratsiya Gateway";
  * u proekta N E T svojstva .devices.

Znachit nuzhno: dojti do ustrojstva i vklyuchit u nego rezhim simulyatsii
(ili zadat adres/gateway). Zdes razvedka: kak poluchit ustrojstvo i kakie
u nego est metody pro simulyatsiyu i shlyuz.

ZAPUSK: run_sim.ps1 -Script tools\probe_sim_api.py   (ili napryamuyu cherez
        podmenu; glavnoe -- NE chistit build, poetomu tolko run_sim.ps1)
"""
import io
import os
import sys

import scriptengine

ROOT = os.environ.get(u"Z80_ROOT")
if not ROOT:
    ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUILD = os.path.join(ROOT, u"build")
LOG = os.path.join(ROOT, u"log")
PROJ = os.path.join(BUILD, u"Z80_EMU.project")
OUT = os.path.join(LOG, u"probe_sim_api.txt")

LINES = []


def log(m):
    LINES.append((u"%s" % (m,)))


def main():
    log(u"=== PROBE SIM API ===")
    proj = scriptengine.projects.open(PROJ)
    app = proj.active_application

    #  1. kak dojti do ustrojstva
    log(u"")
    log(u"--- poisk ustrojstva ---")
    for expr in (u'proj.find(u"Device")',):
        pass
    try:
        found = list(proj.find(u"Device"))
        log(u"  proj.find('Device'): %d sht" % len(found))
        for f in found:
            log(u"    %s" % f)
    except Exception as exc:                                   # noqa: BLE001
        log(u"  proj.find OSHIBKA: %s" % exc)

    for meth in (u"get_children", u"find", u"children"):
        try:
            m = getattr(proj, meth)
            log(u"  proj.%s EST" % meth)
        except Exception:                                      # noqa: BLE001
            log(u"  proj.%s net" % meth)

    dev = None
    try:
        kids = list(proj.get_children())
        log(u"  get_children(): %d sht" % len(kids))
        for k in kids:
            log(u"    %s" % ((u"%s" % k)[:100]))
        if kids:
            dev = kids[0]
    except Exception as exc:                                   # noqa: BLE001
        log(u"  get_children OSHIBKA: %s" % exc)

    #  2a. PROBUEM PO IMENAM NAPRYAMUYU (dir() u takih obektov ne polnyj)
    if dev is not None:
        log(u"")
        log(u"--- pryamye popytki metodov ustrojstva ---")
        for nm in (u"set_simulation_mode", u"get_simulation_mode",
                   u"set_gateway_and_address", u"set_address",
                   u"gateway", u"address", u"set_gateway",
                   u"set_communication"):
            try:
                v = getattr(dev, nm)
                log(u"  dev.%s EST (%s)" % (nm, v))
            except Exception as exc:
                log(u"  dev.%s net: %s" % (nm, (u"%s" % exc)[:60]))
        try:
            dev.set_simulation_mode(True)
            log(u"  set_simulation_mode(True) -- OK")
        except Exception as exc:
            log(u"  set_simulation_mode(True) OSHIBKA: %s" % exc)
        try:
            log(u"  get_simulation_mode = %s" % dev.get_simulation_mode())
        except Exception as exc:
            log(u"  get_simulation_mode OSHIBKA: %s" % exc)

    #  2. metody ustrojstva pro simulyatsiyu i shlyuz
    if dev is not None:
        log(u"")
        log(u"--- metody ustrojstva (simulyatsiya / shlyuz / adres) ---")
        hit = 0
        for nm in sorted(dir(dev)):
            low = nm.lower()
            if u"sim" in low or u"gate" in low or u"addr" in low or u"connect" in low:
                log(u"  dev." + nm)
                hit += 1
        if hit == 0:
            log(u"  (nichego ne najdeno)")

    #  3. onlajn-ustrojstvo
    log(u"")
    log(u"--- online.create_online_device ---")
    if dev is not None:
        try:
            od = scriptengine.online.create_online_device(dev)
            log(u"  sozdano: %s" % od)
            for nm in sorted(dir(od)):
                if nm.startswith(u"_"):
                    continue
                log(u"    od." + nm)
        except Exception as exc:                               # noqa: BLE001
            log(u"  OSHIBKA: %s" % exc)

    #  4. shlyuzy
    log(u"")
    log(u"--- scriptengine.online.gateways ---")
    try:
        gws = scriptengine.online.gateways
        log(u"  %s" % gws)
        try:
            log(u"  set(gateways) = %s" % list(gws))
        except Exception:                                      # noqa: BLE001
            pass
    except Exception as exc:                                   # noqa: BLE001
        log(u"  OSHIBKA: %s" % exc)

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
sys.stdout.write(u"probe_sim_api: %d strok\n" % len(LINES))
