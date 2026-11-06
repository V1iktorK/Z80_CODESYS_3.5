# -*- coding: utf-8 -*-
u"""Razbit' podgotovku testov v TEST_Z80 na port sii (po 8 testov za skan).

ZAPUSKAT SISTEMNYM PYTHON 3 ODIN RAZ.

Z A D A Ch A. Kompilyator CODESYS padaet (vyhod obryvaetsya na stroke
"Kompilyaciya : Prilozhenie"), kogda v odnoj programme pochti 1000 prisvaivanij
polyam struktur massiva: 62 testa x ~16 polej. Proverено bisekciej: bez
TEST_Z80 sborka prohodit, s nim padaet. U TEST_Z80_CPM takih prisvaivanij
v dva raza menshe, i on kompiliruetsya.

R E Sh E N I E. Zapolnyaem massiv porciyami, po 8 testov za skan:

    IF GVL_Tests.Cpu_Test_Run AND NOT bPrepared THEN
        IF NOT fbCase.Run THEN
            CASE nPrep OF
                0: <testy 1..8>
                1: <testy 9..16>
                ...
                7: <testy 57..62 + itog>
            END_CASE
            bPrepared := nPrep >= 7;
            nPrep := nPrep + 1;
        END_IF
    END_IF

Kazhdaya porciya kompaktna, kompilyator ee perevarivaet.
"""
import io
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GEN = os.path.join(ROOT, u"generator", u"gen_z80.py")
BAK = GEN + u".predprep"

CHUNK = 8
FIRST_T = 1
LAST_T = 62


def main():
    if not os.path.exists(BAK):
        sys.stdout.write(u"rezerva net -- snachala sozdajte ego kopiej gen_z80.py\n")
        return
    t = io.open(BAK, encoding=u"utf-8").read()

    #  V A Zh N O: iskat' nado VNUTRI imenno ST_TEST_Z80. Slovo PODGOTOVKA
    #  est i v ST_TEST_Z80_CPM (on vyshe po fajlu), i poisk s samogo nachala
    #  nahodil chuzhoj blok -- iz-za etogo skript rugalsya "ne najdeno".
    st_i = t.find(u"ST_TEST_Z80 = ")
    if st_i < 0:
        sys.stdout.write(u"ne najden ST_TEST_Z80\n")
        return
    st_j = t.find(u"'''", t.find(u"'''", st_i) + 3)
    scope = t[st_i:st_j if st_j > 0 else len(t)]

    i = scope.find(u"(* ============================== PODGOTOVKA")
    j = scope.find(u"(* ============================== PROGON", i)
    if i < 0 or j < 0:
        sys.stdout.write(u"granicy bloka ne najdeny (PODGOTOVKA=%d PROGON=%d)\n" % (i, j))
        return
    block = scope[i:j]

    # vnutrennost: ot pervoj stroki posle IF bFirstScan THEN do poslednego END_IF
    k = block.find(u"IF bFirstScan THEN")
    if k < 0:
        sys.stdout.write(u"ne najdeno 'IF bFirstScan THEN'\n")
        return
    inner = block[k + len(u"IF bFirstScan THEN"):]
    #  Shablon myagkij: v bloke est stroka "        END_IF" (8 probelov,
    #  zakryvaet vnutrennij FOR) i "END_IF" (bez otstupa, vneshnij).
    #  Zhestkij shablon s chetyrmya probelami ne sovpadal ni s odnoj --
    #  otsyuda oshibka "ne najden koncevoj END_IF".
    ends = [m.start() for m in re.finditer(u"(?m)^\\s*END_IF;?[ \\t]*$", inner)]
    if not ends:
        sys.stdout.write(u"ne najden koncevoj END_IF\n")
        return
    inner = inner[:ends[-1]]

    # uberaem sluzhebnye stroki i otstup 4 probela
    inner = re.sub(u"(?m)^\\s*bFirstScan\\s*:=\\s*FALSE;\\s*$", u"", inner)
    lines = []
    for ln in inner.split(u"\n"):
        lines.append(ln[4:] if ln.startswith(u"    ") else ln)
    inner = u"\n".join(lines)

    # rezhem na porcii po nomeru testa: nachalo porcii -- stroka s indeksom,
    # kratnym CHUNK (naprimer [1], [9], ...) ili itogovaya chast
    marks = []
    for m in re.finditer(u"Cpu_Tests\\[(\\d+)\\]", inner):
        n = int(m.group(1))
        if (n - FIRST_T) % CHUNK == 0 and (not marks or marks[-1][1] != n):
            marks.append((m.start(), n))
    if not marks:
        sys.stdout.write(u"ne najdeny granicy porcij\n")
        return
    sys.stdout.write(u"porcij najdeno: %d (testy: %s)\n"
                     % (len(marks), u", ".join(str(n) for _, n in marks)))

    # itogovaya chast -- ot poslednego "Cpu_Test_Count := 0" do konca
    tail_i = inner.rfind(u"Cpu_Test_Count := 0;")
    tail = inner[tail_i:] if tail_i > 0 else u""

    chunks = []
    for idx, (pos, n) in enumerate(marks):
        end = marks[idx + 1][0] if idx + 1 < len(marks) else (tail_i if tail_i > pos else len(inner))
        chunks.append((n, inner[pos:end].rstrip()))
    if tail:
        chunks[-1] = (chunks[-1][0], chunks[-1][1] + u"\n\n" + tail.rstrip())

    # sobiraem novyj blok
    out = [u"(* ============================== PODGOTOVKA ============================== *)",
           u"(* Porcii po %d testov za skan: kompilyator CODESYS ne perevarivaet" % CHUNK,
           u"   pochti 1000 prisvaivanij polyam struktur v odnoj programme. *)",
           u"IF GVL_Tests.Cpu_Test_Run AND NOT bPrepared THEN",
           u"    IF NOT fbCase.Run THEN",
           u"        CASE nPrep OF"]
    for n, body in chunks:
        out.append(u"            %d:" % ((n - FIRST_T) // CHUNK))
        for ln in body.split(u"\n"):
            out.append(u"                " + ln if ln.strip() else u"")
    out.append(u"        END_CASE")
    out.append(u"        bPrepared := nPrep >= %d;" % (len(chunks) - 1))
    out.append(u"        nPrep := nPrep + 1;")
    out.append(u"    END_IF")
    out.append(u"END_IF")
    out.append(u"")
    out.append(u"")

    new_block = u"\n".join(out)
    t2 = t[:st_i] + scope[:i] + new_block + scope[j:] + t[(st_j if st_j > 0 else len(t)):]
    io.open(GEN, u"w", encoding=u"utf-8").write(t2)
    sys.stdout.write(u"novyj blok: %d strok (bylo %d)\n"
                     % (new_block.count(u"\n"), block.count(u"\n")))


if __name__ == u"__main__":
    main()
