# -*- coding: utf-8 -*-
u"""probe_many_nets.py -- skolko setey POU perenositsya?

Zapuskaetsya VNUTRI CODESYS. Sozdaem tri POU: s 5, 10 i 20 setyami
(kazhdaya set -- odin AND i odna vyhodnaya peremennaya, vse vhody raznye).
Schitaem, skolko setey doehalo.

Nuzhno ponyat, est li u CODESYS predel po chislu setey v odnom FBD-POU
ili delo v chem-to drugom.
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
WORK = os.path.join(BUILD, u"nets")
LOG = os.path.join(ROOT, u"log", u"probe_many_nets.log")


def log(m):
    f = io.open(LOG, "a", encoding="utf-8")
    f.write(u"%s\n" % (m,))
    f.close()


f = io.open(LOG, "w", encoding="utf-8")
f.write(u"")
f.close()

log(u"=== PROBE_MANY_NETS START ===")


def blocks_of(path, pou):
    t = io.open(path, u"r", encoding=u"utf-8").read()
    i = t.find(u'<pou name="%s"' % pou)
    if i < 0:
        return -1
    j = t.find(u"</pou>", i)
    return len(re.findall(u"<block ", t[i:j]))


if not os.path.isdir(WORK):
    os.makedirs(WORK)

for p in list(scriptengine.projects.all):
    try:
        p.close()
    except Exception:
        pass
scriptengine.system.delay(800)

proj = None
app = None
try:
    for junk in os.listdir(BUILD):
        if junk.startswith(u"probe_nets"):
            try:
                os.remove(os.path.join(BUILD, junk))
            except Exception:
                pass
    proj = scriptengine.projects.create(os.path.join(BUILD, u"probe_nets.project"))
    proj.add(name=u"Device", type=4096, id=u"0000 0001", version=u"3.5.17.30")
    app = proj.active_application
    log(u"proekt sozdan")
except Exception:
    log(u"OSHIBKA:\n%s" % traceback.format_exc())

for name in (u"P5", u"P10", u"P20"):
    src = os.path.join(SRC, u"%s.plcopenxml" % name)
    if not os.path.exists(src):
        log(u"  %s: NET FAJLA" % name)
        continue
    dst = os.path.join(WORK, u"%s.plcopenxml" % name)
    try:
        shutil.copyfile(src, dst)
    except Exception:
        log(u"  %s: kopiya FAIL" % name)
        continue
    try:
        app.import_xml(dst)
        log(u"  %s: import OK" % name)
    except Exception:
        log(u"  %s: import ISKLYuChENIE %s" % (name, traceback.format_exc().splitlines()[-1]))

scriptengine.system.delay(1000)


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


names = set(walk(app, 0, 4, []))
log(u"v dereve: %s" % u", ".join(sorted(names)))

found = []
for name in (u"P5", u"P10", u"P20"):
    if name in names:
        for n, o in [(n, o) for n, o in []]:
            pass
for n, o in []:
    pass


def walk2(o, ind=0, depth=4, acc=None):
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
        walk2(k, ind + 1, depth, acc)
    return acc


allobj = dict(walk2(app, 0, 4, []))
for name in (u"P5", u"P10", u"P20"):
    if name not in allobj:
        log(u"  %s: NE NAJDEN v dereve" % name)
        continue
    out = os.path.join(WORK, u"%s_out.xml" % name)
    try:
        proj.export_xml([allobj[name]], path=out, declarations_as_plaintext=True)
        scriptengine.system.delay(800)
        cp = out + u".copy"
        shutil.copyfile(out, cp)
        log(u"  %s: v ishodnike blokov, posle importa=%d" % (name, blocks_of(cp, name)))
    except Exception:
        log(u"  %s: export FAIL %s" % (name, traceback.format_exc().splitlines()[-1]))

try:
    proj.close()
except Exception:
    pass

log(u"=== PROBE_MANY_NETS END ===")
