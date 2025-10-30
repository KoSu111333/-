import interface
import struct
import sensorModule
import threading
import util
import time


class PayloadCont:
    def __init__(self):
        self.camera_module = sensorModule.cameraModule()
        self.camera_module.init_camera()

    def make_payload(self,gate_ctrl,p_type):
        if util.DEBUG_FLAG:
            print(f"PAYLOAD MAKE START")
        payload = {}
        union_data ={}
        gate_id = gate_ctrl.gate_id()
        # if gate_ctrl.mqtt_payload is not None or gate_ctrl.uart_payload is not None:
        mqtt_payload = gate_ctrl.mqtt_payload
        uart_payload = gate_ctrl.uart_payload

        timestamp = int(time.time())

        # For server 
        if p_type == util.CMD_STARTUP:
            union_data = {"gate_id" : gate_id}
        elif p_type ==  util.CMD_OCR_RESULT_REQUEST:
            license_plate_img = self.camera_module.capture_images()
            union_data = {"gate_id" : gate_id, "timestamp" :  timestamp ,"img": license_plate_img}
        elif p_type ==  util.CMD_PAYMENT_INFO_REUQEST:
            mqtt_payload = gate_ctrl.mqtt_payload["payload"]
            union_data = {"gate_id" : gate_id, "license_plate" :  mqtt_payload["license_plate"] , "timestamp" :  timestamp}
        elif p_type ==  util.CMD_PAYMENT_RESULT:
            mqtt_payload = gate_ctrl.mqtt_payload["payload"]
            union_data = {"gate_id" : gate_id, "license_plate" :  mqtt_payload["license_plate"] , "is_paid" :  mqtt_payload["is_paid"]}
        # For stm32 
        elif p_type ==  util.CMD_GATE_OPEN:
            mqtt_payload = gate_ctrl.mqtt_payload["payload"]
            union_data = {"license_plate" : mqtt_payload["license_plate"]}
        elif p_type == util.CMD_DISPLAY_PAYMENT_INFO:
            mqtt_payload = gate_ctrl.mqtt_payload["payload"]
            union_data = mqtt_payload
        elif p_type ==  util.CMD_AVAILABLE_COUNT:
            union_data = 10
        elif p_type ==  util.CMD_GATE_CLOSE or \
             p_type ==  util.CMD_DISPLAY_PAYMENT_DONE or \
             p_type ==  util.CMD_DISPLAY_PAYMENT_FAIL or \
             p_type ==  util.CMD_REQUEST_STM32_STATUS or \
             p_type ==  util.CMD_RESET:
            #only send command
            union_data = 0
        else :
            print("PAYLOAD CANT FIND THE TYPE")
        payload["cmd_type"] = p_type
        payload["gate_id"] = gate_id
        payload["union_data"] = union_data
        if util.DEBUG_FLAG:
            if p_type != util.CMD_OCR_RESULT_REQUEST:
                print(f"PAYLOAD MAKE DONE! \nPAYLOAD : {payload}")

        return payload

    def clear(self):
        self.type    = None
        self.payload = None
        self.camera_module.release_camera()

#logger = util.logging.getLogger("MyApp.IF") 
class ErrorHandler:
    def __init__(self,if_cont):
        self.IF_cont =if_cont
        self._error_code = []
        self._error_flg = False
    
    def set_error_code(self,error_code):
        self._error_flg = True
        self._error_code.append(error_code)
        
    def get_error_code(self):
        return self.error_code
    def mqtt_re_connect(self):
        IFCtrl.send_payload(util.COMM_FOR_SERVER,self,util.CMD_DISPLAY_ERROR_CODE)
        count = 0
        while(count < 10):
            IFCtrl.send_payload(util.COMM_FOR_SERVER,self,util.CMD_STARTUP)
            IFCtrl.wait_for_mqtt_msg(util.MQTT_TOPIC_RESPONSE_STARTUP,10)
            count += 1  
            if (IFCtrl.wait_for_mqtt_msg(util.MQTT_TOPIC_RESPONSE_STARTUP,10)):
                return False
        return True
    def uart_re_connect(self):
        IFCtrl.send_payload(util.COMM_FOR_SERVER,self,util.CMD_DISPLAY_ERROR_CODE)
        count = 0
        while(count < 10):
            IFCtrl.send_payload(util.COMM_FOR_STM32,self,util.CMD_RESET)
            IFCtrl.wait_for_mqtt_msg(util.STATUS_SYSTEM_CONNECT,10)
            IF_Cont.send_payload(util.COMM_FOR_STM32 ,self, util.CMD_AVAILABLE_COUNT)
            count += 1
            if (IFCtrl.wait_for_mqtt_msg(util.STATUS_SYSTEM_IDLE,10)):
                return False
        return True

    def chk_error(self):
        if not self._error_flg :
            return False
        # 인터페이스 연결 문제
        # uart 문제, 껏다가 다시 연결
        # mqtt 문제, 서버에 데이터 요청 했는데 response안 온 경우
        # 일단은 이렇게 세개 정도 ???
        if error_flg:
            error_code = self._error_code.pop()
            print(f"[ERROR OCCURED][{error_code}]")

            # uart err
            if error_code >= 0x70 and error_code <= 0x80:
                if error_code == 0x70 :
                    return self.uart_re_connect()
            elif error_code >= 0x80:
                # mqtt connect error
                if error_code  == 0x80 :
                    return self.mqtt_re_connect()
        return False
    def clear(self):
        self.error_code = ""
        self.error_flg = False

class IFCont:
    def __init__(self,entry_gate_ctrl,exit_gate_ctrl):        
        # 2. 공유 상태 변수
        self.entry_gate_ctrl = entry_gate_ctrl
        self.exit_gate_ctrl = exit_gate_ctrl

        # 3. 통신 컨트롤러 초기화 (서로 참조)        
        self.mqtt_ctrl = None
        self.uart_ctrl = None
        
        self.payload_cont = PayloadCont()
        self.error_handler = ErrorHandler(self)
    def start_up(self):
        if util.DEBUG_FLAG == True:
            return self.exit_gate_ctrl.start_up(self)
        
        return self.entry_gate_ctrl.start_up(self)
        
    def which_gate(self,gate_id):
        if util.DEBUG_FLAG:
            return self.exit_gate_ctrl
        if gate_id == util.ENTRY_GATE_ID or gate_id == '0xa':
            return self.entry_gate_ctrl
        elif gate_id == util.EXIT_GATE_ID or gate_id == '0xb':
            return self.exit_gate_ctrl
        

    def notify_uart_msg(self, payload, gate_id):
        cur_gate_ctrl = self.which_gate(gate_id)
        uart_cur_cond = cur_gate_ctrl.get_cur_uart_cond()
        with uart_cur_cond:
            cur_gate_ctrl.uart_payload = payload
            uart_cur_cond.notify_all()
            if util.DEBUG_FLAG:
                payload['gate_id'] = '0xb'
                cur_gate_ctrl.uart_payload = payload
                print(f"[UART][{cur_gate_ctrl.prt_gate()}][UPADTAE] : {payload}")

    def notify_mqtt_msg(self,payload,gate_id):
        cur_gate_ctrl = self.which_gate(gate_id)
        mqtt_cur_cond = cur_gate_ctrl.get_cur_mqtt_cond()
        with mqtt_cur_cond:
            cur_gate_ctrl.mqtt_payload = payload
            mqtt_cur_cond.notify_all()
            if util.DEBUG_FLAG:
                print(f"[MQTT][{cur_gate_ctrl.prt_gate()}][UPADTAE] : {payload}")


    def wait_for_uart_status(self, required_status, gate_id, timeout=8) -> bool:
        cur_gate_ctrl = self.which_gate(gate_id)
        uart_cur_cond = cur_gate_ctrl.get_cur_uart_cond()
        
        print(f"[WAIT][{cur_gate_ctrl.prt_gate()}][UART][{required_status}]")
        status_type = ""
        with uart_cur_cond:
            # while 루프를 사용하여 조건을 확인하고 대기

            while True:        
                uart_payload = cur_gate_ctrl.uart_payload
                if cur_gate_ctrl.uart_payload is None:
                    continue
                elif "status_type" in uart_payload :
                    status_type = int(uart_payload["status_type"],16)
                if status_type == required_status:
                    break
                if (required_status == util.STATUS_VEHICLE_DETECTED):
                    uart_cur_cond.wait()
                else :    
                    is_notified = uart_cur_cond.wait(timeout) 
                    
                    if not is_notified and uart_payload != required_status:
                        print(f"[ERROR][{cur_gate_ctrl.prt_gate()}]: UART Status 대기 중 {timeout}초 타임아웃 발생.")
                        # connect error
                        error_handler.set_error_code(0x70)
                        return False 
                
            print(f"[INFO][{cur_gate_ctrl.prt_gate()}] : USART '{required_status}' 확인 완료.")
            interface.last_payload = uart_payload

            return True 
            
    def wait_for_mqtt_msg(self, topic, gate_id, timeout=20) -> bool:
        cur_gate_ctrl = self.which_gate(gate_id)
        mqtt_cur_cond = cur_gate_ctrl.get_cur_mqtt_cond()
        print(f"[WAIT][{cur_gate_ctrl.prt_gate()}][MQTT_TOPIC] : {topic}")
        comp_topic = ""
        with mqtt_cur_cond:
            while True:
                comp_topic = cur_gate_ctrl.mqtt_payload["topic"]
                is_notified = mqtt_cur_cond.wait(timeout) 
                if comp_topic == topic :
                    break

                # 1. 타임아웃으로 인해 False를 반환한 경우
                if not is_notified and comp_topic != topic:
                    print(f"[ERROR][{cur_gate_ctrl.prt_gate()}]: Mqtt 대기 중 {timeout}초 타임아웃 발생.")
                    # connect error
                    error_handler.set_error_code(0x80)
                    return False # 타임아웃 발생 시 즉시 False 반환
                
            # 3. 조건이 충족되어 while 루프를 빠져나온 경우
            print(f"[INFO][{cur_gate_ctrl.prt_gate()}]: MQTT '{topic}' 확인 완료.")

            return True
            
        
    def set_mqtt_setting(self, bk_addr, bk_port, topics, client_id):
        self.mqtt_ctrl = interface.MqttModule(
                                    bk_addr = bk_addr,
                                    bk_port = bk_port,
                                    topics = topics,
                                    client_id = client_id,
                                    if_cont = self
                                    )
    def set_uart_setting(self, port, baudrate, timeout = 1):
        self.uart_ctrl = interface.UARTModule(port = util.UART_PORT,baudrate = util.UART_BAUDRATE,if_cont = self)
    
    def init_interface(self):
        self.init_uart()
        self.init_mqtt()

    def init_uart(self):
        return self.uart_ctrl.start()

    def init_mqtt(self):
        return self.mqtt_ctrl.connect_mqtt_broker()
    
    def send_payload(self,destination,gate_ctrl,cmd_type):
        if destination == util.COMM_FOR_STM32:
            payload = self.uart_make_frame(util.MSG_TYPE_COMMAND,self.payload_cont.make_payload(gate_ctrl,cmd_type))
            if util.DEBUG_FLAG:
                print(f"[SEND_MSG][STM32][MSG_TYPE][PAYLOAD] -> [{cmd_type}] : [{payload}]") 
            #logger.info(f"[SEND_MSG][STM32][MSG_TYPE][PAYLOAD] -> [{cmd_type}] : [{payload}]") 
            self.uart_ctrl.uart_send_payload(payload)

        elif destination == util.COMM_FOR_SERVER:
            if cmd_type == util.CMD_OCR_RESULT_REQUEST : 
                #logger.info("[SEND_MSG][SERVER][CMD_OCR_RESULT_REQUEST] ->") 
                mqtt_payload = self.payload_cont.make_payload(gate_ctrl,util.CMD_OCR_RESULT_REQUEST)['union_data']

                return self.mqtt_ctrl.mqtt_publish(util.MQTT_TOPIC_REQUEST_OCR, mqtt_payload)
            elif cmd_type == util.CMD_PAYMENT_INFO_REUQEST : 
                #logger.info("[SEND_MSG][SERVER][CMD_PAYMENT_INFO_REUQEST]") 
                mqtt_payload = self.payload_cont.make_payload(gate_ctrl,util.CMD_PAYMENT_INFO_REUQEST)['union_data']

                return self.mqtt_ctrl.mqtt_publish(util.MQTT_TOPIC_REQUEST_FEE_INFO ,mqtt_payload)
            elif cmd_type == util.CMD_STARTUP : 
                #logger.info("[SEND_MSG][SERVER][CMD_PAYMENT_INFO_REUQEST]") 
                mqtt_payload = self.payload_cont.make_payload(gate_ctrl,util.CMD_STARTUP)['union_data']

                return self.mqtt_ctrl.mqtt_publish(util.MQTT_TOPIC_REQUEST_STARTUP ,mqtt_payload)

    def uart_make_frame(self,msg_type,payload):
        # cmd_type(1B) + gate_id (1B) + Payload (union nB)
        cmd_type = payload.get("cmd_type")
        gate_id = payload.get("gate_id")
        union_data = payload.get("union_data")

        if msg_type == util.MSG_TYPE_COMMAND:
            if cmd_type == util.CMD_DISPLAY_PAYMENT_INFO :
                plate_bytes = union_data.get("license_plate").encode('utf-8').ljust(10,b' ') # 문자열을 바이트로 변환
                entry_time = union_data.get("entry_time")
                exit_time = union_data.get("exit_time")
                fee = union_data.get("fee")
                is_paid =  1 if union_data.get("is_paid")  else 0
                discount_applied = 1000
                self._tmp_data = struct.pack('<BB10sIIHBH', cmd_type,gate_id,plate_bytes, entry_time, exit_time, fee, is_paid,discount_applied)
            
            #CMD_GATE_OPEN
            elif cmd_type == util.CMD_GATE_OPEN:
                plate_bytes = union_data.get("license_plate").encode('utf-8').ljust(10,b' ') # 문자열을 바이트로 변환
                self._tmp_data = struct.pack('<BB10s', cmd_type,gate_id,plate_bytes)
            else:
                self._tmp_data = struct.pack('<BBB', cmd_type,gate_id, union_data)


        elif msg_type == util.MSG_TYPE_STATUS:
            pass

        self.uart_set_struct_data()
        if util.DEBUG_FLAG:
            print(f"SUCCESS PACKING FOR UART STRUCT -> {self._data}")

        return self._data   
    
    def uart_set_struct_data(self):
        self._dest  = util.COMM_FOR_STM32

        start_byte1 = 0x55
        start_byte2 = 0xAA
        # except command 
        length      = len(self._tmp_data)
        # cmd type
        msg_type_fr = 0x01
        end_byte    = 0xCC
        checksum    = interface.calculate_checksum(self._tmp_data)
        dynamic_format = f'<BBH B{length}s HB'
        self._data  = struct.pack(
            dynamic_format,
            start_byte1,
            start_byte2,
            length,
            msg_type_fr,
            self._tmp_data,
            checksum,
            end_byte
        )
    # def send_cmd_reset(self,payload):

    def entry_gate_task(self):
        """Entry Gate의 전체 동기적 시퀀스 로직을 실행"""
        gate_ctrl = self.entry_gate_ctrl
        gate_id = gate_ctrl.gate_id()
        print("\n--- [SEQUENCE START: Entry Gate] ---")
        while True:
            retry_cnt = 0 
            self.wait_for_uart_status(util.STATUS_VEHICLE_DETECTED,gate_id)        
            if gate_ctrl.is_garage_full():
                gate_ctrl.gate_full(self)
            else :
                gate_ctrl.ocr_request(self)
                self.wait_for_mqtt_msg(util.MQTT_TOPIC_RESPONSE_OCR,gate_id)
                if gate_ctrl.is_ocr_ok():
                    # 5. Uart로 게이트 OPEN 커맨드 전송
                    gate_ctrl.gate_open(self)
                    self.wait_for_uart_status(util.STATUS_GATE_OPEN,gate_id)
                    self.wait_for_uart_status(util.STATUS_VEHICLE_PASSED,gate_id)
                    gate_ctrl.gate_close(self)           
                else:
                    while retry_cnt < 3:
                        print(f"Retry[{retry_cnt}] : Proccessing...")
                        gate_ctrl.ocr_request(self)
                        retry_cnt += 1
                        self.wait_for_mqtt_msg(util.MQTT_TOPIC_RESPONSE_OCR,gate_id)
                        if gate_ctrl.is_ocr_ok():
                            gate_ctrl.payment_process(self)
                            break
                    
                if retry_cnt == 3:
                    print("ocr Fail!!")

                if not self.error_handler.chk_error():
                    print("YOU SHOULD RE-BOOT")
                    return


    def exit_gate_task(self):
        gate_ctrl = self.exit_gate_ctrl
        gate_id = gate_ctrl.gate_id()
        print("\n--- [SEQUENCE START: Exit Gate] ---")
        while True:
            retry_cnt = 0 
            self.wait_for_uart_status(util.STATUS_VEHICLE_DETECTED,gate_id)                
            gate_ctrl.ocr_request(self)
            self.wait_for_mqtt_msg(util.MQTT_TOPIC_RESPONSE_OCR,gate_id)
            if gate_ctrl.is_ocr_ok():
                gate_ctrl.payment_process(self)
            else:
                while retry_cnt < 3:
                    print(f"Retry[{retry_cnt}] : Proccessing...")
                    gate_ctrl.ocr_request(self)
                    retry_cnt += 1
                    self.wait_for_mqtt_msg(util.MQTT_TOPIC_RESPONSE_OCR,gate_id)
                    if gate_ctrl.is_ocr_ok():
                        gate_ctrl.payment_process(self)
                        break
            if retry_cnt == 3:
                print("ocr Fail!!")
            if not self.error_handler.chk_error():
                print("YOU SHOULD RE-BOOT")
                return

    def stop_interface(self):
        print(f"STOP IF ")
        self.error_handler.clear()
        self.mqtt_ctrl.disconnect()
        self.mqtt_ctrl.loop_stop()
        self.uart_ctrl.stop()
        self.uart_ctrl.join()


    def __del__(self):

        # 객체가 삭제될 때 자동으로 호출됩니다.
        print(f"IFController is Deleted")
        
        




