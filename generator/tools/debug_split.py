# -*- coding: utf-8 -*-
u"""O T L A D K A razbieniya bloka PODGOTOVKA v TEST_Z80."""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BAK = os.path.join(ROOT, u"generator", u"gen_z80.py.predprep")

t = io.open(BAK, encoding=u"utf-8").read()
sys.stdout.write(u"predprep: bFirstScan=%d bFirst=%d\n"
                 % (t.count(u"bFirstScan"), t.count(u"bFirst")))

st_i = t.find(u"ST_TEST_Z80 = ")
sys.stdout.write(u"ST_TEST_Z80 na pozicii %d\n" % st_i)
scope = t[st_i:]
i = scope.find(u"(* ============================== PODGOTOVKA")
sys.stdout.write(u"PODGOTOVKA na %d\n" % i)
block = scope[i:scope.find(u"(* ============================== PROGON", i)]
sys.stdout.write(u"blok: %d simvolov\n" % len(block))

k = block.find(u"IF bFirstScan THEN")
sys.stdout.write(u"uslovie 'IF bFirstScan THEN' na %d\n" % k)
inner = block[k + len(u"IF bFirstScan THEN"):]
sys.stdout.write(u"inner: %d simvolov\n" % len(inner))

matches = list(re.finditer(u"(?m)^\\s*END_IF;?[ \\t]*$", inner))
sys.stdout.write(u"najdeno strok END_IF: %d\n" % len(matches))
for m in matches:
    ln = inner[:m.start()].count(u"\n") + 1
    sys.stdout.write(u"   stroka %d: %r\n" % (ln, m.group(0)))
