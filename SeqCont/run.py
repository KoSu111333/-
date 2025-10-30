import interface
import util
import time
import threading

TWO_GATE_MODE = False
#logger = util.logging.getLogger("MyApp.main") 

def initialize_system():
   ety_gate_ctrl = util.GateCtrl(util.ENTRY_GATE_ID)
    exit_gate_ctrl = util.GateCtrl(util.EXIT_GATE_ID)

    interface_cont = interface.IFCont(ety_gate_ctrl,exit_gate_ctrl)

    TOPIC_LIST = [util.MQTT_TOPIC_RESPONSE_OCR,util.MQTT_TOPIC_RESPONSE_FEE_INFO,util.MQTT_TOPIC_RESPONSE_FEE_RESULT,util.MQTT_TOPIC_RESPONSE_STARTUP]
    # mqtt thread, uart thread start! -
    interface_cont.set_uart_setting(port = util.UART_PORT,baudrate = util.UART_BAUDRATE)
    interface_cont.set_mqtt_setting(bk_addr = util.MQTT_BROKER_ADDRESS,bk_port = util.MQTT_BROKER_PORT,topics = TOPIC_LIST,client_id = util.MQTT_CLIENT_ID)
    interface_cont.init_interface()
    return interface_cont
    
def run():
    interface_cont = initialize_system()

    if interface_cont.start_up():
        return print("[Error] Can't Start up")
    entry_t = threading.Thread(target=interface_cont.entry_gate_task)
    exit_t = threading.Thread(target=interface_cont.exit_gate_task)

    entry_t.start()
    exit_t.start()
    
    entry_t.join()
    exit_t.join()

if __name__ == "__main__":
    run()
