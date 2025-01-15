#include <stdio.h>
#include "util.h"

#define MS_PER_SEC   1000
#define SEC_PER_MIN  60
#define MIN_PER_HOUR 60
#define HOUR_PER_DAY 24

#define MS_PER_DAY  (HOUR_PER_DAY * MIN_PER_HOUR * SEC_PER_MIN * MS_PER_SEC)
#define MS_PER_HOUR (MIN_PER_HOUR * SEC_PER_MIN * MS_PER_SEC)
#define MS_PER_MIN  (SEC_PER_MIN * MS_PER_SEC)

void uptime_to_string(int64_t uptime, char *out)
{
    int32_t days = uptime / MS_PER_DAY;
    int32_t hours = (uptime - (days * MS_PER_DAY)) / MS_PER_HOUR;
    int32_t mins  = (uptime - (days * MS_PER_DAY) - (hours * MS_PER_HOUR)) / MS_PER_MIN;
    int32_t secs  = (uptime - (days * MS_PER_DAY) - (hours * MS_PER_HOUR) - (mins * MS_PER_MIN)) / MS_PER_SEC;

    sprintf(out, "%d days, %d hours, %d minutes, %d seconds", days, hours, mins, secs);
}

/**
 * [  0 >= RSSI > -55] -> Great
 * [-55 >= RSSI > -75] -> Good
 * [-75 >= RSSI > -90] -> Poor
 * [-90 >= RSSI      ] -> Unusable
 */
#define RSSI_GREAT_THRESHOLD    -55
#define RSSI_GOOD_THRESHOLD     -75
#define RSSI_POOR_THRESHOLD     -90

util_ble_signal_quality_t util_get_ble_signal_quality(int16_t rssi)
{
    util_ble_signal_quality_t signal_quality = UTIL_BLE_SIGNAL_QUALITY_UNKNOWN;

    if (rssi >= 0)
    {
        // RSSI should always be negative
        signal_quality = UTIL_BLE_SIGNAL_QUALITY_UNKNOWN;
    }
    else if(rssi <= RSSI_POOR_THRESHOLD)
    {
        signal_quality = UTIL_BLE_SIGNAL_QUALITY_UNUSABLE;
    }
    else if (rssi <= RSSI_GOOD_THRESHOLD)
    {
        signal_quality = UTIL_BLE_SIGNAL_QUALITY_POOR;
    }
    else if (rssi <=  RSSI_GREAT_THRESHOLD)
    {
        signal_quality = UTIL_BLE_SIGNAL_QUALITY_GOOD;
    }
    else if (rssi > RSSI_GREAT_THRESHOLD)
    {
        signal_quality = UTIL_BLE_SIGNAL_QUALITY_GREAT;
    }

    return signal_quality;
}
