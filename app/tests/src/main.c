#include <zephyr/ztest.h>
#include <zephyr/ztest_assert.h>
#include <zephyr/ztest_test.h>

#include "../src/conversions.h"

ZTEST(nrf52dk_eo_testsuite, test_pressure_conversion) {
  struct sensor_value val;

  val.val1 = 1;
  val.val2 = 500000;
  zassert_equal(sensor_value_to_pressure(val), 1500,
                "1.5 kPa should equal 1500 Pa");

  val.val1 = 0;
  val.val2 = 0;
  zassert_equal(sensor_value_to_pressure(val), 0,
                "Zero input should give zero output");

  val.val1 = -1;
  val.val2 = -500000;
  zassert_equal(sensor_value_to_pressure(val), 0,
                "Negative input should clamp to 0");

  val.val1 = 1000;
  val.val2 = 999000;
  zassert_equal(sensor_value_to_pressure(val), 1000999,
                "Large value conversion failed");

  val.val1 = 0;
  val.val2 = 999;
  zassert_equal(sensor_value_to_pressure(val), 0,
                "999 micro-kPa should truncate to 0 Pa");

  val.val2 = 1000;
  zassert_equal(sensor_value_to_pressure(val), 1,
                "1000 micro-kPa should equal 1 Pa");
}

ZTEST(nrf52dk_eo_testsuite, test_humidity_conversion) {
  struct sensor_value val;

  val.val1 = 50;
  val.val2 = 0;
  zassert_equal(sensor_value_to_humidity(val), 5000,
                "50.00%% RH should equal 5000 centi-percent");

  val.val1 = 12;
  val.val2 = 340000;
  zassert_equal(sensor_value_to_humidity(val), 1234,
                "12.34%% RH should equal 1234 centi-percent");

  val.val1 = -5;
  val.val2 = -100000;
  zassert_equal(sensor_value_to_humidity(val), 0,
                "Negative humidity should clamp to 0");

  val.val1 = 100;
  val.val2 = 1;
  zassert_equal(sensor_value_to_humidity(val), 10000,
                "Humidity >100%% should clamp to 10000");

  val.val1 = 99;
  val.val2 = 990000;
  zassert_equal(sensor_value_to_humidity(val), 9999,
                "99.99%% RH should equal 9999");

  val.val1 = 100;
  val.val2 = 1000000;
  zassert_equal(sensor_value_to_humidity(val), 10000,
                "101%% RH should clamp to 10000");
}

ZTEST(nrf52dk_eo_testsuite, test_temperature_conversion) {
  struct sensor_value val;

  val.val1 = 25;
  val.val2 = 0;
  zassert_equal(sensor_value_to_temperature(val), 2500,
                "25.00°C should equal 2500 centi-degrees");

  val.val1 = -5;
  val.val2 = -250000;
  zassert_equal(sensor_value_to_temperature(val), -525,
                "-5.25°C should equal -525 centi-degrees");

  val.val1 = 0;
  val.val2 = 10000;
  zassert_equal(sensor_value_to_temperature(val), 1,
                "0.01°C should equal 1 centi-degree");

  val.val1 = 0;
  val.val2 = 9999;
  zassert_equal(sensor_value_to_temperature(val), 0,
                "0.009999°C should truncate to 0 centi-degrees");

  val.val2 = 10000;
  zassert_equal(sensor_value_to_temperature(val), 1,
                "0.01°C should equal 1 centi-degree");

  val.val1 = -10;
  val.val2 = -9999;
  zassert_equal(sensor_value_to_temperature(val), -1000,
                "-10.009999°C should truncate to -1000 centi-degrees");
}

ZTEST_SUITE(nrf52dk_eo_testsuite, NULL, NULL, NULL, NULL, NULL);
