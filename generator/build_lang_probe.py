# -*- coding: utf-8 -*-
u"""Sborka yazykovogo eksperimenta (tests/lang_probe.plcopenxml).

ZAPUSKAT TOLKO cherez CODESYS (run_lang_probe.cmd). Rezultat -- log/lang_probe.log.
"""
import io
import os
import traceback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
XML = os.path.join(ROOT, u"tests", u"lang_probe.plcopenxml")
PROJ = os.path.join(ROOT, u"tests", u"lang_probe.project")
LOG = os.path.join(ROOT, u"log", u"lang_probe.log")
_f = None


def log(m):
    global _f
    if _f is None:
        if not os.path.isdir(os.path.dirname(LOG)):
            os.makedirs(os.path.dirname(LOG))
        _f = io.open(LOG, u"w", encoding=u"utf-8")
    _f.write(m + u"\n")
    _f.flush()


def main():
    import scriptengine
    for p in list(scriptengine.projects.all):
        try:
            p.close()
        except Exception:
            pass
    for junk in (PROJ, PROJ + u".~u"):
        if os.path.exists(junk):
            try:
                os.remove(junk)
            except Exception:
                pass
    proj = scriptengine.projects.create(PROJ)
    proj.add(name=u"Device", type=4096, id=u"0000 0001", version=u"3.5.17.30")
    app = proj.active_application
    log(u"proekt sozdan")
    try:
        app.import_xml(XML)
        log(u"import OK")
    except Exception:
        log(u"import OSHIBKA: %s" % traceback.format_exc())
    try:
        tc = app.create_task_configuration()
        task = tc.create_task(u"MainTask")
        task.priority = u"1"
        task.interval = u"T#10ms"
        for n in (u"P1_ORD_A", u"P2_ORD_DOLLAR", u"P3_HEX", u"P4_STRING"):
            try:
                task.pous.add(n, n)
            except Exception:
                pass
    except Exception:
        log(u"zadacha: %s" % traceback.format_exc())
    try:
        app.build()
        log(u"build OK")
    except Exception:
        log(u"build: %s" % traceback.format_exc())
    try:
        app.generate_code()
        log(u"generate_code OK")
    except Exception:
        log(u"generate_code: %s" % traceback.format_exc())
    log(u"=== KONEC ===")
    try:
        proj.save()
        proj.close()
    except Exception:
        pass


if __name__ == u"__main__":
    try:
        main()
    except Exception:
        log(u"FATAL:\n%s" % traceback.format_exc())
