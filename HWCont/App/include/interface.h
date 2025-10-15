/*
 * interface.h
 *
 *  Created on: Aug 15, 2025
 *      Author: minseopkim
 */

#ifndef INCLUDE_INTERFACE_H_
#define INCLUDE_INTERFACE_H_

 #include <stdbool.h>
 #include <stdint.h>
 #include "main.h"
 #include "ring_buff.h"
 #include "uart.h"
// #include "sonar.h"
// #include "lcd.h"
// #include "servo.h"
//#include "df.h"

/*    
    PB8     ------> I2C1_SCL
    PB9     ------> I2C1_SDA
    */
typedef struct 
{
    // 핀 설정 (선택 사항이지만 명확성을 위해 유지)
    GPIO_TypeDef* scl_port;     // 예: GPIOA
    uint16_t      scl_pin;      // 예: GPIO_PIN_0

    GPIO_TypeDef* sdl_port;     // 예: GPIOA
    uint16_t      sdl_pin;      // 예: GPIO_PIN_0

    // ★ PWM 제어를 위한 핵심 정보
    I2C_HandleTypeDef* i2c_handle; // 서보모터에 연결된 타이머의 핸들 (주소)

} LCDPin_t; // 구조체 이름도 더 명확하게 변경했습니다.

typedef struct __attribute__((packed))
{
    LCDPin_t* pins;
    uint8_t lcd_addr;
}LCDConfig_t;

typedef struct 
{
    // 핀 설정 (선택 사항이지만 명확성을 위해 유지)
    GPIO_TypeDef* port;     // 예: GPIOA
    uint16_t      pin;      // 예: GPIO_PIN_0

    // ★ PWM 제어를 위한 핵심 정보
    TIM_HandleTypeDef* timer_handle; // 서보모터에 연결된 타이머의 핸들 (주소)
    uint32_t           timer_channel; // 타이머의 어떤 채널을 사용할지 지정

} ServoPin_t; // 구조체 이름도 더 명확하게 변경했습니다.

typedef struct __attribute__((packed))
{
    ServoPin_t* pins;
    volatile uint8_t cur_pwm;
}ServoConfig_t;

typedef struct 
{
    // ★ PWM 제어를 위한 핵심 정보
    TIM_HandleTypeDef* echo_timer_handle; // 서보모터에 연결된 타이머의 핸들 (주소)
    uint32_t           echo_timer_channel; // 타이머의 어떤 채널을 사용할지 지정

    GPIO_TypeDef* echo_port;
    GPIO_TypeDef* trig_port;

    uint16_t echo_pin; // ★ uint16_t로 수정
    uint16_t trig_pin; // ★ uint16_t로 수정

} SonarPin_t;


typedef struct __attribute__((packed))
{
    SonarPin_t* pins;
    volatile uint8_t cur_distance;
    volatile bool car_detect_flg;
}SonarConfig_t;



typedef enum{
    ENTRY_GATE = 10,
    EXIT_GATE,
}gateID_t;

// 시스템의 현재 상태 (State Machine)
typedef enum
{
    SYS_STATE_START_UP,
    SYS_STATE_IDLE,                 // 대기 중 (차량 없음, 게이트 닫힘)
    SYS_STATE_OCR_REQUESTED,        // OCR 요청 후 응답 대기 중
    SYS_STATE_GATE_OPENED,          // 게이트 열림 완료
    SYS_STATE_VEHICLE_PASSED,       // 차량 통과 완료 (진입 또는 진출)
    SYS_STATE_GATE_CLOSED,          // 게이트 닫히는 중
    SYS_STATE_PAYMENT,				// 정산 중
    SYS_STATE_PAYMENT_DONE,			// 정산 중
    SYS_STATE_PAYMENT_FAIL,			// 정산 중
    SYS_STATE_RESET,				// 정산 중
    SYS_STATE_ERROR,                // 시스템 오류 발생
} SystemState_t;

typedef enum
{
  ERROR_SONAR_NO_CONNECT = 0x90,
  ERROR_SERVO_NO_CONNECT = 0x91,
  ERROR_TIMEOUT          = 0x92,
}Erorr_code_t;

typedef struct 
{
    Erorr_code_t                    err_code;
    bool                            err_flg; 
}Error_Handler_t;


// 일단 대기 ?? 
typedef struct
{
    volatile SonarConfig_t*         sonar_config;
    volatile ServoConfig_t*         servo_config;
    volatile LCDConfig_t*           lcd_config;
    volatile uint8_t                available_count;
}garageConfig_t;


// 전체 시스템의 컨텍스트 (상태 및 관련 데이터)
typedef struct
{
	volatile gateID_t		     gate_type;	  // 입차 출차 상태
    volatile SystemState_t       cur_sys_state;     // 시스템의 현재 상태
    volatile garageConfig_t*     garage_config;
    volatile bool                new_uart_cmd_received_flag; // UART로부터 새 명령 수신됨
    volatile bool                is_vehicle_present;
} SystemContext_t;

// 3. Command Message (Jetson -> STM32) 내부의 명령 타입
typedef enum
{
    CMD_GATE_OPEN            = 0x10,
    CMD_GATE_CLOSE           = 0x11,
    CMD_DISPLAY_PAYMENT_INFO = 0x12,
    CMD_DISPLAY_PAYMENT_DONE = 0x13, 
    CMD_DISPLAY_PAYMENT_FAIL = 0x14, 
    CMD_REQUEST_STM32_STATUS = 0x15, 
    CMD_RESET                = 0x16,
    CMD_AVAILABLE_COUNT 	 = 0x17,

} CommandType_t;

// STATUS_PAYMENT_INFO 메시지의 데이터 구조체
typedef struct __attribute__((packed))
{
    char                    license_plate[10];
    uint32_t                entry_time;
    uint32_t                exit_time;
    uint16_t                fee;
    bool                    is_paid;
    uint16_t                discount_applied;
} PaymentInfoPayload_t;

// Command Message Payload 구조체 (union 활용)
typedef struct __attribute__((packed))
{
    CommandType_t               type; // 어떤 명령인지 식별
    gateID_t                    gate_id;
    union                       // 명령에 따른 매개변수 (메모리 공유)
    {
        uint8_t                 available_count;
        uint16_t                gate_open_duration_ms; // CMD_GATE_OPEN 시
        PaymentInfoPayload_t    parking_fee_config;    
        char                    license_plate[10];
    } payload;
} Command_t;


// STM32가 Jetson에게 보내는 상태 보고 메시지 종류
typedef enum {
	STATUS_SYSTEM_STARTUP 		  = 0x19,
    STATUS_SYSTEM_IDLE       	  = 0x20,  // 기본 상태
    STATUS_VEHICLE_DETECTED  	  = 0x21,  // 차량 감지됨
    STATUS_GATE_OPEN         	  = 0x22,  // 게이트가 완전히 열림
    STATUS_GATE_CLOSED       	  = 0x23,  // 게이트가 완전히 닫힘
    STATUS_VEHICLE_LEFT      	  = 0x24,  // 차량이 지나감
	STATUS_DISPLAY_PAYMENT   	  = 0x25,
	STATUS_DISPLAY_PAYMENT_DONE   = 0x26,
	STATUS_DISPLAY_PAYMENT_FAIL   = 0x27,
    STATUS_VEHICLE_PASSED      	  = 0x28,  // 차량이 지나감
    STATUS_ERROR_CODE             = 0xFF,  // 하드웨어 오류 발생
} StatusType_t;

// Status Message Payload 구조체 (union 활용)
typedef struct __attribute__((packed))
{
    StatusType_t                type; // 어떤 상태인지 식별
    gateID_t                    gate_id;
    union
    {        
        uint8_t                 gate_id;
        uint8_t                 error_code;                
    } payload;
} Status_t;


// extern SystemContext_t      g_SystemContext;
void init_entry_gate(SystemContext_t *sys_context);
#if SYS_TWO_GATE_MODE   
void init_exit_gate(SystemContext_t *sys_context);
#endif
bool parse_cmd(SystemContext_t *g_SystemContext);
bool send_msg_state_type(SystemContext_t *sys_context, StatusType_t type);


#endif /* INCLUDE_INTERFACE_H_ */
