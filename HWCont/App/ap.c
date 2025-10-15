/*
 * ap.c
 *
 *  Created on: Jul 31, 2025
 *      Author: minseopkim
 */

#include"ap.h"


void seq_start(SystemContext_t *g_SystemContext);

uint8_t tmp_buffer;
SystemContext_t entry_sys_context;
SystemContext_t exit_sys_context;
extern volatile uint8_t avr_Distance;
extern SonarConfig_t exit_sonar_config;
extern RingBuffer uart_rx_rb;
extern UART_HandleTypeDef huart2;
extern TIM_HandleTypeDef htim3;
extern TIM_HandleTypeDef htim4;

static void* tmp_data;


void apInit(void)
{
  RingBuffer_Init(&uart_rx_rb);
  HAL_UART_Receive_IT(&huart2, &tmp_buffer, 1);
  HAL_TIM_IC_Start_IT(&htim3, TIM_CHANNEL_1);
  init_entry_gate(&entry_sys_context);
  display_lcd(&entry_sys_context,tmp_data);
#if SYS_TWO_GATE_MODE
  init_exit_gate(&exit_sys_context);
  display_lcd(&exit_sys_context,tmp_data);
#endif

}
void apMain(void)
{
    
   apInit(); // apMain 진입 시 초기화
#if SYS_TWO_GATE_MODE   
   while(entry_sys_context->garage_config->available_count == 0 && exit_sys_context.garage_config.available_count == 0){uart_connect_chk();}
   exit_sys_context.cur_sys_state = SYS_STATE_IDLE;
   display_lcd(&exit_sys_context,&exit_sys_context.garage_config.available_count);
   entry_sys_context.cur_sys_state = SYS_STATE_IDLE;
   display_lcd(&entry_sys_context,&entry_sys_context->garage_config->available_count);
#else

   while(1)
   {
	   uart_connect_chk(&entry_sys_context);

       if (entry_sys_context.new_uart_cmd_received_flag)
       {
    	   entry_sys_context.new_uart_cmd_received_flag = false;
    	   parse_cmd(&entry_sys_context);
    	   if(entry_sys_context.garage_config->available_count != 0)
    	   {
    		   break;
    	   }
//    	   display_lcd(&entry_sys_context,&entry_sys_context.garage_config->available_count);
#if SYS_TWO_GATE_MODE
		   parse_cmd(&exit_sys_context);
		   uart_connect_chk(&exit_sys_context);
#endif
       }
       HAL_Delay(500);
   }
   send_msg_state_type(&entry_sys_context,STATUS_SYSTEM_IDLE);
#if SYS_TWO_GATE_MODE
   send_msg_state_type(&exit_sys_context,STATUS_SYSTEM_IDLE);
#endif
#endif
    while(1)
    {
        seq_start(&entry_sys_context);
#if SYS_TWO_GATE_MODE   
        seq_start(&exit_sys_context);
#endif
        HAL_Delay(100);
    }
}


void seq_start(SystemContext_t *g_SystemContext)
{       
        // 1. 거리 측정
        sonar_getDistance();        
        // 차량감지가 되었을 경우      &&    
        // context가 초기 단계일 경우 &&
        // 이전에 차량감지를 안했을 경우
        if (g_SystemContext->cur_sys_state == SYS_STATE_IDLE && \
             g_SystemContext->garage_config->sonar_config->car_detect_flg \
             && !g_SystemContext->is_vehicle_present)
        {
            g_SystemContext->is_vehicle_present = true; // 차량 감지 상태 업데이트
            send_msg_state_type(g_SystemContext, STATUS_VEHICLE_DETECTED);
        }
        else if (g_SystemContext->is_vehicle_present && !g_SystemContext->garage_config->sonar_config->car_detect_flg)
        {
            g_SystemContext->is_vehicle_present = false;
            // 정상 동작(GATE_OPEN) 이 후 차량이 지나간 경우 
            if (g_SystemContext->cur_sys_state == SYS_STATE_GATE_OPENED)
            {
                send_msg_state_type(g_SystemContext, STATUS_VEHICLE_PASSED);
                g_SystemContext->cur_sys_state = STATUS_VEHICLE_PASSED;
            }
            // 정상 동작전에 차량이 벗어난 경우
            else 
            {            
                // 만약 OCR 요청 중이었다면 취소 또는 초기화
                if (g_SystemContext->cur_sys_state == SYS_STATE_OCR_REQUESTED) 
                {
                    g_SystemContext->cur_sys_state = SYS_STATE_IDLE; 
                    send_msg_state_type(g_SystemContext, SYS_STATE_IDLE);
                }
                // OCR 요청 들어가기전에 나간 경우
                else 
                {                
                    send_msg_state_type(g_SystemContext, STATUS_VEHICLE_LEFT);
                    g_SystemContext->cur_sys_state = SYS_STATE_IDLE; // OCR 요청 대기 상태로 전이
                }
            }
        }
        if (g_SystemContext->cur_sys_state == SYS_STATE_GATE_CLOSED)
        {
        	g_SystemContext->cur_sys_state = SYS_STATE_IDLE;
            send_msg_state_type(g_SystemContext, STATUS_SYSTEM_IDLE);
            HAL_Delay(200);
            display_lcd(g_SystemContext,&g_SystemContext->garage_config->available_count);
        }

        // 새로운 uart가 있을 경우
        if (g_SystemContext->new_uart_cmd_received_flag) 
        {
            g_SystemContext->new_uart_cmd_received_flag = false;
            parse_cmd(g_SystemContext);
        }        
}
