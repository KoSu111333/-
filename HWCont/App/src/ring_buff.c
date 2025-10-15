/*
 * ring_buff.c
 *
 *  Created on: Aug 5, 2025
 *      Author: minseopkim
 */


// ring_buffer.c

#include "ring_buff.h"


void RingBuffer_Init(RingBuffer *rb)
{
    rb->head = 0;
    rb->tail = 0;
    rb->size = RING_BUFFER_SIZE;
}

bool RingBuffer_IsEmpty(RingBuffer *rb)
{
    return rb->head == rb->tail;
}

bool RingBuffer_IsFull(RingBuffer *rb)
{
    if (rb == NULL || rb->size == 0)
        return false;  // 혹은 에러 처리

    return ((rb->head + 1) % rb->size) == rb->tail;
}

bool RingBuffer_Write(RingBuffer *rb, uint8_t data)
{

	if (RingBuffer_IsFull(rb))
        return false;
    rb->buffer[rb->head] = data;
    rb->head = (rb->head + 1) % rb->size;
    return true;
}

bool RingBuffer_Read(RingBuffer *rb, uint8_t *data)
{
    if (RingBuffer_IsEmpty(rb))
        return false;

    *data = rb->buffer[rb->tail];
    rb->tail = (rb->tail + 1) % rb->size;
    return true;
}

uint16_t RingBuffer_Available(RingBuffer *rb)
{
    if (rb->head >= rb->tail)
        return rb->head - rb->tail;
    else
        return rb->size - rb->tail + rb->head;
}
