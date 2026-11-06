# -*- coding: utf-8 -*-
u"""K A K O J  T I P  I N D E K S A  nuzhen massivu ARRAY[0..65535].

Z A Ch E M. U nas massiv pamyati 64 KB: Z80_Mem : ARRAY[0..65535] OF BYTE.
Kompilyator ruzhalsya preduprezhdeniem
    C196: Neyavnaya konversiya iz tipa bez znaka WORD v tip so znakom INT
i my nachali zakladyvat indeks v WORD_TO_DINT. Eto, v svoyu ochered,
porodilo novye preduprezhdeniya INT -> WORD i oshibki DINT -> INT.

Vmesto togo chtoby ugadyvat, stavim chistyj opyt: odna programma, odin
massiv i V S E  V O Z M O Zh N Y E  formy indeksa. Kompilyator sam skazhet,
kakaya forma chistaya.

ZAPUSK: generator\run_probe_fb.cmd -Script tools\probe_index.py  (sm. .ps1)
Rezultat: log\probe_fb_out.txt
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

DECL = u"""PROGRAM P_IDX
VAR
    m  : ARRAY[0..65535] OF BYTE;
    w  : WORD;
    i  : INT;
    d  : DINT;
    u  : UDINT;
    wi : INT;
    dm : ARRAY[0..524287] OF BYTE;
END_VAR"""

BODY = u"""(* kazhdaya stroka -- otdel nyy variant indeksa *)
m[0]  := 1;                    (* 1: konstantnyj literal *)
m[i]  := 2;                    (* 2: INT *)
m[d]  := 3;                    (* 3: DINT *)
m[u]  := 4;                    (* 4: UDINT *)
m[w]  := 5;                    (* 5: WORD napryamuyu *)
m[WORD_TO_DINT(w)] := 6;       (* 6: WORD -> DINT *)
m[WORD_TO_UDINT(w)] := 7;      (* 7: WORD -> UDINT *)
m[wi] := 8;                    (* 8: INT, a pervaya peremennaya drugaya *)
m[d + 1] := 9;                 (* 9: DINT + literal *)
m[w + 1] := 10;                (* 10: WORD + literal *)
m[WORD_TO_DINT(w + 1)] := 11;  (* 11: WORD + literal -> DINT *)
m[w + i] := 12;               (* 12: WORD + INT -- SMEShENIE *)
m[w + INT_TO_WORD(i)] := 14;  (* 14: WORD + INT->WORD *)
m[w + SHL(INT_TO_WORD(i), 5)] := 15; (* 15: WORD + sdvig *)
dm[16#800 + i] := 30;          (* 30: bol shoy massiv + INT *)
dm[i] := 31;                   (* 31: bol shoy massiv, INT *)
dm[16#800 + 128 * i + 1] := 32;(* 32: s umnozheniem *)
dm[WORD#16#FA00 + INT_TO_WORD(3 * i) + 1] := 33; (* 33: WORD# + literaly *)"""

LINES = []


def log(m):
    LINES.append(u"%s" % (m,))


def main():
    log(u"=== PROBE INDEX ===")
    proj = scriptengine.projects.create(os.path.join(BUILD, u"probe_idx.project"))
    proj.add(name=u"Device", type=DEVICE_TYPE, id=DEVICE_ID,
             version=DEVICE_VERSION)
    app = proj.active_application

    name = u"P_IDX"
    app.create_pou(name, PT.Program, scriptengine.ImplementationLanguages.st,
                   None, None, None)
    p = None
    for cand in app.find(name):
        if hasattr(cand, u"textual_declaration"):
            p = cand
            break
    p.textual_declaration.replace(DECL)
    p.textual_implementation.replace(BODY)
    log(u"P_IDX sozdan")

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
    try:
        app.generate_code()
    except Exception as exc:                                   # noqa: BLE001
        log(u"generate_code(): %s" % exc)

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
f = open(os.path.join(LOG, u"probe_idx.txt"), u"w")
f.write(u"\n".join(LINES).encode(u"utf-8"))
f.close()
sys.stdout.write(u"probe_idx: %d strok\n" % len(LINES))
