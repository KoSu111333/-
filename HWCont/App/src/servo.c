/*
 * servo.c
 *
 *  Created on: Aug 3, 2025
 *      Author: minseopkim
 */

#include "servo.h"

static void set_entry_servo_config(ServoConfig_t *servo_config);
extern TIM_HandleTypeDef 	htim4;


static void set_entry_servo_config(ServoConfig_t *servo_config)
{
    servo_config->pins->port = GPIOB;
    servo_config->pins->pin  = GPIO_PIN_7;
    servo_config->pins->timer_handle = &htim4;
    servo_config->pins->timer_channel = TIM_CHANNEL_2;
}

/**
 * @brief 링 버퍼에서 유효한 UART 메시지 프레임을 파싱하고 유효성을 검증합니다.
 * @param rb UART 수신 데이터를 포함하는 링 버퍼 포인터
 * @param received_frame 유효한 프레임 데이터를 저장할 구조체 포인터
 * @return 유효한 프레임 파싱에 성공하면 true, 실패하면 false 반환
 */
void entry_servo_init(ServoConfig_t *servo_config)
{
//	set_entry_servo_config(servo_config);

    servo_setAngle(servo_config->pins->timer_handle, servo_config->pins->timer_channel,GATE_CLOSE_ANGLE);
    HAL_Delay(200); // 1000ms
    servo_setAngle(servo_config->pins->timer_handle, servo_config->pins->timer_channel,GATE_OPEN_ANGLE);
    HAL_Delay(200); // 1000ms
    servo_setAngle(servo_config->pins->timer_handle, servo_config->pins->timer_channel,GATE_CLOSE_ANGLE);
    HAL_Delay(200); // 1000ms

}
#if SYS_TWO_GATE_MODE   
void exit_servo_init(ServoConfig_t *servo_config)
{
    servo_config->pins.port = GPIOB;
    servo_config->pins->pin = GPIO_PIN_7;
    servo_config->pins.timer_handle = &htim4;
    servo_config->pins.timer_channel = TIM_CHANNEL_2;

    servo_setAngle(servo_config->pins.timer_handle, servo_config->pins.timer_channel,GATE_CLOSE_ANGLE);
    HAL_Delay(200); // 1000ms
    servo_setAngle(servo_config->pins.timer_handle, servo_config->pins.timer_channel,GATE_OPEN_ANGLE);
    HAL_Delay(200); // 1000ms
    servo_setAngle(servo_config->pins.timer_handle, servo_config->pins.timer_channel,GATE_CLOSE_ANGLE);
    HAL_Delay(200); // 1000ms
}
#endif

/**
 * @brief 링 버퍼에서 유효한 UART 메시지 프레임을 파싱하고 유효성을 검증합니다.
 * @param rb UART 수신 데이터를 포함하는 링 버퍼 포인터
 * @param received_frame 유효한 프레임 데이터를 저장할 구조체 포인터
 * @return 유효한 프레임 파싱에 성공하면 true, 실패하면 false 반환
 */
void gate_open(SystemContext_t *sys_context)
{
	// 출차 시퀀스
	ServoConfig_t *tmp_servo_cfg = sys_context->garage_config->servo_config;
	TIM_HandleTypeDef *tmp_tim_handler = tmp_servo_cfg->pins->timer_handle;
	uint16_t tmp_ch = tmp_servo_cfg->pins->timer_channel;

	servo_setAngle(tmp_tim_handler,tmp_ch,GATE_OPEN_ANGLE);

    sys_context->cur_sys_state = SYS_STATE_GATE_OPENED;
    send_msg_state_type(sys_context, STATUS_GATE_OPEN);

}
/**
 * @brief 링 버퍼에서 유효한 UART 메시지 프레임을 파싱하고 유효성을 검증합니다.
 * @param rb UART 수신 데이터를 포함하는 링 버퍼 포인터
 * @param received_frame 유효한 프레임 데이터를 저장할 구조체 포인터
 * @return 유효한 프레임 파싱에 성공하면 true, 실패하면 false 반환
 */
void gate_close(SystemContext_t *sys_context)
{
    // 예: 0도
	ServoConfig_t *tmp_servo_cfg = sys_context->garage_config->servo_config;
	TIM_HandleTypeDef *tmp_tim_handler = tmp_servo_cfg->pins->timer_handle;
	uint16_t tmp_ch = tmp_servo_cfg->pins->timer_channel;

    if (sys_context->cur_sys_state != SYS_STATE_GATE_CLOSED )
    {
        servo_setAngle(tmp_tim_handler,tmp_ch,GATE_CLOSE_ANGLE);
        sys_context->cur_sys_state = SYS_STATE_GATE_CLOSED;
    }

    send_msg_state_type(sys_context, STATUS_GATE_CLOSED);

}
/**
 * @brief 링 버퍼에서 유효한 UART 메시지 프레임을 파싱하고 유효성을 검증합니다.
 * @param rb UART 수신 데이터를 포함하는 링 버퍼 포인터
 * @param received_frame 유효한 프레임 데이터를 저장할 구조체 포인터
 * @return 유효한 프레임 파싱에 성공하면 true, 실패하면 false 반환
 */
void servo_setAngle(TIM_HandleTypeDef *tim_h, uint32_t ch, uint16_t angle)
{
//    change_pwm(CH2, angle);

    __HAL_TIM_SetCompare(tim_h, ch, angle);
    HAL_Delay(200); // 1000ms


}



