#include "unity.h"
#include <stdio.h>

void setUp(void)
{
}

void tearDown(void)
{
}

void test_template(void)
{
    uint32_t expected = 0;
    uint32_t actual = 0;
    TEST_ASSERT_EQUAL_UINT32(expected, actual);
}