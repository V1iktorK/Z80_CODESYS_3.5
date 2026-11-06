# -*- coding: utf-8 -*-
u"""E S T '  L I  D O S T U P  K  O N L A J N - R E Zh I M U  I Z  S K R I P T A.

Z A Ch E M. Sborka dokazyvaet korrektnost tipov, no ne korrektnost emulyatsii.
Chtoby proverit, chto komandy Z80 deystvitelno rabotayut, nuzhno vypolnit
proekt i prochitat rezultaty testov. Esli ScriptEngine umeet sozdavat online-
prisposoblenie, eto mozhno sdelat bez ruchnogo F5.

Zdes tolko RAZVEDKA: chto est v scriptengine.online i chto umeet prilozhenie.

ZAPUSK: run_probe_fb.ps1 -Fbs none -Script tools\probe_online.py
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
OUT = os.path.join(LOG, u"probe_online.txt")

DEVICE_TYPE = 4096
DEVICE_ID = u"0000 0001"
DEVICE_VERSION = u"3.5.17.30"

LINES = []


def log(m):
    LINES.append((u"%s" % (m,)))


def main():
    log(u"=== PROBE ONLINE ===")

    log(u"")
    log(u"--- scriptengine.online ---")
    try:
        om = scriptengine.online
        for nm in sorted(dir(om)):
            if nm.startswith(u"_"):
                continue
            log(u"  online." + nm)
    except Exception as exc:                                   # noqa: BLE001
        log(u"  net scriptengine.online: %s" % exc)

    #  probuem sozdat proekt i posmotret, chto est u prilozheniya dlya onlajna
    proj = scriptengine.projects.create(os.path.join(BUILD, u"probe_online.project"))
    proj.add(name=u"Device", type=DEVICE_TYPE, id=DEVICE_ID,
             version=DEVICE_VERSION)
    app = proj.active_application

    log(u"")
    log(u"--- metody prilozheniya dlya onlajna ---")
    for meth in (u"set_simulation_mode", u"get_simulation_mode",
                 u"login", u"logout", u"start", u"stop", u"online_application",
                 u"create_online_application", u"generate_code", u"build"):
        try:
            f = getattr(app, meth)
            log(u"  app.%-30s EST" % meth)
        except Exception:                                      # noqa: BLE001
            log(u"  app.%-30s net" % meth)

    log(u"")
    log(u"--- popytka create_online_application ---")
    try:
        onl = scriptengine.online.create_online_application(app)
        log(u"  SOZDANO: %s" % onl)
        for nm in sorted(dir(onl)):
            if nm.startswith(u"_"):
                continue
            log(u"    onl." + nm)
    except Exception as exc:                                   # noqa: BLE001
        log(u"  OSHIBKA: %s" % exc)

    proj.save()
    proj.close()
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
sys.stdout.write(u"probe_online: %d strok\n" % len(LINES))
