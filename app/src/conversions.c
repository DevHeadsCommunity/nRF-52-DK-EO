#include "conversions.h"

/* conversions */
uint32_t sensor_value_to_pressure(void *val) {
  /* this hack to allow testing in ceedling without reliance on the
     <zephyr/drivers/sensor.h> library
   */
  struct sensor_value {
    int32_t val1;
    int32_t val2;
  };

  if (!val) {
    return 0;
  }

  struct sensor_value value = *(struct sensor_value *)val;
  /* Zephyr pressure: val1 in kPa, val2 in micro-kPa */
  /* Convert to Pa: kPa * 1000 + microkPa * 0.001 */
  int64_t pa = (int64_t)value.val1 * 1000 + (int64_t)(value.val2 / 1000);
  if (pa < 0)
    pa = 0;

  return (uint32_t)pa;
}

uint16_t sensor_value_to_humidity(void *val) {
  struct sensor_value {
    int32_t val1;
    int32_t val2;
  };

  if (!val) {
    return 0;
  }

  struct sensor_value value = *(struct sensor_value *)val;
  /* %RH: val1 in %, val2 in micro-% */
  int32_t cpermil = (int32_t)value.val1 * 100 + (int32_t)(value.val2 / 10000);
  if (cpermil < 0)
    cpermil = 0;
  if (cpermil > 10000)
    cpermil = 10000; // clamp 0..100.00%
  return (uint16_t)cpermil;
}

int16_t sensor_value_to_temperature(void *val) {
  struct sensor_value {
    int32_t val1;
    int32_t val2;
  };

  if (!val) {
    return 0;
  }

  struct sensor_value value = *(struct sensor_value *)val;
  /* t.val1 in °C, t.val2 in 1e-6 °C */
  int32_t cdeg = (int32_t)value.val1 * 100 +
                 (int32_t)(value.val2 / 10000); // 1e-6 / 1e4 = 1e-2
  return (int16_t)cdeg;
}
