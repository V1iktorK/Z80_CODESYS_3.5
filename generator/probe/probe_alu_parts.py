# -*- coding: utf-8 -*-
u"""probe_alu_parts.py -- importiruet 5 chastej ALU i pokazyvaet, kakaya padaet.

Zapuskaetsya VNUTRI CODESYS. Bisekciya: polnyj ALU teryaetsya pri importe,
nuzhno ponyat, kakaya imenno set' (ili ih sochetanie) vinovna.
"""

import io
import os
import traceback

import scriptengine

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(ROOT, u"src")
BUILD = os.path.join(ROOT, u"build")
LOG = os.path.join(ROOT, u"log", u"probe_alu_parts.log")


def log(m):
    f = io.open(LOG, "a", encoding="utf-8")
    f.write(u"%s\n" % (m,))
    f.close()


f = io.open(LOG, "w", encoding="utf-8")
f.write(u"")
f.close()

log(u"=== PROBE_ALU_PARTS START ===")

for p in list(scriptengine.projects.all):
    try:
        p.close()
    except Exception:
        pass

proj = None
app = None
try:
    for junk in os.listdir(BUILD):
        if junk.startswith(u"probe_alu"):
            try:
                os.remove(os.path.join(BUILD, junk))
            except Exception:
                pass
    proj = scriptengine.projects.create(os.path.join(BUILD, u"probe_alu.project"))
    proj.add(name=u"Device", type=4096, id=u"0000 0001", version=u"3.5.17.30")
    app = proj.active_application
    log(u"proekt sozdan")
except Exception:
    log(u"oshibka sozdaniya:\n%s" % traceback.format_exc())


def walk(o, ind=0, depth=6, acc=None):
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


for k in range(1, 6):
    name = u"ALU_PART%d" % k
    path = os.path.join(SRC, u"%s.plcopenxml" % name)
    if not os.path.exists(path):
        log(u"  %s: net fajla" % name)
        continue
    try:
        app.import_xml(path)
        ok = name in walk(app, 0, 4, [])
        log(u"  %-12s import=OK   v dereve=%s" % (name, u"DA" if ok else u"NET (poteryan!)"))
    except Exception:
        log(u"  %-12s import=ISKLYuChENIE:\n%s" % (name, traceback.format_exc()))

# polnyj ALU dlya sravneniya
try:
    app.import_xml(os.path.join(SRC, u"FB_ALU_Z80.plcopenxml"))
    ok = u"FB_ALU_Z80" in walk(app, 0, 4, [])
    log(u"  %-12s import=OK   v dereve=%s" % (u"FB_ALU_Z80", u"DA" if ok else u"NET (poteryan!)"))
except Exception:
    log(u"  FB_ALU_Z80 import=ISKLYuChENIE:\n%s" % traceback.format_exc())

try:
    proj.close()
except Exception:
    pass

log(u"=== PROBE_ALU_PARTS END ===")
