# -*- coding: utf-8 -*-
u"""Sborka proverochnogo proekta tipov (tests/type_probe.plcopenxml).

ZAPUSKAT TOLKO cherez CODESYS (run_codesys.ps1 ili run_probe_log.cmd).
Rezultat -- log/type_probe.log.
"""
import io
import os
import traceback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(ROOT, u"log", u"type_probe.log")
XML = os.path.join(ROOT, u"tests", u"type_probe.plcopenxml")
PROJ = os.path.join(ROOT, u"tests", u"type_probe.project")
_f = None


def log(m):
    global _f
    if _f is None:
        if not os.path.isdir(os.path.dirname(LOG)):
            os.makedirs(os.path.dirname(LOG))
        _f = io.open(LOG, u"w", encoding=u"utf-8")
    _f.write(m + u"\n")
    _f.flush()


NAMES = [u"T_A_BoolShift", u"T_B_ShlByte", u"T_C_AddByte",
         u"T_D_SelByte", u"T_E_WordChain", u"T_F_ShrWord"]


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

    for n in NAMES:
        try:
            app.import_xml(XML)
            log(u"importirovan: %s" % n)
        except Exception:
            log(u"OSHIBKA importa %s: %s" % (n, traceback.format_exc()))
        break                                    # v fajle vse POU srazu

    # zadacha nuzhna, inache generate_code rugaetsya "ne zadano zadach"
    try:
        tc = app.create_task_configuration()
        task = tc.create_task(u"MainTask")
        task.priority = u"1"
        task.interval = u"T#10ms"
        log(u"zadacha sozdana")
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
    try:
        log(u"soobshcheniy: %d" % len(scriptengine.system.get_messages()))
    except Exception:
        pass
    log(u"=== KONEC. Smotrite vyvod CODESYS: tam budut imena krossov s oshibkami ===")
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
