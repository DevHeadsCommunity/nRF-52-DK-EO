#ifndef _SENSORS_H_
#define _SENSORS_H_

#include <stdint.h>

int sensor_initialize(void);
int16_t sensor_get_temperature(void);
uint32_t sensor_get_pressure(void);
uint16_t sensor_get_humidity(void);

#endif
