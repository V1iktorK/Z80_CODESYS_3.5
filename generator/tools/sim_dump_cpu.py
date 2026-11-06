# -*- coding: utf-8 -*-
u"""SIM_DUMP_CPU -- vypuskaet PO ODNOMU vse 40 testov processor a ih rezultaty.

Z A Ch E M. run_simulation.py pechataet tol ko itogi (8 / 32). Chtoby pon yat,
P O Ch E M U test padaet, nuzhno videt sam opisanie testa i ego rezultat
vmeste: opcode, nachalnye i ozhidaemye znacheniya, maski.

V Y V O D -- po odnoj stroke na test:
    N  Id  Opc  A0  >A  F0  >F  PC0  >PC  Cyp  R  maski
gde '>' -- ozhidaemoe znachenie (Exp_*), a 'R' -- rezultat (TRUE = proshel).
"""

import os
import sys
import time

import scriptengine

ROOT = os.environ.get(u"Z80_ROOT")
BUILD = os.path.join(ROOT, u"build")
LOG = os.path.join(ROOT, u"log")
PROJ = os.path.join(BUILD, u"Z80_EMU.project")
OUT = os.path.join(LOG, u"sim_dump_cpu.txt")

LINES = []


def log(m):
    LINES.append(u"%s" % (m,))


NT = 40

FIELDS = [u"Id", u"Opcode", u"Init_A", u"Init_B", u"Init_F", u"Init_PC",
          u"Exp_A", u"Exp_F", u"Exp_PC", u"Exp_Cycles", u"Exp_Mem",
          u"Mask_A", u"Mask_F", u"Mask_PC", u"Mask_Mem", u"Mask_Flag",
          u"Enabled", u"Stage"]


def main():
    log(u"=== DUMP CPU TESTOV ===")
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

    onl.set_prepared_value(u"GVL_Tests.Cpu_Test_Run", u"TRUE")
    onl.write_prepared_values()

    names = [u"GVL_Tests.Cpu_Test_Total_Pass", u"GVL_Tests.Cpu_Test_Fail_Count",
             u"GVL_Tests.Cpu_Test_Run"]
    for _i in range(40):
        time.sleep(1)
        v = dict(zip(names, list(onl.read_values(names))))
        if u"FALSE" in (u"%s" % v.get(names[2])):
            break
    log(u"itog: %s" % v)

    #  odnim paketom chitaem vse polya vseh testov
    req = []
    for i in range(1, NT + 1):
        req.append(u"GVL_Tests.Cpu_Test_Result[%d]" % i)
        req.append(u"GVL_Tests.Cpu_Act_A[%d]" % i)
        req.append(u"GVL_Tests.Cpu_Act_F[%d]" % i)
        req.append(u"GVL_Tests.Cpu_Act_PC[%d]" % i)
        for f2 in (u"IR", u"Op", u"Dst", u"Src", u"Bus"):
            req.append(u"GVL_Tests.Cpu_Act_%s[%d]" % (f2, i))
        for f2 in (u"WE", u"ID", u"MR", u"MW", u"Rst"):
            req.append(u"GVL_Tests.Cpu_Act_%s[%d]" % (f2, i))
        for f2 in (u"RsPC", u"NxPC", u"Mem0", u"Mem2", u"MemE", u"AA",
                   u"DV", u"SR", u"RA", u"RB", u"RH", u"RL"):
            req.append(u"GVL_Tests.Cpu_Act_%s[%d]" % (f2, i))
        req.append(u"GVL_Tests.Cpu_Act_FE[%d]" % i)
        for f2 in (u"PA", u"PB", u"PH"):
            req.append(u"GVL_Tests.Cpu_Act_%s[%d]" % (f2, i))
        for f2 in (u"CK", u"RN", u"HT", u"WEF", u"FE2", u"YY",
                   u"OW", u"PN", u"PL", u"CD"):
            req.append(u"GVL_Tests.Cpu_Act_%s[%d]" % (f2, i))
        for f2 in (u"I0", u"I1", u"SD"):
            req.append(u"GVL_Tests.Cpu_Act_%s[%d]" % (f2, i))
        req.append(u"GVL_Tests.Cpu_Act_IE[%d]" % i)
        for f in FIELDS:
            req.append(u"GVL_Tests.Cpu_Tests[%d].%s" % (i, f))
    #  ScriptEngine ne prinimaet slishkom dlinnyj spisok vyrazhenij
    #  ("Slishkom mnogo vyrazhenij"), poetomu chitaem paketami.
    vals = []
    CH = 50
    for k0 in range(0, len(req), CH):
        part = req[k0:k0 + CH]
        try:
            vals.extend(list(onl.read_values(part)))
        except Exception as exc:                               # noqa: BLE001
            log(u"read_values OSHIBKA na pakete %d: %s" % (k0 // CH, exc))
            vals.extend([u"?"] * len(part))

    dbg = [u"GVL_Tests.Cpu_Dbg_Init_A", u"GVL_Tests.Cpu_Dbg_Init_F",
           u"GVL_Tests.Cpu_Dbg_Init_N", u"GVL_PLCVisu.A", u"GVL_PLCVisu.F",
           u"GVL_PLCVisu.PC", u"GVL_PLCVisu.Reg_Checksum",
           u"GVL_PLCVisu.Halted"]
    try:
        d = dict(zip(dbg, list(onl.read_values(dbg))))
        log(u"otladka: %s" % d)
    except Exception as exc:                                   # noqa: BLE001
        log(u"dbg OSHIBKA: %s" % exc)

    if vals:
        rec = {}
        for nm, val in zip(req, vals):
            rec[nm] = u"%s" % (val,)
        log(u"")
        log(u"N   Id  Opc   A0    A     >A    F0    F     >F    PC0    >PC   Cyp  R    "
            u"mA mF mPC mM mFl En")
        for i in range(1, NT + 1):
            def g(f):
                return rec.get(u"GVL_Tests.Cpu_Tests[%d].%s" % (i, f), u"?")
            def num(f):
                s = g(f)
                if u"#" in s:
                    s = s.split(u"#")[-1]
                return s
            res = rec.get(u"GVL_Tests.Cpu_Test_Result[%d]" % i, u"?")
            def a(nm2):
                s = rec.get(u"GVL_Tests.%s[%d]" % (nm2, i), u"?")
                return s.split(u"#")[-1]
            en = u"1" if u"TRUE" in g(u"Enabled") else u"0"
            log(u"%-3d %-3s %-5s %-5s %-5s %-5s %-5s %-5s %-5s %-6s %-6s %-4s %-5s %-2s %-2s %-3s %-2s %-3s %s"
                % (i, num(u"Id"), num(u"Opcode"),
                   num(u"Init_A"), a(u"Cpu_Act_A"), num(u"Exp_A"),
                   num(u"Init_F"), a(u"Cpu_Act_F"), num(u"Exp_F"),
                   num(u"Init_PC"),
                   num(u"Exp_PC"), num(u"Exp_Cycles"),
                   (u"PASS" if u"TRUE" in res else u"fail"),
                   (u"1" if u"TRUE" in g(u"Mask_A") else u"0"),
                   (u"1" if u"TRUE" in g(u"Mask_F") else u"0"),
                   (u"1" if u"TRUE" in g(u"Mask_PC") else u"0"),
                   (u"1" if u"TRUE" in g(u"Mask_Mem") else u"0"),
                   (u"1" if u"TRUE" in g(u"Mask_Flag") else u"0"), en))
            log(u"      PCrs=%s PCnx=%s Mem0=%s Mem2=%s MemE=%s Rst=%s" %
                (a(u"Cpu_Act_RsPC"), a(u"Cpu_Act_NxPC"), a(u"Cpu_Act_Mem0"),
                 a(u"Cpu_Act_Mem2"), a(u"Cpu_Act_MemE"),
                 rec.get(u"GVL_Tests.Cpu_Act_Rst[%d]" % i, u"?")))
            log(u"      now FlagsEn=%s Y=%s OpWord=%s PCNew=%s PCLoad=%s Cond=%s" %
                (rec.get(u"GVL_Tests.Cpu_Act_FE2[%d]" % i, u"?"),
                 a(u"Cpu_Act_YY"), a(u"Cpu_Act_OW"), a(u"Cpu_Act_PN"),
                 rec.get(u"GVL_Tests.Cpu_Act_PL[%d]" % i, u"?"),
                 rec.get(u"GVL_Tests.Cpu_Act_CD[%d]" % i, u"?")))
            log(u"      clock ClkExec=%s Run=%s Halted=%s WrEnEff=%s" %
                (rec.get(u"GVL_Tests.Cpu_Act_CK[%d]" % i, u"?"),
                 rec.get(u"GVL_Tests.Cpu_Act_RN[%d]" % i, u"?"),
                 rec.get(u"GVL_Tests.Cpu_Act_HT[%d]" % i, u"?"),
                 rec.get(u"GVL_Tests.Cpu_Act_WEF[%d]" % i, u"?")))
            log(u"      posle perebora A=%s B=%s H=%s" %
                (a(u"Cpu_Act_PA"), a(u"Cpu_Act_PB"), a(u"Cpu_Act_PH")))
            log(u"      init V0=%s V1=%s SelDst=%s InitEn=%s" %
                (a(u"Cpu_Act_I0"), a(u"Cpu_Act_I1"), a(u"Cpu_Act_SD"),
                 rec.get(u"GVL_Tests.Cpu_Act_IE[%d]" % i, u"?")))
            log(u"      regs A=%s B=%s H=%s L=%s | ALU_A=%s Src=%s Dst=%s FEn=%s" %
                (a(u"Cpu_Act_RA"), a(u"Cpu_Act_RB"), a(u"Cpu_Act_RH"),
                 a(u"Cpu_Act_RL"), a(u"Cpu_Act_AA"), a(u"Cpu_Act_SR"),
                 a(u"Cpu_Act_DV"),
                 rec.get(u"GVL_Tests.Cpu_Act_FE[%d]" % i, u"?")))
            log(u"      IR=%s Op=%s Dst=%s Src=%s Bus=%s WE=%s ID=%s MR=%s MW=%s"
                % (a(u"Cpu_Act_IR"), a(u"Cpu_Act_Op"), a(u"Cpu_Act_Dst"),
                   a(u"Cpu_Act_Src"), a(u"Cpu_Act_Bus"),
                   rec.get(u"GVL_Tests.Cpu_Act_WE[%d]" % i, u"?"),
                   rec.get(u"GVL_Tests.Cpu_Act_ID[%d]" % i, u"?"),
                   rec.get(u"GVL_Tests.Cpu_Act_MR[%d]" % i, u"?"),
                   rec.get(u"GVL_Tests.Cpu_Act_MW[%d]" % i, u"?")))

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
except Exception, exc:                                         # noqa: E999
    log(u"AVARIYA: %s" % exc)
    import traceback
    log(traceback.format_exc())

if not os.path.isdir(LOG):
    os.makedirs(LOG)
f = open(OUT, u"w")
f.write(u"\n".join(LINES).encode(u"utf-8"))
f.close()
sys.stdout.write(u"sim_dump_cpu: %d strok -> %s\n" % (len(LINES), OUT))
