# -*- coding: utf-8 -*-
u"""P O P Y T K A  2: dobavit modul vvoda/vyvoda POD ustrojstvo.

V pervoj popytke ya vzyal rezul tat proj.add() i poluchil None -- potomu i
"dev.add" ne srabotal. Ustrojstvo nuzhno brat iz dereva cherez get_children().

Zdes probuem:
  * dostat uzly dereva i najti sam PLC;
  * posmotret ego razemy (connectors) -- chto v nego voobshche mozhno vstavit;
  * dobavit Digital Input / Digital Output dochernimi k PLC;
  * sobrat proekt s AT %IX0.0 i posmotret, ostalsya li C373.

ZAPUSK: generator\run_diag.ps1 -Script "probe_add_io2.py" -OutName "probe_add_io2"
"""
import os
import sys

import scriptengine

ROOT = os.environ.get(u"Z80_ROOT")
if not ROOT:
    ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUILD = os.path.join(ROOT, u"build")
LOG = os.path.join(ROOT, u"log")
if not os.path.isdir(LOG):
    os.makedirs(LOG)
OUT = os.path.join(LOG, u"probe_add_io2.txt")

PT = scriptengine.PouType
DEV_TYPE = 4096
DEV_ID = u"0000 0001"
DEV_VER = u"3.5.17.30"

L = []


def log(m):
    L.append(u"%s" % (m,))


def name_of(o):
    for a in (u"get_name", u"name"):
        try:
            v = getattr(o, a)
            v = v() if callable(v) else v
            if v:
                return u"%s" % v
        except Exception:                                      # noqa: BLE001
            pass
    return u"?"


def find(root, want, depth=0):
    if depth > 8:
        return None
    try:
        kids = root.get_children()
    except Exception:                                          # noqa: BLE001
        return None
    for ch in kids:
        if name_of(ch) == want:
            return ch
        got = find(ch, want, depth + 1)
        if got is not None:
            return got
    return None


def main():
    log(u"=== PROBE ADD IO 2 ===")
    path = os.path.join(BUILD, u"probe_io2.project")
    if os.path.exists(path):
        try:
            os.remove(path)
        except Exception:                                      # noqa: BLE001
            pass
    proj = scriptengine.projects.create(path)
    proj.add(name=u"Device", type=DEV_TYPE, id=DEV_ID, version=DEV_VER)
    app = proj.active_application

    dev = find(proj, u"Device")
    log(u"uzel PLC: %s" % (dev if dev is not None else u"NE NAJDEN"))
    if dev is None:
        return

    log(u"")
    log(u"--- razemy PLC ---")
    try:
        cs = dev.connectors
        log(u"  svojstva: %s" % u", ".join([x for x in dir(cs) if not x.startswith(u"_")]))
        for a in (u"get_connectors", u"connectors", u"items"):
            try:
                v = getattr(cs, a)
                v = v() if callable(v) else v
                log(u"  %-16s = %s" % (a, v))
            except Exception:                                  # noqa: BLE001
                pass
        try:
            for c in cs:
                log(u"    razem: %s" % c)
        except Exception:                                      # noqa: BLE001
            pass
    except Exception as exc:                                   # noqa: BLE001
        log(u"  connectors: %s" % exc)

    log(u"")
    log(u"--- popytki dobavit pod PLC ---")
    cands = [(176, u"0000 0010", u"3.5.11.0", u"Digital Input"),
             (176, u"0000 0011", u"3.5.11.0", u"Digital Output")]
    added = 0
    for typ, cid, cver, cname in cands:
        try:
            dev.add(name=cname, type=typ, id=cid, version=cver)
            log(u"  dev.add(%s) -> OK" % cname)
            added += 1
        except Exception as exc:                               # noqa: BLE001
            log(u"  dev.add(%s) -> OTKAZ: %s" % (cname, exc))
        try:
            dev.insert(name=cname, type=typ, id=cid, version=cver)
            log(u"  dev.insert(%s) -> OK" % cname)
            added += 1
        except Exception as exc:                               # noqa: BLE001
            log(u"  dev.insert(%s) -> OTKAZ: %s" % (cname, exc))

    log(u"")
    log(u"--- sostav dereva posle popytok ---")
    def walk(o, d=0):
        try:
            kids = o.get_children()
        except Exception:                                      # noqa: BLE001
            return
        for ch in kids:
            log(u"  %s%s" % (u"    " * d, name_of(ch)))
            walk(ch, d + 1)
    walk(proj)

    #  kompilyaciya s adresami
    log(u"")
    log(u"--- kompilyaciya s AT %IX0.0 ---")
    try:
        app.create_pou(u"P_IO", PT.Program, scriptengine.ImplementationLanguages.st,
                       None, None, None)
        p = None
        for cand in app.find(u"P_IO"):
            if hasattr(cand, u"textual_declaration"):
                p = cand
                break
        p.textual_declaration.replace(
            u"PROGRAM P_IO\nVAR\n    DI_0 AT %IX0.0 : BOOL;\n"
            u"    DO_0 AT %QX0.0 : BOOL;\n    AI_0 AT %IW0 : INT;\nEND_VAR")
        p.textual_implementation.replace(u"DO_0 := DI_0;\n")
        tc = app.create_task_configuration()
        task = tc.create_task(u"MainTask")
        task.pous.add(u"P_IO", u"P_IO")
    except Exception as exc:                                   # noqa: BLE001
        log(u"  P_IO: %s" % exc)
    try:
        app.build()
        app.generate_code()
    except Exception as exc:                                   # noqa: BLE001
        log(u"  sborka: %s" % exc)
    proj.save()
    proj.close()
    log(u"=== KONEC, dobavleno moduley: %d ===" % added)


try:
    main()
except Exception, exc:                                          # noqa: E999
    log(u"AVARIYA: %s" % exc)
    import traceback
    log(traceback.format_exc())

f = open(OUT, u"w")
f.write(u"\n".join(L).encode(u"utf-8"))
f.close()
sys.stdout.write(u"probe_add_io2: %d strok\n" % len(L))
