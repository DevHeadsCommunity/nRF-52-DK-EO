/** main.c - Application main entry point
 *
 * Copyright 2023 Dojo Five
 **/

#include <zephyr/types.h>
#include <stddef.h>
#include <string.h>
#include <zephyr/sys/printk.h>
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <zephyr/settings/settings.h>
#include <dk_buttons_and_leds.h>
#include "app_version.h"

#include "ble.h"
#include "serial.h"

#define LOG_MODULE_NAME EO_HIL_MAIN
LOG_MODULE_REGISTER(LOG_MODULE_NAME);

// Uncomment the following line to enable LED3 on the nRF53DK
// #define ENABLE_LED3

#define LED_PERIOD_MS 1000

int main(void)
{
    bool heartbeat_led_state = false;
    bool bt_led_state = false;

    if(dk_leds_init())
    {
        LOG_ERR("DK LEDs failed to init\n");
        return 0;
    }

#ifdef ENABLE_LED3
    dk_set_led(DK_LED3, 1);
#endif

    /* Set the DIS FW Version from the Zephyr application version system */
    char app_version_str[64];
    sprintf(app_version_str, "%d.%d", APP_VERSION_MAJOR, APP_VERSION_MINOR);
    settings_runtime_set("bt/dis/fw",
                 app_version_str,
                 strlen(app_version_str));

    if(!ble_init())
    {
        LOG_ERR("BLE failed to init\n");
        return 0;
    }

    while(true)
    {
        dk_set_led(DK_LED1, heartbeat_led_state);
        heartbeat_led_state = !heartbeat_led_state;

        if(!ble_is_connected())
        {
            dk_set_led(DK_LED2, heartbeat_led_state);
            bt_led_state = !bt_led_state;
        }
        else
        {
            dk_set_led(DK_LED2, true);
        }

        k_msleep(LED_PERIOD_MS);
    }
}

#define STACKSIZE 2048
#define PRIORITY 7
K_THREAD_DEFINE(ble_write_thread_id, STACKSIZE, ble_write_thread, NULL, NULL, NULL, PRIORITY, 0, 0);
K_THREAD_DEFINE(serial_echo_thread_id, STACKSIZE, serial_echo_thread, NULL, NULL, NULL, PRIORITY, 0, 0);
