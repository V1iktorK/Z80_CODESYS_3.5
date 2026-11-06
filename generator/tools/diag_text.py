# -*- coding: utf-8 -*-
u"""C H T O  I M E N N O  lezhit v proekte: obyavleniya i tela vseh POU.

Pochemu eto nuzhno. Kompilyator soobshchaet "Obnaruzhen nedopustimyj simvol '-'"
BEZ nomera stroki i bez imeni POU. Poisk po nashim fajlam src/ nishchego ne
najdeno -- znachit nado smotret na to, chto REALNO poluchilos v proekte posle
importa: CODESYS mog Perepisat tekst po-svoemu.

ZAPUSK: generator\run_diag_text.cmd
Rezultat: log\diag_text.txt
"""
import os
import sys

import scriptengine

ROOT = os.environ.get(u"Z80_ROOT")
if not ROOT:
    ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROJ = os.path.join(ROOT, u"build", u"Z80_EMU.project")
if not os.path.isdir(os.path.join(ROOT, u"log")):
    os.makedirs(os.path.join(ROOT, u"log"))
OUT = os.path.join(ROOT, u"log", u"diag_text.txt")

LOG = []


def log(msg):
    LOG.append(u"%s" % msg)


def get_text(obj, attr):
    try:
        v = getattr(obj, attr)
    except Exception as exc:                                   # noqa: BLE001
        return u"<%s: %s>" % (attr, exc)
    if v is None:
        return u"<None>"
    if isinstance(v, (str, unicode)):                          # noqa: F821
        return v
    t = getattr(v, u"text", None)
    if t is not None:
        return t
    try:
        return u"\n".join([u"%s" % x for x in v])
    except Exception:                                          # noqa: BLE001
        return u"%s" % v


def main():
    log(u"=== DIAG TEXT ===")
    proj = scriptengine.projects.open(PROJ)
    app = proj.active_application

    kids = app.get_children()
    named = {}
    for ch in kids:
        nm = u"?"
        for attr in (u"get_name", u"name"):
            try:
                v = getattr(ch, attr)
                nm = v() if callable(v) else v
                if nm:
                    break
            except Exception:                                  # noqa: BLE001
                pass
        named[u"%s" % nm] = ch

    #  Chto imenno ishchem: odinokie '-' vne kommentariev, a tak zhe lyubye
    #  stroki s '--' vne kommentariev.
    import re
    com = re.compile(u"\\(\\*.*?\\*\\)", re.S)

    for nm in (u"PRG_InitMemory", u"PLC_PRG", u"TEST_Z80", u"FB_ADDER8",
               u"FB_ALU_Z80", u"FB_Memory64K"):
        o = named.get(nm)
        if o is None:
            log(u"")
            log(u"### %s -- NE NAJDEN" % nm)
            continue
        d = get_text(o, u"textual_declaration")
        b = get_text(o, u"textual_implementation")
        d = (u"%s" % d).replace(u"\r\n", u"\n")
        b = (u"%s" % b).replace(u"\r\n", u"\n")
        log(u"")
        log(u"### %s" % nm)
        log(u"--- OBYaVLENIE (%d strok) ---" % (d.count(u"\n") + 1))
        for n, l in enumerate(d.split(u"\n"), 1):
            mark = u""
            if u"-" in com.sub(u" ", l):
                mark = u"   <<< TIRE VNE KOMMENTARIYa"
            log(u"%4d| %s%s" % (n, l[:120], mark))
        log(u"--- TELO (%d strok) ---" % (b.count(u"\n") + 1))
        for n, l in enumerate(b.split(u"\n"), 1):
            mark = u""
            if u"-" in com.sub(u" ", l):
                mark = u"   <<< TIRE VNE KOMMENTARIYa"
            log(u"%4d| %s%s" % (n, l[:120], mark))

    proj.close()
    log(u"=== KONEC ===")


try:
    main()
except Exception, exc:                                          # noqa: E999
    log(u"AVARIYA: %s" % exc)
    import traceback
    log(traceback.format_exc())

f = open(OUT, u"w")
f.write(u"\n".join(LOG).encode(u"utf-8"))
f.close()
sys.stdout.write(u"diag_text: %d strok -> %s\n" % (len(LOG), OUT))
