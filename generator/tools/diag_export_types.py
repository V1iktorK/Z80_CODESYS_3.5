# -*- coding: utf-8 -*-
u"""E K S P O R T  P O U  iz sobrannogo proekta dlya razbora tipov.

Z A Ch E M. Kompilyator soobshchaet "C32: Nevozmozhno konvertirovat tip
'BOOL' v tip 'USINT'" i ne govorit, ni v kakom POU, ni v kakoj seti.
No sobrannyj proekt mozhno V Y G R U Z I T v PLCopenXML -- i togda u kazhdogo
vyzova bloka poyavitsya addData s razdelami inputparamtypes /
outputparamtypes, gde zapisany T I P Y, kotorye CODESYS vyvel sam.

Eto i est otvet: sravnivaya zhelaemyy tip vetki s tem, chto on vyvel,
mozhno uvidet, gde imenno tip "poplyl", -- bez bisekcii po setyam.

ZAPUSK: generator\run_diag_types.cmd <imya_POU> [<imya_POU> ...]
Rezultat: log\diag_types_<imya>.xml
"""
import os
import sys

import scriptengine

ROOT = os.environ.get(u"Z80_ROOT")
if not ROOT:
    ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROJ = os.path.join(ROOT, u"build", u"Z80_EMU.project")
LOG = os.path.join(ROOT, u"log")
OUTDIR = LOG

NAMES = os.environ.get(u"Z80_EXPORT_POUS")
if not NAMES:
    NAMES = u"FB_IO_Ports,FB_RegFileZ80,PLC_PRG,FB_DecoderZ80,FB_ALU_Z80"
names = [x.strip() for x in NAMES.split(u",") if x.strip()]

LOG_LINES = []


def log(m):
    LOG_LINES.append(u"%s" % (m,))


def find_deep(root, name, depth=0):
    u"""Rekursivnyj poisk obekta po imeni: u dochernih net svojstva .name."""
    if depth > 8:
        return None
    try:
        kids = root.get_children()
    except Exception:                                          # noqa: BLE001
        return None
    for ch in kids:
        nm = u""
        for attr in (u"get_name", u"name"):
            try:
                v = getattr(ch, attr)
                nm = v() if callable(v) else v
                if nm:
                    break
            except Exception:                                  # noqa: BLE001
                pass
        if u"%s" % nm == name:
            return ch
        got = find_deep(ch, name, depth + 1)
        if got is not None:
            return got
    return None


def main():
    log(u"=== DIAG TYPES: eksport POU dlya razbora tipov ===")
    log(u"proekt: %s" % PROJ)
    if not os.path.exists(PROJ):
        log(u"NET FAJLA PROEKTA -- snachala sborka")
        return 1
    proj = scriptengine.projects.open(PROJ)
    app = proj.active_application
    ok = 0
    for nm in names:
        o = find_deep(app, nm)
        if o is None:
            log(u"  %-20s NE NAJDEN" % nm)
            continue
        dst = os.path.join(OUTDIR, u"diag_types_%s.xml" % nm)
        try:
            proj.export_xml([o], path=dst, declarations_as_plaintext=True)
            sz = os.path.getsize(dst)
            log(u"  %-20s vygruzhen -> %s (%d bajt)" % (nm, os.path.basename(dst), sz))
            ok += 1
        except Exception as exc:                               # noqa: BLE001
            log(u"  %-20s OSHIBKA eksporta: %s" % (nm, exc))
    proj.close()
    log(u"vygruzheno POU: %d" % ok)
    return 0


try:
    rc = main()
except Exception, exc:                                          # noqa: E999
    log(u"AVARIYA: %s" % exc)
    import traceback
    log(traceback.format_exc())
    rc = 1

if not os.path.isdir(LOG):
    os.makedirs(LOG)
f = open(os.path.join(LOG, u"diag_types.txt"), u"w")
f.write(u"\n".join(LOG_LINES).encode(u"utf-8"))
f.close()
sys.stdout.write(u"diag_types: %d strok\n" % len(LOG_LINES))
