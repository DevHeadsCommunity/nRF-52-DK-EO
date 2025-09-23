#ifndef _CONVERSIONS_H_
#define _CONVERSIONS_H_

#include <stdint.h>

uint32_t sensor_value_to_pressure(void *value);
uint16_t sensor_value_to_humidity(void *value);
int16_t sensor_value_to_temperature(void *value);

#endif
