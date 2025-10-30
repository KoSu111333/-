import interface
import util

ety_gate_ctrl = util.GateCtrl(util.ENTRY_GATE_ID)
exit_gate_ctrl = util.GateCtrl(util.EXIT_GATE_ID)

interface_cont = interface.IFCont(ety_gate_ctrl,exit_gate_ctrl)
