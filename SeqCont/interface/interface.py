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
        mqtt_payload = gate_ctrl.mqtt_payload()
        
        uart_payload = gate_ctrl.uart_payload()

        mqtt_payload["gate_id"] = gate_id

        timestamp = int(time.time())

        # For server 
        if p_type == util.CMD_STARTUP:
            union_data = {"startUp" : True}
        elif p_type ==  util.CMD_OCR_RESULT_REQUEST:
            license_plate_img = self.camera_module.capture_images()
            union_data = {"gate_id" : gate_id, "timestamp" :  timestamp ,"img": license_plate_img}
        elif p_type ==  util.CMD_PAYMENT_INFO_REUQEST:
            union_data = {"gate_id" : gate_id, "license_plate" :  mqtt_payload["license_plate"] , "timestamp" :  timestamp}
        elif p_type ==  util.CMD_PAYMENT_RESULT:
            union_data = {"gate_id" : gate_id, "license_plate" :  mqtt_payload["license_plate"] , "is_paid" :  mqtt_payload["is_paid"]}
        # For stm32 
        elif p_type ==  util.CMD_GATE_OPEN:
            union_data = {"license_plate" : mqtt_payload["license_plate"]}
        elif p_type == util.CMD_DISPLAY_PAYMENT_INFO:
            union_data = mqtt_payload["available_count"]
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
    
    def chk_error(self):
        if not self._error_flg :
            return False
        # 인터페이스 연결 문제
        # uart 문제, 껏다가 다시 연결
        # mqtt 문제, 서버에 데이터 요청 했는데 response안 온 경우
        # 일단은 이렇게 세개 정도 ???
        
        ret = False
        # while(len(self._error_code)):
        #     error_code = self._error_code.pop(0)
        #     # uart err
        #     if error_code >= 0x70 and error_code <= 0x80:
        #         if error_code == 0x70 :
        #             # stm32 sys reset
        #             # stm32 only one reset but mqtt is three reset? 
        #             # payload = self.IFCtrl.uart_make_frame(util.MSG_TYPE_COMMAND,util.CMD_RESET,None)
        #             print("ERROR")
        #             IFCtrl.send_payload(util.COMM_FOR_STM32,self,util.CMD_RESET)
        #             IFCtrl.init_interface()
        #         elif error_code == 0x81:
                    
        #             pass
        #             # ret = retry(self.IFCtrl.init_interface())

        #         elif error_code == 0x82:
        #             pass
        #             # ret = retry(self.IFCtrl.init_interface())
        #     # mqtt err
        #     elif error_code >= 0x80:
        #         # mqtt connect error
        #         pass
        #         if error_code  == 0x81 :
        #             pass
        #             # ret = retry(self.IFCtrl.init_interface())
        #     if ret : 
        #         self.clear()
        #     else :
        #         # SYSTEM RESET
        #         IFCtrl.send_payload(util.COMM_FOR_STM32,self,util.CMD_RESET)

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
    def start_up(self,):
        return self.entry_gate_ctrl.start_up()
        # self.exit_gate_ctrl.start_up()
        
    def is_etnry_gate(self,gate_id):
        if gate_id == util.TMP_ENTRY_GATE_ID:
            return self.entry_gate_ctrl
        elif gate_id == util.TMP_EXIT_GATE_ID:
            return self.exit_gate_ctrl
        
    def notify_uart_msg(self, payload, gate_id):
        cur_gate_ctrl = self.is_etnry_gate(gate_id)
        uart_cur_cond = cur_gate_ctrl.get_cur_uart_cond()
        with uart_cur_cond:
            cur_gate_ctrl.uart_payload(payload)
            uart_cur_cond.notify_all()
                
    def notify_mqtt_msg(self,payload,gate_id):
        cur_gate_ctrl = self.is_etnry_gate(gate_id)
        uart_cur_cond = cur_gate_ctrl.get_cur_uart_cond()
        with uart_cur_cond:
            cur_gate_ctrl.mqtt_payload(payload)
            uart_cur_cond.notify_all()
            
    def wait_for_uart_status(self, required_status, gate_id, timeout=5) -> bool:
        cur_gate_ctrl = self.is_etnry_gate(gate_id)
        uart_cur_cond = cur_gate_ctrl.get_cur_uart_cond()
        uart_payload = cur_gate_ctrl.uart_payload()
        status_type = uart_payload["status_type"]
        print(f"[WAIT][{gate_id}] status : {status_type}")

        with uart_cur_cond:
            # while 루프를 사용하여 조건을 확인하고 대기
            while status_type != required_status:                
                if (required_status == util.STATUS_VEHICLE_DETECTED):
                    uart_cur_cond.wait()
                else :    
                    is_notified = uart_cur_cond.wait(timeout) 
                    
                    if not is_notified and uart_payload != required_status:
                        print(f"[ERROR] Gate {gate_id}: UART Status 대기 중 {timeout}초 타임아웃 발생.")
                        
                        cur_gate_ctrl.current_uart_status = None
                        return False 
                
            print(f"[INFO] Gate {gate_id}: UART Status '{required_status}' 확인 완료.")
            
            return True 
            
    def wait_for_mqtt_response(self, topic, gate_id, timeout=5) -> bool:
        """순서 4: Mqtt 응답을 동기적으로 대기"""
        cur_gate_ctrl = self.is_etnry_gate(gate_id)
        mqtt_cur_cond = cur_gate_ctrl.get_cur_mqtt_cond()
        mqtt_payload = cur_gate_ctrl.mqtt_payload()
        print(f"[WAIT][{gate_id}] MQTT_TOPIC : {topic}")

        with mqtt_cur_cond:
            while topic != mqtt_payload["topic"]:
                is_notified = mqtt_cur_cond.wait(timeout) 
                
                # 1. 타임아웃으로 인해 False를 반환한 경우
                if not is_notified and cur_gate_ctrl.current_uart_status != topic:
                    print(f"[ERROR] Gate {gate_id}: Mqtt 대기 중 {timeout}초 타임아웃 발생.")
                    
                    # 💡 대기 완료 후 상태 소비 및 리셋 (선택적)
                    cur_gate_ctrl.current_uart_status = None
                    return False # 타임아웃 발생 시 즉시 False 반환
                
            # 3. 조건이 충족되어 while 루프를 빠져나온 경우
            print(f"[INFO] Gate {gate_id}: UART Status '{topic}' 확인 완료.")

            return True
            
            
    def set_error(self,error_code):
        self.error_handler.set_error_code(error_code)
        
    def set_mqtt_setting(self, bk_addr, bk_port, topics, client_id):
        self.mqtt_ctrl = interface.MqttModule(
                                    bk_addr = bk_addr,
                                    bk_port = bk_port,
                                    topics = topics,
                                    client_id = client_id,
                                    if_cont = self
                                    )
    def set_uart_setting(self, port, baudrate, queue, timeout = 1):
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
            mqtt_payload = self.payload_cont.make_payload(gate_ctrl,util.CMD_OCR_RESULT_REQUEST)['union_data']
            if cmd_type == util.CMD_OCR_RESULT_REQUEST : 
                #logger.info("[SEND_MSG][SERVER][CMD_OCR_RESULT_REQUEST] ->") 
                return self.mqtt_ctrl.mqtt_publish(util.MQTT_TOPIC_REQUEST_OCR, mqtt_payload)
            elif cmd_type == util.CMD_PAYMENT_INFO_REUQEST : 
                #logger.info("[SEND_MSG][SERVER][CMD_PAYMENT_INFO_REUQEST]") 
                return self.mqtt_ctrl.mqtt_publish(util.MQTT_TOPIC_REQUEST_FEE_INFO ,mqtt_payload)

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
            
            self.wait_for_uart_status(util.STATUS_VEHICLE_DETECTED,gate_id)                

            gate_ctrl.ocr_request(self)
            
            self.wait_for_mqtt_response(util.MQTT_TOPIC_RESPONSE_OCR,gate_id)
            
            if gate_ctrl.is_ocr_ok():
                # 5. Uart로 게이트 OPEN 커맨드 전송
                gate_ctrl.gate_open(self)
                self.wait_for_uart_status(util.STATUS_VEHICLE_PASSED,gate_id)
                gate_ctrl.gate_close(self)           
            else:
                retry_cnt = 0 
                while retry_cnt < 3:
                    print(f"Retry[{retry_cnt}] : Proccessing...")
                    gate_ctrl.ocr_request(self)
                    retry_cnt += 1
                    self.wait_for_mqtt_response(util.MQTT_TOPIC_RESPONSE_OCR,gate_id)
                    if gate_ctrl.is_ocr_ok():
                        gate_ctrl.payment_process(self)
                        break
                
            if retry_cnt == 3:
                print("ocr Fail!!")

        

    def exit_gate_task(self):
        """Entry Gate의 전체 동기적 시퀀스 로직을 실행"""
        gate_ctrl = self.exit_gate_ctrl
        gate_id = gate_ctrl.gate_id()

        while True:
            # 1. & 2. Uart 상태(차량 감지)를 동기적으로 대기
            self.wait_for_uart_status(util.STATUS_VEHICLE_DETECTED,gate_id)                
                
            gate_ctrl.ocr_request(self)

            self.wait_for_mqtt_response(util.MQTT_TOPIC_RESPONSE_OCR,gate_id)
            
            if gate_ctrl.is_ocr_ok():
                gate_ctrl.payment_process(self)
            else:
                
                retry_cnt = 0 
                while retry_cnt < 3:
                    print(f"Retry[{retry_cnt}] : Proccessing...")
                    gate_ctrl.ocr_request(self)
                    retry_cnt += 1
                    self.wait_for_mqtt_response(util.MQTT_TOPIC_RESPONSE_OCR,gate_id)
                    if gate_ctrl.is_ocr_ok():
                        gate_ctrl.payment_process(self)
                        break
                
            if retry_cnt == 3:
                print("ocr Fail!!")


    def __del__(self):

        # 객체가 삭제될 때 자동으로 호출됩니다.
        print(f"IFController is Deleted")
        
    def stop_interface(self):
        print(f"STOP IF ")

        self.error_handler.clear()
        self.mqtt_ctrl.disconnect()
        self.mqtt_ctrl.loop_stop()
        self.uart_ctrl.stop()
        self.uart_ctrl.join()
        




