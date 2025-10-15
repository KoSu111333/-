/*
 * lcd.h
 *
 *  Created on: Sep 9, 2025
 *      Author: minseopkim
 */

#ifndef INCLUDE_LCD_H_
#define INCLUDE_LCD_H_

#include <stdbool.h>
#include <stdint.h>
#include "main.h"
//#include "df.h"
#include "interface.h"

#define I2C_ENTRY_LCD_SLAVE_ADDRESS				 (0x27 << 1)
#define I2C_EXIT_LCD_SLAVE_ADDRESS				 (0x27 << 1)


#define SAVE_BIT(address, ab) (address |= (0x01<<ab))
#define CLEAR_BIT(address, ab) (address &= ~(0x01<<ab))

#define LCD_BUSY_FLG 						(0b10000000)

#define CMD_DISPLAY_ON						(0b00001100)
#define CMD_DISPLAY_OFF						(0b00001000)
#define CMD_DISPLAY_CLEAR					(0b00000001)
#define CMD_RETURN_HOME						(0b00000010)

// commands
#define LCD_CLEARDISPLAY 		0x01
#define LCD_RETURNHOME 			0x02
#define LCD_ENNTRYMODESET 		0x04
#define LCD_CURSORSHIFT 		0x10
#define LCD_FUNCTIONSET 		0x20
#define LCD_SETCGRAMADDR 		0x40
#define LCD_SETDDRAMADDR 		0x80

// flags for display entry mode
#define LCD_ENNTRYRIGHT 			0x00
#define LCD_ENNTRYLEFT 				0x02
#define LCD_ENNTRYSHIFTINCREMENT 	0x01
#define LCD_ENNTRYSHIFTDECREMENT 	0x00

// flags for display on/off control
#define LCD_DISPLAYON 			0x04
#define LCD_DISPLAYOFF 			0x00
#define LCD_CURSORON 			0x02
#define LCD_CURSOROFF 			0x00
#define LCD_BLINKON 			0x01
#define LCD_BLINKOFF 			0x00

// flags for display/cursor shift
#define LCD_DISPLAYMOVE 		0x08
#define LCD_CURSORMOVE 			0x00
#define LCD_MOVERIGHT 			0x04
#define LCD_MOVELEFT 			0x00

// flags for function set
#define LCD_8BITMODE 			0x10
#define LCD_4BITMODE 			0x00
#define LCD_2LINE 				0x08
#define LCD_1LINE 				0x00
#define LCD_5x10DOTS 			0x04
#define LCD_5x8DOTS 			0x00

// flags for backlight control
#define LCD_BACKLIGHT 			0x08
#define LCD_NOBACKLIGHT 		0x00

#define LCD_RS					0
#define LCD_RW					1
#define LCD_EN					2
#define LCD_BACKLIGHT			3



void LCD_init();
void _write_str(LCDConfig_t *lcd_config,uint8_t *str,uint8_t length);
void display_lcd(SystemContext_t *sys_state, void *p_data);



#endif /* INCLUDE_LCD_H_ */
