# -*- coding: utf-8 -*-
u"""PROBE_IO_MAPPING -- est li u ustroystva API dlya privyazki adresov %I/%Q.

V O P R O S. Kompilyator daet 20 preduprezhdenij C373 "Adres %IX0.0 ne zadan
ni v odnom ustroystve". Zadan li adres v kode (AT %IX0.0) ili v tablitse
sopostavleniya ustroystva -- dlya kompilyatora eto odno i to zhe, no
ScriptEngine mog by privyazat adresa cherez API ustroystva. Togda
preduprezhdenij ne bylo by, i privyazka byla by imenno "cherez derevo
ustroystv", kak trebuet zadanie.

Probuem najti u ustroystva obekty sopostavleniya vvoda/vyvoda i perechislyaem
ih chleny. Rezultat -- v log/probe_io_mapping.txt.
"""

import io
import os
import sys

import scriptengine

ROOT = os.environ.get(u"Z80_ROOT")
PROJ = os.path.join(ROOT, u"build", u"Z80_EMU.project")
LOG = os.path.join(ROOT, u"log")
OUT = os.path.join(LOG, u"probe_io_mapping.txt")

L = []


def log(m):
    L.append(u"%s" % (m,))


def main():
    log(u"=== PROBE IO MAPPING ===")
    proj = scriptengine.projects.open(PROJ)
    devs = list(proj.find(u"Device"))
    log(u"ustroystv najdeno: %d" % len(devs))
    dev = devs[0]
    log(u"ustroystvo: %s" % ((u"%s" % dev)[:100]))

    names = [x for x in dir(dev) if not x.startswith(u"_")]
    log(u"chleny ustroystva (%d): %s" % (len(names), u", ".join(sorted(names))))

    for attr in (u"io_mapping", u"io_mappings", u"mapping", u"io_map",
                 u"add_io_mapping", u"create_io_mapping", u"parameters",
                 u"connectors", u"slots"):
        try:
            v = getattr(dev, attr)
            log(u"  %s = %s" % (attr, v))
            sub = [x for x in dir(v) if not x.startswith(u"_")]
            log(u"    chleny: %s" % (u", ".join(sorted(sub))[:600]))
        except Exception as exc:                               # noqa: BLE001
            log(u"  %s net: %s" % (attr, (u"%s" % exc)[:80]))

    # est li u proekta sposob dobavit ustroystvo-modul
    log(u"")
    log(u"popytka dobavit modul vvoda:")
    for nm in (u"Digital Input", u"I/O", u"DI", u"SM_DI", u"Generic I/O"):
        try:
            d = dev.add(nm)
            log(u"  dev.add(%s) -- OK: %s" % (nm, d))
        except Exception as exc:                               # noqa: BLE001
            log(u"  dev.add(%s) -- %s" % (nm, (u"%s" % exc)[:90]))

    try:
        proj.close()
    except Exception:                                          # noqa: BLE001
        pass


try:
    main()
except Exception, exc:                                          # noqa: E999
    log(u"AVARIYA: %s" % exc)
    import traceback
    log(traceback.format_exc())

if not os.path.isdir(LOG):
    os.makedirs(LOG)
f = open(OUT, u"w")
f.write(u"\n".join(L).encode(u"utf-8"))
f.close()
sys.stdout.write(u"probe_io_mapping: %d strok -> %s\n" % (len(L), OUT))
