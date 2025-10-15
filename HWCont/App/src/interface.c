/*
 * interface.c
 *
 *  Created on: Aug 15, 2025
 *      Author: minseopkim
 */


#include "interface.h"

extern I2C_HandleTypeDef hi2c1;
extern TIM_HandleTypeDef htim3;
extern TIM_HandleTypeDef htim4;

extern RingBuffer uart_rx_rb;
// 1. 필요한 모든 설정 구조체의 실제 메모리 공간 (파일 scope에서 static으로 선언)
static SonarConfig_t  entry_sonar_config_data;
static ServoConfig_t  entry_servo_config_data;
static LCDConfig_t    entry_lcd_config_data; // (LCDConfig_t는 정의되지 않았지만 필요하다고 가정)
static garageConfig_t entry_garage_config_data;

// SonarConfig_t가 내부적으로 포인터를 가지고 있으므로, 그것도 선언해야 합니다.
static SonarPin_t     entry_sonar_pin_data;
static SonarPin_t     exit_sonar_pin_data;

static ServoPin_t     entry_servo_pin_data;
static SonarPin_t     entry_sonar_pin_data;
static LCDPin_t       entry_lcd_pin_data;

void entry_lcd_config_init()
{
    entry_lcd_config_data.pins = &entry_lcd_pin_data;
	entry_lcd_pin_data.scl_port = GPIOB;
    entry_lcd_pin_data.sdl_port = GPIOB;
	entry_lcd_pin_data.scl_pin = GPIO_PIN_8;
	entry_lcd_pin_data.sdl_pin = GPIO_PIN_9;
	entry_lcd_pin_data.i2c_handle = &hi2c1;
}

void entry_servo_config_init()
{
    entry_servo_config_data.pins = &entry_servo_pin_data;
    entry_servo_pin_data.port = GPIOB;
    entry_servo_pin_data.pin = GPIO_PIN_7;
    entry_servo_pin_data.timer_handle = &htim4;
    entry_servo_pin_data.timer_channel = TIM_CHANNEL_2;
}
void entry_sonar_config_init()
{
    // 3. SonarConfig_t 내부의 pins 포인터 연결
    // g_sonar_config_data.pins 포인터가 실제 g_sonar_pin_data를 가리키게 합니다.
    entry_sonar_config_data.pins = &entry_sonar_pin_data;

    // 이제 SonarPin_t 구조체에 핀 정보 등을 안전하게 설정 가능
    entry_sonar_pin_data.echo_port = GPIOA;
    entry_sonar_pin_data.echo_pin = 0;
    // ... (나머지 SonarPin_t 설정)
    entry_sonar_pin_data.echo_timer_handle = &htim3; // 서보모터에 연결된 타이머의 핸들 (주소)
    entry_sonar_pin_data.echo_timer_channel = TIM_IT_CC1; // 타이머의 어떤 채널을 사용할지 지정

    // 기타 초기값 설정
    entry_sonar_config_data.cur_distance = 0;
    entry_sonar_config_data.car_detect_flg = false;
}
void entry_garage_config_init()
{
    // 2. garageConfig_t 내부의 포인터들 연결
    // g_garage_config_data.sonar_config 포인터가 실제 g_sonar_config_data를 가리키게 합니다.
    entry_garage_config_data.sonar_config = &entry_sonar_config_data;
    entry_garage_config_data.servo_config = &entry_servo_config_data;
    entry_garage_config_data.lcd_config = &entry_lcd_config_data; // LCD도 연결
    // 기타 초기값 설정
    entry_garage_config_data.available_count = 0;
}
bool send_msg_state_type(SystemContext_t *sys_context, StatusType_t type)
{
    Status_t status_payload;    
    bool ret;
    status_payload.type = type;
    status_payload.gate_id = sys_context->gate_type;

    // Jetson에 '차량 감지됨' 상태 보고
    ret = UART_SEND_WITH_PAYLOAD(MSG_TYPE_STATUS, status_payload);

    return ret;
}

void init_entry_gate(SystemContext_t *sys_context)
{
    // 시스템 컨텍스트 초기화
    sys_context->gate_type = ENTRY_GATE;
    sys_context->cur_sys_state = SYS_STATE_START_UP;
    sys_context->is_vehicle_present =  false;
    sys_context->new_uart_cmd_received_flag = false;
    sys_context->garage_config = &entry_garage_config_data;
    entry_garage_config_init();
    entry_sonar_config_init();
    entry_servo_config_init();
    entry_lcd_config_init();

    entry_servo_init(sys_context->garage_config->servo_config);
    entry_sonar_init(sys_context->garage_config->sonar_config);
    entry_LCD_init(sys_context->garage_config->lcd_config);
}
#if SYS_TWO_GATE_MODE   
void init_exit_gate(SystemContext_t *sys_context)
{
    // 시스템 컨텍스트 초기화
    sys_context->gate_type = EXIT_GATE;
    sys_context->cur_sys_state = SYS_STATE_START_UP;
    sys_context->is_vehicle_present =  false;
    sys_context->new_uart_cmd_received_flag = false;
    exit_servo_init(&sys_context->garage_config->servo_config);
    exit_sonar_init(&sys_context->garage_config->sonar_config);
    exit_LCD_init(&sys_context->garage_config->lcd_config);
}
#endif
static bool init_flg = true;
bool parse_cmd(SystemContext_t *g_SystemContext)
{
    bool ret = true;
    UartMessageFrame_t received_frame;
    Command_t cmd_payload;  
    Status_t status_payload;    

    void *lcd_payload;
    
    if (uart_ParseAndValidateFrame(&uart_rx_rb, &received_frame)) // 파싱 성공 및 유효성 검사
    {
        // 메세지 타입이 '명령'인 경우
        if (received_frame.msg_type == MSG_TYPE_COMMAND)
        {
            // payload_data의 첫 바이트(타입)를 먼저 복사 (대입)
            cmd_payload.type = received_frame.payload_data[0];
            cmd_payload.gate_id = received_frame.payload_data[1];
            if (cmd_payload.gate_id != g_SystemContext->gate_type && !init_flg)
            {
                // 해당 컨텍스트의 명령어가 아님
                return false;
            }
            memcpy(&cmd_payload.payload,received_frame.payload_data + 2,received_frame.length - 2);
            switch (cmd_payload.type)
            {
                case CMD_GATE_OPEN:
                    // OCR 요청-응답 시퀀스에 따라 게이트를 열어야 할 때만 처리
                    gate_open(g_SystemContext);
                    lcd_payload = &cmd_payload.payload;
                    break;
                case CMD_GATE_CLOSE:
                    // 게이트가 열려있거나 움직이는 중일 때만 닫기 명령 처리
                	gate_close(g_SystemContext);
                    lcd_payload = &cmd_payload.payload;
                    break;
                // --- 기타 명령 처리 ---
                case CMD_DISPLAY_PAYMENT_INFO:
                    g_SystemContext->cur_sys_state = SYS_STATE_PAYMENT;
                    lcd_payload = &cmd_payload.payload;
                    send_msg_state_type(g_SystemContext,STATUS_DISPLAY_PAYMENT);
                    break;  
                case CMD_DISPLAY_PAYMENT_DONE:
                    gate_open(g_SystemContext);
                    break;  
                case CMD_DISPLAY_PAYMENT_FAIL:
                    g_SystemContext->cur_sys_state = SYS_STATE_PAYMENT_FAIL;
                    lcd_payload = &cmd_payload.payload;
                    send_msg_state_type(g_SystemContext,STATUS_DISPLAY_PAYMENT_FAIL);
                    break;
                case CMD_REQUEST_STM32_STATUS:
                    printf("\r\n CMD_REQUEST_STM32_STATUS\r\n");
                    break;  
                case CMD_RESET:
                    g_SystemContext->cur_sys_state = SYS_STATE_RESET;
                    send_msg_state_type(g_SystemContext,STATUS_ERROR_CODE);
                    sys_reset();
                    break;
                case CMD_AVAILABLE_COUNT:
                    g_SystemContext->cur_sys_state = SYS_STATE_IDLE;
                    g_SystemContext->garage_config->available_count = cmd_payload.payload.available_count;
                    lcd_payload = &cmd_payload.payload.available_count;
                    break;
                default:
                    // g_SystemContext->cur_sys_state = SYS_STATE_RESET;
                    // send_msg_state_type(g_SystemContext,STATUS_ERROR_CODE);
                    break;
            }
        }
    }
    else if (g_SystemContext->cur_sys_state != SYS_STATE_IDLE && \
    		g_SystemContext->cur_sys_state != SYS_STATE_START_UP)
    {
		g_SystemContext->cur_sys_state = SYS_STATE_ERROR;
		send_msg_state_type(g_SystemContext,STATUS_ERROR_CODE);
		ret = false;
        sys_reset();
    }
    display_lcd(g_SystemContext,lcd_payload);

    return ret;
}
