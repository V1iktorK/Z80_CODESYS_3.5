# -*- coding: utf-8 -*-
u"""D I A G N O S T I K A  2: kakie svojstva est u obektov proekta.

Pervaya popytka pokazala, chto u dochernih obektov net svojstva .name --
znachit nado smotret, chto est. Vyvodim spisok svojstv i ih znacheniya
dlya pervyh neskolkih obektov prilozheniya, dlya neskolkih POU i dlya
konfiguracii zadach. Nichego ne menyAem -- tolko chitaem.

ZAPUSK: generator\run_diag_props.cmd
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
OUT = os.path.join(ROOT, u"log", u"diag_props.txt")

LOG = []


def log(msg):
    LOG.append(u"%s" % msg)


SKIP = (u"__", u"get_children", u"parent", u"project", u"image", u"help",
        u"guid", u"objid", u"handle")


def dump(obj, title, maxprops=40):
    log(u"")
    log(u"### %s" % title)
    log(u"    type: %s" % type(obj))
    try:
        props = sorted(dir(obj))
    except Exception as exc:                                   # noqa: BLE001
        log(u"    dir() OSHIBKA: %s" % exc)
        return
    shown = 0
    for p in props:
        if p.startswith(SKIP):
            continue
        try:
            v = getattr(obj, p)
        except Exception as exc:                               # noqa: BLE001
            log(u"    %-28s = <%s>" % (p, u"%s" % exc)[:90])
            continue
        if callable(v):
            log(u"    %-28s = <metod>" % p)
            continue
        s = u"%s" % v
        s = s.replace(u"\n", u"\\n").replace(u"\r", u"")
        log(u"    %-28s = %s" % (p, s[:110]))
        shown += 1
        if shown > maxprops:
            log(u"    ... (spisok obrezan)")
            break


def main():
    log(u"=== DIAG PROPS ===")
    log(u"proekt: %s" % PROJ)
    if not os.path.exists(PROJ):
        log(u"NET FAJLA PROEKTA")
        return
    proj = scriptengine.projects.open(PROJ)
    app = proj.active_application

    kids = app.get_children()
    log(u"dochernih obektov: %d" % len(kids))
    for i in (0, 1, 2):
        if i < len(kids):
            dump(kids[i], u"dochernij obekt #%d" % i)

    log(u"")
    log(u"=== imena vseh dochernih (cherez raznye svojstva) ===")
    for i, ch in enumerate(kids):
        nm = u"?"
        for attr in (u"name", u"Name", u"get_name", u"pou_name"):
            try:
                v = getattr(ch, attr)
                nm = v() if callable(v) else v
                if nm:
                    break
            except Exception:                                  # noqa: BLE001
                pass
        log(u"  %2d) %s" % (i, nm))

    for nm in (u"PRG_InitMemory", u"PLC_PRG", u"FB_Reg8"):
        try:
            o = proj.find(nm)
        except Exception as exc:                               # noqa: BLE001
            log(u"poisk %s: %s" % (nm, exc))
            continue
        if o is None:
            log(u"%s NE NAJDEN" % nm)
            continue
        dump(o, u"POU %s" % nm)

    #  konfiguratsiya zadach -- ishchem po tipu, a ne po imeni
    log(u"")
    log(u"=== poisk konfiguracii zadach ===")
    for i, ch in enumerate(kids):
        try:
            tn = u"%s" % ch.type
        except Exception:                                      # noqa: BLE001
            tn = u"?"
        if u"ask" in tn or u"Task" in tn:
            log(u"  pokhozh #%d: type=%s" % (i, tn))
    dump(app, u"prilozhenie (svojstva)", maxprops=60)

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
sys.stdout.write(u"diag_props: %d strok -> %s\n" % (len(LOG), OUT))
