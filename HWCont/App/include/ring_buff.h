/*
 * ring_buff.h
 *
 *  Created on: Aug 5, 2025
 *      Author: minseopkim
 */

#ifndef INCLUDE_RING_BUFF_H_
#define INCLUDE_RING_BUFF_H_

#include <stdbool.h>
#include <stdint.h>
#include "main.h"

#define RING_BUFFER_SIZE				 (128)

typedef struct {
    uint8_t buffer[RING_BUFFER_SIZE];  // 데이터 저장 공간
    volatile uint16_t head;            // 저장 인덱스 (쓰기)
    volatile uint16_t tail;            // 읽기 인덱스
    uint16_t size;                     // 버퍼 크기
} RingBuffer;

void RingBuffer_Init(RingBuffer *rb);
bool RingBuffer_IsEmpty(RingBuffer *rb);
bool RingBuffer_IsFull(RingBuffer *rb);
bool RingBuffer_Write(RingBuffer *rb, uint8_t data);
bool RingBuffer_Read(RingBuffer *rb, uint8_t *data);
uint16_t RingBuffer_Available(RingBuffer *rb);



#endif /* INCLUDE_RING_BUFF_H_ */
