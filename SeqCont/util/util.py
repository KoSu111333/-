import util
import time
import threading

tim     =  None
    
    
def set_timer(sec):
    global tim
    tim = time.monotonic() + sec    

def result_timer(sec):
    global tim
    if tim is None : 
        set_timer(sec)
        return False

    if time.monotonic() >= tim:
        tim = None
        return True
    else : 
        return False
    
# how to re-connect mqtt or uart;
def pack_payload(dest ,topic ,payload):
    return {"topic"      : topic,"payload"    : payload}


# 함수 자체에 대한 반복, 근데 이걸 테스크로 해야할 것 같은게 이거 하다가 값이 오면 어캄?
# 멀티 스레딩 개념에서 uart,mqtt에서는 도중에 받는게 가능할 것 같은데
# 받고서 큐 처리하는 건 호출이 안될 것 같아.
retry_cnt = 0
def retry(max_retry_count = 3) -> bool:
    global retry_cnt
    time.sleep(1)

    if retry_cnt >= max_retry_count:
        retry_clear()
        return True
    else :
        print(f"Retry...({retry_cnt + 1})")
        retry_cnt += 1
        return False
def retry_clear():
    global retry_cnt
    retry_cnt = 0

class gateStatus:
    def __init__(self):
        # Entry = True , Exit = False
        self._cur_direction      = None
        # Open = True , Close = False
        self._cur_gate           = False
        self._car_detect_flg     = None
        self._gate_id            = None
        self.cur_available_count = util.INIT_AVAILABLE_COUNT
    def set_state_gate_open(self) :
        self._cur_gate = True
    def set_state_gate_close(self) :
        self._cur_gate = False
    def set_state_car_detect(self):
        self._car_detect_flg =True
    def set_state_car_left(self):
        self._car_detect_flg =False
    def set_state_gate_entry(self):
        self._cur_direction = True
        self.set_gate_ID()
    def set_state_gate_exit(self) :
        self._cur_direction = False
        self.set_gate_ID()
    def entry_car(self):
        self.cur_available_count += 1
    def exit_car(self):
        self.cur_available_count -= 1
    def is_full_garage(self):
        if self.cur_available_count == util.INIT_AVAILABLE_COUNT: 
            return True
        else:
            return False
    def get_available_count(self):
        return self.cur_available_count
    def is_cur_detected_car(self):
        return self._car_detect_flg
    def get_cur_direction(self):
        """
        Direction 
            return False == Car Exit
            return True == Car Entry
        """
        return self._cur_direction
    def is_closed(self):
        if self._cur_gate:
            return False
        else :
            return True

    def get_gate_ID(self):  
        return self._gate_id

    def set_gate_ID(self):  
        if self._cur_direction == None:
            return 
        elif self._cur_direction == True:
            # entry_gate ID
            self._gate_id = util.TMP_ENTRY_GATE_ID
        elif self._cur_direction == False:
            # exit_gate ID
            self._gate_id = util.TMP_EXIT_GATE_ID
            return util.TMP_ENTRY_GATE_ID 
    def clear(self):
        # Entry = True , Exit = False
        self._cur_direction = None
        # Open = True , Close = False
        self._cur_gate = False
        self._car_detect_flg = False
        self._gate_id = None
        self.cur_available_count = util.INIT_AVAILABLE_COUNT

class GateCtrl:
    def __init__(self,gate_id):
        # IDLE, READY, BUSY
        # self.gate_state       = gateStatus()
        self._gate_id = gate_id
        
        self.uart_payload = None
        self.mqtt_payload = None
        
        self._uart_cond  = threading.Condition() 
        self._mqtt_cond  = threading.Condition() 
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
        return self.mqtt_payload["success"] == True
    def get_cur_uart_cond(self):
        return self._uart_cond
    def get_cur_mqtt_cond(self):
        return self._mqtt_cond
    def start_up(self,IF_Cont):
        # Server Init 
        # uart Init
        IF_Cont.send_payload(util.COMM_FOR_SERVER ,self, util.JN_STARTUP)
        if not IF_Cont.wait_for_mqtt_status(util.MQTT_TOPIC_RESPONSE_STARTUP,self.gate_id()):
            return False

        # uart Init
        if not IF_Cont.wait_for_uart_status(util.STATUS_SYSTEM_CONNECT,self.gate_id()):
            return False
        IF_Cont.send_payload(util.COMM_FOR_STM32 ,self, util.CMD_AVAILABLE_COUNT)
    def payment_process(self,IF_Cont):
        IF_Cont.send_payload(util.COMM_FOR_SERVER ,self, util.CMD_PAYMENT_INFO_REUQEST)
        IF_Cont.wait_for_mqtt_response(util.MQTT_TOPIC_RESPONSE_OCR,self.gate_id())
        IF_Cont.send_payload(util.COMM_FOR_STM32 ,self, util.CMD_DISPLAY_PAYMENT_INFO)
        print("5. [ACTION] Gate OPEN 커맨드 전송 완료.")
        time.sleep(1) 
        # 5. Uart로 게이트 OPEN 커맨드 전송
        self.gate_open(self)
        IF_Cont.wait_for_uart_status(util.STATUS_VEHICLE_PASSED,self.gate_id())
        self.gate_close(self)           
        print("6. [ACTION] Gate CLOSE 커맨드 전송 완료.")

    def gate_open(self,IF_Cont):
        # 5. Uart로 게이트 OPEN 커맨드 전송
        IF_Cont.send_payload(util.COMM_FOR_STM32 ,self, util.CMD_GATE_OPEN)

    def gate_close(self,IF_Cont):
        IF_Cont.send_payload(util.COMM_FOR_STM32 ,self, util.CMD_GATE_CLOSE)
        time.sleep(0.5) 
        self.send_payload(util.COMM_FOR_STM32 ,self, util.CMD_AVAILABLE_COUNT)
        
    def ocr_request(self,IF_Cont):
        IF_Cont.send_payload(util.COMM_FOR_SERVER ,self, util.CMD_OCR_RESULT_REQUEST)

    def display_payment(self,IF_Cont):
        IF_Cont.send_payload(util.COMM_FOR_STM32 ,self, util.CMD_DISPAY_PAYMENT_INFO)

    def clear(self):
        self.uart_payload = None
        self.mqtt_payload = None


    def __str__(self):
        return f"--------CUR_SYS_CONTEXT-------\nSTATE = {self._state}  ENTRY_GATE = {self.gate_state.get_cur_direction()}  DETECTED_CAR = {self.gate_state.is_cur_detected_car()}"  