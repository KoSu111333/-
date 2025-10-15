#include <df.h>


extern SystemContext_t entry_sys_context;
extern SystemContext_t exit_sys_context;
extern volatile uint8_t avr_Distance;
extern SonarConfig_t exit_sonar_config;
extern RingBuffer uart_rx_rb;
extern UART_HandleTypeDef huart2;
extern TIM_HandleTypeDef htim3;
extern TIM_HandleTypeDef htim4;

UartMessageFrame_t debug_uart_makeFrame(MessageType_t msg_t, const void *payload_ptr, uint16_t payload_len)
{    
    // 2. Message Frame Construction
    UartMessageFrame_t tx_frame;
    memset(&tx_frame, 0, sizeof(UartMessageFrame_t)); // Good: Initializes all bytes to zero.

    // 3. Header Fields
    tx_frame.start_byte1 = UART_START_BYTE1; // Assigns the first start byte (0x55).
    tx_frame.start_byte2 = UART_START_BYTE2; // Assigns the second start byte (0xAA).
    tx_frame.msg_type    = (uint8_t)msg_t;   // Assigns the message type (e.g., 0x01 for Command).
    tx_frame.length = payload_len;           // Assigns the length of the actual data payload.
    
    // 4. Payload Copy (Serialization)
    if (payload_len > 0)
    {
        // Copies the actual payload data into the frame's payload_data array.
        // This is the serialization step for the payload.
        memcpy(tx_frame.payload_data, payload_ptr, payload_len);
    }
    
    // 5. Checksum Calculation
    // Calculates the checksum based on the payload data.
    // As discussed, consider a more robust CRC (e.g., CRC-16) for real applications.
    tx_frame.checksum = calculate_checksum(tx_frame.payload_data, tx_frame.length);
    
    // 6. End Byte
    tx_frame.end_byte = UART_END_BYTE; // Assigns the end byte (0xCC).
    return tx_frame;
}
// typedef struct
// {
// 	volatile gateID_t		     gate_type;	  // 입차 출차 상태
//     volatile SystemState_t       cur_sys_state;     // 시스템의 현재 상태
//     volatile garageConfig_t*     garage_config;
//     volatile bool                new_uart_cmd_received_flag; // UART로부터 새 명령 수신됨
//     volatile bool                is_vehicle_present;
// }
bool debug_set_available_cnt()
{
    entry_sys_context.garage_config->available_count = 10;
    exit_sys_context.garage_config->available_count = 10;
}

bool debug_set_uart_flg()
{
    entry_sys_context.new_uart_cmd_received_flag = true;
    exit_sys_context.new_uart_cmd_received_flag = true;
}
bool debug_set_detectedCar_flg()
{
    entry_sys_context.is_vehicle_present = true;
    exit_sys_context.is_vehicle_present = true;
}
bool debug_set_cmd_msg(StatusType_t type)
{
    UartMessageFrame_t msg_frame;

    MessageType_t msg_t;
    uint8_t size = sizeof(uart_rx_rb) / sizeof(uint8_t);
    Status_t status_payload;    
    status_payload.type = type;
    status_payload.gate_id = entry_sys_context.gate_type;

    msg_frame = debug_uart_makeFrame(MSG_TYPE_STATUS, &status_payload, sizeof(status_payload));
//    memcpy(uart_rx_rb,&msg_t,sizeof(MessageType_t));
//    status_payload.gate_id = exit_sys_context.gate_type;
//    msg_frame = debug_uart_makeFrame(MSG_TYPE_STATUS, &status_payload, sizeof(status_payload));
//    memcpy(uart_rx_rb,&msg_t,sizeof(MessageType_t));

}

bool test_case1()
{
    debug_set_available_cnt();
    debug_set_uart_flg();

}
bool test_case2()
{
    debug_set_available_cnt();
    debug_set_detectedCar_flg();

}
bool test_case3()
{
    
}
bool test_case4()
{
    
}
bool test_case5()
{
    
}
bool test_case6()
{
    
}
