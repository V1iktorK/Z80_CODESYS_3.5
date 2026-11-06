# -*- coding: utf-8 -*-
u"""B I S E K Ts I Ya  P O  T E L U  PRG_CPM_Boot.

Z A Ch E M. V PRG_CPM_Boot ostalos odno preduprezhdenie
    C196: Neyavnaya konversiya iz tipa bez znaka 'UINT' v tip so znakom 'INT'
bez imeni POU i nomera stroki. Chtoby najti ego, berem T E L O  programmy
kak est (s GVL i FB ono kompiliruetsya v probe) i otsekaem chasti cherez
peremennuyu okruzheniya Z80_BOOT_PART:

    Z80_BOOT_PART=1  -- tolko nulevaya stranitsa
    Z80_BOOT_PART=2  -- + tablitsa vektorov BIOS
    Z80_BOOT_PART=3  -- + katalog
    Z80_BOOT_PART=4  -- vsyo (po umolchaniyu)

ZAPUSK: run_probe_fb.ps1 -Fbs none -Script tools\probe_boot.py
"""
import io
import os
import sys

import scriptengine

ROOT = os.environ.get(u"Z80_ROOT")
if not ROOT:
    ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUILD = os.path.join(ROOT, u"build")
LOG = os.path.join(ROOT, u"log")
PT = scriptengine.PouType

DEVICE_TYPE = 4096
DEVICE_ID = u"0000 0001"
DEVICE_VERSION = u"3.5.17.30"

DECL = u"""PROGRAM P_BOOT
VAR
    i : INT;
END_VAR"""

PART = int(os.environ.get(u"Z80_BOOT_PART", u"4"))

SEC1 = u"""IF TRUE THEN
    FOR i := 0 TO 255 DO
        Z80_Mem[i] := 0;
    END_FOR
    Z80_Mem[0] := 16#C3;
    Z80_Mem[1] := 16#00;
    Z80_Mem[2] := 16#FA;
    Z80_Mem[3] := 16#01;
    Z80_Mem[4] := 0;
    Z80_Mem[5] := 16#C3;
    Z80_Mem[6] := 16#00;
    Z80_Mem[7] := 16#F0;
    Z80_Mem[16#5C] := 0;
    Z80_Mem[16#5D] := 0;
    Z80_Mem[16#5E] := 0;
    Z80_Mem[16#5F] := 0;
    Z80_Mem[16#60] := 0;
"""

SEC2 = u"""    FOR i := 0 TO 16 DO
        Z80_Mem[WORD#16#FA00 + INT_TO_WORD(3 * i)]     := 16#C3;
        Z80_Mem[WORD#16#FA00 + INT_TO_WORD(3 * i) + 1] := INT_TO_BYTE(16#20 + i);
        Z80_Mem[WORD#16#FA00 + INT_TO_WORD(3 * i) + 2] := 16#FA;
    END_FOR
"""

SEC3 = u"""    FOR i := 0 TO 2047 DO
        Disk_Mem[i] := 16#E5;
    END_FOR
    FOR i := 18 TO 31 DO
        Disk_Mem[i] := 0;
    END_FOR
"""

SEC4 = u"""    FOR i := 0 TO 127 DO
        Disk_Mem[16#800 + i] := Z80_Mem[16#0100 + i];
    END_FOR
END_IF
"""

LINES = []


def log(m):
    LINES.append(u"%s" % (m,))


def main():
    log(u"=== PROBE BOOT, chastej: %d ===" % PART)
    body = SEC1
    if PART >= 2:
        body += SEC2
    if PART >= 3:
        body += SEC3
    if PART >= 4:
        body += SEC4
    else:
        body += u"END_IF\n"

    proj = scriptengine.projects.create(os.path.join(BUILD, u"probe_boot.project"))
    proj.add(name=u"Device", type=DEVICE_TYPE, id=DEVICE_ID,
             version=DEVICE_VERSION)
    app = proj.active_application

    #  GVL: bez nih telo ne skompiliruetsya
    for f in sorted(os.listdir(os.path.join(ROOT, u"src"))):
        if not f.endswith(u".gvl"):
            continue
        gname = f[:-len(u".gvl")]
        txt = io.open(os.path.join(ROOT, u"src", f), encoding=u"utf-8").read()
        try:
            g = app.create_gvl(gname)
            g.textual_declaration.replace(txt)
        except Exception as exc:                               # noqa: BLE001
            log(u"GVL %s: %s" % (gname, exc))

    name = u"P_BOOT"
    app.create_pou(name, PT.Program, scriptengine.ImplementationLanguages.st,
                   None, None, None)
    p = None
    for cand in app.find(name):
        if hasattr(cand, u"textual_declaration"):
            p = cand
            break
    p.textual_declaration.replace(DECL)
    p.textual_implementation.replace(body)
    log(u"P_BOOT sozdan, strok tela: %d" % len(body.split(u"\n")))

    tc = app.create_task_configuration()
    task = tc.create_task(u"MainTask")
    try:
        task.priority = u"1"
        task.interval = u"T#10ms"
    except Exception:                                          # noqa: BLE001
        pass
    task.pous.add(name, name)

    try:
        app.build()
    except Exception as exc:                                   # noqa: BLE001
        log(u"build(): %s" % exc)

    proj.save()
    proj.close()
    log(u"=== KONEC ===")


try:
    main()
except Exception, exc:                                          # noqa: E999
    log(u"AVARIYA: %s" % exc)
    import traceback
    log(traceback.format_exc())

if not os.path.isdir(LOG):
    os.makedirs(LOG)
f = open(os.path.join(LOG, u"probe_boot.txt"), u"w")
f.write(u"\n".join(LINES).encode(u"utf-8"))
f.close()
sys.stdout.write(u"probe_boot: %d strok\n" % len(LINES))
