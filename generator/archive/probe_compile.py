# -*- coding: utf-8 -*-
u"""Probe: kak vyzvat POLNUYu kompilyaciyu i poluchit soobshcheniya.

ZAPUSKAT TOLKO cherez CODESYS (run_codesys.ps1). Rezultat -- log/probe_compile.log.

ZADAChA. app.build() vo mnogih progonah vozvashchal "soobshcheniya: 0",
dazhe kogda v POU zavedomo dobavlen musor. Nuzhno ponyat:
  1) est li u Application drugie metody sborki (compile, generate_code...);
  2) chto vernet build() -- vozmozhno, on vozvashchaet soobshcheniya sam;
  3) poyavlyayutsya li soobshcheniya s zaderzhkoy.
"""
import io
import os
import sys
import traceback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, u"build")
LOG = os.path.join(ROOT, u"log", u"probe_compile.log")
_f = None


def log(m):
    global _f
    if _f is None:
        if not os.path.isdir(os.path.dirname(LOG)):
            os.makedirs(os.path.dirname(LOG))
        _f = io.open(LOG, u"w", encoding=u"utf-8")
    _f.write(m + u"\n")
    _f.flush()


def dump_methods(obj, title):
    log(u"=== %s ===" % title)
    names = []
    for n in dir(obj):
        if n.startswith(u"_"):
            continue
        names.append(n)
    log(u"  " + u", ".join(names))
    log(u"")


def main():
    import scriptengine
    proj = scriptengine.projects.open(os.path.join(BUILD, u"Z80_EMU.project"))
    app = proj.active_application
    log(u"proekt: %r  application: %r" % (proj is not None, app is not None))

    dump_methods(app, u"CHLENY Application")
    dump_methods(scriptengine.system, u"CHLENY system")

    for label, call in ((u"build()", lambda: app.build()),
                        (u"compile()", lambda: app.compile()),
                        (u"generate_code()", lambda: app.generate_code())):
        log(u"--- probuem %s ---" % label)
        try:
            r = call()
            log(u"  bez isklyucheniya, vozvrat: %r" % (r,))
            if r is not None:
                try:
                    log(u"  dlinna vozvratа: %d" % len(r))
                    for m in r:
                        log(u"    %r" % (m,))
                except Exception:
                    log(u"  (len ne primenim)")
        except Exception:
            log(u"  ISKLYuChENIE: %s" % traceback.format_exc())
        for delay in (300, 1500):
            scriptengine.system.delay(delay)
            try:
                msgs = scriptengine.system.get_messages()
                log(u"  posle %d ms soobshcheniy: %d" % (delay, len(msgs)))
                for m in msgs:
                    try:
                        log(u"    severity=%s text=%s" % (m.severity, m.text))
                    except Exception:
                        log(u"    %r" % (m,))
            except Exception:
                log(u"  get_messages: %s" % traceback.format_exc())

    log(u"")
    log(u"=== PROBE END ===")
    proj.close()


if __name__ == u"__main__":
    try:
        main()
    except Exception:
        log(u"FATAL:\n%s" % traceback.format_exc())
