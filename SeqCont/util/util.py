import util
import time
import threading
    
# how to re-connect mqtt or uart;
def pack_payload(topic ,payload):
    return {"topic"      : topic,"payload"    : payload}

# def ptr_cmd_str(cmd):
#     if cmd == util.STATUS_SYSTEM_CONNECT :
#         return "STATUS_SYSTEM_CONNECT"
#     elif cmd == util.STATUS_SYSTEM_IDLE :
#         return "STATUS_SYSTEM_IDLE"
#     elif cmd == util.STATUS_VEHICLE_DETECTED :
#         return "STATUS_VEHICLE_DETECTED"

#     elif cmd == util.STATUS_GATE_OPEN :
#     elif cmd == util.STATUS_GATE_CLOSED :
#     elif cmd == util.STATUS_VEHICLE_LEFT :
#     elif cmd == util.STATUS_DISPLAY_PAYMENT :
#     elif cmd == util.STATUS_DISPLAY_PAYMENT_DONE :
#     elif cmd == util.STATUS_DISPLAY_PAYMENT_FAIL :
#     elif cmd == util.STATUS_VEHICLE_PASSED :
#     elif cmd == util.STATUS_ERROR_CODE :

class GateCtrl:
    def __init__(self,gate_id):
        # IDLE, READY, BUSY
        # self.gate_state       = gateStatus()
        self._gate_id = gate_id
        
        self.uart_payload = None
        self.mqtt_payload = None
        
        self._uart_cond  = threading.Condition() 
        self._mqtt_cond  = threading.Condition() 

        self._available_count = None
    def prt_gate(self):
        if self._gate_id == util.ENTRY_GATE_ID:
            return "ENTRY_GATE"
        elif self._gate_id == util.EXIT_GATE_ID:
            return "EXIT_GATE"
    def is_garage_full(self):
        return self._available_count == util.INIT_AVAILABLE_COUNT
    @property       
    def available_count(self):
        return self._mqtt_payload

    @available_count.setter 
    def available_count(self, count):
        self._available_count = count

    @property       
    def mqtt_payload(self):
        return self._mqtt_payload

    @mqtt_payload.setter 
    def mqtt_payload(self, payload):
        self._mqtt_payload = payload
    @property
    def uart_payload(self):
        return self._uart_payload
    @uart_payload.setter
    def uart_payload(self, payload):
        self._uart_payload = payload
    def gate_id(self):
        return self._gate_id
    def is_ocr_ok(self):
        return self._mqtt_payload["payload"]["success"] == True
    def get_cur_uart_cond(self):
        return self._uart_cond
    def get_cur_mqtt_cond(self):
        return self._mqtt_cond
    def start_up(self,IF_Cont):
        # Server Init 
        # uart Init
        self.mqtt_payload = pack_payload(topic = util.MQTT_TOPIC_RESPONSE_STARTUP, payload = {"payload" : ""})

        if self.gate_id() == util.ENTRY_GATE_ID:
            IF_Cont.send_payload(util.COMM_FOR_SERVER ,self, util.CMD_STARTUP)
            if not IF_Cont.wait_for_mqtt_msg(util.MQTT_TOPIC_RESPONSE_STARTUP,self.gate_id()):
                return False
            # uart Init
        IF_Cont.send_payload(util.COMM_FOR_STM32 ,self, util.CMD_RESET)
        time.sleep(3)

        if not IF_Cont.wait_for_uart_status(util.STATUS_SYSTEM_CONNECT,self.gate_id()):
            return False
        IF_Cont.send_payload(util.COMM_FOR_STM32 ,self, util.CMD_AVAILABLE_COUNT)
    def payment_process(self,IF_Cont):
        IF_Cont.send_payload(util.COMM_FOR_SERVER ,self, util.CMD_PAYMENT_INFO_REUQEST)
        IF_Cont.wait_for_mqtt_msg(util.MQTT_TOPIC_RESPONSE_OCR,self.gate_id())
        IF_Cont.send_payload(util.COMM_FOR_STM32 ,self, util.CMD_DISPLAY_PAYMENT_INFO)
        time.sleep(1) 
        # 5. Uart로 게이트 OPEN 커맨드 전송
        self.gate_open(IF_Cont)
        IF_Cont.wait_for_uart_status(util.STATUS_VEHICLE_PASSED,self.gate_id())
        self.gate_close(IF_Cont)           

    def gate_open(self,IF_Cont):
        # 5. Uart로 게이트 OPEN 커맨드 전송
        IF_Cont.send_payload(util.COMM_FOR_STM32 ,self, util.CMD_GATE_OPEN)

    def gate_close(self,IF_Cont):
        IF_Cont.send_payload(util.COMM_FOR_STM32 ,self, util.CMD_GATE_CLOSE)
        time.sleep(0.5) 
        IF_Cont.send_payload(util.COMM_FOR_STM32 ,self, util.CMD_AVAILABLE_COUNT)
    def gate_full(self,IF_Cont):
        # 5. Uart로 게이트 OPEN 커맨드 전송
        IF_Cont.send_payload(util.COMM_FOR_STM32 ,self, util.CMD_GARAGE_FULL)

    def ocr_request(self,IF_Cont):
        IF_Cont.send_payload(util.COMM_FOR_SERVER ,self, util.CMD_OCR_RESULT_REQUEST)

    def display_payment(self,IF_Cont):
        IF_Cont.send_payload(util.COMM_FOR_STM32 ,self, util.CMD_DISPAY_PAYMENT_INFO)

    def clear(self):
        self.uart_payload = None
        self.mqtt_payload = None


    def __str__(self):
        return f"--------CUR_SYS_CONTEXT-------\nSTATE = {self._state}  ENTRY_GATE = {self.gate_state.get_cur_direction()}  DETECTED_CAR = {self.gate_state.is_cur_detected_car()}"  