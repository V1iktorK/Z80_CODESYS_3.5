# -*- coding: utf-8 -*-
u"""P O Ch E M U  registraciya v zadache lomaet sborku.

Fakty, ustanovlennye bisekciej (generator/tools/probe_min.py):
  * vse 31 POU + 15 GVL + 2 DUT, B E Z konfiguracii zadach -- 0 oshibok,
    kod sgenerirovan (68310 bajt);
  * ta zhe sborka s P U S T O J konfiguraciej zadach (MainTask bez programm)
    -- 0 oshibok, odno preduprezhdenie C373 "Ne zadan POU dlya zadachi";
  * kak tolko v zadachu popadaet programma -- sypletsya buket oshibok
    C9/C189/C8/C77, kotorye k tekstu POU otnosheniya ne imeyut.

Znachit delo v S A M O M  S P I S K E programm zadachi. V staryh progonah
task.pous[imya] = imya brosalo "object does not support item assignment",
a v build.py tot zhe kod rabotal -- znachit est drugie sposoby, i nado
vybrat rabochij.

Ch T O  D E L A E M. Sozdaem proekt s odnoj programmoj i probuem po ocheredi
kazhdyj sposob registracii, K A Zh D Y J  R A Z  p er ez ap u sk ay a
kompilyaciyu i chitaya spisok zadachi. To, chto deystvitelno popalo
v zadachu, i est kriterij.

ZAPUSK: generator\run_probe_task.cmd
"""
import os
import sys

import scriptengine

ROOT = os.environ.get(u"Z80_ROOT")
if not ROOT:
    ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUILD = os.path.join(ROOT, u"build")
LOG = os.path.join(ROOT, u"log")
PT = scriptengine.PouType
DT = scriptengine.DutType
DEVICE_TYPE = 4096
DEVICE_ID = u"0000 0001"
DEVICE_VERSION = u"3.5.17.30"

LOG_LINES = []


def log(msg):
    LOG_LINES.append(u"%s" % msg)


def try_way(label, way, task, name):
    u"""Poprobovat odin sposob registracii. Vernut tekst rezultata."""
    try:
        if way == u"add2":
            task.pous.add(name, name)
        elif way == u"add1":
            task.pous.add(name)
        elif way == u"append":
            task.pous.append(name)
        elif way == u"iassign":
            task.pous[name] = name
        elif way == u"pou_add":
            task.pous.Add(name)
        elif way == u"create_pou":
            task.pous.create_pou(name)
        lst = list(task.pous)
        return u"OK, v spiske: %r" % (lst,)
    except Exception as exc:                                   # noqa: BLE001
        try:
            lst = list(task.pous)
        except Exception:                                      # noqa: BLE001
            lst = u"<spisok ne chitaetsya>"
        return u"OTKAZ (%s); v spiske: %r" % (exc, lst)


def dump_pous_methods(task):
    u"""Chto voobshche umeet spisok programm zadachi."""
    try:
        p = task.pous
        log(u"  type(pous) = %s" % type(p))
        names = [x for x in dir(p) if not x.startswith(u"_")]
        log(u"  metody: %s" % u", ".join(names))
    except Exception as exc:                                   # noqa: BLE001
        log(u"  pous nedostupen: %s" % exc)


def main():
    log(u"=== PROBE TASK ===")
    proj = scriptengine.projects.create(os.path.join(BUILD, u"probe_task.project"))
    proj.add(name=u"Device", type=DEVICE_TYPE, id=DEVICE_ID, version=DEVICE_VERSION)
    app = proj.active_application

    # odna skromnaya programma
    nm = u"P_T"
    app.create_pou(nm, PT.Program, scriptengine.ImplementationLanguages.st,
                   None, None, None)
    p = None
    for cand in app.find(nm):
        if hasattr(cand, u"textual_declaration"):
            p = cand
            break
    p.textual_declaration.replace(u"PROGRAM P_T\nVAR\n\ti : INT;\nEND_VAR")
    p.textual_implementation.replace(u"i := 1;")
    log(u"programma %s sozdana" % nm)

    tc = app.create_task_configuration()
    task = tc.create_task(u"MainTask")
    try:
        task.priority = u"1"
        task.interval = u"T#10ms"
    except Exception:                                          # noqa: BLE001
        pass
    log(u"")
    log(u"--- [1] chto umeet spisok programm zadachi ---")
    dump_pous_methods(task)

    log(u"")
    log(u"--- [2] probuem sposoby registracii ---")
    for way in (u"add2", u"add1", u"append", u"iassign", u"pou_add"):
        r = try_way(way, way, task, nm)
        log(u"  %-10s -> %s" % (way, r))
        #  posle kazhdoj udachnoj popytki -- ubrat, chtoby ne meshalo
        try:
            if len(list(task.pous)) > 0:
                task.pous.clear()
        except Exception:                                      # noqa: BLE001
            pass

    log(u"")
    log(u"--- [3] kompilyaciya s tem, chto ostalos ---")
    try:
        app.build()
    except Exception as exc:                                   # noqa: BLE001
        log(u"  build(): %s" % exc)
    try:
        app.generate_code()
    except Exception as exc:                                   # noqa: BLE001
        log(u"  generate_code(): %s" % exc)
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
f = open(os.path.join(LOG, u"probe_task.txt"), u"w")
f.write(u"\n".join(LOG_LINES).encode(u"utf-8"))
f.close()
sys.stdout.write(u"probe_task: %d strok\n" % len(LOG_LINES))
