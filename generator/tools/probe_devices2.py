# -*- coding: utf-8 -*-
u"""P O I S K  modulya vvoda/vyvoda v repozitorii ustrojstv.

Z A Ch E M. V proekte 20 obyavlenij s fizicheskimi adresami (`AT %IX0.0` i t. d.),
i kompilyator dayot 20 preduprezhdenij
    C373: Adres %IX0.0 ne zadan ni v odnom ustrojstve.
Prichina: v dereve ustrojstv est tolko SoftPLC, a modulya vvoda/vyvoda net.
Chtoby ustranit prichinu, a ne zaglushit sledstvie, nuzhno dobavit v derevo
modul, kotoryy daet adresa %I/%Q.

Ch T O  D E L AEM. Vyvodim IMENA ustrojstv iz repozitoriya (v proshlom probe
oni ne pechatalis -- u obektov DeviceID net svojstva name) i ishchem sredi
nih podhodyashchij modul. Dalee probuem dobavit ego dochernim k SoftPLC
i smotrim, prinimaet li derevo.

ZAPUSK: generator\run_diag.ps1 -Script "probe_devices2.py" -OutName "probe_devices2"
"""
import os
import sys

import scriptengine

ROOT = os.environ.get(u"Z80_ROOT")
if not ROOT:
    ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOG = os.path.join(ROOT, u"log")
if not os.path.isdir(LOG):
    os.makedirs(LOG)
OUT = os.path.join(LOG, u"probe_devices2.txt")

L = []


def log(m):
    L.append(u"%s" % (m,))


def attr_of(obj, names):
    for a in names:
        try:
            v = getattr(obj, a)
        except Exception:                                      # noqa: BLE001
            continue
        if v is None:
            continue
        if callable(v):
            try:
                v = v()
            except Exception:                                  # noqa: BLE001
                continue
        return v
    return None


def main():
    log(u"=== PROBE DEVICES 2: imena ustrojstv ===")
    repo = scriptengine.device_repository
    devs = list(repo.get_all_devices())
    log(u"vsego ustrojstv: %d" % len(devs))
    log(u"")
    log(u"--- svojstva pervogo obekta (chto voobshche est) ---")
    try:
        for a in dir(devs[0]):
            if a.startswith(u"_"):
                continue
            try:
                v = getattr(devs[0], a)
            except Exception as exc:                           # noqa: BLE001
                log(u"  %-22s <%s>" % (a, exc))
                continue
            if callable(v):
                log(u"  %-22s <metod>" % a)
            else:
                log(u"  %-22s = %s" % (a, u"%s" % v)[:80])
    except Exception as exc:                                   # noqa: BLE001
        log(u"  dir() oshibka: %s" % exc)

    log(u"")
    log(u"--- svojstva device_info ---")
    try:
        di = devs[0].device_info
        for a in dir(di):
            if a.startswith(u"_"):
                continue
            try:
                v = getattr(di, a)
            except Exception as exc:                           # noqa: BLE001
                log(u"  %-22s <%s>" % (a, exc))
                continue
            log(u"  %-22s = %s" % (a, u"<metod>" if callable(v) else (u"%s" % v)[:90]))
    except Exception as exc:                                   # noqa: BLE001
        log(u"  net: %s" % exc)
    log(u"")
    log(u"--- poisk moduley vvoda/vyvoda po imeni ---")
    keys = (u"i/o", u"io module", u"input", u"output", u"digital", u"analog",
            u"terminal", u"di ", u"do ", u"modul")
    found = 0
    for d in devs:
        nm = attr_of(d, (u"device_name", u"name", u"description",
                         u"get_name", u"title"))
        if nm is None:
            try:
                nm = d.device_info.name
            except Exception:
                nm = None
        did = attr_of(d, (u"device_id", u"id"))
        nm_s = u"%s" % (nm if nm is not None else u"")
        low = nm_s.lower()
        if nm_s and any(k in low for k in keys):
            log(u"  %-60s | %s" % (nm_s[:60], did))
            found += 1
    log(u"najdeno po imeni: %d" % found)


try:
    main()
except Exception, exc:                                          # noqa: E999
    log(u"AVARIYA: %s" % exc)
    import traceback
    log(traceback.format_exc())

f = open(OUT, u"w")
f.write(u"\n".join(L).encode(u"utf-8"))
f.close()
sys.stdout.write(u"probe_devices2: %d strok\n" % len(L))
