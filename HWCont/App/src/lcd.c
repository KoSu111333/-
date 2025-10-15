/*
 * lcd.c
 *
 *  Created on: Sep 9, 2025
 *      Author: minseopkim
 */


#include <lcd.h>

static uint8_t  _current_line = 1;

static uint8_t _lcd_chk_busy_flg(LCDConfig_t *lcd_config);
static void _LCD_4bit_Write(LCDConfig_t *lcd_config,uint8_t rs, uint8_t data);
static void _lcd_preset(LCDConfig_t *lcd_config);
static void _set_etnry_lcd_config(LCDPin_t *lcd_pins);

extern I2C_HandleTypeDef hi2c1;

static uint8_t _lcd_chk_busy_flg(LCDConfig_t *lcd_config)
{
	// Enable Low
    uint8_t Tdata[2] = {0,0};

	uint8_t busy_flg = (0b00000001 << LCD_RW);
	// Enable High
	uint8_t val;
    HAL_I2C_Master_Transmit(lcd_config->pins->i2c_handle,lcd_config->lcd_addr,busy_flg,1,10);
	// Enable set'
    SAVE_BIT(busy_flg, LCD_EN);
    HAL_I2C_Master_Transmit(lcd_config->pins->i2c_handle,lcd_config->lcd_addr,busy_flg,1,10);

    HAL_I2C_Master_Receive(lcd_config->pins->i2c_handle,lcd_config->lcd_addr,&val,1,10);

	return val;
}
static void _LCD_4bit_Write(LCDConfig_t *lcd_config, uint8_t rs, uint8_t data){


    uint8_t tx_buf[4];
    uint8_t base = (rs ? (1 << LCD_RS) : 0) | (1 << LCD_BACKLIGHT); // 백라이트 ON
    
	while(_lcd_chk_busy_flg(lcd_config)&0x80){}// lcd_bf 0b10000000 일시 무한 루프

    // 상위 4비트
    tx_buf[0] = base | (data & 0xF0) | (1 << LCD_EN); // E HIGH
    tx_buf[1] = base | (data & 0xF0);            // E LOW

    // 하위 4비트
    tx_buf[2] = base | ((data << 4) & 0xF0) | (1 << LCD_EN); // E HIGH
    tx_buf[3] = base | ((data << 4) & 0xF0);            // E LOW

    HAL_I2C_Master_Transmit(&hi2c1, lcd_config->lcd_addr, tx_buf, 4, 100);

}
static void _lcd_preset(LCDConfig_t *lcd_config)
{
    _LCD_4bit_Write(lcd_config,0,0b00101000);    //function set //
    HAL_Delay(1);

    _LCD_4bit_Write(lcd_config,0,CMD_DISPLAY_OFF);    //display off
    HAL_Delay(1);

    _LCD_4bit_Write(lcd_config,0,CMD_DISPLAY_CLEAR);    //clear display
    HAL_Delay(1);

    _LCD_4bit_Write(lcd_config,0,CMD_RETURN_HOME);    //return home
    HAL_Delay(1);

    _LCD_4bit_Write(lcd_config,0,0b00000110);    //entry mode set
    HAL_Delay(1);

    _LCD_4bit_Write(lcd_config,0,CMD_DISPLAY_ON);    //display on    //cursor off*/
}
static void _set_etnry_lcd_config(LCDPin_t *lcd_pins)
{
	lcd_pins-> scl_port = GPIOB;
    lcd_pins-> sdl_port = GPIOB;
	lcd_pins-> scl_pin = GPIO_PIN_8;
	lcd_pins-> sdl_pin = GPIO_PIN_9;
	lcd_pins-> i2c_handle = &hi2c1;
}

void entry_LCD_init(LCDConfig_t *lcd_config){
    _set_etnry_lcd_config(lcd_config -> pins);
    lcd_config->lcd_addr = I2C_ENTRY_LCD_SLAVE_ADDRESS;
    LCD_init(lcd_config);
}   
#if SYS_TWO_GATE_MODE   
void _set_exit_sonar_config(LCDPin_t *lcd_pins);

static void _set_exit_sonar_config(LCDPin_t *lcd_pins)
{
	lcd_pins-> scl_port = GPIOB;
    lcd_pins-> sdl_port = GPIOB;
	lcd_pins-> scl_pin = GPIO_PIN_8;
	lcd_pins-> sdl_pin = GPIO_PIN_9;
	lcd_pins-> i2c_handle = &hi2c1;
}

void exit_LCD_init(LCDConfig_t *lcd_config){
    _set_exit_sonar_config(lcd_config);
    lcd_config->lcd_addr = I2C_ENTRY_LCD_SLAVE_ADDRESS;
    LCD_init(lcd_config);
}
#endif
void LCD_init(LCDConfig_t *lcd_config){

    uint8_t Tdata[2]={0x30,0x34};
	HAL_Delay(50);
    HAL_I2C_Master_Transmit(lcd_config->pins->i2c_handle,lcd_config->lcd_addr,Tdata,2,10);
    HAL_Delay(5);
    HAL_I2C_Master_Transmit(lcd_config->pins->i2c_handle,lcd_config->lcd_addr,Tdata,2,10);
    HAL_Delay(1);
    HAL_I2C_Master_Transmit(lcd_config->pins->i2c_handle,lcd_config->lcd_addr,Tdata,2,10);
    HAL_Delay(1);

    Tdata[0]=0x20;
    Tdata[1]=0x24;

    HAL_I2C_Master_Transmit(lcd_config->pins->i2c_handle,lcd_config->lcd_addr,Tdata,2 ,10);
    HAL_Delay(1);

    _lcd_preset(lcd_config);

}

void _write_str(LCDConfig_t *lcd_config,uint8_t *str,uint8_t length)
{
    for(int i=0;i<length;i++)
    {
        if(str[i]==NULL)
            str[i]=' ';
        _LCD_4bit_Write(lcd_config,1,str[i]);
    }
}

void LCD_set_cursor_second_line(LCDConfig_t *lcd_config){
    // rs=0 (Command Mode), data=0xC0 (Set DDRAM Address 0x40)
    _LCD_4bit_Write(lcd_config,0, LCD_SETDDRAMADDR | 0x40);
}

// 첫 번째 라인의 맨 앞으로 커서를 옮기는 함수
void LCD_set_cursor_first_line(LCDConfig_t *lcd_config){
    // rs=0 (Command Mode), data=0x80 (Set DDRAM Address 0x00)
    _LCD_4bit_Write(lcd_config,0, LCD_SETDDRAMADDR | 0x00);
}

void LCD_toggle_line(LCDConfig_t *lcd_config){
    // 현재 라인이 첫 번째 라인(1)일 경우
    if(_current_line == 1){
    	LCD_set_cursor_second_line(lcd_config);
        _current_line = 2;
    }
    // 현재 라인이 두 번째 라인(2)일 경우
    else {
    	LCD_set_cursor_first_line(lcd_config);
        _current_line = 1;
    }
}

static SystemState_t _tmp_state = SYS_STATE_IDLE;


void display_lcd(SystemContext_t *sys_state, void *p_data)
{
    char lcd_buffer[32];
    uint8_t str_size;
    SystemState_t state = sys_state->cur_sys_state;
    LCDConfig_t* l_config = sys_state->garage_config->lcd_config;
    PaymentInfoPayload_t* payload = NULL;
    uint8_t* available_count = NULL;

    if (_tmp_state != state)
    {
        _lcd_preset(l_config);
    }
    _tmp_state = state;

    switch(state)
    {
        case SYS_STATE_START_UP:
            str_size = sprintf(lcd_buffer, "Garage System");
            _write_str(l_config,(uint8_t*)lcd_buffer, str_size);
            LCD_toggle_line(l_config);
            str_size = sprintf(lcd_buffer, "Starting ... ");
            _write_str(l_config,(uint8_t*)lcd_buffer, str_size); // ★ 이 부분이 추가됨
    		LCD_toggle_line(l_config);

            break;

        case SYS_STATE_IDLE :
            available_count = (uint8_t*)p_data;
            str_size = sprintf(lcd_buffer, "Garage System");
            _write_str(l_config,(uint8_t*)lcd_buffer, str_size);
            LCD_toggle_line(l_config);
            str_size = sprintf(lcd_buffer, "Available : %d", *available_count);
            _write_str(l_config,(uint8_t*)lcd_buffer, str_size); // ★ 이 부분이 추가됨
    		LCD_toggle_line(l_config);

            break;

        case SYS_STATE_GATE_OPENED :
            char *license_plate = (char*)p_data; // p_data를 char*로 캐스팅
            if (license_plate == NULL) {
                // NULL 포인터 체크는 필수입니다.
            	license_plate = "ERROR";
            }
            str_size = sprintf(lcd_buffer, "Welcome %s", license_plate);
            _write_str(l_config,(uint8_t*)lcd_buffer, str_size);
            LCD_toggle_line(l_config);
    		LCD_toggle_line(l_config);


            break;
        case SYS_STATE_GATE_CLOSED :
            str_size = sprintf(lcd_buffer, "Thank You!");
            _write_str(l_config,(uint8_t*)lcd_buffer, str_size);
            LCD_toggle_line(l_config);
    		LCD_toggle_line(l_config);

            break;

        case SYS_STATE_PAYMENT :
            payload = (PaymentInfoPayload_t*)p_data;
            // 데이터를 잘못 받았을 가능성이 높으므로 p_data가 올바른지 확인해야 합니다.
            // 그리고 데이터가 올바르게 들어온다는 가정 하에, 아래 코드는 동작합니다.
            str_size = sprintf(lcd_buffer, "%s", payload->license_plate);
            _write_str(l_config,(uint8_t*)lcd_buffer, str_size);
            LCD_toggle_line(l_config);

            str_size = sprintf(lcd_buffer, "Payment:%hu WON", payload->fee);
            _write_str(l_config,(uint8_t*)lcd_buffer, str_size); // ★ 이 부분이 추가됨
    		LCD_toggle_line(l_config);

            break;

        case SYS_STATE_PAYMENT_DONE :
            payload = (PaymentInfoPayload_t*)p_data;
            str_size = sprintf(lcd_buffer, "Thank you");
            _write_str(l_config,(uint8_t*)lcd_buffer, str_size);
            LCD_toggle_line(l_config);
            str_size = sprintf(lcd_buffer, "%s", payload->license_plate);
            _write_str(l_config,(uint8_t*)lcd_buffer, str_size); // ★ 이 부분이 추가됨
    		LCD_toggle_line(l_config);

            break;

        case SYS_STATE_PAYMENT_FAIL :
            str_size = sprintf(lcd_buffer, "Error Occured");
            _write_str(l_config,(uint8_t*)lcd_buffer, str_size);
            LCD_toggle_line(l_config);
    		LCD_toggle_line(l_config);

            // str_size = sprintf(lcd_buffer, "Error Code :%d", p_data->error_code); // ★ sys_state에서 값을 가져오도록 수정
            // _write_str((uint8_t*)lcd_buffer, str_size); // ★ 이 부분이 추가됨
            break;

        case SYS_STATE_ERROR :
            str_size = sprintf(lcd_buffer, "System Reset");
            _write_str(l_config,(uint8_t*)lcd_buffer, str_size);
            LCD_toggle_line(l_config); // ★ 두 번째 줄도 표시할 내용이 있다면 추가
    		LCD_toggle_line(l_config);

            break;

        default :
            // 아무것도 하지 않음 (기존 코드에서 마지막 _write_str가 없어졌으므로)
            break;
		LCD_toggle_line(l_config);

    }
}
