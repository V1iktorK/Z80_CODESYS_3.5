# -*- coding: utf-8 -*-
u"""M O Zh N O  L I  D O B A V I T  modul vvoda/vyvoda v derevo ustrojstv.

Z A Ch E M. Ostayutsya 20 preduprezhdenij
    C373: Adres %IX0.0 ne zadan ni v odnom ustrojstve.
Prichina -- v dereve est tolko SoftPLC, a modulya net. V repozitorii najdeny
    Digital Input  (type=176, Id='0000 0010', Version='3.5.11.0')
    Digital Output (type=176, Id='0000 0011', Version='3.5.11.0')
Nado ponyat, mozhno li ih dobavit dochernimi k PLC i ischeznet li C373.

Ch T O  D E L A E M (v otdelnom vremennom proekte, nash ne tronem):
  1) sozdaem proekt s SoftPLC;
  2) vyvodim, kakie razemy (connectors) est u ustrojstva -- chtoby ponyat,
     chto voobshche mozhno v nego vstavit;
  3) probuem dobavit Digital Input / Digital Output raznymi sposobami;
  4) esli poluchilos -- obyavlyaem peremennuyu s AT %IX0.0, kompiliruem
     i smotrim, ostalsya li C373.

ZAPUSK: generator\run_diag.ps1 -Script "probe_add_io.py" -OutName "probe_add_io"
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
OUT = os.path.join(LOG, u"probe_add_io.txt")

PT = scriptengine.PouType
DT = scriptengine.DutType
DEV_TYPE = 4096
DEV_ID = u"0000 0001"
DEV_VER = u"3.5.17.30"

L = []


def log(m):
    L.append(u"%s" % (m,))


def try_label(fn, label):
    try:
        r = fn()
        log(u"  %-38s -> OK %s" % (label, u"" if r is None else u"%s" % r))
        return True
    except Exception as exc:                                   # noqa: BLE001
        log(u"  %-38s -> OTKAZ: %s" % (label, exc))
        return False


def main():
    log(u"=== PROBE ADD IO ===")
    path = os.path.join(BUILD, u"probe_io.project")
    for junk in (path,):
        if os.path.exists(junk):
            try:
                os.remove(junk)
            except Exception:                                  # noqa: BLE001
                pass
    proj = scriptengine.projects.create(path)
    dev = proj.add(name=u"Device", type=DEV_TYPE, id=DEV_ID, version=DEV_VER)
    log(u"PLC dobavlen: %s" % dev)
    app = proj.active_application

    # 1. razemy ustrojstva
    log(u"")
    log(u"--- [1] razemy PLC ---")
    try:
        cs = dev.connectors
        names = [x for x in dir(cs) if not x.startswith(u"_")]
        log(u"  svojstva: %s" % u", ".join(names))
        try:
            log(u"  interfejsy: %s" % u", ".join([u"%s" % x for x in cs]))
        except Exception as exc:                               # noqa: BLE001
            log(u"  perechislit ne udalos: %s" % exc)
    except Exception as exc:                                   # noqa: BLE001
        log(u"  connectors nedostupny: %s" % exc)

    # 2. popytki dobavit modul
    log(u"")
    log(u"--- [2] popytki dobavit modul ---")
    candidates = [
        (176, u"0000 0010", u"3.5.11.0", u"Digital Input"),
        (176, u"0000 0011", u"3.5.11.0", u"Digital Output"),
    ]
    added = []
    for typ, cid, cver, cname in candidates:
        ok = try_label(lambda: dev.add(name=cname, type=typ, id=cid, version=cver),
                       u"dev.add(%s)" % cname)
        if ok:
            added.append(cname)
    #  variant cherez proj.add
    for typ, cid, cver, cname in candidates:
        if cname in added:
            continue
        ok = try_label(lambda: proj.add(name=cname, type=typ, id=cid, version=cver),
                       u"proj.add(%s)" % cname)
        if ok:
            added.append(cname)
    log(u"  dobavleno: %s" % (u", ".join(added) if added else u"nichego"))

    # 3. chto teper v dereve
    log(u"")
    log(u"--- [3] sostav dereva ---")
    try:
        def walk(o, d=0):
            for ch in o.get_children():
                nm = u""
                for a in (u"get_name", u"name"):
                    try:
                        v = getattr(ch, a)
                        nm = v() if callable(v) else v
                        if nm:
                            break
                    except Exception:                          # noqa: BLE001
                        pass
                log(u"  %s%s" % (u"  " * d, nm))
                walk(ch, d + 1)
        walk(proj)
    except Exception as exc:                                   # noqa: BLE001
        log(u"  sostav ne chitaetsya: %s" % exc)

    # 4. kompilyaciya s AT %IX0.0
    log(u"")
    log(u"--- [4] kompilyaciya s AT %IX0.0 ---")
    try:
        app.create_pou(u"P_IO", PT.Program, scriptengine.ImplementationLanguages.st,
                       None, None, None)
        p = None
        for cand in app.find(u"P_IO"):
            if hasattr(cand, u"textual_declaration"):
                p = cand
                break
        decl = (u"PROGRAM P_IO\nVAR\n"
                u"    DI_0 AT %IX0.0 : BOOL;\n"
                u"    DO_0 AT %QX0.0 : BOOL;\n"
                u"    AI_0 AT %IW0 : INT;\n"
                u"END_VAR")
        p.textual_declaration.replace(decl)
        p.textual_implementation.replace(u"DO_0 := DI_0;\n")
        tc = app.create_task_configuration()
        task = tc.create_task(u"MainTask")
        task.pous.add(u"P_IO", u"P_IO")
        log(u"  programma P_IO sozdana, v zadache")
    except Exception as exc:                                   # noqa: BLE001
        log(u"  ne udalos sozdat P_IO: %s" % exc)
    try:
        app.build()
    except Exception as exc:                                   # noqa: BLE001
        log(u"  build(): %s" % exc)
    try:
        app.generate_code()
    except Exception as exc:                                   # noqa: BLE001
        log(u"  generate_code(): %s" % exc)
    proj.save()
    proj.close()
    log(u"=== KONEC (itog sm. vyvod CODESYS) ===")


try:
    main()
except Exception, exc:                                          # noqa: E999
    log(u"AVARIYA: %s" % exc)
    import traceback
    log(traceback.format_exc())

f = open(OUT, u"w")
f.write(u"\n".join(L).encode(u"utf-8"))
f.close()
sys.stdout.write(u"probe_add_io: %d strok\n" % len(L))
