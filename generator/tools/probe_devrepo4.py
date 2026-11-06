# -*- coding: utf-8 -*-
u"""C H T O  V N U T R I  device_info -- i est li moduli vvoda/vyvoda.

Predydushchie popytki pokazali, chto u zapisi repozitoriya est
device_id (type/Id/Version) i device_info, no device_info.name ne chitaetsya
napryamuyu. Zdes vyvodim dir() samogo device_info i ego znacheniya dlya
pervyh zapisej, a takzhe schitaem raspredelenie po TIPAM.

ZAPUSK: run_probe_fb.ps1 -Fbs none -Script tools\probe_devrepo4.py
"""
import io
import os
import sys

import scriptengine

ROOT = os.environ.get(u"Z80_ROOT")
if not ROOT:
    ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOG = os.path.join(ROOT, u"log")
OUT = os.path.join(LOG, u"devrepo4.txt")

LINES = []


def log(m):
    LINES.append(u"%s" % (m,))


def main():
    log(u"=== DEVICE INFO ===")
    repo = scriptengine.device_repository
    allv = list(repo.get_all_devices())
    log(u"zapisej: %d" % len(allv))

    #  1. chto vnutri device_info
    d0 = allv[0]
    info = d0.device_info
    log(u"")
    log(u"--- dir(device_info) ---")
    for nm in sorted(dir(info)):
        if nm.startswith(u"_"):
            continue
        try:
            v = getattr(info, nm)
        except Exception as exc:                               # noqa: BLE001
            log(u"  %-24s <%s>" % (nm, (u"%s" % exc)[:60]))
            continue
        log(u"  %-24s = %s" % (nm, (u"%s" % v)[:80]))

    #  2. raspredelenie po tipam + primery imen
    log(u"")
    log(u"--- tipy i primery ---")
    by_type = {}
    for d in allv:
        try:
            di = d.device_id
            tp = di.type
        except Exception:                                      # noqa: BLE001
            continue
        nm = u""
        try:
            info = d.device_info
            for attr in (u"device_name", u"name", u"Name", u"description"):
                try:
                    v = getattr(info, attr)
                    if v:
                        nm = u"%s" % v
                        break
                except Exception:                              # noqa: BLE001
                    continue
            if not nm:
                nm = (u"%s" % info)[:60]
        except Exception:                                      # noqa: BLE001
            pass
        by_type.setdefault(tp, []).append(nm)

    for tp in sorted(by_type):
        names = by_type[tp]
        log(u"  type=%-6s vsego %-4d napr.: %s"
            % (tp, len(names), u" | ".join([n[:34] for n in names[:3]])))

    log(u"=== KONEC ===")


try:
    main()
except Exception, exc:                                          # noqa: E999
    log(u"AVARIYA: %s" % exc)
    import traceback
    log(traceback.format_exc())

if not os.path.isdir(LOG):
    os.makedirs(LOG)
f = open(OUT, u"w")
f.write(u"\n".join(LINES).encode(u"utf-8"))
f.close()
sys.stdout.write(u"devrepo4: %d strok\n" % len(LINES))
