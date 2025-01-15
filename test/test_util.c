#include "unity.h"     // compile/link in Unity test framework
#include "util.h"

#define UPTIME_STRING_LEN 64

void test_uptime_1()
{
    int64_t uptime = 1768;

    char actual_string[UPTIME_STRING_LEN];

    uptime_to_string(uptime, actual_string);

    char expected_string[] = "0 days, 0 hours, 0 minutes, 1 seconds";

    TEST_ASSERT_EQUAL_STRING(expected_string, actual_string);
}

void test_uptime_2()
{
    int64_t uptime = 347654189;

    char actual_string[UPTIME_STRING_LEN];

    uptime_to_string(uptime, actual_string);

    char expected_string[] = "4 days, 0 hours, 34 minutes, 14 seconds";

    TEST_ASSERT_EQUAL_STRING(expected_string, actual_string);
}