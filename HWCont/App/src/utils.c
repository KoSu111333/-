/*
 * utils.c
 *
 *  Created on: Aug 3, 2025
 *      Author: minseopkim
 */


#include "utils.h"

volatile uint32_t timeout_counter = 0;


/**
 * @brief 링 버퍼에서 유효한 UART 메시지 프레임을 파싱하고 유효성을 검증합니다.
 * @param rb UART 수신 데이터를 포함하는 링 버퍼 포인터
 * @return 유효한 프레임 파싱에 성공하면 true, 실패하면 false 반환
 */
void sys_reset(void){
    SCB->AIRCR = AIRCR_VECTKEY_MASK | (uint32_t)0x04;
    // 만약 리셋 실패하면 while
    while (1) {}
}

/**
 * 
 * @brief 링 버퍼에서 유효한 UART 메시지 프레임을 파싱하고 유효성을 검증합니다.
 * @param received_frame 유효한 프레임 데이터를 저장할 구조체 포인터
 * @return 유효한 프레임 파싱에 성공하면 true, 실패하면 false 반환
 */
void start_timeout(uint32_t timeout_ms) {
  timeout_counter = timeout_ms;
}
/**
 * @brief 링 버퍼에서 유효한 UART 메시지 프레임을 파싱하고 유효성을 검증합니다.
 * @param received_frame 유효한 프레임 데이터를 저장할 구조체 포인터
 * @return 유효한 프레임 파싱에 성공하면 true, 실패하면 false 반환
 */
bool is_timeout() {
  return (timeout_counter == 0);
}

void  print_cmd(void)
{
	printf("-------------------------\r\n");
	printf("Smart Garage Service Mode\r\n");
	printf("FirmWare Version : 00.00\r\n");
	printf("-------------------------\r\n");
}
