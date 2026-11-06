# -*- coding: utf-8 -*-
u"""probe_check_project.py -- proveryaem, chto realno lezhit v Z80_EMU.project.

Zapuskaetsya VNUTRI CODESYS. Nuzhno ponyat, pochemu v GUI derevo POU pustoe:
net ni Device, ni Application. Proverim:
  1) otkryvaetsya li proekt;
  2) chto v dereve obektov (polnoe derevo);

Rezultat -> log/probe_check_project.log
"""

import io
import os
import traceback

import scriptengine

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
BUILD = os.path.join(ROOT, u"build")
LOG = os.path.join(ROOT, u"log", u"probe_check_project.log")
PROJ = os.path.join(BUILD, u"Z80_EMU.project")
DEVICE_TYPE = 4096
DEVICE_ID = u"0000 0001"
DEVICE_VERSION = u"3.5.17.30"


def log(m):
    f = io.open(LOG, "a", encoding="utf-8")
    f.write(u"%s\n" % (m,))
    f.close()


f = io.open(LOG, "w", encoding="utf-8")
f.write(u"")
f.close()

log(u"=== PROVERKA PROEKTA START ===")

for p in list(scriptengine.projects.all):
    try:
        p.close()
    except Exception:
        pass

proj = None
try:
    proj = scriptengine.projects.open(PROJ)
    log(u"[1] proekt otkryt OK")
    log(u"    put: %s" % getattr(proj, u"path", u"?"))
except Exception:
    log(u"[1] OSHIBKA otkrytiya:\n%s" % traceback.format_exc())

if proj is not None:
    # --- derevo s tipami obektov ---
    def tree(o, ind=0, depth=6):
        try:
            nm = o.get_name()
        except Exception:
            nm = u"?"
        try:
            tn = o.GetType().Name
        except Exception:
            tn = u"?"
        # raspoznaem tip po markeram v repr
        r = repr(o)
        marks = []
        for k in (u"ScriptApplication", u"ScriptDeviceObject", u"LibManObject",
                  u"TaskConfigObject", u"TaskObject", u"ScriptIecLanguageObjectContainerObject"):
            if k in r:
                marks.append(k.replace(u"Script", u"").replace(u"Object", u""))
        log(u"%s- %s  [%s] %s" % (u"  " * ind, nm, tn, u",".join(marks)))
        if ind >= depth:
            return
        try:
            kids = o.get_children()
        except Exception:
            kids = []
        for k in kids:
            tree(k, ind + 1, depth)

    log(u"[2] --- POLNOE DEREVO PROEKTA ---")
    tree(proj, 0, 6)

    # --- est li Application i skolko POU ---
    def walk(o, ind=0, depth=8, acc=None):
        if acc is None:
            acc = []
        try:
            acc.append((o.get_name(), o))
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

    objs = walk(proj, 0, 8, [])
    log(u"")
    log(u"[3] vsego obektov: %d" % len(objs))
    names = [n for n, _ in objs]
    fb = [n for n in names if n.startswith(u"FB_")]
    prg = [n for n in names if n.startswith(u"PRG_") or n.startswith(u"TEST_") or n == u"PLC_PRG"]
    gvl = [n for n in names if n.startswith(u"GVL_")]
    log(u"    FB: %d, programm: %d, GVL: %d" % (len(fb), len(prg), len(gvl)))

    # --- sohranim kopiyu i poprobuem najti Application ---
    app = None
    try:
        app = proj.active_application
        log(u"[4] active_application = %r" % (app,))
    except Exception:
        log(u"[4] active_application OSHIBKA: %s"
            % traceback.format_exc().splitlines()[-1])

try:
    proj.close()
except Exception:
    pass

# --- KONTROLNYY EKSPERIMENT: sozdaem proekt s nulya i srazu smotrim derevo ---
log(u"")
log(u"=== KONTROL: sozdaem proekt s nulya ===")
try:
    test = os.path.join(BUILD, u"probe_ctl.project")
    if os.path.exists(test):
        os.remove(test)
    p2 = scriptengine.projects.create(test)
    log(u"[5] projects.create OK")
    p2.add(name=u"Device", type=DEVICE_TYPE, id=DEVICE_ID, version=DEVICE_VERSION)
    log(u"[5] ustrojstvo dobavleno: type=%d id=%s ver=%s"
        % (DEVICE_TYPE, DEVICE_ID, DEVICE_VERSION))

    def tree2(o, ind=0, depth=5):
        try:
            nm = o.get_name()
        except Exception:
            nm = u"?"
        log(u"%s- %s" % (u"  " * ind, nm))
        if ind >= depth:
            return
        try:
            kids = o.get_children()
        except Exception:
            kids = []
        for k in kids:
            tree2(k, ind + 1, depth)

    log(u"[5] --- DEREVO KONTROLNOGO PROEKTA ---")
    tree2(p2, 0, 5)
    log(u"[5] active_application = %r" % (p2.active_application,))
except Exception:
    log(u"[5] OSHIBKA:\n%s" % traceback.format_exc())

log(u"=== PROVERKA PROEKTA END ===")
