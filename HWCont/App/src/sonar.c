/*
 * sonar.c
 *
 *  Created on: Aug 4, 2025
 *      Author: minseopkim
 */


#include "sonar.h"

#define AVARGE_ARR_NUM		(10)


// func
static void _set_entry_sonar_config(SonarPin_t *sonar_pins);
static void _set_exit_sonar_config(SonarPin_t *sonar_pins);
static uint8_t _get_avr_sonar_distance(uint8_t dist);

static volatile uint32_t _IC_Val1            = 0;
static volatile uint32_t _IC_Val2            = 0;
static volatile uint32_t _Difference         = 0;
static volatile uint8_t _Is_First_Captured 	= 0;
static volatile uint8_t _Distance = 0;

static volatile uint32_t _EXIT_IC_Val1            = 0;
static volatile uint32_t _EXIT_IC_Val2            = 0;
static volatile uint32_t _EXIT_Difference         = 0;
static volatile uint8_t _EXIT_Is_First_Captured 	= 0;
static volatile uint8_t _EXIT_Distance = 0;

static volatile uint8_t _avr_arr[AVARGE_ARR_NUM];      // the readings from the analog input
static volatile uint8_t _avr_idx = 0;              // the index of the current reading
static volatile uint8_t _avr_total = 0;                  // the running _avr_total
volatile uint8_t avr_Distance = 0;

static bool is_vehicle_detected = false;
static bool is_detection_in_progress = false;
static uint32_t detection_start_tick = 0;
static bool is_release_in_progress = false;  // 새로 추가: 해제 감지 시작 플래그
static uint32_t release_start_tick = 0;      // 새로 추가: 해제 감지 시작 틱

extern SystemContext_t entry_sys_context;
extern SystemContext_t exit_sys_context;

extern TIM_HandleTypeDef htim3;

// 타이머 입력 캡처 콜백 함수
void _u_delay (uint16_t time)
{
	__HAL_TIM_SET_COUNTER(&htim3, 0);
	while (__HAL_TIM_GET_COUNTER (&htim3) < time);
}

static void _set_entry_sonar_config(SonarPin_t *sonar_pins)
{
	sonar_pins-> echo_timer_handle = &htim3;
	sonar_pins-> echo_timer_channel = HAL_TIM_ACTIVE_CHANNEL_1;
	sonar_pins-> echo_port = GPIOA;
	sonar_pins-> trig_port = GPIOA;
	sonar_pins-> echo_pin = GPIO_PIN_6;
	sonar_pins-> trig_pin = ENTRY_TRIG_PIN;
}

static void _set_exit_sonar_config(SonarPin_t *sonar_pins)
{
	sonar_pins-> echo_timer_handle = &htim3;
	sonar_pins-> echo_timer_channel = HAL_TIM_ACTIVE_CHANNEL_1;
	sonar_pins-> echo_port = GPIOA;
	sonar_pins-> trig_port = GPIOA;
	sonar_pins-> echo_pin = GPIO_PIN_6;
	sonar_pins-> trig_pin = ENTRY_TRIG_PIN;
}

void entry_sonar_init(SonarConfig_t *sonar_config)
{
	_set_entry_sonar_config(sonar_config->pins);
    GPIO_InitTypeDef GPIO_InitStruct = {0};

    __HAL_RCC_GPIOA_CLK_ENABLE();  

	GPIO_InitStruct.Pin = ENTRY_TRIG_PIN;         
    GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
    GPIO_InitStruct.Pull = GPIO_NOPULL;
    GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);

    // 4. TRIG 핀 LOW로 초기화
    HAL_GPIO_WritePin(GPIOA, ENTRY_TRIG_PIN, GPIO_PIN_RESET);

}
#if SYS_TWO_GATE_MODE   
void exit_sonar_init(SonarConfig_t *sonar_config)
{
	_set_exit_sonar_config(&sonar_config->pins);
    GPIO_InitTypeDef GPIO_InitStruct = {0};
	
	__HAL_RCC_GPIOA_CLK_ENABLE();  

	GPIO_InitStruct.Pin = ENTRY_TRIG_PIN;         
    GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
    GPIO_InitStruct.Pull = GPIO_NOPULL;
    GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(ENTRY_TRIG_PIN, &GPIO_InitStruct);

    // 4. TRIG 핀 LOW로 초기화
    HAL_GPIO_WritePin(GPIOA, ENTRY_TRIG_PIN, GPIO_PIN_RESET);

}
#endif

static uint8_t _get_avr_sonar_distance(uint8_t dist)
{
	  _avr_total = _avr_total - _avr_arr[_avr_idx];
	  // read from the sensor:
	  _avr_arr[_avr_idx] = _Distance;
	  // add the reading to the _avr_total:
	  _avr_total = _avr_total + _avr_arr[_avr_idx];
	  // advance to the next position in the array:
	  _avr_idx = _avr_idx + 1;

	  // if we're at the end of the array...
	  if (_avr_idx >= AVARGE_ARR_NUM) {
		  // ...wrap around to the beginning:
		  _avr_idx = 0;
	  }
	  // calculate the average:
	  avr_Distance = _avr_total / AVARGE_ARR_NUM;

	  return avr_Distance;
}


// 이 함수는 HAL 드라이버에 의해 자동으로 호출됩니다.
void HAL_TIM_IC_CaptureCallback(TIM_HandleTypeDef *htim)
{

	if (htim->Channel == HAL_TIM_ACTIVE_CHANNEL_1)  // if the interrupt source is channel1
	{
		if (_Is_First_Captured==0) // if the first value is not captured
		{
			_IC_Val1 = HAL_TIM_ReadCapturedValue(htim, TIM_CHANNEL_1); // read the first value
			_Is_First_Captured = 1;  // set the first captured as true
			// Now change the polarity to falling edge
			__HAL_TIM_SET_CAPTUREPOLARITY(htim, TIM_CHANNEL_1, TIM_INPUTCHANNELPOLARITY_FALLING);
		}

		else if (_Is_First_Captured==1)   // if the first is already captured
		{
			_IC_Val2 = HAL_TIM_ReadCapturedValue(htim, TIM_CHANNEL_1);  // read second value
			__HAL_TIM_SET_COUNTER(htim, 0);  // reset the counter

			if (_IC_Val2 > _IC_Val1)
			{
				_Difference = _IC_Val2-_IC_Val1;
			}

			else if (_IC_Val1 > _IC_Val2)
			{
				_Difference = (0xffff - _IC_Val1) + _IC_Val2;
			}

			_Distance = _Difference * .034/2;
			_Is_First_Captured = 0; // set it back to false
			entry_sys_context.garage_config->sonar_config->car_detect_flg = is_detected_car(_get_avr_sonar_distance(_Distance));

			// set polarity to rising edge
			__HAL_TIM_SET_CAPTUREPOLARITY(htim, TIM_CHANNEL_1, TIM_INPUTCHANNELPOLARITY_RISING);
			__HAL_TIM_DISABLE_IT(&htim3, TIM_IT_CC1);
		}
	}
#if SYS_TWO_GATE_MODE   
	else if(htim->Channel == exit_sys_context.garage_config->sonar_config->pins->echo_timer_channel)
	{
		if (_EXIT_Is_First_Captured==0) // if the first value is not captured
		{
			_EXIT_IC_Val1 = HAL_TIM_ReadCapturedValue(htim, TIM_CHANNEL_1); // read the first value
			_EXIT_Is_First_Captured = 1;  // set the first captured as true
			// Now change the polarity to falling edge
			__HAL_TIM_SET_CAPTUREPOLARITY(htim, TIM_CHANNEL_1, TIM_INPUTCHANNELPOLARITY_FALLING);
		}

		else if (_EXIT_Is_First_Captured==1)   // if the first is already captured
		{
			_EXIT_IC_Val2 = HAL_TIM_ReadCapturedValue(htim, TIM_CHANNEL_1);  // read second value
			__HAL_TIM_SET_COUNTER(htim, 0);  // reset the counter

			if (_EXIT_IC_Val2 > _EXIT_IC_Val1)
			{
				_EXIT_Difference = _EXIT_IC_Val2-_EXIT_IC_Val1;
			}

			else if (_EXIT_IC_Val1 > _EXIT_IC_Val2)
			{
				_EXIT_Difference = (0xffff - _EXIT_IC_Val1) + _EXIT_IC_Val2;
			}

			_EXIT_Distance = _EXIT_Difference * .034/2;
			_EXIT_Is_First_Captured = 0; // set it back to false
			exit_sonar_config.car_detect_flg = is_detected_car(_get_avr_sonar_distance(_EXIT_Distance));

			// set polarity to rising edge
			__HAL_TIM_SET_CAPTUREPOLARITY(htim, TIM_CHANNEL_1, TIM_INPUTCHANNELPOLARITY_RISING);
			__HAL_TIM_DISABLE_IT(&htim3, TIM_IT_CC1);
		}

	}
#endif

}

/**
 * @brief 링 버퍼에서 유효한 UART 메시지 프레임을 파싱하고 유효성을 검증합니다.
 * @param rb UART 수신 데이터를 포함하는 링 버퍼 포인터
 * @param received_frame 유효한 프레임 데이터를 저장할 구조체 포인터
 * @return 유효한 프레임 파싱에 성공하면 true, 실패하면 false 반환
 */
void sonar_getDistance()
{
	entryGate_sonar_getDistance();
#if SYS_TWO_GATE_MODE   
	exitGate_sonar_getDistance();
#endif
}

void entryGate_sonar_getDistance()
{	
	SonarPin_t* pins = entry_sys_context.garage_config->sonar_config->pins;
	HAL_GPIO_WritePin(pins->trig_port,pins->trig_pin, GPIO_PIN_SET);  // pull the TRIG pin HIGH
	_u_delay(10);  // wait for 10 us
	HAL_GPIO_WritePin(pins->trig_port,pins->trig_pin, GPIO_PIN_RESET);  // pull the TRIG pin HIGH

	__HAL_TIM_ENABLE_IT(pins->echo_timer_handle, TIM_IT_CC1);
	__HAL_TIM_ENABLE_IT(pins->echo_timer_handle, TIM_IT_CC1);


}
#if SYS_TWO_GATE_MODE   
void exitGate_sonar_getDistance()
{
	SonarPin_t* pins = exit_sonar_config.garage_config->sonar_config->pins;
	HAL_GPIO_WritePin(pins->trig_port,pins->trig_pin, GPIO_PIN_SET);  // pull the TRIG pin HIGH
	_u_delay(10);  // wait for 10 us
	HAL_GPIO_WritePin(pins->trig_port,pins->trig_pin, GPIO_PIN_RESET);  // pull the TRIG pin HIGH

	__HAL_TIM_ENABLE_IT(pins->echo_timer_handle, TIM_IT_CC1);
	__HAL_TIM_ENABLE_IT(pins->echo_timer_handle, TIM_IT_CC1);

}
#endif
bool is_detected_car(uint8_t sonar_distance)
{
	// 2. 1초동안 감지된 상태이면 vehicle_detect_flg ON
	if (sonar_distance > 0 && sonar_distance < VEHICLE_DETECT_THRESHOLD) {
		// 감지 로직이 시작되지 않았으면 시작
		// 감지되면, 해제 타이머는 즉시 중단
		is_release_in_progress = false;

		if (!is_detection_in_progress) {
			is_detection_in_progress = true;
			detection_start_tick = HAL_GetTick(); // 감지 시작 시간 기록
		}

		// 감지 로직 진행 중, 일정 시간(DETECTION_TIME_MS)이 경과했는지 확인
		if (is_detection_in_progress && (HAL_GetTick() - detection_start_tick >= DETECTION_TIME_MS)) {
			// **지속적인 감지가 확인됨**
			is_vehicle_detected = true;
		}
	} 
	else // sonar_distance가 임계값 밖으로 나감 (차량 없음)
	{
		// ----------------------------------------------------
		// 2. 차량 해제 (ABSENCE) 로직
		// ----------------------------------------------------

		// 감지 타이머는 즉시 중단
		is_detection_in_progress = false;

		if (!is_release_in_progress) {
			is_release_in_progress = true;
			release_start_tick = HAL_GetTick(); // 해제 시작 시간 기록
		}

		// 해제 로직 진행 중, 일정 시간(DETECTION_TIME_MS)이 경과했는지 확인
		// DETECTION_TIME_MS + Margin(50ms)
		if (is_release_in_progress && (HAL_GetTick() - release_start_tick >= DETECTION_TIME_MS + 50)) {
			// **지속적인 해제가 확인됨**
			is_vehicle_detected = false; // 차량 상태 초기화 (해제 확정)
		}
		// 주의: is_vehicle_detected가 즉시 false가 되지 않도록, 이 로직을 통과해야 false가 됨
	}

	// 최종 확정된 차량 상태를 반환
	return is_vehicle_detected;
}

