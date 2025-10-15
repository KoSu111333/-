/*
 * uart.c
 *
 *  Created on: Aug 3, 2025
 *      Author: minseopkim
 */
#include "uart.h"


RingBuffer uart_rx_rb;
extern UART_HandleTypeDef huart2;
extern SystemContext_t g_SystemContext;
extern SystemContext_t entry_sys_context;
extern SystemContext_t exit_sys_context;

extern uint8_t tmp_buffer;
static bool is_uart_conect_flg = false;
static uint16_t calculate_checksum(const uint8_t *data, uint16_t len);

#ifdef __GNUC__
  /* With GCC, small printf (option LD Linker->Libraries->Small printf
     set to 'Yes') calls __io_putchar() */
  #define PUTCHAR_PROTOTYPE int __io_putchar(int ch)
#else
  #define PUTCHAR_PROTOTYPE int fputc(int ch, FILE *f)
#endif /* __GNUC__ */
PUTCHAR_PROTOTYPE
{
  /* Place your implementation of fputc here */
  /* e.g. write a character to the EVAL_COM1 and Loop until the end of transmission */
  HAL_UART_Transmit(&huart2, (uint8_t *)&ch, 1, 0xFFFF);

  return ch;
}


/**
 * @brief 링 버퍼에서 유효한 UART 메시지 프레임을 파싱하고 유효성을 검증합니다.
 * @param rb UART 수신 데이터를 포함하는 링 버퍼 포인터
 * @param received_frame 유효한 프레임 데이터를 저장할 구조체 포인터
 * @return 유효한 프레임 파싱에 성공하면 true, 실패하면 false 반환
 */
static uint16_t calculate_checksum(const uint8_t *data, uint16_t len)
{
    uint16_t sum = 0; // 체크섬을 저장할 변수 (uint16_t로 선언)
    for (uint16_t i = 0; i < len; i++)
    {
        sum += data[i]; // 모든 바이트의 값을 단순히 더함
    }
    return sum; // 최종 합계를 반환
}
/**
 * @brief 링 버퍼에서 유효한 UART 메시지 프레임을 파싱하고 유효성을 검증합니다.
 * @param rb UART 수신 데이터를 포함하는 링 버퍼 포인터
 * @param received_frame 유효한 프레임 데이터를 저장할 구조체 포인터
 * @return 유효한 프레임 파싱에 성공하면 true, 실패하면 false 반환
 */
bool uart_connect_chk(SystemContext_t* sys_context)
{
	Status_t test_payload;

	test_payload.type = STATUS_SYSTEM_STARTUP;
	test_payload.gate_id = sys_context->gate_type;

    UART_SEND_WITH_PAYLOAD(MSG_TYPE_STATUS, test_payload); // Jetson에 보고
    
    return is_uart_conect_flg;
}
/**
 * @brief UART의 데이터를 송신하는 함수입니다.
 * @param p_data UART 송신 데이터를 포함하는 데이터의 포인터
 * @param length 송신 데이터의 길이
 * @return UART 송신에 성공하면 length 반환, 실패하면 False 반환 
 */
uint32_t uart_Write(const uint8_t *p_data, uint32_t length)
{
    uint32_t ret = 0;
    HAL_StatusTypeDef status;

    status = HAL_UART_Transmit(&huart2, p_data, length, HAL_MAX_DELAY);
    if (status == HAL_OK)
    {
        ret = length; // 전송한 바이트 수
    }
	return ret;
}
/**
 * @brief UART 콜백 함수, UART 수신 시 함수 호출
 * @param huart UART handler 구조체의 포인터
 * @return None
 */
void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart)
{
    if (huart->Instance == USART2) {
        RingBuffer_Write(&uart_rx_rb,tmp_buffer);
		HAL_UART_Receive_IT(&huart2, &tmp_buffer, 1);
		if (!is_uart_conect_flg)
        {
			is_uart_conect_flg = true;
        }
		else
		{
			entry_sys_context.new_uart_cmd_received_flag = true;
            exit_sys_context.new_uart_cmd_received_flag = true;
		}
	}
}
/**
 * @brief 링 버퍼에서 유효한 UART 메시지 프레임을 파싱하고 유효성을 검증합니다.
 * @param rb UART 수신 데이터를 포함하는 링 버퍼 포인터
 * @param received_frame 유효한 프레임 데이터를 저장할 구조체 포인터
 * @return 유효한 프레임 파싱에 성공하면 true, 실패하면 false 반환
 */
bool uart_SendFrame(MessageType_t msg_t, const void *payload_ptr, uint16_t payload_len)
{
    bool ret = true; // Issue: This needs to be updated on success.
    
    // 1. Input Validation
    if (huart2.Instance == NULL || (payload_ptr == NULL && payload_len > 0) || payload_len > UART_MAX_PAYLOAD_SIZE)
    {
        return false; // Return false if inputs are invalid.
    }
    
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

    // 7. UART Transmission
    // This is where the entire constructed message frame is sent out via UART.
    // 'uartWrite' is assumed to be your low-level function that interfaces with the UART peripheral.
    uart_Write((uint8_t*)&tx_frame, sizeof(tx_frame));
    // Issue: The 'ret' variable is never updated to true.
	HAL_Delay(200);

    return ret; 

}



bool Uart_protocol_chker(RingBuffer *rb)
{   
    bool ret = false;
    UartMessageFrame_t* tmp_frame;
    uint8_t temp_byte;

    while (RingBuffer_Available(rb) >= sizeof(tmp_frame->start_byte1) + sizeof(tmp_frame->start_byte2))
    {
        RingBuffer_Read(rb, &temp_byte);
        if (temp_byte == UART_START_BYTE1)
        {
            RingBuffer_Read(rb, &temp_byte);
            if (temp_byte == UART_START_BYTE2)
            {
                ret = true;
                break; // 시작 바이트 발견

            }
        }
    }
    return ret;
}
/**
 * @brief 링 버퍼에서 유효한 UART 메시지 프레임을 파싱하고 유효성을 검증합니다.
 * @param rb UART 수신 데이터를 포함하는 링 버퍼 포인터
 * @param received_frame 유효한 프레임 데이터를 저장할 구조체 포인터
 * @return 유효한 프레임 파싱에 성공하면 true, 실패하면 false 반환
 */
bool uart_ParseAndValidateFrame(RingBuffer* rb, UartMessageFrame_t* received_frame)
{

    // 1. 동기화: 시작 바이트(0xAA, 0xBB)를 찾을 때까지 버퍼를 스킵합니다.
    if (!Uart_protocol_chker(rb))
    {
        // start bit, end_bit 형식 에러
        return false;
    }

    // 2. 남은 데이터 길이 확인: 프레임의 최소 길이를 충족하는지 확인합니다.
    // 최소 길이: (length) + (msg_type) + (payload) + (checksum) + (end_byte)
    // 여기서 payload는 길이가 0일 수 있으므로, 최소 길이는 5바이트입니다.
    const uint16_t min_frame_size = sizeof(received_frame->length) + sizeof(received_frame->msg_type) +
                                    sizeof(received_frame->checksum) + sizeof(received_frame->end_byte);
    if (RingBuffer_Available(rb) < min_frame_size)
    {
        return false;
    }

    // 3. 길이(length) 필드 읽기
    // 16비트 길이를 읽기 위해 2바이트를 순차적으로 읽습니다.
    RingBuffer_Read(rb, (uint8_t*)&received_frame->length);
    RingBuffer_Read(rb, ((uint8_t*)&received_frame->length) + 1);

    const uint16_t payload_length = received_frame->length;

    // 4. 전체 프레임 길이 확인
    const uint16_t total_frame_size = sizeof(received_frame->msg_type) + payload_length +
                                      sizeof(received_frame->checksum) + sizeof(received_frame->end_byte);

    if (RingBuffer_Available(rb) < total_frame_size)
    {
        // 전체 프레임이 아직 수신되지 않았으므로 대기
        return false;
    }

    // 5. 프레임의 나머지 부분(msg_type, payload, checksum, end_byte)을 읽습니다.
    RingBuffer_Read(rb, (uint8_t*)&received_frame->msg_type);

    for (uint16_t i = 0; i < payload_length; i++)
    {
        RingBuffer_Read(rb, &received_frame->payload_data[i]);
    }

    RingBuffer_Read(rb, (uint8_t*)&received_frame->checksum);
    RingBuffer_Read(rb, ((uint8_t*)&received_frame->checksum) + 1);

    RingBuffer_Read(rb, &received_frame->end_byte);

    // 6. 유효성 검증
    uint16_t calculated_checksum = calculate_checksum(received_frame->payload_data, payload_length);
    
    if (received_frame->end_byte != 0xCC || received_frame->checksum != calculated_checksum)
    {
        // 유효성 검증 실패 (손상된 데이터)
        return false;
    }
    
    // 7. 모든 검증 성공
    return true;
}
