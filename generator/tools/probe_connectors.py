# -*- coding: utf-8 -*-
u"""C H T O  R A Z R E Sh E N O  v s t a v l y a t  v  PLC: razbor razemov.

U PLC est dva razema (connector). U nih est metody by_id / get_device_object.
Nado ponyat, kakiye identifikatory ustrojstv oni prinimayut -- togda mozhno
vybrat podhodyashchiy modul vvoda/vyvoda i dobavit ego, chtoby adresa
%IX0.0 poluchili realnogo vladelca i preduprezhdeniya C373 ischezli.

ZAPUSK: generator\run_diag.ps1 -Script "probe_connectors.py" -OutName "probe_conn"
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
OUT = os.path.join(LOG, u"probe_connectors.txt")

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


def dump(obj, title, maxn=25):
    log(u"")
    log(u"--- %s ---" % title)
    try:
        props = [x for x in dir(obj) if not x.startswith(u"_")]
    except Exception as exc:                                   # noqa: BLE001
        log(u"  dir(): %s" % exc)
        return
    shown = 0
    for a in sorted(props):
        try:
            v = getattr(obj, a)
        except Exception as exc:                               # noqa: BLE001
            log(u"  %-24s <{0}>" % a + u" %s" % exc)
            continue
        if callable(v):
            log(u"  %-24s <metod>" % a)
            continue
        s = u"{0}".format(v).replace(u"\n", u" ")
        log(u"  %-24s = %s" % (a, s[:100]))
        shown += 1
        if shown > maxn:
            log(u"  ...")
            break


def main():
    log(u"=== PROBE CONNECTORS ===")
    path = os.path.join(BUILD, u"probe_conn.project")
    if os.path.exists(path):
        try:
            os.remove(path)
        except Exception:                                      # noqa: BLE001
            pass
    proj = scriptengine.projects.create(path)
    proj.add(name=u"Device", type=DEV_TYPE, id=DEV_ID, version=DEV_VER)
    dev = find(proj, u"Device")
    if dev is None:
        log(u"PLC ne najden")
        return
    cs = dev.connectors
    log(u"razemov: %d" % cs.Count)
    idx = 0
    for c in cs:
        idx += 1
        dump(c, u"razem %d" % idx)
        #  poprobuem poluchit spisok dopustimyh ustrojstv
        for meth in (u"get_device_ids", u"device_ids", u"get_children",
                     u"all_devices", u"allowed"):
            try:
                v = getattr(c, meth)
                v = v() if callable(v) else v
                log(u"  %s -> {0}" % meth + u"{0}".format(v))
            except Exception:                                  # noqa: BLE001
                pass

    #  prяmaya proverka: probuem dobavit cherez connector
    log(u"")
    log(u"--- popytka dobavit cherez connector ---")
    for c in cs:
        for typ, cid, cver, cname in ((176, u"0000 0010", u"3.5.11.0", u"Digital Input"),
                                      (176, u"0000 0011", u"3.5.11.0", u"Digital Output")):
            try:
                proj.add(name=cname, type=typ, id=cid, version=cver, parent=dev)
                log(u"  proj.add(%s, parent=Device) -> OK" % cname)
            except Exception as exc:                           # noqa: BLE001
                log(u"  proj.add(%s, parent=Device) -> %s" % (cname, exc))
            break
        break

    proj.save()
    proj.close()
    log(u"=== KONEC ===")


try:
    main()
except Exception, exc:                                          # noqa: E999
    log(u"AVARIYA: %s" % exc)
    import traceback
    log(traceback.format_exc())

f = open(OUT, u"w")
f.write(u"\n".join(L).encode(u"utf-8"))
f.close()
sys.stdout.write(u"probe_connectors: %d strok\n" % len(L))
