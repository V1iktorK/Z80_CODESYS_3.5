# -*- coding: utf-8 -*-
u"""C H T O  E S T'  V  R E P O Z I T O R I I  U S T R O J S T V.

Z A Ch E M. Pri sborke ostayutsya 20 preduprezhdenij
    C373: Adres %IX0.0 ne zadan ni v odnom ustrojstve.
Oni voznikayut potomu, chto v dereve ustrojstv est tolko SoftPLC, a modul ej
vvoda/vyvoda net. Chtoby reshit eto po-nastoyashchemu (a ne zaglushit),
nuzhno ponyat, est li v repozitorii ustrojstv podhodyashchij modul I/O,
kotoryj mozhno dobavit v derevo programmno.

V Y V O D I M: spisok dostupnyh ustrojstv i ih identifikatory -- dalee
mozhno probovat dobavit modul i posmotret, ischeznet li C373.

ZAPUSK: generator\run_diag.ps1 -Script "probe_devices.py" -OutName "probe_devices"
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
OUT = os.path.join(LOG, u"probe_devices.txt")

L = []


def log(m):
    L.append(u"%s" % (m,))


def main():
    log(u"=== PROBE DEVICES: chto est v repozitorii ustrojstv ===")
    #  U scriptengine est nabor katalogov; imena mogut otlichat'sya po versii,
    #  poetomu probuem neskolko variantov i pechataem, chto poluchilos.
    repos = []
    for attr in (u"device_repository", u"devicerepository", u"device_repo"):
        try:
            r = getattr(scriptengine, attr)
            repos.append((attr, r))
        except Exception:                                      # noqa: BLE001
            pass
    log(u"najdeno katalogov: %d" % len(repos))
    for nm, r in repos:
        log(u"  %s = %s" % (nm, r))
        try:
            devs = list(r.get_all_devices())
        except Exception as exc:                               # noqa: BLE001
            log(u"    get_all_devices() ne rabotaet: %s" % exc)
            try:
                devs = list(r.devices)
            except Exception as exc2:                          # noqa: BLE001
                log(u"    .devices tozhe net: %s" % exc2)
                continue
        log(u"    ustrojstv: %d" % len(devs))
        #  ishchem vse, chto pokhozhe na modul vvoda/vyvoda
        for d in devs:
            try:
                name = u"%s" % d.device_id
            except Exception:                                  # noqa: BLE001
                name = repr(d)
            try:
                desc = u"%s" % d.name
            except Exception:                                  # noqa: BLE001
                desc = u""
            low = (name + u" " + desc).lower()
            if any(k in low for k in (u"i/o", u"io", u"input", u"output",
                                      u"di", u"do", u"module", u"adapter",
                                      u"ethernet", u"modbus")):
                log(u"      KANDIDAT: %s | %s" % (name, desc))


try:
    main()
except Exception, exc:                                          # noqa: E999
    log(u"AVARIYA: %s" % exc)
    import traceback
    log(traceback.format_exc())

f = open(OUT, u"w")
f.write(u"\n".join(L).encode(u"utf-8"))
f.close()
sys.stdout.write(u"probe_devices: %d strok\n" % len(L))
