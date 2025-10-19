import interface
import sensorModule
import util
import time
import signal
import queue

TWO_GATE_MODE = False

#logger = util.logging.getLogger("MyApp.main") 

def initialize_system():
    recv_msg_queue = queue.Queue() 
    # I/F Controller Creaete!
    interface_cont = interface.IFCont()
    initialize_IF(interface_cont,recv_msg_queue)
    ety_gate_ctrl,exit_gate_ctrl = initialize_SysContext()
    interface_cont.send_payload(util.COMM_FOR_STM32,ety_gate_ctrl,util.CMD_RESET)
    # stm32 booting time 
    time.sleep(0.3)
    interface_cont.send_payload(util.COMM_FOR_STM32,ety_gate_ctrl,util.CMD_AVAILABLE_COUNT)

    return recv_msg_queue,interface_cont,ety_gate_ctrl, exit_gate_ctrl

def initialize_IF(IFCont,cmd_queue):
    TOPIC_LIST = [util.MQTT_TOPIC_RESPONSE_OCR,util.MQTT_TOPIC_RESPONSE_FEE_INFO,util.MQTT_TOPIC_RESPONSE_FEE_RESULT]
    # mqtt thread, uart thread start! -
    IFCont.set_uart_setting(port = util.UART_PORT,baudrate = util.UART_BAUDRATE,queue = cmd_queue)
    IFCont.set_mqtt_setting(bk_addr = util.MQTT_BROKER_ADDRESS,bk_port = util.MQTT_BROKER_PORT,topics = TOPIC_LIST,client_id = util.MQTT_CLIENT_ID,queue =cmd_queue)
    IFCont.init_interface()
    

def initialize_SysContext():
    if not TWO_GATE_MODE:
        # 게이트 하나일 때, 진입 게이트 객체만 생성하여 반환
        ety_gate_ctrl = util.GateCtrl()
        ety_gate_ctrl.gate_state.set_state_gate_entry()                                                                                                                                                                         
        # 출구 게이트는 None 또는 필요 없는 값 반환
        return ety_gate_ctrl, None
    else : 
        # 게이트 두 개일 때, 두 객체 모두 생성하여 반환
        ety_gate_ctrl = util.GateCtrl()                                                                                                                                                                         
        ety_gate_ctrl.gate_state.set_state_gate_entry()
        exit_gate_ctrl = util.GateCtrl()
        exit_gate_ctrl.gate_state.set_state_direction_exit()
        return ety_gate_ctrl, exit_gate_ctrl
    
def cleanup_system(interface_cont):
    print("\n--- [CLEANUP START] ---")
    # interface_cont가 성공적으로 초기화되었는지 확인 후 정리
    if interface_cont is not None:
        try:
            interface_cont.stop_interface()            
            # 여기에 ety_gate_ctrl, exit_gate_ctrl 등의 추가 정리 로직을 넣을 수 있습니다.
        except Exception as e:
            print(f"[CLEANUP ERROR] 객체 정리 중 오류 발생: {e}")
    print("--- [CLEANUP END] ---")

def run():
    interface_cont = None
    try:
        recv_msg_queue, interface_cont,ety_gate_ctrl, exit_gate_ctrl = initialize_system()
        while True:
            # 1. if received mesPayloadContsage 
            if recv_msg_queue or util.DEBUG_FLAG :
                recv_msg = recv_msg_queue.get()
                if(not interface.parse_received_data(recv_msg,ety_gate_ctrl,exit_gate_ctrl)):
                    continue
                # 1. Parse received command
                if (not TWO_GATE_MODE):
                    ety_gate_ctrl.mange_context(interface_cont)
                else : 
                    ety_gate_ctrl.mange_context(interface_cont)
                    exit_gate_ctrl.mange_context(interface_cont)
                time.sleep(0.5) 
    except Exception as e:
        print(f"Error Occured : {e}")
        if (interface_cont is not None) :
            cleanup_system(interface_cont)                



if __name__ == "__main__":
    while(True):
        #if occured Exception, retry;
        run()
        print("[SYS][ERROR][RESTART]")
        time.sleep(5)
