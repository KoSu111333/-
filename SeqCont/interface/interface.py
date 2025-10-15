import interface
import struct
import sensorModule
import util
import time


def parse_mqtt_msg(sys_ctrl,received_msg):
    topic = received_msg.get("topic")
    msg_data = received_msg.get("payload")
    status_str = "[SERVER]"

    if topic == util.MQTT_TOPIC_RESPONSE_OCR and sys_ctrl._state == util.JN_OCR_REQUESTED:
        if msg_data["success"]:
            sys_ctrl.set_cur_status(util.JN_OCR_OK)
            status_str += "[JN_OCR_OK]"

        else:
            sys_ctrl.set_cur_status(util.JN_OCR_NG)
            status_str += "[JN_OCR_NG]"

        sys_ctrl.car_info.set_car_info(msg_data)

    elif topic == util.MQTT_TOPIC_RESPONSE_FEE_INFO:
        if sys_ctrl._state == util.JN_PAYMENT and msg_data["success"]:
            sys_ctrl.set_cur_status(util.JN_PAYMENT_DONE)
            status_str += "[JN_OCR_NG]" 
        else:
            sys_ctrl.set_cur_status(util.JN_PAYMENT)
            status_str += "[JN_PAYMENT]"     
        sys_ctrl.car_info.set_car_info(msg_data)
    print(status_str)
    return True

def parse_uart_msg(sys_ctrl,received_payload):
        status_str = "[STM32]"
        msg_type = received_payload.get("main_msg_type")
        status_type = int(received_payload.get("status_type"),16)
        msg_data = received_payload.get("status_data")
        if msg_type  == util.MSG_TYPE_STATUS:
            status_str += "[STATUS]"
            if status_type == util.STATUS_SYSTEM_CONNECT:
                status_str += "[STATUS_SYSTEM_STARTUP]"
                sys_ctrl.set_cur_status(util.JN_STARTUP)
            elif status_type == util.STATUS_SYSTEM_IDLE:
                status_str += "[STATUS_SYSTEM_IDLE]"
                sys_ctrl.set_cur_status(util.JN_IDLE)
            elif status_type == util.STATUS_VEHICLE_DETECTED:
                status_str += "[STATUS_CAR_DETECT]"
                sys_ctrl.gate_state.set_state_car_detect()
            elif status_type == util.STATUS_GATE_OPEN:
                status_str += "[STATUS_GATE_OPEN]"
                sys_ctrl.gate_state.set_state_gate_open()
            elif status_type == util.STATUS_GATE_CLOSED:
                status_str += "[STATUS_GATE_CLOSE]"
                sys_ctrl.gate_state.set_state_gate_close()
                sys_ctrl.set_cur_status(util.STATUS_GATE_CLOSED)
            elif status_type  == util.STATUS_VEHICLE_LEFT:
                status_str += "[STATUS_CAR_LEFT]"    
                sys_ctrl.gate_state.set_state_car_left()
                sys_ctrl.set_cur_status(util.JN_IDLE)
            elif status_type == util.STATUS_DISPLAY_PAYMENT:
                status_str += "[STATUS_DISPLAY_PAYMENT]"    
                sys_ctrl.set_cur_status(util.STATUS_DISPLAY_PAYMENT)
            elif status_type == util.STATUS_DISPLAY_PAYMENT_FAIL:
                status_str += "[STATUS_DISPLAY_PAYMENT_FAIL]"    
                sys_ctrl.set_cur_status(util.STATUS_DISPLAY_PAYMENT_FAIL)
            elif status_type == util.STATUS_VEHICLE_PASSED:
                status_str += "[STATUS_VEHICLE_PASSED]"    
                sys_ctrl.gate_state.set_state_car_left()
            elif status_type == util.STATUS_ERROR_CODE:
                sys_ctrl.error_handler.set_error_code(msg_data["error_code"])
                sys_ctrl.set_cur_status(util.STATUS_ERROR_CODE)
            else : 
                print(f"Can't find status list state: {status_type}")
                return False
        print(status_str)
        return True
def parse_received_data(received_msg,entry_gate_ctrl,exit_gate_ctrl):
    # received_msg = test_payload
    destination = received_msg["dest"]
    received_payload = received_msg["payload"]
    if destination is None or received_payload is None:
        return False
    status_gate_id = received_payload.get("gate_id")
    # 0xa -> 10진수로 바꿔서 util 에 있는거랑 if문 해야됨
    if status_gate_id == "0xa" or status_gate_id == 10:#f"{util.TMP_ENTRY_GATE_ID}":
        sys_ctrl = entry_gate_ctrl
    elif status_gate_id == "0xb" or status_gate_id == 10:#f"{util.TMP_EXIT_GATE_ID}":
        sys_ctrl = exit_gate_ctrl
    else :
        return False
    if destination == util.COMM_FOR_STM32:
        if(not parse_uart_msg(sys_ctrl,received_payload)):
            return False
    elif destination == util.COMM_FOR_SERVER:
        if(not parse_mqtt_msg(sys_ctrl,received_msg)):
            return False

    return True    
    #received from server

class PayloadCont:
    def __init__(self):
        self.camera_module = sensorModule.cameraModule()
        self.camera_module.init_camera()
    def make_payload(self,sys_context,p_type):
        print(f"PAYLOAD MAKE START")
        payload = {}
        union_data ={}
        gate_id = sys_context.gate_state.get_gate_ID()
        car_dict= sys_context.car_info.get_car_info()
        car_dict["gate_id"] = gate_id

        timestamp = int(time.time())

        # For server 
        if p_type ==  util.CMD_OCR_RESULT_REQUEST:
            license_plate_img = self.camera_module.capture_images()
            union_data = {"gate_id" : gate_id, "timestamp" :  timestamp ,"img": license_plate_img}
        elif p_type ==  util.CMD_PAYMENT_INFO_REUQEST:
            union_data = {"gate_id" : gate_id, "license_plate" :  car_dict["license_plate"] , "timestamp" :  timestamp}
        elif p_type ==  util.CMD_PAYMENT_RESULT:
            union_data = {"gate_id" : gate_id, "license_plate" :  car_dict["license_plate"] , "is_paid" :  car_dict["is_paid"]}
        # For stm32 
        elif p_type ==  util.CMD_GATE_OPEN:
            union_data = {"license_plate" : car_dict["license_plate"]}
        elif p_type == util.CMD_DISPLAY_PAYMENT_INFO:
            union_data = car_dict
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
        if p_type != util.CMD_OCR_RESULT_REQUEST:
            print(f"PAYLOAD MAKE DONE! \nPAYLOAD : {payload}")

        return payload

    def clear(self):
        self.type    = None
        self.payload = None
        self.camera_module.release_camera()

#logger = util.logging.getLogger("MyApp.IF") 
class ErrorHandler:
    def __init__(self):
        self._error_code = []
        self._error_flg = False
    
    def set_error_code(self,error_code):
        self._error_flg = True
        self._error_code.append(error_code)
        
    def get_error_code(self):
        return self.error_code

    def chk_error(self,IFCtrl):
        if not len(self._error_flg) :
            return False
        # 인터페이스 연결 문제
        # uart 문제, 껏다가 다시 연결
        # mqtt 문제, 서버에 데이터 요청 했는데 response안 온 경우
        # 일단은 이렇게 세개 정도 ???
        
        ret = False
        while(len(self._error_code)):
            error_code = self._error_code.pop(0)
            # uart err
            if error_code >= 0x70 and error_code <= 0x80:
                if error_code == 0x70 :
                    # stm32 sys reset
                    # stm32 only one reset but mqtt is three reset? 
                    # payload = self.IFCtrl.uart_make_frame(util.MSG_TYPE_COMMAND,util.CMD_RESET,None)
                    IFCtrl.send_payload(util.COMM_FOR_STM32,self,util.CMD_RESET)
                    IFCtrl.init_interface()
                elif error_code == 0x81:
                    
                    pass
                    # ret = retry(self.IFCtrl.init_interface())

                elif error_code == 0x82:
                    pass
                    # ret = retry(self.IFCtrl.init_interface())
            # mqtt err
            elif error_code >= 0x80:
                # mqtt connect error
                pass
                if error_code  == 0x81 :
                    pass
                    # ret = retry(self.IFCtrl.init_interface())
            if ret : 
                self.clear()
            else :
                # SYSTEM RESET
                IFCtrl.send_payload(util.COMM_FOR_STM32,self,util.CMD_RESET)

    def clear(self):
        self.error_code = ""
        self.error_flg = False

class IFCont:
    def __init__(self):
        self.mqtt_ctrl = None
        self.uart_ctrl = None
        self.payload_cont     = PayloadCont()
        self.error_handler = ErrorHandler()

    def confirm_connection(self):
        if self.mqtt_ctrl is None  or self.uart_ctrl is None:
            return False
        if self.uart_ctrl.is_connected():
            return 0x70
        elif self.mqtt_ctrl.is_connected():
            return 0x80
        
        return True
    def set_error(self,error_code):
        self.error_handler.set_error_code(error_code)
        
    def set_mqtt_setting(self, bk_addr, bk_port, topics, client_id, queue):
        self.mqtt_ctrl = interface.MqttModule(
                                    bk_addr = bk_addr,
                                    bk_port = util.MQTT_BROKER_PORT,
                                    topics = topics,
                                    client_id = util.MQTT_CLIENT_ID,
                                    queue = queue
                                    )
    def set_uart_setting(self, port, baudrate, queue, timeout = 1):
        self.uart_ctrl = interface.UARTModule(port = util.UART_PORT,baudrate = util.UART_BAUDRATE,msg_queue = queue)
    
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
            print(f"[SEND_MSG][STM32][MSG_TYPE][PAYLOAD] -> [{cmd_type}] : [{payload}]") 
            #logger.info(f"[SEND_MSG][STM32][MSG_TYPE][PAYLOAD] -> [{cmd_type}] : [{payload}]") 
            self.uart_ctrl.uart_send_payload(payload)

        elif destination == util.COMM_FOR_STM32:
            mqtt_payload = self.payload_cont.make_payload(self,util.CMD_OCR_RESULT_REQUEST)
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

    def stop_interface(self):
        self.error_handler.clear()
        self.mqtt_ctrl.disconnect()
        self.mqtt_ctrl.loop_stop()
        self.uart_ctrl.stop()
        self.uart_ctrl.join()
        
    def __del__(self):
        # 객체가 삭제될 때 자동으로 호출됩니다.
        print(f"IFController is Deleted")
