import interface
def iF_init():
    TOPIC_LIST = [util.MQTT_TOPIC_REQUEST_OCR,util.MQTT_TOPIC_REQUEST_FEE_INFO, util.MQTT_TOPIC_RESPONSE_OCR,util.MQTT_TOPIC_RESPONSE_FEE_INFO]
    recv_msg_queue = queue.Queue() 

    # I/F Cont test 
    t_if_cont = interface.IFCont()

    interface_cont.set_uart_setting(port = util.UART_PORT,baudrate = util.UART_BAUDRATE,queue = recv_msg_queue)
    interface_cont.set_mqtt_setting(bk_addr = util.MQTT_BROKER_ADDRESS_TMP,bk_port = util.MQTT_BROKER_PORT,topics = TOPIC_LIST,client_id = util.MQTT_CLIENT_ID,queue =recv_msg_queue)

    interface_cont.init_interface()
    return interface_cont
interface_cont = iF_init()

# for stm32
def send_gate_open_cmd():
    global interface_cont
def send_gate_close_cmd():
    global interface_cont

def send_display_payment_info_cmd():
    global interface_cont

def send_display_payment_done_cmd():
    global interface_cont

def send_display_payment_fail_cmd():
    global interface_cont

def send_reset_cmd():
    global interface_cont

def send_display_err():
    global interface_cont



# for server
def send_payment_info_req():
    global interface_cont

def send_payment_result_response():
    global interface_cont




import util
# context test 
t_gate_context = util.GateCtrl()
JN_STARTUP                    = 0x29
JN_IDLE                       = 0x30
JN_OCR_REQUESTED              = 0x32
JN_OCR_OK                     = 0x33
JN_OCR_NG                     = 0x34
JN_CAR_INFO_REQUEST           = 0x35
JN_PAYMENT                    = 0x36
JN_PAYMENT_DONE               = 0x37

def set_start_up():
    global t_gate_context
    t_gate_context._state = util.JN_STARTUP
def set_car_detect():
    global t_gate_context
    t_gate_context._state = util.JN_STARTUP

def set_ocr_reqest():
    global t_gate_context
    t_gate_context._state = util.JN_OCR_REQUESTED

def set_ocr_ng():
    global t_gate_context
    t_gate_context._state = util.JN_OCR_NG

def set_ocr_ok_door_open():
    global t_gate_context
    t_gate_context._state = util.JN_OCR_OK

def set_ocr_ok_fee_inof_req():
    global t_gate_context
    t_gate_context._state = util.JN_CAR_INFO_REQUEST


import sensorModule


t_camera_module = sensorModule.cameraModule()



