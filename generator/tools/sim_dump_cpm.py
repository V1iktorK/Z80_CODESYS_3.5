# -*- coding: utf-8 -*-
u"""SIM_DUMP_CPM -- vypuskaet po odnoj stroke vse proverki CP/M i I/O.

V Y V O D: nomer, gruppa (Kind), ozhidaemoe, fakticheskoe, rezul tat.
Tak srazu vidno, kakaya gruppa provalivaetsya i na skol ko.
"""

import os
import sys
import time

import scriptengine

ROOT = os.environ.get(u"Z80_ROOT")
PROJ = os.path.join(ROOT, u"build", u"Z80_EMU.project")
LOG = os.path.join(ROOT, u"log")
OUT = os.path.join(LOG, u"sim_dump_cpm.txt")

LINES = []
NT = 36


def log(m):
    LINES.append(u"%s" % (m,))


def main():
    log(u"=== DUMP CP/M TESTOV ===")
    proj = scriptengine.projects.open(PROJ)
    app = proj.active_application
    dev = list(proj.find(u"Device"))[0]
    try:
        dev.set_simulation_mode(True)
    except Exception:                                          # noqa: BLE001
        pass
    onl = scriptengine.online.create_online_application(app)
    onl.login(scriptengine.OnlineChangeOption.Try, True)
    onl.start()

    onl.set_prepared_value(u"GVL_Tests_CPM.Cpm_Test_Run", u"TRUE")
    onl.write_prepared_values()

    names = [u"GVL_Tests_CPM.Cpm_Test_Total_Pass",
             u"GVL_Tests_CPM.Cpm_Test_Fail_Count",
             u"GVL_Tests_CPM.Cpm_Test_Run"]
    v = {}
    for _i in range(40):
        time.sleep(1)
        v = dict(zip(names, list(onl.read_values(names))))
        if u"FALSE" in (u"%s" % v.get(names[2])):
            break
    log(u"itog: %s" % v)

    for nm in (u"GVL_CPM.Bdos_Count", u"GVL_CPM.Out_Count", u"GVL_CPM.In_Cnt",
               u"GVL_CPM.File_Open", u"GVL_CPM.Bdos_Hit", u"GVL_CPM.Cpm_MsgLen",
               u"GVL_PLCVisu.PC", u"GVL_PLCVisu.Halted",
               u"GVL_HW_IO.AI_0", u"GVL_HW_IO.AI_1",
               u"GVL_HW_Buffer.HW_In_AI0", u"GVL_HW_Buffer.HW_In_AI1",
               u"GVL_HW_Buffer.HW_In_DI", u"GVL_IO.Bus_IO_Addr"):
        try:
            log(u"  %s = %s" % (nm, onl.read_value(nm)))
        except Exception as exc:                               # noqa: BLE001
            log(u"  %s -- net: %s" % (nm, exc))

    req = []
    for i in range(1, NT + 1):
        req.append(u"GVL_Tests_CPM.Cpm_Test_Result[%d]" % i)
        req.append(u"GVL_Tests_CPM.Cpm_Act_A[%d]" % i)
        req.append(u"GVL_Tests_CPM.Cpm_Act_W[%d]" % i)
        req.append(u"GVL_Tests_CPM.Cpm_Act_MaskA[%d]" % i)
        req.append(u"GVL_Tests_CPM.Cpm_Act_MaskP[%d]" % i)
        for f in (u"Kind", u"Exp_Byte", u"Exp_Word", u"Enabled", u"Id"):
            req.append(u"GVL_Tests_CPM.Cpm_Tests[%d].%s" % (i, f))

    rec = {}
    CH = 50
    for k0 in range(0, len(req), CH):
        part = req[k0:k0 + CH]
        try:
            vals = list(onl.read_values(part))
        except Exception as exc:                               # noqa: BLE001
            log(u"read OSHIBKA: %s" % exc)
            vals = [u"?"] * len(part)
        for nm2, vl in zip(part, vals):
            rec[nm2] = u"%s" % (vl,)

    def g(nm2):
        s = rec.get(nm2, u"?")
        return s.split(u"#")[-1]

    log(u"")
    log(u"N   Id Kind En ExpB ExpW ActB ActW mA mP  R")
    for i in range(1, NT + 1):
        res = rec.get(u"GVL_Tests_CPM.Cpm_Test_Result[%d]" % i, u"?")
        log(u"%-3d %-3s %-4s %-2s %-4s %-4s %-4s %-4s %-2s %-2s %s"
            % (i, g(u"GVL_Tests_CPM.Cpm_Tests[%d].Id" % i),
               g(u"GVL_Tests_CPM.Cpm_Tests[%d].Kind" % i),
               (u"1" if u"TRUE" in rec.get(u"GVL_Tests_CPM.Cpm_Tests[%d].Enabled" % i, u"") else u"0"),
               g(u"GVL_Tests_CPM.Cpm_Tests[%d].Exp_Byte" % i),
               g(u"GVL_Tests_CPM.Cpm_Tests[%d].Exp_Word" % i),
               g(u"GVL_Tests_CPM.Cpm_Act_A[%d]" % i),
               g(u"GVL_Tests_CPM.Cpm_Act_W[%d]" % i),
               (u"1" if u"TRUE" in rec.get(u"GVL_Tests_CPM.Cpm_Act_MaskA[%d]" % i, u"") else u"0"),
               (u"1" if u"TRUE" in rec.get(u"GVL_Tests_CPM.Cpm_Act_MaskP[%d]" % i, u"") else u"0"),
               (u"PASS" if u"TRUE" in res else u"fail")))

    try:
        onl.stop()
    except Exception:                                          # noqa: BLE001
        pass
    try:
        onl.logout()
    except Exception:                                          # noqa: BLE001
        pass
    try:
        proj.close()
    except Exception:                                          # noqa: BLE001
        pass


try:
    main()
except Exception, exc:                                          # noqa: E999
    log(u"AVARIYA: %s" % exc)
    import traceback
    log(traceback.format_exc())

if not os.path.isdir(LOG):
    os.makedirs(LOG)
f = open(OUT, u"w")
f.write(u"\n".join(LINES).encode(u"utf-8"))
f.close()
sys.stdout.write(u"sim_dump_cpm: %d strok -> %s\n" % (len(LINES), OUT))
