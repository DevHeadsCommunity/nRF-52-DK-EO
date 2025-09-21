#include "bme280.h"
#include "conversions.h"

#include <zephyr/device.h>
#include <zephyr/drivers/sensor.h>
#include <zephyr/logging/log.h>
LOG_MODULE_REGISTER(nrf52dk_eo_bme280);

const struct device *bme280_dev = DEVICE_DT_GET_ANY(bosch_bme280);

int bme280_initialize_device(void) {
  if (!bme280_dev) {
    LOG_ERR("BME280 device node not found");
    return -1;
  }
  if (!device_is_ready(bme280_dev)) {
    LOG_ERR("BME280 device not ready");
    return -1;
  }
  LOG_INF("BME280 initialized");
  return 0;
}

/* Helper: fetch once before reading channels */
static int bme280_fetch(void) {
  int ret = sensor_sample_fetch(bme280_dev);
  if (ret) {
    LOG_ERR("sample_fetch failed (%d)", ret);
    return -1;
  }
  return 0;
}

/* Return temperature in centi-degC (e.g., 2534 => 25.34°C) */
int16_t bme280_get_temperature(void) {
  struct sensor_value t;
  int ret;

  if (bme280_fetch() != 0)
    return -1;

  ret = sensor_channel_get(bme280_dev, SENSOR_CHAN_AMBIENT_TEMP, &t);
  if (ret != 0) {
    LOG_ERR("get temperature failed (%d)", ret);
    return -1;
  }
  return sensor_value_to_temperature(t);
}

uint32_t bme280_get_pressure(void) {
  struct sensor_value p;
  int ret;

  if (bme280_fetch() != 0)
    return (uint32_t)-1;

  ret = sensor_channel_get(bme280_dev, SENSOR_CHAN_PRESS, &p);
  if (ret != 0) {
    LOG_ERR("get pressure failed (%d)", ret);
    return (uint32_t)-1;
  }

  return sensor_value_to_pressure(p);
}

/* Return humidity in centi-%RH (e.g., 4567 => 45.67%) */
uint16_t bme280_get_humidity(void) {
  struct sensor_value h;
  int ret;

  if (bme280_fetch() != 0)
    return (uint16_t)-1;

  ret = sensor_channel_get(bme280_dev, SENSOR_CHAN_HUMIDITY, &h);
  if (ret != 0) {
    LOG_ERR("get humidity failed (%d)", ret);
    return (uint16_t)-1;
  }

  return sensor_value_to_humidity(h);
}
