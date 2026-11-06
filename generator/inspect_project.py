# -*- coding: utf-8 -*-
u"""Inspekciya sobrannego proekta: chto real'no lezhit v GVL i v POU.

Zapuskat' TOLKO cherez CODESYS (run_codesys.ps1). Rezultat -- log/inspect.log.

ZACheM. Dubliruyushchiesya imena peremennyh v raznyh GVL kompilyator SP17
NE schitaet oshibkoj, no togda neponyatno, chto imenno sozdal create_gvl i
chto vidit polzovatel. Skript chitaet uzhe sobrannyj proekt i vyvodit
fakticheskie obyavleniya.
"""
import io
import os
import sys
import traceback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, u"build")
LOG = os.path.join(ROOT, u"log", u"inspect.log")

_f = None


def log(m):
    global _f
    if _f is None:
        if not os.path.isdir(os.path.dirname(LOG)):
            os.makedirs(os.path.dirname(LOG))
        _f = io.open(LOG, u"w", encoding=u"utf-8")
    _f.write(m + u"\n")
    _f.flush()


def text_of(obj):
    u"""Dostat' tekst obyavleniya i tela ob''ekta.

    textual_declaration / textual_implementation -- eto NE stroki, a
    ob''ekty-dokumenty (ScriptTextDocument) s metodom replace(). U nih est
    svojstvo .text -- im i chitaem.
    """
    res = {}
    for attr in (u"textual_declaration", u"textual_implementation"):
        try:
            d = getattr(obj, attr)
        except Exception:
            d = None
        if not d:
            continue
        try:
            v = unicode(d.text)
        except Exception:
            continue
        if v:
            res[attr] = v
    return res


def main():
    import scriptengine
    proj = scriptengine.projects.open(os.path.join(BUILD, u"Z80_EMU.project"))
    log(u"proekt otkryt: %r" % (proj is not None,))
    app = proj.active_application
    log(u"application: %r" % (app is not None,))

    # --- odin raz: chto voobshche est u dokumenta obyavleniya ---
    for c in list(app.get_children()):
        try:
            d = c.textual_declaration
        except Exception:
            continue
        log(u"CHLENY ScriptTextDocument (%s):" % c.get_name())
        names = []
        for n in dir(d):
            if n.startswith(u"_"):
                continue
            names.append(n)
        log(u"  " + u", ".join(names))
        break

    def walk(node, depth=0):
        try:
            ch = list(node.get_children())
        except Exception:
            ch = []
        for c in ch:
            try:
                nm = c.get_name()
            except Exception:
                nm = u"?"
            line = u"%s%s" % (u"  " * depth, nm)
            texts = text_of(c)
            if texts:
                log(u"%s   [%s]" % (line, u", ".join([u"%s=%d simv" % (k, len(v))
                                                      for k, v in sorted(texts.items())])))
                log(u"-------- %s --------" % nm)
                for k in sorted(texts):
                    log(u"### %s ###" % k)
                    log(texts[k])
                log(u"-------- konec %s --------" % nm)
            else:
                log(line)
            walk(c, depth + 1)

    walk(app)
    log(u"")
    log(u"=== INSPECT END ===")
    proj.close()


if __name__ == u"__main__":
    try:
        main()
    except Exception:
        log(u"FATAL:\n%s" % traceback.format_exc())
