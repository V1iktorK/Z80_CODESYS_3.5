# -*- coding: utf-8 -*-
u"""probe_build_only.py -- otkryvaet gotovyy proekt i tol'ko kompiliruet ego.

Zapuskaetsya VNUTRI CODESYS. Nuzhen, chtoby ponyat, na kakom etape padenie:
import uzhe proshl, ostaetsya build().
"""

import io
import os
import traceback

import scriptengine

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
BUILD = os.path.join(ROOT, u"build")
LOG = os.path.join(ROOT, u"log", u"probe_build_only.log")
PROJECT = os.path.join(BUILD, u"Z80_EMU.project")


def log(m):
    f = io.open(LOG, "a", encoding="utf-8")
    f.write(u"%s\n" % (m,))
    f.close()


f = io.open(LOG, "w", encoding="utf-8")
f.write(u"")
f.close()

log(u"=== BUILD_ONLY START ===")

for p in list(scriptengine.projects.all):
    try:
        p.close()
    except Exception:
        pass

proj = None
app = None
try:
    proj = scriptengine.projects.open(PROJECT)
    app = proj.active_application
    log(u"proekt otkryt, Application = %s" % app.get_name())
except Exception:
    log(u"OSHIBKA otkrytiya:\n%s" % traceback.format_exc())


def walk(o, ind=0, depth=4, acc=None):
    if acc is None:
        acc = []
    try:
        acc.append(o.get_name())
    except Exception:
        pass
    if ind >= depth:
        return acc
    try:
        kids = o.get_children()
    except Exception:
        kids = []
    for k in kids:
        walk(k, ind + 1, depth, acc)
    return acc


if app is not None:
    log(u"obekty: %s" % u", ".join(sorted(walk(app, 0, 4, []))))
    log(u"--- vyzov build() ---")
    try:
        app.build()
        log(u">>> build() zavershen bez isklyucheniya")
    except Exception:
        log(u">>> build() ISKLYuChENIE:\n%s" % traceback.format_exc())
    try:
        msgs = list(scriptengine.system.get_messages())
        log(u"soobshchenij: %d" % len(msgs))
        for m in msgs[:60]:
            try:
                log(u"  [%s] %s" % (getattr(m, u"severity", u"?"),
                                    getattr(m, u"text", u"?")))
            except Exception:
                pass
    except Exception:
        log(u"get_messages FAIL:\n%s" % traceback.format_exc())

try:
    proj.save()
    log(u"sohranено OK")
except Exception:
    log(u"save FAIL: %s" % traceback.format_exc())

log(u"=== BUILD_ONLY END ===")
