ENTRY_GATE_ID                               = 10
EXIT_GATE_ID                                = 11

COMM_FOR_SERVER                             = 0x90
COMM_FOR_STM32                              = 0x91


#3.CONSTANT - MQTT
MQTT_BROKER_ADDRESS                         = "172.30.1.85"
MQTT_BROKER_PORT                            = 1883
MQTT_CLIENT_ID                              = "MQTT-Receiver-Client"

MQTT_TOPIC_REQUEST_OCR                      = "parking/request/ocr"
MQTT_TOPIC_REQUEST_FEE_INFO                 = "parking/request/feeInfo"
MQTT_TOPIC_REQUEST_AVAILABLE_COUNT          = "parking/request/available_count"

MQTT_TOPIC_RESPONSE_OCR                     = "parking/response/ocr"
MQTT_TOPIC_RESPONSE_FEE_INFO                = "parking/response/feeInfo"
MQTT_TOPIC_RESPONSE_FEE_RESULT              = "parking/response/feeResult"
MQTT_TOPIC_RESPONSE_AVAILABLE_COUNT         = "parking/response/available_count"

INIT_AVAILABLE_COUN = 10
#3.CONSTANT - UART
UART_PORT                                   = '/dev/ttyACM0'
UART_BAUDRATE                               = 115200
#3.CONSTANT - UART - BYTE FRAME
UART_START_BYTE1                            = 0x55
UART_START_BYTE2                            = 0xAA
UART_END_BYTE                               = 0xCC
UART_MAX_PAYLOAD_SIZE                       = 64
#3.CONSTANT - UART MSG TYPE
MSG_TYPE_COMMAND                            = 0x01
MSG_TYPE_STATUS                             = 0x02
MSG_TYPE_RESPONSE                           = 0x03

#3.CONSTANT - UART CMD TYPE
CMD_GATE_OPEN                               = 0x10         
CMD_GATE_CLOSE                              = 0x11       
CMD_DISPLAY_PAYMENT_INFO                    = 0x12
CMD_DISPLAY_PAYMENT_DONE                    = 0x13
CMD_DISPLAY_PAYMENT_FAIL                    = 0x14
CMD_REQUEST_STM32_STATUS                    = 0x15
CMD_RESET                                   = 0x16
CMD_AVAILABLE_COUNT                         = 0x17
CMD_GARAGE_FULL                             = 0x18
# FOR SERVER CMD
CMD_OCR_RESULT_REQUEST                      = 0x40
CMD_PAYMENT_INFO_REUQEST                    = 0x41
CMD_PAYMENT_RESULT                          = 0x42
CMD_DISPLAY_ERROR_CODE                      = 0x43
CMD_AVAILABLE_COUNT_REQUEST                 = 0x44

#3.CONSTANT - UART STATUS TYPE
STATUS_SYSTEM_CONNECT                       = 0x19# 시스템 대기 중
STATUS_SYSTEM_IDLE                          = 0x20# 시스템 대기 중
STATUS_VEHICLE_DETECTED                     = 0x21# 차량 감지됨
STATUS_GATE_OPEN                            = 0x22# 게이트 열림
STATUS_GATE_CLOSED                          = 0x23# 게이트 닫힘
STATUS_VEHICLE_LEFT                         = 0x24
STATUS_DISPLAY_PAYMENT                      = 0x25
STATUS_DISPLAY_PAYMENT_DONE                 = 0x26
STATUS_DISPLAY_PAYMENT_FAIL                 = 0x27
STATUS_VEHICLE_PASSED                       = 0x28
STATUS_ERROR_CODE                           = 0xFF# 오류 발생
#3.CONSTANT - JSNN STATE
JN_STARTUP                    = 0x29
JN_IDLE                       = 0x30
JN_OCR_REQUESTED              = 0x32
JN_OCR_OK                     = 0x33
JN_OCR_NG                     = 0x34
JN_CAR_INFO_REQUEST           = 0x35
JN_PAYMENT                    = 0x36
JN_PAYMENT_DONE               = 0x37

#3.CONSTANT - UART DECODE STEP
STATE_WAIT_START_BYTES = 0
STATE_READ_LENGTH      = 1
STATE_READ_MSG_TYPE    = 2
STATE_READ_PAYLOAD     = 3
STATE_READ_CHECKSUM    = 4
STATE_READ_END_BYTE    = 5
STATE_FRAME_COMPLETE   = 6 # 완전한 프레임이 수신되어 파싱 대기 중

UART_FRAME_HEADER_FORMAT = '<BBH B' # start1, start2, length, msg_type (5 bytes)
UART_FRAME_FOOTER_FORMAT = '<H B'   # checksum, end_byte (3 bytes)

GATE_CLOSE_TIME          = 5
DEBUG_FLAG = False


#ERROR CODE UART
ERROR_UART_CONNECT = 0x70

INIT_AVAILABLE_COUNT = 10
#ERROR CODE MQTT
ERROR_MQTT_CONNECT = 0x80
 
EXIT_GATE_MODE = True