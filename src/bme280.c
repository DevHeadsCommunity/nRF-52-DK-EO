#include "bme280.h"

#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/sensor.h>
#include <zephyr/sys/printk.h>
#include <zephyr/types.h>

#include <zephyr/logging/log.h>
LOG_MODULE_REGISTER(nrf52dk_eo_bme280);

const struct device *bme280_dev = DEVICE_DT_GET_ANY(bosch_bme280);

int bme280_initialize_device(void) {
  if (!bme280_dev) {
    LOG_ERR("device node not found.");
    return -1;
  }

  if (!device_is_ready(bme280_dev)) {
    LOG_ERR("device is not ready");
    return -1;
  }

  LOG_INF("device is initialized");
  return 0;
}

int16_t bme280_get_temperature(void) {
  struct sensor_value temp;

  if (!sensor_channel_get(bme280_dev, SENSOR_CHAN_AMBIENT_TEMP, &temp)) {
    LOG_ERR("failed to get sensor temperature value");
    return -1;
  }
  return (int16_t)(temp.val1 * 100 + temp.val2 / 10000);
}

uint16_t bme280_get_pressure(void) {
  uint32_t pressure_off;
  struct sensor_value pressure;

  if (!sensor_channel_get(bme280_dev, SENSOR_CHAN_PRESS, &pressure)) {
    LOG_ERR("failed to get sensor pressure value");
    return -1;
  }

  pressure_off = (uint32_t)(pressure.val1 * 1000 + pressure.val2 / 10000);
  return (uint16_t)(pressure_off - 50000);
}

uint16_t bme280_get_humidity() {
  struct sensor_value humid;

  if (!sensor_channel_get(bme280_dev, SENSOR_CHAN_HUMIDITY, &humid)) {
    LOG_ERR("failed to get sensor humidity value");
    return -1;
  }

  return (uint16_t)(humid.val1 * 100 + humid.val2 / 10000);
}
