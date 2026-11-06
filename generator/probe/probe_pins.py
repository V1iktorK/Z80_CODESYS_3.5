# -*- coding: utf-8 -*-
u"""probe_pins.py -- vyyasnit' imena pinov elementarnyh blokov dlya importa.

Zapuskaetsya VNUTRI CODESYS. Delaet tri shaga:
  1) importiruet odnu shemu s yavno nazvannymi pinami;
  2) esli import proshel -- vygruzhaet POU obratno v XML;
  3) vyvodit poluchennyj XML, chtoby uvidet kanonicheskie imena pinov.

Rezultat -> log/probe_pins.log i src/_pins_reexport.xml
"""

import io
import os
import traceback

import scriptengine

HERE = os.path.dirname(os.path.abspath(__file__))          # .../generator/probe
ROOT = os.path.dirname(os.path.dirname(HERE))              # .../Z80_EMU
SRC = os.path.join(ROOT, u"src")
LOG = os.path.join(ROOT, u"log", u"probe_pins.log")
BUILD = os.path.join(ROOT, u"build")
OUT_PROJECT = os.path.join(BUILD, u"probe_pins.project")


def log(m):
    f = io.open(LOG, "a", encoding="utf-8")
    f.write(u"%s\n" % (m,))
    f.close()


f = io.open(LOG, "w", encoding="utf-8")
f.write(u"")
f.close()

log(u"=== PROBE_PINS START ===")

for p in list(scriptengine.projects.all):
    try:
        p.close()
    except Exception:
        pass

proj = None
app = None
try:
    for junk in os.listdir(BUILD):
        if junk.startswith(u"probe_pins"):
            try:
                os.remove(os.path.join(BUILD, junk))
            except Exception:
                pass
    proj = scriptengine.projects.create(OUT_PROJECT)
    proj.add(name=u"Device", type=4096, id=u"0000 0001", version=u"3.5.17.30")
    app = proj.active_application
    log(u"proekt i Application sozdany")
except Exception:
    log(u"oshibka sozdaniya:\n%s" % traceback.format_exc())

# --- probuem raznye imena pinov --------------------------------------------
CANDIDATES = [
    (u"FB_PIN_A", u"IN1", u"IN2", u"OUT"),
    (u"FB_PIN_B", u"IN", u"", u"OUT"),
    (u"FB_PIN_C", u"", u"", u""),
]

imported = []
for name, pin1, pin2, pout in CANDIDATES:
    path = os.path.join(SRC, u"%s.plcopenxml" % name)
    if not os.path.exists(path):
        log(u"  net fajla %s -- propusk" % path)
        continue
    try:
        app.import_xml(path)
        imported.append(name)
        log(u"  IMPORT OK: %s (piny: %r %r / %r)" % (name, pin1, pin2, pout))
    except Exception:
        log(u"  IMPORT FAIL: %s\n%s" % (name, traceback.format_exc()))

log(u"importirovano: %r" % (imported,))

# --- vygruzka obratno ------------------------------------------------------
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


found = []
for n, o in walk(app, 0, 4, []):
    log(u"  v dereve: %s" % n)
    if n in [c[0] for c in CANDIDATES]:
        found.append(o)

if found:
    try:
        out = os.path.join(SRC, u"_pins_reexport.xml")
        proj.export_xml(found, path=out, declarations_as_plaintext=True)
        log(u"vygruzheno: %s" % out)
        t = io.open(out, u"r", encoding=u"utf-8").read()
        log(u"---------- nachalo vygruzki ----------")
        log(t[:6000])
    except Exception:
        log(u"export_xml FAIL:\n%s" % traceback.format_exc())

try:
    proj.close()
except Exception:
    pass

log(u"=== PROBE_PINS END ===")
