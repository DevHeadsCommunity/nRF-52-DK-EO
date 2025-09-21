#include "sensors.h"
#include "bme280.h"
#include "conversions.h"

#include <zephyr/device.h>
#include <zephyr/drivers/sensor.h>
#include <zephyr/logging/log.h>
LOG_MODULE_REGISTER(nrf52dk_eo_sensor);

#if defined(CONFIG_BOARD_THINGY52_NRF52832)
const struct device *temp_sensor = DEVICE_DT_GET_ANY(DT_ALIAS(hts221));
const struct device *press_sensor = DEVICE_DT_GET_ANY(DT_ALIAS(lps22hbpress));
#endif

int sensor_initialize(void) {
  int ret;
#if defined(CONFIG_BOARD_THINGY52_NRF52832)
  if (!temp_sensor) {
    LOG_ERR("temp sensor not found");
    return -1;
  }

  if (!press_sensor) {
    LOG_ERR("pressure sensor not found");
    return -1;
  }

  if (!device_is_ready(temp_sensor)) {
    LOG_ERR("temp sensor is not ready");
    return -1;
  }

  if (!device_is_ready(press_sensor)) {
    LOG_ERR("pressure sensor is not ready");
    return -1;
  }
#else
  ret = bme280_initialize_device();
#endif
  return ret;
}

int16_t sensor_get_temperature(void) {
#if defined(CONFIG_BOARD_THINGY52_NRF52832)
  int ret;
  struct sensor_value temp;
  if (sensor_sample_fetch(temp_sensor) != 0) {
    return (int16_t)-1;
  }

  ret = sensor_channel_get(temp_sensor, SENSOR_CHAN_AMBIENT_TEMP, &temp);
  if (ret != 0) {
    LOG_ERR("get temperature failed");
    return (int16_t)-1;
  }

  return sensor_value_to_temperature(temp);
#else
  return bme280_get_temperature();
#endif
}

uint32_t sensor_get_pressure(void) {
#if defined(CONFIG_BOARD_THINGY52_NRF52832)
  int ret;
  struct sensor_value press;
  if (sensor_sample_fetch(press_sensor) != 0) {
    return (uint32_t)-1;
  }

  ret = sensor_channel_get(press_sensor, SENSOR_CHAN_PRESS, &press);
  if (ret != 0) {
    LOG_ERR("get pressure failed");
    return (int16_t)-1;
  }

  return sensor_value_to_pressure(press);
#else
  return bme280_get_pressure();
#endif
}
uint16_t sensor_get_humidity(void) {
#if defined(CONFIG_BOARD_THINGY52_NRF52832)
  int ret;
  struct sensor_value humid;
  if (sensor_sample_fetch(temp_sensor) != 0) {
    return (uint16_t)-1;
  }

  ret = sensor_channel_get(temp_sensor, SENSOR_CHAN_HUMIDITY, &humid);
  if (ret != 0) {
    LOG_ERR("get humidity failed");
    return (int16_t)-1;
  }

  return sensor_value_to_humidity(humid);
#else
  return bme280_get_humidity();
#endif
}
