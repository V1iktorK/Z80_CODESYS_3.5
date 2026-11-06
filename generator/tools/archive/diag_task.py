# -*- coding: utf-8 -*-
u"""D I A G N O S T I K A  3: spisok zapuskaemyh POU i ih vid.

Chto nuzhno ponyat:
  1) chto realno lezhit v Task Configuration posle nashej zapisi
     task.pous[imya] = imya;
  2) kakogo vida POU -- programma ili funk. blok. Svojstva .name u obektov
     net (proverено), poetomu opredelyaem vid po otvetu API:
     u programmy uspeшно chitaetsya textual_declaration i textual_implementation,
     i oni ne pusty.
  3) chto vyglyadit tekstovoe obyavlenie -- ot syuda CODESYS i beret vid POU.

ZAPUSK: generator\run_diag_task.cmd
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
OUT = os.path.join(ROOT, u"log", u"diag_task.txt")

LOG = []


def log(msg):
    LOG.append(u"%s" % msg)


NAMES = [u"PLC_PRG", u"PRG_InitMemory", u"PRG_LoadTestProgram", u"PRG_CPM_Boot",
         u"PRG_CPM_BDOS", u"TEST_Z80", u"TEST_Z80_CPM", u"FB_Reg8",
         u"FB_Memory64K"]


def get_text(obj, attr):
    u"""Dostat tekst svojstva, razobravshis s ego formoj."""
    try:
        v = getattr(obj, attr)
    except Exception as exc:                                   # noqa: BLE001
        return u"<%s>" % exc
    if v is None:
        return u"<None>"
    if isinstance(v, (str, unicode)):                          # noqa: F821
        return v
    t = getattr(v, u"text", None)
    if t is not None:
        return t
    try:
        return u" | ".join([u"%s" % x for x in v])
    except Exception:                                          # noqa: BLE001
        return u"%s" % v


def main():
    log(u"=== DIAG TASK ===")
    proj = scriptengine.projects.open(PROJ)
    app = proj.active_application

    #  O B H O D  L O V U Sh K I: u proekta est svojstvo 'find' (spisok),
    #  poetomu proj.find(imya) rabotaet kak poisk obekta, a ne kak filt r -- no
    #  u dochernih obektov .name net, i nado iskat po drugomu.
    kids = app.get_children()
    log(u"dochernih: %d" % len(kids))

    #  imena cherez .get_name(), a ne .name
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
    log(u"imen polucheno: %d" % len(named))

    log(u"")
    log(u"--- [1] vid POU i ego obyavlenie ---")
    for nm in NAMES:
        o = named.get(nm)
        if o is None:
            log(u"  %-20s NE NAJDEN" % nm)
            continue
        d = get_text(o, u"textual_declaration")
        i = get_text(o, u"textual_implementation")
        d1 = (u"%s" % d).replace(u"\r\n", u"\n").strip()
        i1 = (u"%s" % i).replace(u"\r\n", u"\n").strip()
        log(u"  %-20s | obyavl.: %-46s | telo: %s"
            % (nm, d1.split(u"\n")[0][:46], i1.split(u"\n")[0][:40]))
        d = i = d1 = i1 = None

    log(u"")
    log(u"--- [2] Task Configuration ---")
    tc = named.get(u"TaskConfiguration")
    if tc is None:
        log(u"  ne najdena")
    else:
        tk = tc.get_children()
        log(u"  dochernih u konfiguracii: %d" % len(tk))
        for t in tk:
            nm = u"?"
            for attr in (u"get_name", u"name"):
                try:
                    v = getattr(t, attr)
                    nm = v() if callable(v) else v
                    if nm:
                        break
                except Exception:                              # noqa: BLE001
                    pass
            log(u"  zadacha: %s" % nm)
            try:
                pou = t.pous
                log(u"    type(pous) = %s" % type(pou))
                try:
                    log(u"    len(pous) = %d" % len(pou))
                except Exception:                              # noqa: BLE001
                    pass
                for k in pou:
                    log(u"      element: %r  (type %s)" % (k, type(k)))
            except Exception as exc:                           # noqa: BLE001
                log(u"    pous OSHIBKA: %s" % exc)

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
sys.stdout.write(u"diag_task: %d strok -> %s\n" % (len(LOG), OUT))
