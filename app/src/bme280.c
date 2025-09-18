#include "bme280.h"
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
  if (bme280_fetch() != 0) return -1;

  struct sensor_value t;
  int ret = sensor_channel_get(bme280_dev, SENSOR_CHAN_AMBIENT_TEMP, &t);
  if (ret != 0) {
    LOG_ERR("get temperature failed (%d)", ret);
    return -1;
  }
  /* t.val1 in °C, t.val2 in 1e-6 °C */
  int32_t cdeg = (int32_t)t.val1 * 100 + (int32_t)(t.val2 / 10000); // 1e-6 / 1e4 = 1e-2
  return (int16_t)cdeg;
}

/* Return pressure in Pa (clamped to uint32 range; change type if you need more) */
uint32_t bme280_get_pressure(void) {
  if (bme280_fetch() != 0) return (uint32_t)-1;

  struct sensor_value p;
  int ret = sensor_channel_get(bme280_dev, SENSOR_CHAN_PRESS, &p);
  if (ret != 0) {
    LOG_ERR("get pressure failed (%d)", ret);
    return (uint32_t)-1;
  }
  /* Zephyr pressure: val1 in kPa, val2 in micro-kPa */
  /* Convert to Pa: kPa * 1000 + microkPa * 0.001 */
  int64_t pa = (int64_t)p.val1 * 1000 + (int64_t)(p.val2 / 1000);
  if (pa < 0) pa = 0;
  return (uint32_t)pa;
}

/* Return humidity in centi-%RH (e.g., 4567 => 45.67%) */
uint16_t bme280_get_humidity(void) {
  if (bme280_fetch() != 0) return (uint16_t)-1;

  struct sensor_value h;
  int ret = sensor_channel_get(bme280_dev, SENSOR_CHAN_HUMIDITY, &h);
  if (ret != 0) {
    LOG_ERR("get humidity failed (%d)", ret);
    return (uint16_t)-1;
  }
  /* %RH: val1 in %, val2 in micro-% */
  int32_t cpermil = (int32_t)h.val1 * 100 + (int32_t)(h.val2 / 10000);
  if (cpermil < 0) cpermil = 0;
  if (cpermil > 10000) cpermil = 10000; // clamp 0..100.00%
  return (uint16_t)cpermil;
}