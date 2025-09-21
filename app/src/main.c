#include "ble.h"
#include "sensors.h"

#include <stdbool.h>
#include <stdio.h>

#include <zephyr/drivers/gpio.h>
#include <zephyr/kernel.h>

#include <zephyr/logging/log.h>
LOG_MODULE_REGISTER(nrf52dk_eo);

#define SLEEP_TIME_MS 1000

#define LED0_NODE DT_ALIAS(led0)

static const struct gpio_dt_spec led = GPIO_DT_SPEC_GET(LED0_NODE, gpios);

static int led_initialize(void) {
  int ret;

  if (!gpio_is_ready_dt(&led)) {
    return -1;
  }

  ret = gpio_pin_configure_dt(&led, GPIO_OUTPUT_ACTIVE);
  if (ret != 0) {
    return -1;
  }

  return 0;
}

static void led_toggle(void) {
  int ret;

  ret = gpio_pin_toggle_dt(&led);
  if (ret < 0) {
    LOG_ERR("failed to toggle led %d", ret);
  }
}

static void led_status(int err) {
  int i;

  if (err) {
    for (i = 0; i < 3; ++i) { // three blinks for an err
      led_toggle();
      k_msleep(SLEEP_TIME_MS);
    }
  }
}

int main(void) {
  int ret;

  ret = led_initialize();
  if (ret < 0) {
    LOG_ERR("failed to initialize led");
    return 0;
  }

  ret = sensor_initialize();
  if (ret < 0) {
    LOG_ERR("bme280 failed to initialize");
    return 0;
  }

  ret = ble_initialize();
  if (ret < 0) {
    LOG_ERR("ble failed to initialize");
    return 0;
  }

  while (1) {
    led_status(ret);
    ret = ble_notify();
    k_msleep(SLEEP_TIME_MS);
  }
  return 0;
}
