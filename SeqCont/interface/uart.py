
#
# uart_module.py
#
import serial
import util
import threading
import struct
import time
import globals 
from collections import deque


last_payload = None

#logger = util.logging.getLogger("MyApp.UART") 


STATUS_PAYLOAD_SIZE         = 6

def calculate_checksum(_payload_bytes: bytes) -> int:
    checksum = 0
    for byte in _payload_bytes:
        checksum += byte
    
    # 16비트(0x0000 ~ 0xFFFF) 값으로 제한
    return checksum & 0xFFFF


def is_equal_payload(last_payload, cur_payload):
    if last_payload == cur_payload:
        return True
    else :
        return False
    
def _parse_payload(msg_type: int, _payload_bytes: bytes) -> dict:
    ety_gate_ctrl = globals.ety_gate_ctrl
    exit_gate_ctrl = globals.exit_gate_ctrl

    parsed_payload = {"main_msg_type": msg_type} # UartMessageFrame_t의 msg_type
    
    status_str = "[STM32]"

    if msg_type == util.MSG_TYPE_STATUS:
        # status_t + union = 6 Byte
        if len(_payload_bytes) < STATUS_PAYLOAD_SIZE:
            return {"error": "Incomplete STATUS payload"}

        STATUS_PAYLOAD_FORMAT = '<BBI' # 1B(TYPE) + 1B(GATE_ID) + 4B(UNION)
        status_type, status_gate_id, status_payload = struct.unpack(STATUS_PAYLOAD_FORMAT, _payload_bytes[:STATUS_PAYLOAD_SIZE])
        parsed_payload["status_type"] = hex(status_type)
        parsed_payload["gate_id"] = hex(status_gate_id)
        if hex(status_gate_id) == util.TMP_ENTRY_GATE_ID:
            sys_ctrl = ety_gate_ctrl
        elif hex(status_gate_id) == util.TMP_EXIT_GATE_ID :
            sys_ctrl = exit_gate_ctrl
        else :
            print("parsed Error Occured) UART_GATE_ID_ERROR")
        #Get union data
        
        status_str += "[STATUS]"
        if status_type == util.STATUS_ERROR_CODE:
            # sys_ctrl.error_handler.set_error_code(msg_data["error_code"])
            print(status_payload)
            sys_ctrl.set_cur_status(util.STATUS_ERROR_CODE)
        else : 
            print(f"Can't find status list state: {status_type}")
            return False

    else:
        parsed_payload["error"] = "Unknown main message type for Payload Interpretation"
    print(status_str)

    return parsed_payload

class UartMsgFrame():
    def __init__(self,if_cont):
        self.if_cont = if_cont # 파싱된 메시지를 저장할 큐
        self._current_parse_state = util.STATE_WAIT_START_BYTES
        self._receive_buffer = bytearray()
        self._frame_length = 0
        self._msg_type_frame = 0
        self._payload_bytes = bytearray()
        self._frame_checksum = 0
        self._received_cmd_flg = False

    def process_incoming_byte(self, byte: int):
        """
        수신된 바이트를 파싱 상태 머신에 따라 처리합니다.
        """
        if self._current_parse_state == util.STATE_WAIT_START_BYTES:
            if byte == util.UART_START_BYTE1:
                self._receive_buffer = bytearray([byte]) # 버퍼 초기화 및 첫 바이트 저장
                self._current_parse_state = util.STATE_READ_LENGTH # 다음 상태로 전이
            else:
                self._receive_buffer.clear() # 잘못된 시작 바이트, 버퍼 클리어
                # print(f"[UART][START_BIT][FAIL]  (BYTE -> {byte})")
                #logger.exception(f"[UART][START_BIT][FAIL]  (BYTE -> {byte})")
                
        elif self._current_parse_state == util.STATE_READ_LENGTH:
            self._receive_buffer.append(byte)
            if len(self._receive_buffer) == 1 + 1 + 2: # start1 + start2 + length (4바이트)
                # 길이 필드 (2바이트)를 읽어와서 페이로드 길이 파악
                # length 필드는 start1, start2 다음이므로, 버퍼의 2,3번째 바이트
                self._frame_length = struct.unpack('<H', self._receive_buffer[2:4])[0]
                
                if self._frame_length > util.UART_MAX_PAYLOAD_SIZE:
                    self._reset_parser_state() # 오류 시 초기 상태로 복귀
                else:
                    self._current_parse_state = util.STATE_READ_MSG_TYPE

        elif self._current_parse_state == util.STATE_READ_MSG_TYPE:
            self._receive_buffer.append(byte)
            if len(self._receive_buffer) == 1 + 1 + 2 + 1: # start1+start2+length+msg_type (5바이트)
                self._msg_type_frame = self._receive_buffer[4] # msg_type은 버퍼의 4번째 바이트
                self._payload_bytes.clear() # 새 페이로드 시작
                self._current_parse_state = util.STATE_READ_PAYLOAD

        elif self._current_parse_state == util.STATE_READ_PAYLOAD:
            self._receive_buffer.append(byte)
            self._payload_bytes.append(byte)
            # if len(self._payload_bytes) == self._frame_length: # 예상 페이로드 길이에 도달
            if len(self._payload_bytes) == 64: # 예상 페이로드 길이에 도달
                self._current_parse_state = util.STATE_READ_CHECKSUM

        elif self._current_parse_state == util.STATE_READ_CHECKSUM:
            self._receive_buffer.append(byte)

            if len(self._receive_buffer) == 1 + 1 + 2 + 1 + 64 + 2: # 헤더+페이로드+체크섬

            # if len(self._receive_buffer) == 1 + 1 + 2 + 1 + self._frame_length + 2: # 헤더+페이로드+체크섬
                self._frame_checksum = struct.unpack('<H', self._receive_buffer[-2:])[0] # 마지막 2바이트가 체크섬
                self._current_parse_state = util.STATE_READ_END_BYTE

        elif self._current_parse_state == util.STATE_READ_END_BYTE:
            if byte == util.UART_END_BYTE:
                self._receive_buffer.append(byte) # 종료 바이트도 버퍼에 추가
                self._handle_complete_frame() # 완전한 프레임 처리

            else:
                print(f"Error: Invalid end byte {hex(byte)}. Expected {hex(util.UART_END_BYTE)}. Resetting.")
                self._reset_parser_state() # 오류 시 초기 상태로 복귀

    def _handle_complete_frame(self):
        """
        완전하게 수신된 프레임을 처리하고, 큐에 추가합니다.
        """
        global last_payload

        # 체크섬 검증
        calculated_checksum = calculate_checksum(self._payload_bytes)
        if calculated_checksum != self._frame_checksum:
            print(f"Checksum mismatch! Calculated: {hex(calculated_checksum)}, Received: {hex(self._frame_checksum)}")
            self._reset_parser_state()
            return

        # 페이로드 해석 (이전 답변의 _parse_payload 함수 사용)
        parsed_payload = _parse_payload(self._msg_type_frame, self._payload_bytes)

        if not is_equal_payload(last_payload,parsed_payload) :#or True:
            self.if_cont.notify_uart_msg(parsed_payload,parsed_payload["gate_id"])

        last_payload = parsed_payload

        time.sleep(0.1) # 1ms

        self._reset_parser_state() # 다음 메시지를 위해 상태 리셋

    def _reset_parser_state(self):
        """파서 상태를 초기화합니다."""
        self._current_parse_state = util.STATE_WAIT_START_BYTES
        self._receive_buffer.clear()
        self._frame_length = 0
        self._msg_type_frame = 0
        self._payload_bytes.clear()
        self._frame_checksum = 0


# --- 5. UART 수신 스레드 클래스 ---
class UARTModule(threading.Thread):
    def __init__(self, port, baudrate, if_cont):
        super().__init__()
        self._ser = None
        self.port = port
        self.baudrate = baudrate
        self._running = True
        self._connect = False
        self.if_cont = if_cont # 파싱된 메시지를 저장할 큐
        self._msg_fr = UartMsgFrame(if_cont)

    def is_connected(self):
        return self._connect

    def uart_send_payload(self,payload):
        if self._ser is None:
            return 0 
        try:    
            self._ser.write(payload)
        except serial.SerialException as e:
            print(f"error occoured :{e}")
        finally:
            pass
            # self.stop()
    def run(self):
        try:
            self._ser = serial.Serial(self.port, self.baudrate, timeout=0.1) # 짧은 타임아웃
            print(f"UART connection established on {self.port}")
            self._connect = True
            while self._running: 
                byte = self._ser.read(1)
                # 1바이트씩 읽기 (타임아웃 설정으로 블로킹
                if byte:
                    self._msg_fr.process_incoming_byte(byte[0]) # 바이트 처리 상태 머신 호출
                else:
                    # 데이터가 없으면 잠시 대기 (CPU 부하 줄이기)
                    time.sleep(0.1) # 1ms
            
        except Exception as e:
            print(f"UART Error: {e}")            
            # 4. 재연결 쿨다운 (시스템 부하 방지)
        finally:
            if self._ser and self._ser.is_open:
                self._ser.close()
                print("UART connection closed.")      
                self._connect = False

    def err_handler(self):
        pass
    def re_connect(self):
        pass
    def stop(self):
        self._running = False
        self._connect = False
        print("Stopping UART Receiver thread...")