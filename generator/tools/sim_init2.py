# -*- coding: utf-8 -*-
u"""SIM INIT2 -- nablyudaem initsializaciyu VNUTRI prohoda testa.

Ostavlyaem odin test (13, INC A), zapuskaem ego cherez shtatnyj mehanizm
TEST_Z80 i chasto oproshaem: nomer shaga, Init_En, Init_Sel_Dst i A.
Tak vidno, dohodit li Init_Vals[0] = 0Fh do registra A.
"""
import io, os, sys, time
import scriptengine

ROOT = os.environ.get(u"Z80_ROOT")
PROJ = os.path.join(ROOT, u"build", u"Z80_EMU.project")
OUT = os.path.join(ROOT, u"log", u"sim_init2.txt")
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

    log(u"=== SIM INIT2 ===")
    pairs = [(u"GVL_Tests.Cpu_Tests[%d].Enabled" % i, u"TRUE" if i == 13 else u"FALSE")
             for i in range(1, 41)]
    wr(oapp, pairs)
    time.sleep(0.3)
    wr(oapp, [(u"GVL_Tests.Cpu_Test_Run", u"TRUE")])

    prev = None
    for k in range(700):
        time.sleep(0.005)
        st = rd(oapp, u"GVL_Tests.Cpu_Test_Stage")
        en = rd(oapp, u"GVL_InitRegs.Init_En")
        sd = rd(oapp, u"GVL_InitRegs.Init_Sel_Dst")
        a = rd(oapp, u"GVL_PLCVisu.A")
        cur = (st, en, sd, a)
        if cur != prev:
            log(u"  stage=%-7s Init_En=%-6s Sel_Dst=%-9s A=%s"
                % (st, en, sd, a))
            prev = cur
        if st in (u"INT#9",) or (rd(oapp, u"GVL_Tests.Cpu_Test_Run") == u"FALSE" and k > 200):
            break
    log(u"rezultat Test_Result[13] = %s" % rd(oapp, u"GVL_Tests.Cpu_Test_Result[13]"))
    log(u"A = %s" % rd(oapp, u"GVL_PLCVisu.A"))
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
sys.stdout.write(u"sim_init2: %d strok\n" % len(L))
