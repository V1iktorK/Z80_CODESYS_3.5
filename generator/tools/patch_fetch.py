# -*- coding: utf-8 -*-
u"""PATCH_FETCH -- otdel nyj ekzemplyar pamyati tol ko dlya vyborki koda.

P R I Ch I N A. Set' pamyati (n7) stoit POSLE zashchelki IR, poetomu zashchelka
beret D_Out, poschitannoe v P R O Sh L O M skane. Za odnu komandu poluchaetsya
sdvig na instrukciyu: v faze 1 v IR popadaet kod, vybrannyj eshe po staromu PC,
a v faze 2 ispolnyaetsya predydushchaya komanda. Na odinochnyh testah eto
maskirovalos (PC mezhdu testami ne menyaetsya), a na posledovatel nosti komand
(programma I/O v stende CP/M) -- net: processora vypolnyal NOP i ostavalsya
na PC = 1 vmesto perehoda na 4000h.

P O Ch E M U  V T O R O J  E K Z E M P L Ya R  B E Z O P A S E N. U FB_Memory64K
net svoego sostoyaniya: massiv Z80_Mem lezhit v GVL_Memory, oba ekzemplyara
rabotayut s odnim i tem zhe massivom. Pishet tol ko osnovnoj (u nego est
strob zapisi), vtoroj -- tol ko chitaet kod komandy po PC.

Ch T O  D E L A E M. Set' SET 3a pered zashchelkoj IR: ekzemplyar fbFetch
poluchaet tol ko PC i otdaet D_Out. Vse ostal nye ego vhody podayutsya
nulyami, poetomu nichego ne pishut i ne meshayut.
"""

import io
import sys

sys.stdout.reconfigure(encoding=u"utf-8")

P = r"generator\gen_z80.py"
t = io.open(P, encoding=u"utf-8").read()
n = 0


def rep(old, new):
    global t, n
    assert t.count(old) == 1, (t.count(old), repr(old[:90]))
    t = t.replace(old, new, 1)
    n += 1


# 1) obyavlenie vtorogo ekzemplyara
rep(u'    p.var(u"fbMem", u"FB_Memory64K", u"pamyat\' 64 KB")',
    u'    p.var(u"fbMem", u"FB_Memory64K", u"pamyat\' 64 KB (operand i stek)")\n'
    u'    #  V T O R O J  E K Z E M P L Ya R -- T O L \' K O  D L Ya  V Y B O R K I.\n'
    u'    #  U FB_Memory64K net svoego sostoyaniya (massiv v GVL_Memory), poetomu\n'
    u'    #  dva ekzemplyara bezopasny. Nuzhen, chtoby kod komandy chitalsya V  T O M\n'
    u'    #  Zh E  S K A N E, gde srabatyvaet zashchelka IR: inache IR vsegda otstaval\n'
    u'    #  na odnu komandu, i posledovatel nost komand (programma I/O v stende CP/M)\n'
    u'    #  vypolnyalas\' so sdvigom.\n'
    u'    p.var(u"fbFetch", u"FB_Memory64K", u"pamyat\' 64 KB (tol\'ko vyborka koda)")')

# 2) set' vyborki pered zashchelkoj IR
OLD = (u'    # ================= 3. FETCH =================\n'
       u'    n3 = p.network(u"SET 3: VBORKA: kod komandy v IR")\n'
       u'    c_irq = n3.invar(u"fbIR.Q", y=210)\n'
       u'    n3.outvar(u"GVL_PLCVisu.IR", c_irq, x=F.COL_OUT, y=210)\n'
       u'    n3.block(u"FB_Reg8Latch",\n'
       u'             [(u"D", n3.invar(u"fbMem.D_Out", y=30)),')
NEW = (u'    # ================= 2b. VYBORKA KODA =================\n'
       u'    #  O T D E L \' N Y J  E K Z E M P L Ya R  P A M Ya T I  T O L \' K O  D L Ya  K O D A.\n'
       u'    #  On stoit V Y Sh E zashchelki IR, poetomu kod komandy chitaetsya v tom zhe\n'
       u'    #  skane, gde IR zashchelkivaetsya. Ran\'she vyborka shelа cherez obshchij\n'
       u'    #  ekzemplyar nizhe, i IR vsegda otstaval na odnu komandu -- programma iz\n'
       u'    #  neskol kih komand vypolnyalas so sdvigom.\n'
       u'    n3a = p.network(u"SET 2b: VYBORKA: chitaem kod komandy po PC")\n'
       u'    n3a.block(u"FB_Memory64K",\n'
       u'              [(u"PC", n3a.invar(u"GVL_Regs.Rs_PC", y=30)),\n'
       u'               (u"Addr", n3a.const(u"WORD#0", y=70)),\n'
       u'               (u"Rd", n3a.const(u"FALSE", y=110)),\n'
       u'               (u"Wr", n3a.const(u"FALSE", y=150)),\n'
       u'               (u"D_Bus", n3a.const(u"BYTE#0", y=190)),\n'
       u'               (u"SP_Addr", n3a.const(u"WORD#0", y=230)),\n'
       u'               (u"SP_Rd", n3a.const(u"FALSE", y=270)),\n'
       u'               (u"SP_Wr", n3a.const(u"FALSE", y=310)),\n'
       u'               (u"SP_Data", n3a.const(u"WORD#0", y=350)),\n'
       u'               (u"Wr_Addr", n3a.const(u"WORD#0", y=390)),\n'
       u'               (u"Wr_Data", n3a.const(u"BYTE#0", y=430)),\n'
       u'               (u"Wr_Stb", n3a.const(u"FALSE", y=470))],\n'
       u'              [u"D_Out", u"Rd_Data", u"Op_Word", u"SP_Out", u"Bus_Drv"],\n'
       u'              x=F.COL_BLK2, y=30, instance=u"fbFetch")\n'
       u'    n3a.outvar(u"vFetchCode", n3a.invar(u"fbFetch.D_Out", y=30),\n'
       u'               x=F.COL_OUT, y=30)\n'
       u'\n'
       u'    # ================= 3. FETCH =================\n'
       u'    n3 = p.network(u"SET 3: VBORKA: kod komandy v IR")\n'
       u'    c_irq = n3.invar(u"fbIR.Q", y=210)\n'
       u'    n3.outvar(u"GVL_PLCVisu.IR", c_irq, x=F.COL_OUT, y=210)\n'
       u'    n3.block(u"FB_Reg8Latch",\n'
       u'             [(u"D", n3.invar(u"vFetchCode", y=30)),')
rep(OLD, NEW)

# 3) peremennye
rep(u'    p.var(u"vImmEff", u"BYTE", u"operand dlya ALU: pamyat ili dannye porta")',
    u'    p.var(u"vImmEff", u"BYTE", u"operand dlya ALU: pamyat ili dannye porta")\n'
    u'    p.var(u"vFetchCode", u"BYTE", u"kod komandy, vybrannyj po PC")')

io.open(P, u"w", encoding=u"utf-8").write(t)
print(u"patch_fetch: %d zamen" % n)
print(u"nonascii: %d" % sum(1 for c in t if ord(c) > 127))
