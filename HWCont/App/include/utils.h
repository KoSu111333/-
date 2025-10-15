/*
 * utils.h
 *
 *  Created on: Aug 3, 2025
 *      Author: minseopkim
 */

#ifndef INCLUDE_UTILS_H_
#define INCLUDE_UTILS_H_

#include "df.h"

#define AIRCR_VECTKEY_MASK                   ((uint32_t)0x05FA0000)

void sys_reset(void);
void start_timeout(uint32_t timeout_ms);
bool is_timeout(void);
void print_cmd(void);



#endif /* INCLUDE_UTILS_H_ */
