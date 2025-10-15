import util
import time

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
    return {"dest"       : dest,"topic"      : topic,"payload"    : payload}


# 함수 자체에 대한 반복, 근데 이걸 테스크로 해야할 것 같은게 이거 하다가 값이 오면 어캄?
# 멀티 스레딩 개념에서 uart,mqtt에서는 도중에 받는게 가능할 것 같은데
# 받고서 큐 처리하는 건 호출이 안될 것 같아.
retry_cnt = 0
def retry(max_retry_count = 3) -> bool:
    global retry_cnt
    time.sleep(50)
    if retry_cnt > max_retry_count:
        retry_clear()
        return True
    else :
        print(f"재시도 중... ({retry_cnt + 1})")
        retry_cnt += 1
        return False
def retry_clear():
    global retry_cnt
    retry_cnt = 0
    
# car info for paying the fee 
class CarInfo:
    def __init__(self):
        self.license_plate = None
        self.entry_time = None
        self.exit_time = None
        self.fee = None
        self.is_paid = None
        self.discount_applied = None
    
    # 클래스 메서드로 정의하여 인스턴스를 직접 생성하고 반환
    @classmethod
    def from_dict(cls, car_dict):
        car = cls() # CarInfo 인스턴스 생성
        for key, value in car_dict.items():
            if hasattr(car, key):
                setattr(car, key, value)
        return car

    # 인스턴스 메서드로 정의하여 현재 인스턴스에 값을 설정
    def set_car_info(self, car_dict):
        for key, value in car_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def get_car_info(self):
        car_dict = {}
        # 클래스의 모든 속성을 순회하며 None이 아닌 값만 추가
        for key, value in self.__dict__.items():
            if value is not None:
                car_dict[key] = value
        return car_dict


    def clear(self):
        self.license_plate = None
        self.entry_time = None
        self.exit_time = None
        self.fee = None
        self.is_paid = None
        self.discount_applied = None


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

_tmp_available_state = None
class GateCtrl:
    def __init__(self):
        # IDLE, READY, BUSY
        self._state           = util.JN_STARTUP
        self.gate_state       = gateStatus()
        self.car_info         = CarInfo()

    def set_cur_status(self,state):
        self._state = state

    def is_busy(self):
        return not self._state == util.JN_IDLE

    def mange_context(self,IFCtrl):
        # 2. car detect request        
        print("-------------SEQ_START-------------")
        global _tmp_available_state

        if self.gate_state.get_gate_ID() is None:
            return False
        log_context = "[CON]"

        if self._state == util.JN_STARTUP :
            # license_plate_tmp is Camera data (byte)

            log_context += "[STARTUP]"
            IFCtrl.send_payload(util.COMM_FOR_SERVER,self,util.CMD_AVAILABLE_COUNT)
            time.sleep(1) 
            # payload = self.uart_make_frame(11,util.MSG_TYPE_COMMAND,util.CMD_AVAILABLE_COUNT, 10)
            # self.send_payload(util.COMM_FOR_STM32,util.CMD_AVAILABLE_COUNT,payload)

            # time.sleep(1) 
            self.set_cur_status(util.JN_IDLE)
        if self._state == util.JN_IDLE and _tmp_available_state != self.gate_state.get_available_count():
            # 현재 가용한 주차장 수 표시 
            IFCtrl.send_payload(util.COMM_FOR_SERVER,self,self.gate_state)
            
        if self.gate_state.is_cur_detected_car(): 
            # 4. Payment_hanlder 
            if self._state == util.JN_IDLE:
                log_context += "[CARDETECT]"
                # license_plate_tmp is Camera data (byte)
                IFCtrl.send_payload(util.COMM_FOR_SERVER,self,util.CMD_OCR_RESULT_REQUEST)
                # self._state.car_detect_flg = False
                self._state = util.JN_OCR_REQUESTED

            # 3. OCR result
            if self._state == util.JN_OCR_OK:
                # get_cur_direction() return == False is Exit
                log_context += "[JN_OCR_OK]"
                if self.gate_state.get_cur_direction() == False:
                    IFCtrl.send_payload(util.COMM_FOR_SERVER,self,util.CMD_PAYMENT_INFO_REUQEST)
                    self.set_cur_status(util.JN_CAR_INFO_REQUEST)
                else:
                    # car entry 
                    # send gate open command
                    IFCtrl.send_payload(util.COMM_FOR_SERVER,self,util.CMD_GATE_OPEN)

            # OCR Fail Case
            elif self._state == util.JN_OCR_NG:
                log_context += "[JN_OCR_NG]"
                # true is success
                # false is Fail 
                if (retry()):
                    self._state = util.JN_IDLE
                    # IFCtrl.send_payload(util.COMM_FOR_STM32,self,util.CMD_RESET)
                else : 
                    self._state = util.JN_OCR_REQUESTED
                    IFCtrl.send_payload(util.COMM_FOR_SERVER,self,util.JN_OCR_REQUESTED)
                    
            if self._state == util.JN_PAYMENT:
                # car_info_data should send by payload to stm32
                log_context += "[JN_PAYMENT]"
                payload = IFCtrl.uart_make_frame(util.MSG_TYPE_COMMAND,self.payload_cont.make_payload(self,util.CMD_DISPLAY_PAYMENT_INFO))
                IFCtrl.send_payload(util.COMM_FOR_STM32,util.CMD_DISPLAY_PAYMENT_INFO,payload)

        # JN_CLOSE
        if not self.gate_state.is_closed() and not self.gate_state.is_cur_detected_car():
            if self._state == util.JN_OCR_OK :
                self.gate_state.entry_car()
                
            elif self._state == util.JN_PAYMENT_DONE :
                self.gate_state.exit_car()
            # set timer 2sec 
            log_context += "[TIM_START]"

            if (result_timer(1)) : 
                log_context += "[JN_CLOSED]"
                IFCtrl.send_payload(util.COMM_FOR_STM32,self,util.CMD_GATE_CLOSE)
                self._state = util.JN_IDLE


        # 5. Error_handler, 
        # 치명적인 error 일 경우 시스템 리셋
        # 그게 아닐 경우 자체 해결
        _tmp_available_state = self.gate_state.get_available_count()
        IFCtrl.error_handler.chk_err(IFCtrl)
        if log_context != "[CON]":
            print(log_context)
            print(self)
            print("------------SEQ_END------------")

    def clear(self):
        self._state = util.JN_IDLE
        self.gate_state.clear()
        self.car_info.clear()
        self.payload_cont.clear()
    def __str__(self):
        return f"--------CUR_SYS_CONTEXT-------\nSTATE = {self._state}  ENTRY_GATE = {self.gate_state.get_cur_direction()}  DETECTED_CAR = {self.gate_state.is_cur_detected_car()}"  