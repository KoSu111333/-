import interface
import util
import time
import threading

# 자동 회복 해봐도 안됨
# 에러 발생 display 띄움

TWO_GATE_MODE = False
#logger = util.logging.getLogger("MyApp.main") 

def initialize_system():
    ety_gate_ctrl = util.GateCtrl(util.ENTRY_GATE_ID)
    exit_gate_ctrl = util.GateCtrl(util.EXIT_GATE_ID)

    interface_cont = interface.IFCont(ety_gate_ctrl,exit_gate_ctrl)

<<<<<<< HEAD
    TOPIC_LIST = [util.MQTT_TOPIC_RESPONSE_OCR,util.MQTT_TOPIC_RESPONSE_FEE_INFO,util.MQTT_TOPIC_RESPONSE_AVAILABLE_COUNT]
=======
    TOPIC_LIST = [util.MQTT_TOPIC_RESPONSE_OCR,util.MQTT_TOPIC_RESPONSE_FEE_INFO,util.MQTT_TOPIC_RESPONSE_FEE_RESULT,util.MQTT_TOPIC_RESPONSE_AVAILABLE_COUNT]
>>>>>>> b5a897478f4e3f55660c81175e0974c95f087b74
    # mqtt thread, uart thread start! -
    interface_cont.set_uart_setting(port = util.UART_PORT,baudrate = util.UART_BAUDRATE)
    interface_cont.set_mqtt_setting(bk_addr = util.MQTT_BROKER_ADDRESS,bk_port = util.MQTT_BROKER_PORT,topics = TOPIC_LIST,client_id = util.MQTT_CLIENT_ID)
    interface_cont.init_interface()
    return interface_cont
    
def run():
    interface_cont = initialize_system()
    while not interface_cont.start_up():
        pass
<<<<<<< HEAD
    if util.EXIT_GATE_MODE:
        exit_t = threading.Thread(target=interface_cont.exit_gate_task)
        exit_t.start()
        exit_t.join()

    else :
        entry_t = threading.Thread(target=interface_cont.entry_gate_task)
        entry_t.start()
        entry_t.join()
=======
    entry_t = threading.Thread(target=interface_cont.entry_gate_task)
    exit_t = threading.Thread(target=interface_cont.exit_gate_task)
>>>>>>> b5a897478f4e3f55660c81175e0974c95f087b74

    

if __name__ == "__main__":
    run()
