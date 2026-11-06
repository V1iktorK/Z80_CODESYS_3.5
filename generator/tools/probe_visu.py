# -*- coding: utf-8 -*-
u"""E S T  L I  V  A P I  S O Z D A N I E  V I Z U A L I Z A C I I.

Z A Ch E M. V dokumentatsii vizualizatsiya HMI zapisana kak ruchnoy shag
(risovanie v IDE). No esli ScriptEngine umeet sozdavat vizualizacii, to eto
mozhno sdelat programmno -- i togda produkt polnyj, bez ruchnyh shagov.

Zdes nichego ne men yaem: vytaskivaem spisok metodov prilozheniya i
proektu, chtoby ponyat, chto dostupno.

ZAPUSK: run_probe_fb.ps1 -Fbs none -Script tools\probe_visu.py
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
OUT = os.path.join(LOG, u"probe_visu.txt")

DEVICE_TYPE = 4096
DEVICE_ID = u"0000 0001"
DEVICE_VERSION = u"3.5.17.30"

LINES = []


def log(m):
    LINES.append((u"%s" % (m,)).replace(u"%", u"%"))


def dump(obj, title):
    log(u"")
    log(u"### %s" % title)
    try:
        names = sorted(dir(obj))
    except Exception as exc:                                   # noqa: BLE001
        log(u"    dir() OSHIBKA: %s" % exc)
        return
    for nm in names:
        if nm.startswith(u"_"):
            continue
        try:
            v = getattr(obj, nm)
        except Exception:                                      # noqa: BLE001
            log(u"    " + nm)
            continue
        if callable(v):
            log(u"    " + nm + u"()")
        else:
            log(u"    " + nm)


def main():
    log(u"=== PROBE VISU ===")
    proj = scriptengine.projects.create(os.path.join(BUILD, u"probe_visu.project"))
    proj.add(name=u"Device", type=DEVICE_TYPE, id=DEVICE_ID,
             version=DEVICE_VERSION)
    app = proj.active_application

    log(u"--- proby metodov sozdaniya vizualizacii ---")
    for meth in (u"create_visualization", u"create_visualisation",
                 u"create_visu", u"create_visual", u"create_hmi"):
        try:
            f = getattr(app, meth)
            log(u"  app.%s EST -> %s" % (meth, f))
        except Exception as exc:
            log(u"  app.%s net: %s" % (meth, exc))
    for meth in (u"create_visualization", u"import_xml", u"import_native"):
        try:
            f = getattr(app, meth)
            log(u"  (2) app.%s EST" % meth)
        except Exception as exc:
            log(u"  (2) app.%s net" % meth)

    log(u"")
    log(u"--- poisk slov vizual/visu/web ---")
    for nm in dir(app):
        low = nm.lower()
        if u"visu" in low or u"visual" in low or u"web" in low or u"hmi" in low:
            log(u"    app." + nm)
    for nm in dir(proj):
        low = nm.lower()
        if u"visu" in low or u"visual" in low or u"web" in low or u"hmi" in low:
            log(u"    proj." + nm)

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
sys.stdout.write(u"probe_visu: %d strok\n" % len(LINES))
