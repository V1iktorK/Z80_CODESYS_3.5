# -*- coding: utf-8 -*-
u"""probe_device.py -- dva sposoba dobavleniya ustrojstva v odnom progony.

Zapuskaetsya VNUTRI CODESYS.
  Sposob A: proj.add(name=u"Device", type=4096, id=u"0000 0001", version=u"3.5.17.30")
            -- kak v generator/build.py (padaet).
  Sposob B: device_repository.create_device_identification(4096, u"0000 0001",
            u"3.5.17.30") i zatem proj.add(u"PLCWinNT", ident, None)
            -- kak v rabochem dsh-skripte (rabotal).
"""

import io
import os
import traceback

import scriptengine

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
BUILD = os.path.join(ROOT, u"build")
LOG = os.path.join(ROOT, u"log", u"probe_device.log")


def log(m):
    f = io.open(LOG, "a", encoding="utf-8")
    f.write(u"%s\n" % (m,))
    f.close()


f = io.open(LOG, "w", encoding="utf-8")
f.write(u"")
f.close()

log(u"=== PROBE_DEVICE START ===")

for p in list(scriptengine.projects.all):
    try:
        p.close()
    except Exception:
        pass

# --- SPOSOB A -------------------------------------------------------------
log(u"--- SPOSOB A: proj.add(type, id, version) ---")
try:
    pa = os.path.join(BUILD, u"probe_devA.project")
    if os.path.exists(pa):
        os.remove(pa)
    projA = scriptengine.projects.create(pa)
    log(u"  projects.create OK")
    projA.add(name=u"Device", type=4096, id=u"0000 0001", version=u"3.5.17.30")
    log(u"  proj.add OK")
    appA = projA.active_application
    log(u"  active_application = %s" % appA.get_name())
    projA.save()
    projA.close()
    log(u"  SPOSOB A: USPEH")
except Exception:
    log(u"  SPOSOB A: OSHIBKA\n%s" % traceback.format_exc())

# --- SPOSOB B -------------------------------------------------------------
log(u"--- SPOSOB B: create_device_identification + add(name, ident, None) ---")
try:
    pb = os.path.join(BUILD, u"probe_devB.project")
    if os.path.exists(pb):
        os.remove(pb)
    projB = scriptengine.projects.create(pb)
    log(u"  projects.create OK")
    ident = scriptengine.device_repository.create_device_identification(
        int(4096), u"0000 0001", u"3.5.17.30")
    log(u"  ident = %r" % (ident,))
    projB.add(u"PLCWinNT", ident, None)
    log(u"  proj.add OK")
    appB = projB.active_application
    log(u"  active_application = %s" % appB.get_name())
    projB.save()
    projB.close()
    log(u"  SPOSOB B: USPEH")
except Exception:
    log(u"  SPOSOB B: OSHIBKA\n%s" % traceback.format_exc())

log(u"=== PROBE_DEVICE END ===")
