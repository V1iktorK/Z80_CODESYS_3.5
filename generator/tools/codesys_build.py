# -*- coding: utf-8 -*-
u"""Инфраструктура сборки проекта CODESYS из скрипта (библиотека для сборщиков).

Здесь собрано всё, что выяснено экспериментально и нужно каждому шагу сборки:
создание проекта с устройством, добавление GVL/DUT, импорт FBD, проверка связей,
сборка и разбор сообщений компилятора.

Устройство: CODESYS Control Win V3 = type 4096, id '0000 0001', version '3.5.17.30'.
"""

import io, os, sys, traceback
import scriptengine


DEVICE_TYPE = 4096
DEVICE_ID = u"0000 0001"
DEVICE_VERSION = u"3.5.17.30"


def log_open(path):
    return io.open(path, "w", encoding="utf-8")


class Log(object):
    u"""Простой логгер в файл + дублирование в stdout CODESYS."""

    def __init__(self, path):
        self.f = io.open(path, "w", encoding="utf-8")
        self.path = path

    def __call__(self, msg):
        line = unicode(msg)
        self.f.write(line + u"\n")
        self.f.flush()

    def close(self):
        try:
            self.f.close()
        except Exception:
            pass


def nm(o):
    try:
        return o.get_name()
    except Exception:
        return u"?"


def close_all():
    # ВАЖНО: глобальные objects (projects, system, online) инжектируются только
    # в namespace ГЛАВНОГО скрипта. В импортированном модуле их надо брать
    # из модуля scriptengine: scriptengine.projects и т. д.
    for p in list(scriptengine.projects.all):
        try:
            p.close()
        except Exception:
            pass


def new_project(path, L):
    u"""Создать проект с нуля и добавить устройство. Возвращает (proj, app)."""
    close_all()
    if os.path.exists(path):
        os.remove(path)
    proj = scriptengine.projects.create(path)
    L(u"    projects.create OK -> %s" % path)
    proj.add(name=u"Device", type=DEVICE_TYPE, id=DEVICE_ID, version=DEVICE_VERSION)
    L(u"    устройство добавлено: type=%d id=%s version=%s"
      % (DEVICE_TYPE, DEVICE_ID, DEVICE_VERSION))
    app = proj.active_application
    L(u"    application = %s" % nm(app))
    return proj, app


def add_gvl(app, name, text, L):
    u"""Создать GVL и задать её текст объявления."""
    gvl = app.create_gvl(name)
    gvl.textual_declaration.replace(text)
    L(u"    GVL %s создана (%d символов объявления)" % (name, len(text)))
    return gvl


def add_dut(app, name, text, L):
    u"""Создать DUT (структуру) и задать её текст объявления."""
    dut = app.create_dut(name, type=scriptengine.DutType.Structure)
    dut.textual_declaration.replace(text)
    L(u"    DUT %s создан" % name)
    return dut


def import_pou(app, xml_path, L):
    u"""Импортировать PLCopenXML в приложение."""
    app.import_xml(xml_path)
    L(u"    import_xml OK: %s" % os.path.basename(xml_path))


def walk(o, ind=0, depth=6, acc=None, L=None):
    if acc is None:
        acc = []
    if L is not None:
        L(u"%s- %s [%s]" % (u"  " * ind, nm(o), type(o).__name__))
    try:
        acc.append((nm(o), o))
    except Exception:
        pass
    if ind >= depth:
        return acc
    try:
        kids = o.get_children()
    except Exception:
        kids = []
    for k in kids:
        walk(k, ind + 1, depth, acc, L)
    return acc


def find_deep(root, name):
    u"""Поиск объекта по имени по всему поддереву (app.find ведёт себя нестабильно)."""
    for n, o in walk(root, 0, 8, [], None):
        if n == name:
            return o
    return None


def import_pous_one_by_one(app, pous, src_dir, L):
    u"""Импортировать POU ПООЧЕРЁДНО, каждый своим файлом.

    Пакетный импорт нескольких POU одним XML иногда молча теряет часть объектов
    (проверено: из 5 POU доехали 3). Пофайловый импорт детерминирован и сразу
    показывает, какой именно POU не принят.
    """
    import fbd_xml
    if not os.path.isdir(src_dir):
        os.makedirs(src_dir)
    paths = []
    for p in pous:
        one = u"%s/%s.plcopenxml" % (src_dir, p.name)
        fbd_xml.write_project(one, [p], p.name)
        app.import_xml(one)
        paths.append(one)
    L(u"    импортировано по одному файлу: %d POU" % len(pous))
    return paths


def verify_import(proj, app, pou_names, gen_path, reexport_path, L):
    u"""Проверить, что POU доехали и связи не потерялись.

    Сравниваем число блоков в сгенерированном XML и в выгрузке обратно,
    а также требуем отсутствия пустых входов (<connectionPointIn />).
    """
    gen = _counts(gen_path)
    L(u"    СГЕНЕРИРОВАНО : блоков=%d связей=%d пустых.входов=%d" % (gen[0], gen[3], gen[4]))

    L(u"    --- дерево Application после импорта ---")
    walk(app, 1, 3, [], L)

    found = []
    missing = []
    for n in pou_names:
        o = find_deep(app, n)
        if o is None:
            o = find_deep(proj, n)
        if o is None:
            missing.append(n)
        else:
            found.append(o)

    if missing:
        L(u"    ОШИБКА: не найдены POU: %s" % u", ".join(missing))
    if not found:
        return False

    proj.export_xml(found, path=reexport_path, declarations_as_plaintext=True)
    rex = _counts(reexport_path)
    L(u"    ПОСЛЕ ИМПОРТА: блоков=%d связей=%d пустых.входов=%d" % (rex[0], rex[3], rex[4]))

    ok = True
    if missing:
        ok = False
    if rex[0] != gen[0]:
        L(u"    ОШИБКА: блоков %d вместо %d — часть схемы потерялась" % (rex[0], gen[0]))
        ok = False
    if rex[4] != 0:
        L(u"    ОШИБКА: %d входов без связи" % rex[4])
        ok = False
    if ok:
        L(u"    ПРОВЕРКА СВЯЗЕЙ: OK (%d блоков, все входы подключены)" % rex[0])
    return ok


def _counts(path):
    import fbd_xml
    return fbd_xml.count_elements(path)


def build(app, L):
    u"""Собрать приложение. Сообщения компилятора CODESYS пишет в stdout процесса."""
    app.build()
    L(u"    build() выполнен (сообщения компилятора — в <скрипт>.stdout.txt)")
