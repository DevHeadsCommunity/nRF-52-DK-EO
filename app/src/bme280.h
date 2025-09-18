#ifndef _BME280_H_
#define _BME280_H_

#include <stdint.h>

int bme280_initialize_device(void);
int16_t bme280_get_temperature(void);
uint32_t bme280_get_pressure(void);
uint16_t bme280_get_humidity(void);

#endif
