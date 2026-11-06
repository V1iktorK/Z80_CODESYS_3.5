# -*- coding: utf-8 -*-
import io, os, traceback
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(ROOT, u"log", u"probe_gen.log")
f = io.open(LOG, u"w", encoding=u"utf-8")
def log(m):
    f.write(m + u"\n"); f.flush()
import scriptengine
proj = scriptengine.projects.open(os.path.join(ROOT, u"build", u"Z80_EMU.project"))
app = proj.active_application
log(u"proekt otkryt")
for label, fn in ((u"generate_code()", app.generate_code), (u"build()", app.build)):
    try:
        r = fn()
        log(u"%s -> OK, vozvrat %r" % (label, r))
    except Exception:
        log(u"%s -> ISKLYuChENIE:\n%s" % (label, traceback.format_exc()))
    scriptengine.system.delay(1000)
    try:
        msgs = list(scriptengine.system.get_messages())
        log(u"  soobshcheniy posle %s: %d" % (label, len(msgs)))
        for m in msgs[:8]:
            log(u"    %s" % (getattr(m, u"text", m),))
    except Exception:
        log(u"  get_messages: %s" % traceback.format_exc())
log(u"=== END ===")
proj.close()
