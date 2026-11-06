# -*- coding: utf-8 -*-
u"""probe_ops_import.py -- importiruet FB_OPS_PROBE i vygruzhaet ego obratno.

Zapuskaetsya VNUTRI CODESYS. Chtoby uznat kanonicheskie imena pinov vseh
operatorov: import -> export -> chitaem imena.

Rezultat -> log/probe_ops.log, src/_ops_reexport.xml
"""

import io
import os
import traceback

import scriptengine

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(ROOT, u"src")
BUILD = os.path.join(ROOT, u"build")
LOG = os.path.join(ROOT, u"log", u"probe_ops.log")
OUT_PROJECT = os.path.join(BUILD, u"probe_ops.project")


def log(m):
    f = io.open(LOG, "a", encoding="utf-8")
    f.write(u"%s\n" % (m,))
    f.close()


f = io.open(LOG, "w", encoding="utf-8")
f.write(u"")
f.close()

log(u"=== PROBE_OPS START ===")

for p in list(scriptengine.projects.all):
    try:
        p.close()
    except Exception:
        pass

proj = None
app = None
try:
    for junk in os.listdir(BUILD):
        if junk.startswith(u"probe_ops"):
            try:
                os.remove(os.path.join(BUILD, junk))
            except Exception:
                pass
    proj = scriptengine.projects.create(OUT_PROJECT)
    proj.add(name=u"Device", type=4096, id=u"0000 0001", version=u"3.5.17.30")
    app = proj.active_application
    log(u"proekt sozdan")
except Exception:
    log(u"oshibka:\n%s" % traceback.format_exc())

xc = os.path.join(SRC, u"FB_OPS_PROBE.plcopenxml")
ok = False
try:
    app.import_xml(xc)
    log(u"IMPORT OK: FB_OPS_PROBE")
    ok = True
except Exception:
    log(u"IMPORT FAIL:\n%s" % traceback.format_exc())


def walk(o, ind=0, depth=6, acc=None):
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


if ok:
    tgt = None
    for n, o in walk(app, 0, 4, []):
        log(u"  v dereve: %s" % n)
        if n == u"FB_OPS_PROBE":
            tgt = o
    if tgt is not None:
        try:
            out = os.path.join(SRC, u"_ops_reexport.xml")
            proj.export_xml([tgt], path=out, declarations_as_plaintext=True)
            log(u"vygruzheno: %s" % out)
            t = io.open(out, u"r", encoding=u"utf-8").read()
            i = t.find(u"<FBD>")
            j = t.find(u"</FBD>", i)
            log(u"---------- FBD ----------")
            log(t[i:j + 6] if i >= 0 else u"<FBD> ne najden")
        except Exception:
            log(u"export_xml FAIL:\n%s" % traceback.format_exc())

# --- kompilyaciya kak dopolnitelnaya proverka ------------------------------
if ok:
    try:
        app.build()
        log(u"build() OK")
    except Exception:
        log(u"build() FAIL:\n%s" % traceback.format_exc())
    try:
        for m in scriptengine.system.get_messages():
            try:
                log(u"  [%s] %s" % (getattr(m, u"severity", u"?"),
                                    getattr(m, u"text", u"?")))
            except Exception:
                pass
    except Exception:
        pass

try:
    proj.close()
except Exception:
    pass

log(u"=== PROBE_OPS END ===")
