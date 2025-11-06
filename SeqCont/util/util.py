import util
import time
import threading
<<<<<<< HEAD
def prt_cmd_str(status : str):
    status
    if status == util.STATUS_SYSTEM_CONNECT:
        msg = "SYSTEM_CONNECT"
    elif status ==  util.STATUS_SYSTEM_IDLE:
        msg = "SYSTEM_IDLE"
    elif status ==  util.STATUS_VEHICLE_DETECTED:
        msg = "VEHICLE_DETECTED"
    elif status ==  util.STATUS_GATE_OPEN:
        msg = "GATE_OPEN"
    elif status ==  util.STATUS_GATE_CLOSED:
        msg = "GATE_CLOSED"
    elif status ==  util.STATUS_VEHICLE_LEFT:
        msg = "VEHICLE_LEFT"
    elif status ==  util.STATUS_DISPLAY_PAYMENT:
        msg = "DISPLAY_PAYMENT"
    elif status ==  util.STATUS_DISPLAY_PAYMENT_FAIL:
        msg = "DISPLAY_PAYMENT_FAIL"
    elif status ==  util.STATUS_VEHICLE_PASSED:
        msg = "VEHICLE_PASSED"
    elif status ==  util.STATUS_ERROR_CODE:
        msg = "ERROR_CODE"
    else :
        msg = "NONE"
    return msg
=======
def prt_cmd_str(status : int):
        if status == util.STATUS_SYSTEM_CONNECT:
            msg = "SYSTEM_CONNECT"
        elif status ==  util.STATUS_SYSTEM_IDLE:
            msg = "SYSTEM_IDLE"
        elif status ==  util.STATUS_VEHICLE_DETECTED:
            msg = "VEHICLE_DETECTED"
        elif status ==  util.STATUS_GATE_OPEN:
            msg = "GATE_OPEN"
        elif status ==  util.STATUS_GATE_CLOSED:
            msg = "GATE_CLOSED"
        elif status ==  util.STATUS_VEHICLE_LEFT:
            msg = "VEHICLE_LEFT"
        elif status ==  util.STATUS_DISPLAY_PAYMENT:
            msg = "DISPLAY_PAYMENT"
        elif status ==  util.STATUS_DISPLAY_PAYMENT_FAIL:
            msg = "DISPLAY_PAYMENT_FAIL"
        elif status ==  util.STATUS_VEHICLE_PASSED:
            msg = "VEHICLE_PASSED"
        elif status ==  util.STATUS_ERROR_CODE:
            msg = "ERROR_CODE"
        else :
            msg = "NONE"
        return msg
>>>>>>> b5a897478f4e3f55660c81175e0974c95f087b74

# how to re-connect mqtt or uart;
def pack_payload(topic ,payload):
    return {"topic"      : topic,"payload"    : payload}

class GateCtrl:
    def __init__(self,gate_id):
        # IDLE, READY, BUSY
        # self.gate_state       = gateStatus()
        self._gate_id = gate_id
        
<<<<<<< HEAD
        self._uart_payload = pack_payload("","")
        self._mqtt_payload = pack_payload("","")
=======
        self._uart_payload = None
        self._mqtt_payload = None
>>>>>>> b5a897478f4e3f55660c81175e0974c95f087b74
        
        self._uart_cond  = threading.Condition() 
        self._mqtt_cond  = threading.Condition() 

        self._available_count = None
    def prt_gate(self):
        if self._gate_id == util.ENTRY_GATE_ID:
            return "ENTRY_GATE"
        elif self._gate_id == util.EXIT_GATE_ID:
            return "EXIT_GATE"
    def is_garage_full(self):
        return self._available_count == 0
    @property       
    def available_count(self):
        return self._available_count

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
        print(self.mqtt_payload)
        return self.mqtt_payload["payload"]["success"]
    def get_cur_uart_cond(self):
        return self._uart_cond
    def get_cur_mqtt_cond(self):
        return self._mqtt_cond
    def start_up(self,IF_Cont):
        # Server Init 
<<<<<<< HEAD
        if self.gate_id() == util.ENTRY_GATE_ID or util.EXIT_GATE_ID:
            if not self.update_available_count(IF_Cont,True):
                return False
            IF_Cont.send_payload(util.COMM_FOR_STM32 ,self, util.CMD_RESET)
=======
        if self.gate_id() == util.ENTRY_GATE_ID:
            self.mqtt_payload = pack_payload(topic = util.MQTT_TOPIC_RESPONSE_AVAILABLE_COUNT, payload = {"payload" : ""})
            self.update_available_count(IF_Cont)
            IF_Cont.send_payload(util.COMM_FOR_STM32 ,self, util.CMD_RESET)

>>>>>>> b5a897478f4e3f55660c81175e0974c95f087b74
        time.sleep(3)
        if not IF_Cont.wait_for_uart_status(util.STATUS_SYSTEM_CONNECT,self.gate_id()):
            return False
        IF_Cont.send_payload(util.COMM_FOR_STM32 ,self, util.CMD_AVAILABLE_COUNT)
        return True
<<<<<<< HEAD
    def update_available_count(self,IF_Cont,start_up_flg):
        payload = {"start_up" : start_up_flg}
        self.mqtt_payload = pack_payload(topic = util.MQTT_TOPIC_REQUEST_AVAILABLE_COUNT, payload = payload)
        IF_Cont.send_payload(util.COMM_FOR_SERVER ,self, util.CMD_AVAILABLE_COUNT_REQUEST)
        if not IF_Cont.wait_for_mqtt_msg(util.MQTT_TOPIC_RESPONSE_AVAILABLE_COUNT,self.gate_id()):
            return False

        if not "available_count" in self.mqtt_payload and not "payload" in self.mqtt_payload:
            return False
        self.available_count = self.mqtt_payload["payload"]["available_count"]
        self.clear()

=======
    def update_available_count(self,IF_Cont):
        IF_Cont.send_payload(util.COMM_FOR_SERVER ,self, util.CMD_AVAILABLE_COUNT_REQUEST)
        if not IF_Cont.wait_for_mqtt_msg(util.MQTT_TOPIC_RESPONSE_AVAILABLE_COUNT,self.gate_id()):
            return False
        if not "available_count" in self.mqtt_payload:
            return False
        self.available_count = self.mqtt_payload["available_count"]
>>>>>>> b5a897478f4e3f55660c81175e0974c95f087b74
        return True

    def payment_process(self,IF_Cont):
        IF_Cont.send_payload(util.COMM_FOR_SERVER ,self, util.CMD_PAYMENT_INFO_REUQEST)
<<<<<<< HEAD
        IF_Cont.wait_for_mqtt_msg(util.MQTT_TOPIC_RESPONSE_FEE_INFO,self.gate_id())
        IF_Cont.send_payload(util.COMM_FOR_STM32 ,self, util.CMD_DISPLAY_PAYMENT_INFO)
        time.sleep(3) 
        IF_Cont.send_payload(util.COMM_FOR_SERVER ,self, util.CMD_PAYMENT_RESULT)
        time.sleep(3) 
        self.gate_open(IF_Cont)
        self.gate_close(IF_Cont)
=======
        IF_Cont.wait_for_mqtt_msg(util.MQTT_TOPIC_RESPONSE_OCR,self.gate_id())
        if self.is_ocr_ok():
            IF_Cont.send_payload(util.COMM_FOR_STM32 ,self, util.CMD_DISPLAY_PAYMENT_INFO)
            time.sleep(3) 
            IF_Cont.send_payload(util.COMM_FOR_SERVER ,self, util.CMD_PAYMENT_RESULT)
            #test
            IF_Cont.wait_for_mqtt_msg(util.MQTT_TOPIC_RESPONSE_AVAILABLE_COUNT,self.gate_id())
            self.gate_open(IF_Cont)
            self.gate_close(IF_Cont)
>>>>>>> b5a897478f4e3f55660c81175e0974c95f087b74

    def gate_open(self,IF_Cont):
        # 5. Uart로 게이트 OPEN 커맨드 전송
        IF_Cont.send_payload(util.COMM_FOR_STM32 ,self, util.CMD_GATE_OPEN)
        IF_Cont.wait_for_uart_status(util.STATUS_GATE_OPEN,self.gate_id())
            

    def vehicle_pass(self,IF_Cont):
<<<<<<< HEAD
        if not IF_Cont.wait_for_uart_status(util.STATUS_VEHICLE_PASSED,self.gate_id()):
            return False
        if not self.update_available_count(IF_Cont,False):
            print("AVAILABLE_COUNT UPDATE FAIL")

    def gate_close(self,IF_Cont):
        if not self.vehicle_pass(IF_Cont):
            IF_Cont.send_payload(util.COMM_FOR_STM32 ,self, util.CMD_GATE_CLOSE)
            return False
        else :
            IF_Cont.send_payload(util.COMM_FOR_STM32 ,self, util.CMD_AVAILABLE_COUNT)
            time.sleep(1)   
            IF_Cont.send_payload(util.COMM_FOR_STM32 ,self, util.CMD_GATE_CLOSE)
=======
        IF_Cont.wait_for_uart_status(util.STATUS_VEHICLE_PASSED,self.gate_id())
        if not self.update_available_count(IF_Cont):
            print("AVAILABLE_COUNT UPDATE FAIL")

    def gate_close(self,IF_Cont):
        self.vehicle_pass(IF_Cont)
        IF_Cont.send_payload(util.COMM_FOR_STM32 ,self, util.CMD_GATE_CLOSE)
        time.sleep(0.5) 
        IF_Cont.send_payload(util.COMM_FOR_STM32 ,self, util.CMD_AVAILABLE_COUNT)
>>>>>>> b5a897478f4e3f55660c81175e0974c95f087b74
    def gate_full(self,IF_Cont):
        # 5. Uart로 게이트 OPEN 커맨드 전송
        IF_Cont.send_payload(util.COMM_FOR_STM32 ,self, util.CMD_GARAGE_FULL)

    def ocr_request(self,IF_Cont):
        IF_Cont.send_payload(util.COMM_FOR_SERVER ,self, util.CMD_OCR_RESULT_REQUEST)

    def display_payment(self,IF_Cont):
        IF_Cont.send_payload(util.COMM_FOR_STM32 ,self, util.CMD_DISPAY_PAYMENT_INFO)

    def clear(self):
<<<<<<< HEAD
        self.uart_payload = pack_payload("","")
        self.mqtt_payload = pack_payload("","")
=======
        self.uart_payload = None
        self.mqtt_payload = None
>>>>>>> b5a897478f4e3f55660c81175e0974c95f087b74
