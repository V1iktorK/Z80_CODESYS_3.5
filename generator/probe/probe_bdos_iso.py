# -*- coding: utf-8 -*-
u"""probe_bdos_iso.py -- importiruet FB_CPM_BDOS v chistyy proekt i schitaet.

Zapuskaetsya VNUTRI CODESYS. Nuzhno ponyat, teryaet li import chast blokov
imenno u etogo POU (v proekte 26 blokov vmesto 40 v ishodnike).
"""

import io
import os
import re
import traceback

import scriptengine

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(ROOT, u"src")
BUILD = os.path.join(ROOT, u"build")
LOG = os.path.join(ROOT, u"log", u"probe_bdos_iso.log")


def log(m):
    f = io.open(LOG, "a", encoding="utf-8")
    f.write(u"%s\n" % (m,))
    f.close()


f = io.open(LOG, "w", encoding="utf-8")
f.write(u"")
f.close()

log(u"=== PROBE_BDOS_ISO START ===")


def counts(path, pou_name=None):
    t = io.open(path, u"r", encoding=u"utf-8").read()
    if pou_name:
        i = t.find(u'<pou name="%s"' % pou_name)
        if i < 0:
            return None
        j = t.find(u"</pou>", i)
        t = t[i:j]
    return (len(re.findall(u"<block ", t)),
            len(re.findall(u"<inVariable ", t)),
            len(re.findall(u"<outVariable ", t)),
            len(re.findall(u"<connection ", t)))


for p in list(scriptengine.projects.all):
    try:
        p.close()
    except Exception:
        pass

proj = None
app = None
try:
    for junk in os.listdir(BUILD):
        if junk.startswith(u"probe_bdos"):
            try:
                os.remove(os.path.join(BUILD, junk))
            except Exception:
                pass
    proj = scriptengine.projects.create(os.path.join(BUILD, u"probe_bdos.project"))
    proj.add(name=u"Device", type=4096, id=u"0000 0001", version=u"3.5.17.30")
    app = proj.active_application
    log(u"proekt sozdan")
except Exception:
    log(u"OSHIBKA sozdaniya:\n%s" % traceback.format_exc())

src_path = os.path.join(SRC, u"FB_CPM_BDOS.plcopenxml")
log(u"V ISHODNIKE: blokov=%d invars=%d outvars=%d conns=%d" % counts(src_path))

try:
    app.import_xml(src_path)
    log(u"import proshel bez isklyucheniya")
except Exception:
    log(u"IMPORT ISKLYuChENIE:\n%s" % traceback.format_exc())


def walk(o, ind=0, depth=4, acc=None):
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


found = None
for n, o in walk(app, 0, 4, []):
    log(u"  v dereve: %s" % n)
    if n == u"FB_CPM_BDOS":
        found = o

if found is not None:
    try:
        out = os.path.join(SRC, u"_bdos_iso.xml")
        proj.export_xml([found], path=out, declarations_as_plaintext=True)
        scriptengine.system.delay(500)
        c = counts(out)
        log(u"POSLE IMPORT: blokov=%d invars=%d outvars=%d conns=%d" % c)
        if c[0] != counts(src_path)[0]:
            log(u"!!! POTERYa: %d blokov iz %d" % (c[0], counts(src_path)[0]))
        else:
            log(u"OK: vse bloki na meste")
    except Exception:
        log(u"export FAIL:\n%s" % traceback.format_exc())

try:
    proj.close()
except Exception:
    pass

log(u"=== PROBE_BDOS_ISO END ===")
