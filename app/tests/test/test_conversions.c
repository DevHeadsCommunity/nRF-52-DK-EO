#include "unity.h"

#include "../src/conversions.h"

TEST_SOURCE_FILE("../src/conversions.c");

struct sensor_value {
  int32_t val1;
  int32_t val2;
};

void setUp(void) {}

void tearDown(void) {}

void test_pressure_conversion(void) {
  struct sensor_value val;

  val.val1 = 1;
  val.val2 = 500000;
  TEST_ASSERT_EQUAL_INT32(1500, sensor_value_to_pressure(&val));

  val.val1 = 0;
  val.val2 = 0;
  TEST_ASSERT_EQUAL_INT32(0, sensor_value_to_pressure(&val));

  val.val1 = -1;
  val.val2 = -500000;
  TEST_ASSERT_EQUAL_INT32(0, sensor_value_to_pressure(&val));

  val.val1 = 1000;
  val.val2 = 999000;
  TEST_ASSERT_EQUAL_INT32(1000999, sensor_value_to_pressure(&val));

  val.val1 = 0;
  val.val2 = 999;
  TEST_ASSERT_EQUAL_INT32(0, sensor_value_to_pressure(&val));

  val.val1 = 0;
  val.val2 = 1000;
  TEST_ASSERT_EQUAL_INT32(1, sensor_value_to_pressure(&val));
}

void test_humidity_conversion(void) {
  struct sensor_value val;

  val.val1 = 50;
  val.val2 = 0;
  TEST_ASSERT_EQUAL_INT32(5000, sensor_value_to_humidity(&val));

  val.val1 = 12;
  val.val2 = 340000;
  TEST_ASSERT_EQUAL_INT32(1234, sensor_value_to_humidity(&val));

  val.val1 = -5;
  val.val2 = -100000;
  TEST_ASSERT_EQUAL_INT32(0, sensor_value_to_humidity(&val));

  val.val1 = 100;
  val.val2 = 1;
  TEST_ASSERT_EQUAL_INT32(10000, sensor_value_to_humidity(&val));

  val.val1 = 99;
  val.val2 = 990000;
  TEST_ASSERT_EQUAL_INT32(9999, sensor_value_to_humidity(&val));

  val.val1 = 100;
  val.val2 = 1000000;
  TEST_ASSERT_EQUAL_INT32(10000, sensor_value_to_humidity(&val));
}

void test_temperature_conversion(void) {
  struct sensor_value val;

  val.val1 = 25;
  val.val2 = 0;
  TEST_ASSERT_EQUAL_INT32(2500, sensor_value_to_temperature(&val));

  val.val1 = -5;
  val.val2 = -250000;
  TEST_ASSERT_EQUAL_INT32(-525, sensor_value_to_temperature(&val));

  val.val1 = 0;
  val.val2 = 10000;
  TEST_ASSERT_EQUAL_INT32(1, sensor_value_to_temperature(&val));

  val.val1 = 0;
  val.val2 = 9999;
  TEST_ASSERT_EQUAL_INT32(0, sensor_value_to_temperature(&val));

  val.val1 = 0;
  val.val2 = 10000;
  TEST_ASSERT_EQUAL_INT32(1, sensor_value_to_temperature(&val));

  val.val1 = -10;
  val.val2 = -9999;
  TEST_ASSERT_EQUAL_INT32(-1000, sensor_value_to_temperature(&val));
}
