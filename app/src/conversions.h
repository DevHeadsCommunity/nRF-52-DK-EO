#ifndef _CONVERSIONS_H_
#define _CONVERSIONS_H_

#include <stdint.h>

#include <zephyr/drivers/sensor.h>

uint32_t sensor_value_to_pressure(struct sensor_value value);
uint16_t sensor_value_to_humidity(struct sensor_value value);
int16_t sensor_value_to_temperature(struct sensor_value value);

#endif
