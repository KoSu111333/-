/*
 * sonar.h
 *
 *  Created on: Aug 4, 2025
 *      Author: minseopkim
 */

#ifndef INCLUDE_SONAR_H_
#define INCLUDE_SONAR_H_

#include <stdbool.h>
#include <stdint.h>
#include "main.h"
#include "interface.h"

// htim3, TIM_IT_CC1  <<< ECHO PWM CAPTURE
#define ENTRY_TRIG_PORT 							(GPIOA)      // 예시: GPIOA
#define ENTRY_TRIG_PIN 							(GPIO_PIN_5)

// #define EXIT_TRIG_PORT 							(GPIOA)      // 예시: GPIOA
// #define EXIT_TRIG_PIN 							(GPIO_PIN_5)

// ECHO is Timer input capture pin
#define VEHICLE_DETECT_THRESHOLD                (12)                    // 200cm
#define DETECTION_TIME_MS                       (100)                         // 2초 (2000ms)



void entry_sonar_init(SonarConfig_t *sonar_config);
void entryGate_sonar_getDistance();
void _u_delay (uint16_t time);

void sonar_getDistance();
bool is_detected_car(uint8_t sonar_distance);

#if SYS_TWO_GATE_MODE   
void exit_sonar_init(SonarConfig_t *sonar_config);
void exitGate_sonar_getDistance();
#endif

#endif /* INCLUDE_SONAR_H_ */
