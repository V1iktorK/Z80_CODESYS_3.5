# -*- coding: utf-8 -*-
u"""probe_bdos_iso2.py -- to zhe, no cherez KOPII fajlov i s pauzami.

Vyyasneno: CODESYS derzhit hendly na fajlah eksporta/importa do zatvora
proekta, poetomu povtornoe chtenie togo zhe puti daet IOError 32 i pustye
rezul taty. Zdes my kopiruem vhod v otdel nyy podkatalog i rabotaem tolko
s kopiyami, a mezhdu operatsiyami delaem pauzy.
"""

import io
import os
import re
import shutil
import traceback

import scriptengine

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(ROOT, u"src")
BUILD = os.path.join(ROOT, u"build")
WORK = os.path.join(BUILD, u"iso")
LOG = os.path.join(ROOT, u"log", u"probe_bdos_iso2.log")


def log(m):
    f = io.open(LOG, "a", encoding="utf-8")
    f.write(u"%s\n" % (m,))
    f.close()


f = io.open(LOG, "w", encoding="utf-8")
f.write(u"")
f.close()

log(u"=== PROBE_BDOS_ISO2 START ===")


def counts(path, pou_name=None):
    t = io.open(path, u"r", encoding=u"utf-8").read()
    if pou_name:
        i = t.find(u'<pou name="%s"' % pou_name)
        if i < 0:
            return (0, 0, 0, 0)
        j = t.find(u"</pou>", i)
        t = t[i:j]
    return (len(re.findall(u"<block ", t)),
            len(re.findall(u"<inVariable ", t)),
            len(re.findall(u"<outVariable ", t)),
            len(re.findall(u"<connection ", t)))


if not os.path.isdir(WORK):
    os.makedirs(WORK)

for p in list(scriptengine.projects.all):
    try:
        p.close()
    except Exception:
        pass
scriptengine.system.delay(1000)

# --- kopiruem vhod v rabochuyu papku -------------------------------------------
src_path = os.path.join(SRC, u"FB_CPM_BDOS.plcopenxml")
work_path = os.path.join(WORK, u"fb_bdos_in.plcopenxml")
try:
    shutil.copyfile(src_path, work_path)
    log(u"kopiya vhoda sdelana: %s" % work_path)
except Exception:
    log(u"KOPIROVANIE FAIL:\n%s" % traceback.format_exc())

g = counts(work_path)
log(u"V ISHODNIKE: blokov=%d invars=%d outvars=%d conns=%d" % g)

proj = None
app = None
try:
    for junk in os.listdir(BUILD):
        if junk.startswith(u"probe_iso"):
            try:
                os.remove(os.path.join(BUILD, junk))
            except Exception:
                pass
    proj = scriptengine.projects.create(os.path.join(BUILD, u"probe_iso.project"))
    proj.add(name=u"Device", type=4096, id=u"0000 0001", version=u"3.5.17.30")
    app = proj.active_application
    log(u"proekt sozdan")
except Exception:
    log(u"OSHIBKA sozdaniya:\n%s" % traceback.format_exc())

try:
    app.import_xml(work_path)
    log(u"import proshel bez isklyucheniya")
except Exception:
    log(u"IMPORT ISKLYuChENIE:\n%s" % traceback.format_exc())

scriptengine.system.delay(1000)


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
        out = os.path.join(WORK, u"fb_bdos_out.xml")
        proj.export_xml([found], path=out, declarations_as_plaintext=True)
        scriptengine.system.delay(1500)
        # chitaem KOPIYU -- original zanyat CODESYS-om
        out_copy = out + u".copy"
        shutil.copyfile(out, out_copy)
        c = counts(out_copy)
        log(u"POSLE IMPORT: blokov=%d invars=%d outvars=%d conns=%d" % c)
        if c[0] != g[0]:
            log(u"!!! POTERYa: %d blokov iz %d" % (c[0], g[0]))
        else:
            log(u"OK: vse bloki na meste")
    except Exception:
        log(u"export FAIL:\n%s" % traceback.format_exc())
else:
    log(u"FB_CPM_BDOS NE NAJDEN v dereve!")

try:
    proj.close()
except Exception:
    pass

log(u"=== PROBE_BDOS_ISO2 END ===")
