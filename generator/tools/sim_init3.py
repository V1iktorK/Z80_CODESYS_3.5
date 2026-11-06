# -*- coding: utf-8 -*-
u"""SIM INIT3 -- nablyudaem initsializaciyu vnutri shtatnogo prohoda testa.

Zapuskaem odin test (13, INC A) cherez TEST_Z80 (Stage := 0) i chasto
oposhaem: shag, Init_En, Init_Sel_Dst, Init_Vals[0] i A. Tak vidno,
dohodit li Init_Vals[0] = 0Fh do registra A.
"""
import io, os, sys, time
import scriptengine

ROOT = os.environ.get(u"Z80_ROOT")
PROJ = os.path.join(ROOT, u"build", u"Z80_EMU.project")
OUT = os.path.join(ROOT, u"log", u"sim_init3.txt")
L = []


def log(m):
    L.append(u"%s" % (m,))


def rd(oapp, e, d=u"-"):
    try:
        return u"%s" % oapp.read_value(e)
    except Exception:
        return d


def wr(oapp, pairs):
    for e, v in pairs:
        try:
            oapp.set_prepared_value(e, u"%s" % v)
        except Exception:
            pass
    try:
        oapp.write_prepared_values()
    except Exception:
        pass


def main():
    proj = scriptengine.projects.open(PROJ)
    app = proj.active_application
    app.build()
    list(proj.find(u"Device"))[0].set_simulation_mode(True)
    oapp = scriptengine.online.create_online_application(app)
    oapp.login(scriptengine.OnlineChangeOption.Try, False)
    oapp.start()
    time.sleep(1.2)

    log(u"=== SIM INIT3 ===")
    pairs = [(u"GVL_Tests.Cpu_Tests[%d].Enabled" % i, u"TRUE" if i == 13 else u"FALSE")
             for i in range(1, 41)]
    pairs += [(u"GVL_InitRegs.Init_En", u"FALSE")]
    wr(oapp, pairs)
    time.sleep(0.4)
    wr(oapp, [(u"GVL_Tests.Cpu_Test_Active", u"13"),
              (u"GVL_Tests.Cpu_Test_Stage", u"0"),
              (u"GVL_Tests.Cpu_Test_Run", u"TRUE")])

    #  O P R A Sh I V A E M  T O L K O  SHAG: odno chtenie ~10 ms, poetomu
    #  shag 4 (16 skanov po 10 ms) uspevaem uvidet. Ostatok chitaem tolko
    #  kogda shag SMENILSYa -- inache odna iteraciya zanimala by ~100 ms
    #  i my propuskali ves perebor.
    prev = None
    hits = 0
    for k in range(3000):
        st = rd(oapp, u"GVL_Tests.Cpu_Test_Stage")
        if st != prev:
            en = rd(oapp, u"GVL_InitRegs.Init_En")
            sd = rd(oapp, u"GVL_InitRegs.Init_Sel_Dst")
            a = rd(oapp, u"GVL_PLCVisu.A")
            v0 = rd(oapp, u"GVL_InitRegs.Init_Vals[0]")
            log(u"  stage=%-7s En=%-6s Sel=%-8s A=%-9s V0=%s" % (st, en, sd, a, v0))
            prev = st
            hits += 1
            if hits > 80:
                break
        if st == u"INT#9":
            break
        time.sleep(0.002)
    log(u"")
    log(u"")
    log(u"--- OTLADOChNYE SNIMKI ---")
    for e in (u"GVL_Tests.Cpu_Dbg_Init_A", u"GVL_Tests.Cpu_Dbg_Init_F",
              u"GVL_Tests.Cpu_Dbg_Init_N", u"GVL_Tests.Cpu_Test_Result[13]",
              u"GVL_PLCVisu.A", u"GVL_PLCVisu.F",
              u"GVL_Control.Emu_Reset", u"GVL_Control.Emu_Run",
              u"GVL_Control.Ctl_Sel_Dst", u"GVL_Control.Ctl_ALU_Op",
              u"GVL_Control.Ctl_Wr_Enable", u"GVL_Control.Ctl_IncDec",
              u"GVL_PLCVisu.IR", u"PLC_PRG.vY", u"PLC_PRG.vSrc",
              u"PLC_PRG.vCtl_Sel_Dst", u"TEST_Z80.nInit"):
        log(u"  %-32s = %s" % (e, rd(oapp, e)))
    try:
        oapp.stop(); oapp.logout()
    except Exception:
        pass
    proj.close()


try:
    main()
except Exception, exc:
    log(u"AVARIYA: %s" % exc)
    import traceback
    log(traceback.format_exc())

f = open(OUT, u"w")
f.write(u"\n".join(L).encode(u"utf-8"))
f.close()
sys.stdout.write(u"sim_init3: %d strok\n" % len(L))
