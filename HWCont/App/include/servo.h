/*
 * servo.h
 *
 *  Created on: Aug 3, 2025
 *      Author: minseopkim
 */

#ifndef INCLUDE_SERVO_H_
#define INCLUDE_SERVO_H_

#include <stdbool.h>
#include <stdint.h>
#include "main.h"
//#include "df.h"
#include "interface.h"

#define SERVO_STATE_COUNT 			(4)
#define SERVO_CHANNEL               (CH1)     // 타이머 채널 지정
#define SERVO_MID_PULSE             (75)      // 1.5ms (90도)
#define GATE_OPEN_ANGLE             (100)     // 2ms (ARR=1000 기준)
#define GATE_CLOSE_ANGLE            (50)     // 1ms (ARR=1000 기준)
// #define SERVO_MIN_PULSE             (50)      // 1.5ms (90도)
// #define SERVO_MID_PULSE             (75)     // 2ms (ARR=1000 기준)
// #define SERVO_MAX_PULSE             (100)     // 1ms (ARR=1000 기준)


void entry_servo_init(ServoConfig_t *servo_config);
void exit_servo_init(ServoConfig_t *servo_config);

void gate_open(SystemContext_t *sys_context);
void gate_close(SystemContext_t *sys_context);
void servo_setAngle(TIM_HandleTypeDef *tim_h, uint32_t ch, uint16_t angle);

#endif /* INCLUDE_SERVO_H_ */
