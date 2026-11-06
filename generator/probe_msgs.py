# -*- coding: utf-8 -*-
u"""Probe: kak poluchit soobshcheniya kompilyatora posle app.build().

ZAPUSKAT TOLKO cherez CODESYS. Rezultat -- log/probe_msgs.log.

ZADAChA. app.build() vozvratil 0 soobshcheniy, no sam CODESYS pri zagruzke
proekta soobshchil "39 oshibok". Znachit soobshcheniya suschestvuyut --
nado ponyat, kak imenno ih zabrat posle sborki:
  * mozhet, nuzhno pozvat get_messages() srazu posle build() bez delay;
  * mozhet, nuzhno ukazat kategoriyu (get_message_categories);
  * mozhet, nuzhno vyzvat komandu sborki cherez system.commands.
"""
import io
import os
import traceback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, u"build")
LOG = os.path.join(ROOT, u"log", u"probe_msgs.log")
_f = None


def log(m):
    global _f
    if _f is None:
        if not os.path.isdir(os.path.dirname(LOG)):
            os.makedirs(os.path.dirname(LOG))
        _f = io.open(LOG, u"w", encoding=u"utf-8")
    _f.write(m + u"\n")
    _f.flush()


def show_msgs(tag):
    try:
        msgs = list(scriptengine.system.get_messages())
    except Exception:
        log(u"  [%s] get_messages: %s" % (tag, traceback.format_exc()))
        return
    log(u"  [%s] soobshcheniy: %d" % (tag, len(msgs)))
    for m in msgs[:12]:
        try:
            log(u"     severity=%s cat=%s text=%s" % (
                getattr(m, u"severity", u"?"), getattr(m, u"category", u"?"),
                getattr(m, u"text", u"?")))
        except Exception:
            log(u"     %r" % (m,))


def main():
    global scriptengine
    import scriptengine as se
    scriptengine = se

    proj = se.projects.open(os.path.join(BUILD, u"Z80_EMU.project"))
    app = proj.active_application
    log(u"proekt otkryt: %r, application: %r" % (proj is not None, app is not None))

    # 0) chto est SRAZU posle otkrytiya -- zdes i dolzhny byt oshibki zagruzki
    show_msgs(u"srazu posle otkrytiya")

    # 1) kategorii soobshcheniy
    try:
        cats = list(se.system.get_message_categories())
        log(u"kategorij soobshcheniy: %d" % len(cats))
        for c in cats[:20]:
            log(u"   %r" % (c,))
    except Exception:
        log(u"get_message_categories: %s" % traceback.format_exc())

    # 2) komandy
    try:
        cmds = se.system.commands
        log(u"commands: %r" % (cmds,))
        names = [n for n in dir(cmds) if not n.startswith(u"_")]
        log(u"  chleny commands: %s" % u", ".join(names))
    except Exception:
        log(u"commands: %s" % traceback.format_exc())

    # 3) sborka i NEMEDLENNOE chtenie
    se.system.clear_messages()
    show_msgs(u"posle clear_messages")
    try:
        app.build()
        log(u"app.build() -- OK")
    except Exception:
        log(u"app.build() -- ISKLYuChENIE: %s" % traceback.format_exc())
    show_msgs(u"posle build bez delay")
    for d in (100, 500, 2000, 5000):
        se.system.delay(d)
        show_msgs(u"posle delay %d ms" % d)

    log(u"")
    log(u"=== PROBE END ===")
    proj.close()


if __name__ == u"__main__":
    try:
        main()
    except Exception:
        log(u"FATAL:\n%s" % traceback.format_exc())
