# -*- coding: utf-8 -*-
u"""D I A G N O S T I K A: pochemu kompilyator ne vidit programmy.

Otkryvaem uzhe sobrannyj proekt i smotrim:
  1) chto realno lezhit v prilozhenii (imya, klass objekta);
  2) kak vyglyadit tekstovoe obyavlenie kazhdogo POU -- imenno ot syuda
     CODESYS beret vid POU (PROGRAM / FUNCTION_BLOCK);
  3) chto zapisano v Task Configuration (spisok zapuskaemyh programm).

ZAPUSK:
    CODESYS.exe --profile="CODESYS V3.5 SP17 Patch 3" ^
        --runscript="generator\tools\diag_progs.py" --noUI
"""
import os
import sys

import scriptengine

ROOT = os.environ.get(u"Z80_ROOT")
if not ROOT:
    ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if not os.path.exists(os.path.join(ROOT, u"src")):
        ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if not os.path.exists(os.path.join(ROOT, u"src")):
            ROOT = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.join(ROOT, u"build", u"Z80_EMU.project")
if not os.path.isdir(os.path.join(ROOT, u"log")):
    os.makedirs(os.path.join(ROOT, u"log"))
OUT = os.path.join(ROOT, u"log", u"diag_progs.txt")

LOG = []


def log(msg):
    LOG.append(u"%s" % msg)


def text_of(obj, attr):
    try:
        v = getattr(obj, attr)
    except Exception as exc:                                   # noqa: BLE001
        return u"<%s: %s>" % (attr, exc)
    if v is None:
        return u"<None>"
    return getattr(v, u"text", v)


def main():
    log(u"=== DIAG PROGS ===")
    log(u"proekt: %s" % PROJ)
    if not os.path.exists(PROJ):
        log(u"NET FAJLA PROEKTA")
        return
    proj = scriptengine.projects.open(PROJ)
    log(u"otkryt: %s" % proj)
    app = proj.active_application
    log(u"prilozhenie: %s" % app)

    log(u"")
    log(u"--- [1] sostav prilozheniya ---")
    for ch in app.get_children():
        try:
            cls = ch.__class__.__name__
        except Exception:                                      # noqa: BLE001
            cls = u"?"
        log(u"  %-24s | %s" % (getattr(ch, u"name", u"?"), cls))

    log(u"")
    log(u"--- [2] tekstovye obyavleniya POU (vid POU) ---")
    names = [u"PLC_PRG", u"PRG_InitMemory", u"TEST_Z80",
             u"PRG_CPM_Boot", u"FB_Reg8", u"FB_Memory64K"]
    for nm in names:
        try:
            o = proj.find(nm)
        except Exception as exc:                               # noqa: BLE001
            log(u"  %-18s POISK OSHIBKA: %s" % (nm, exc))
            continue
        if o is None:
            log(u"  %-18s NE NAJDEN" % nm)
            continue
        d = text_of(o, u"textual_declaration")
        d = (u"%s" % d).replace(u"\r\n", u"\n").strip()
        head = d.split(u"\n")[0] if d else u""
        log(u"  %-18s | 1-ya stroka: %s" % (nm, head[:80]))
        log(u"  %-18s | vsego strok: %d" % (u"", d.count(u"\n") + 1))

    log(u"")
    log(u"--- [3] Task Configuration ---")
    tc = None
    for ch in app.get_children():
        n = u"%s" % getattr(ch, u"name", u"")
        if u"Task" in n:
            tc = ch
            break
    if tc is None:
        log(u"  KONFIGURACIYA ZADACH NE NAJDENA")
    else:
        log(u"  najdena: %s" % getattr(tc, u"name", u"?"))
        for t in tc.get_children():
            log(u"    zadacha: %s" % getattr(t, u"name", u"?"))
            try:
                log(u"      priority=%s interval=%s" % (t.priority, t.interval))
            except Exception:                                  # noqa: BLE001
                pass
            try:
                pou = t.pous
                log(u"      tip pous: %s" % type(pou))
                log(u"      len(pous) = %s" % len(pou))
                for k in pou:
                    log(u"        zapis: %r" % (k,))
            except Exception as exc:                           # noqa: BLE001
                log(u"      pous OSHIBKA: %s" % exc)

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
sys.stdout.write(u"diag_progs: %d strok -> %s\n" % (len(LOG), OUT))
