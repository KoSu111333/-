/*
 * uart.h
 *
 *  Created on: Aug 3, 2025
 *      Author: minseopkim
 */

#ifndef INCLUDE_UART_H_
#define INCLUDE_UART_H_

#include <stdbool.h>
#include <stdint.h>
#include "main.h"
#include "ring_buff.h"
#include "interface.h"

//#include "df.h"
// macro
#define UART_SEND_WITH_PAYLOAD(msg_type_val, payload_struct_var)\
										uart_SendFrame(msg_type_val, &(payload_struct_var), sizeof(payload_struct_var))
#define UART_SEND_WITHOUT_PAYLOAD(msg_type_val)\
										uart_SendFrame(msg_type_val, NULL, 0)

#define UART_MAX_CH				        (1)
#define BUADRATE 				        (115200)
#define UART_CMD_START_BYTE             (0xAA)
#define UART_CMD_END_BYTE               (0xBB)

// 1. 메시지 시작/끝/최대 길이 정의
#define UART_START_BYTE1                (0x55)
#define UART_START_BYTE2                (0xAA)
#define UART_END_BYTE                   (0xCC)
#define UART_MAX_PAYLOAD_SIZE           (64) // 실제 데이터의 최대 길이

// 2. 메시지 타입 열거형 (명령/상태/응답 등을 구분)
typedef enum
{
    MSG_TYPE_COMMAND = 0x01,    // 명령
    MSG_TYPE_STATUS  = 0x02,    // 상태 보고
} MessageType_t;


typedef struct __attribute__((packed))
{
    uint8_t     start_byte1;
    uint8_t     start_byte2;
    uint16_t    length;         // payload_data의 길이 (바이트)
    MessageType_t msg_type;     // 메시지 전체 타입 (명령, 상태, 응답)
    uint8_t     payload_data[UART_MAX_PAYLOAD_SIZE]; // 실제 명령/상태 데이터 (Command_t, Status_t 등을 직렬화하여 여기에 저장)
    uint16_t    checksum;       // CRC16 또는 간단한 체크섬
    uint8_t     end_byte;
} UartMessageFrame_t;


uint32_t uart_Write(const uint8_t *p_data, uint32_t length);
bool uart_SendFrame(MessageType_t msg_t, const void *payload_ptr, uint16_t payload_len);
bool uart_ParseAndValidateFrame(RingBuffer* rb, UartMessageFrame_t* received_frame);
void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart);

#endif /* INCLUDE_UART_H_ */
