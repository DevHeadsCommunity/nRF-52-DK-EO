#ifndef UTIL_H
#define UTIL_H

#include <stdint.h>

/**
 * @brief Enumeration for top-level BLE signal quality indicators
 */
typedef enum
{
    UTIL_BLE_SIGNAL_QUALITY_UNKNOWN,
    UTIL_BLE_SIGNAL_QUALITY_UNUSABLE,
    UTIL_BLE_SIGNAL_QUALITY_POOR,
    UTIL_BLE_SIGNAL_QUALITY_GOOD,
    UTIL_BLE_SIGNAL_QUALITY_GREAT,
} util_ble_signal_quality_t;

/**
 * @brief Convert an uptime from raw milliseconds to a string, with
 * the format "X days, X hours, X minutes, X seconds". It is the caller's
 * responsibility to ensure that the output parameter has adequate memory allocated.
 *
 * @param uptime Uptime, in milliseconds
 * @param out    Output parameter for string output
 */
void uptime_to_string(int64_t uptime, char *out);

/**
 * @brief Calculates the BLE signal quality that can be used for a UI element.
 *
 * @param rssi BLE received signal strength indicator (RSSI)
 * @return ble_signal_quality_t that correlates with passed in RSSI
 */
util_ble_signal_quality_t util_get_ble_signal_quality(int16_t rssi);

#endif
