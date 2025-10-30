import interface
import util

ety_gate_ctrl = util.GateCtrl()
exit_gate_ctrl = util.GateCtrl()
ety_gate_ctrl.gate_id = util.TMP_ENTRY_GATE_ID
exit_gate_ctrl.gate_id = util.TMP_ENTRY_GATE_ID

interface_cont = interface.IFCont(ety_gate_ctrl,exit_gate_ctrl)
