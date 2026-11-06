# -*- coding: utf-8 -*-
u"""probe_mem.py -- kompiliruet TOLKO FB_Memory64K.

Zapuskaetsya VNUTRI CODESYS. Proveryaem gipotezu: padenie kompilyatora
vyzyvayut elementy MEM_READ / MEM_WRITE (oni ne yavlyayutsya standartnymi
operatorami IEC 61131-3 i, veroyatno, ne ponimayutsya kompilyatorom).
"""

import io
import os
import traceback

import scriptengine

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(ROOT, u"src")
BUILD = os.path.join(ROOT, u"build")
LOG = os.path.join(ROOT, u"log", u"probe_mem.log")


def log(m):
    f = io.open(LOG, "a", encoding="utf-8")
    f.write(u"%s\n" % (m,))
    f.close()


f = io.open(LOG, "w", encoding="utf-8")
f.write(u"")
f.close()

log(u"=== PROBE_MEM START ===")

for p in list(scriptengine.projects.all):
    try:
        p.close()
    except Exception:
        pass

proj = None
app = None
try:
    for junk in os.listdir(BUILD):
        if junk.startswith(u"probe_mem"):
            try:
                os.remove(os.path.join(BUILD, junk))
            except Exception:
                pass
    proj = scriptengine.projects.create(os.path.join(BUILD, u"probe_mem.project"))
    proj.add(name=u"Device", type=4096, id=u"0000 0001", version=u"3.5.17.30")
    app = proj.active_application
    log(u"proekt sozdan")
except Exception:
    log(u"OSHIBKA sozdaniya:\n%s" % traceback.format_exc())

# GVL s massivom pamyati
try:
    gp = os.path.join(SRC, u"GVL_Memory.gvl")
    t = io.open(gp, u"r", encoding=u"utf-8").read()
    g = app.create_gvl(u"GVL_Memory")
    g.textual_declaration.replace(t)
    log(u"GVL_Memory sozdana")
except Exception:
    log(u"GVL FAIL:\n%s" % traceback.format_exc())

# tolko pamyat'
try:
    app.import_xml(os.path.join(SRC, u"FB_Memory64K.plcopenxml"))
    log(u"FB_Memory64K importirovan")
except Exception:
    log(u"IMPORT FAIL:\n%s" % traceback.format_exc())

# POU, kotoryy prosto vyzyvaet pamyat' -- chtoby kompilyator realno ee obrabotal
try:
    p2 = app.create_pou(u"PRG_MEM_TEST", scriptengine.PouType.Program,
                        scriptengine.ImplementationLanguages.st, None, None, None)
    p2.textual_declaration.replace(
        u"PROGRAM PRG_MEM_TEST\nVAR\n\tm : FB_Memory64K;\nEND_VAR")
    p2.textual_implementation.replace(
        u"m(PC := 0, Addr := 0, Rd := FALSE, Wr := FALSE, D_Bus := 0,\n"
        u"  SP_Addr := 0, SP_Rd := FALSE, SP_Wr := FALSE, SP_Data := 0);")
    log(u"PRG_MEM_TEST sozdan (vyzyvaet FB_Memory64K)")
except Exception:
    log(u"POU FAIL:\n%s" % traceback.format_exc())

log(u"--- build() ---")
try:
    app.build()
    log(u">>> build() bez isklyucheniya")
except Exception:
    log(u">>> build() ISKLYuChENIE:\n%s" % traceback.format_exc())

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
    proj.save()
except Exception:
    pass

log(u"=== PROBE_MEM END ===")
