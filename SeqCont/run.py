import interface
import util
import time
import queue
import globals
import threading

TWO_GATE_MODE = False
#logger = util.logging.getLogger("MyApp.main") 

def initialize_system():
    interface_cont = globals.interface_cont

    TOPIC_LIST = [util.MQTT_TOPIC_RESPONSE_OCR,util.MQTT_TOPIC_RESPONSE_FEE_INFO,util.MQTT_TOPIC_RESPONSE_FEE_RESULT,util.MQTT_TOPIC_RESPONSE_STARTUP]
    # mqtt thread, uart thread start! -
    interface_cont.set_uart_setting(port = util.UART_PORT,baudrate = util.UART_BAUDRATE)
    interface_cont.set_mqtt_setting(bk_addr = util.MQTT_BROKER_ADDRESS,bk_port = util.MQTT_BROKER_PORT,topics = TOPIC_LIST,client_id = util.MQTT_CLIENT_ID)
    interface_cont.init_interface()

    
    
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
    interface_cont = globals.interface_cont
    initialize_system()
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
