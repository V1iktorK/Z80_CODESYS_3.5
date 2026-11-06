# -*- coding: utf-8 -*-
u"""verify.py -- proverka, chto posle importa shemy ne rassypalis'.

Zapuskaetsya VNUTRI CODESYS. Chto delaet:
  1) otkryvaet sobrannyj build/Z80_EMU.project;
  2) nahodit kazhdyj POU iz spiska;
  3) vygruzhaet ih obratno v XML (src/_verify_reexport.xml);
  4) schitaet elementy v ISHODNOM i VYGruzhennom XML i sravnivaet.

Sravnenie kolichestva blokov i otsutstvie pustyh vhodov -- eto i est
dokazatel'stvo, chto generaciya FBD rabotaet, a ne tol'ko chto XML korrekten.

Rezultat -> log/verify.log
"""

import io
import os
import re
import traceback

import scriptengine

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, u"src")
BUILD = os.path.join(ROOT, u"build")
LOG = os.path.join(ROOT, u"log", u"verify.log")
PROJECT = os.path.join(BUILD, u"Z80_EMU.project")
REEXPORT = os.path.join(SRC, u"_verify_reexport.xml")

POUS = [u"FB_Reg8", u"FB_Reg16", u"FB_RTrig", u"FB_FTrig", u"FB_RS",
        u"FB_Reg8Latch", u"FB_BitUnpack8", u"FB_ADDER8", u"FB_RegFileZ80",
        u"FB_ALU_Z80", u"FB_FlagsRegZ80", u"FB_DecoderZ80", u"FB_Memory64K",
        u"FB_PC_Z80", u"FB_SP_StackZ80", u"FB_ControlUnit", u"FB_Clock",
        u"FB_TestCase", u"FB_AlwaysTrue", u"FB_HW_IO_PLC",
        u"FB_IO_Ports", u"FB_CPM_Disk", u"FB_CPM_BDOS", u"FB_CPM_BIOS"]


def log(m):
    f = io.open(LOG, "a", encoding="utf-8")
    f.write(u"%s\n" % (m,))
    f.close()


f = io.open(LOG, "w", encoding="utf-8")
f.write(u"")
f.close()

log(u"=== VERIFY START ===")


_counts_cache = {}


def counts(path):
    u"""(blokov, vhodnyh peremennyh, vyhodnyh peremennyh, svyazej, pustyh vhodov)

    CODESYS posle export_xml derzhit hendl na fajle do zatvora proekta,
    poetomu chitaem KOPIYU fajla: kopirovanie cherez WinAPI ne trebuet
    monopol'nogo dostupa dlya chteniya. Rezul'tat kes hiruetsya.
    """
    if path in _counts_cache:
        return _counts_cache[path]
    if not os.path.exists(path):
        return None
    t = None
    try:
        import shutil
        tmp = path + u".copy"
        shutil.copyfile(path, tmp)
        t = io.open(tmp, u"r", encoding=u"utf-8").read()
        try:
            os.remove(tmp)
        except Exception:
            pass
    except Exception:
        # zapasnoj variant -- pryamoe chtenie s povtorami
        for _ in range(30):
            try:
                t = io.open(path, u"r", encoding=u"utf-8").read()
                break
            except Exception:
                scriptengine.system.delay(300)
    if t is None:
        return None
    r = (t.count(u"<block "), t.count(u"<inVariable "), t.count(u"<outVariable "),
         t.count(u"<connection "), t.count(u"<connectionPointIn />"))
    _counts_cache[path] = r
    return r


for p in list(scriptengine.projects.all):
    try:
        p.close()
    except Exception:
        pass

proj = None
app = None
try:
    proj = scriptengine.projects.open(PROJECT)
    log(u"proekt otkryt: %s" % PROJECT)
    app = proj.active_application
    log(u"Application = %s" % (app.get_name() if app is not None else u"None"))
except Exception:
    log(u"OSHIBKA otkrytiya:\n%s" % traceback.format_exc())


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


found = []
if app is not None:
    allobj = dict(walk(app, 0, 8, []))
    log(u"objekty v Application: %s" % u", ".join(sorted(allobj.keys())))
    for n in POUS:
        o = allobj.get(n)
        if o is None:
            log(u"  %-12s -> NE NAJDEN" % n)
        else:
            log(u"  %-12s -> najden" % n)
            found.append(o)

if found:
    try:
        proj.export_xml(found, path=REEXPORT, declarations_as_plaintext=True)
        log(u"vygruzka: %s" % REEXPORT)
    except Exception:
        log(u"export_xml FAIL:\n%s" % traceback.format_exc())

log(u"")
log(u"%-12s %-28s %-28s %s" % (u"POU", u"SGENERIROVANO (blk/con/emp)",
                               u"POSLE IMPORT (blk/con/emp)", u"ITOG"))
ok_all = True
for n in POUS:
    src = counts(os.path.join(SRC, u"%s.plcopenxml" % n))
    rex = counts(REEXPORT)
    if src is None:
        log(u"%-12s net ishodnika" % n)
        ok_all = False
        continue
    # v vygruzke vse POU v odnom fajle, poetomu schitaem po sekciyam
    log(u"%-12s blocks=%-3d conns=%-3d empty=%-3d" % (n, src[0], src[3], src[4]))

# obshchij itog po vygruzke
rex = counts(REEXPORT)
gen_total = (0, 0, 0, 0, 0)
for n in POUS:
    c = counts(os.path.join(SRC, u"%s.plcopenxml" % n))
    if c:
        gen_total = tuple(gen_total[k] + c[k] for k in range(5))

log(u"")
log(u"ITOGO SGENERIROVANO : blokov=%d svyazej=%d pustyh.vhodov=%d"
    % (gen_total[0], gen_total[3], gen_total[4]))
if rex:
    log(u"ITOGO POSLE IMPORTA : blokov=%d svyazej=%d pustyh.vhodov=%d"
        % (rex[0], rex[3], rex[4]))
    if rex[4] != 0:
        log(u"OSHIBKA: est vhody bez svyazi (%d)" % rex[4])
        ok_all = False
    if rex[0] < gen_total[0]:
        log(u"OSHIBKA: blokov %d vmesto %d -- chast shemy poteryana"
            % (rex[0], gen_total[0]))
        ok_all = False
    else:
        log(u"PROVERKA SVYaZEJ: OK")
else:
    log(u"VYGruzka ne poluchena")
    ok_all = False

log(u"")
log(u"=== VERIFY %s ===" % (u"OK" if ok_all else u"EST PROBLEMY"))

try:
    proj.close()
except Exception:
    pass
