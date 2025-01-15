#ifndef BLE_H
#define BLE_H

#include <stdbool.h>

/* Length, in bytes of a BLE address */
#define BLE_ADDR_LEN 6

/**
 * @brief Initialize BLE and start advertising.
 *
 * @return true On success
 * @return false On error
 */
bool ble_init();

/**
 * @brief Returns the connection status.
 *
 * @return true If connected
 * @return false If not connected
 */
bool ble_is_connected();

/**
 * @brief Returns the BLE address of this device.
 *
 * @param addr_out Out pointer for the address value (must be at least BLE_ADDR_LEN bytes)
 * @return void
 */
void ble_get_address(uint8_t *addr_out);

/**
 * @brief Implementation for a thread that constantly listens for received NUS data,
 * and echos it back to all connected senders. Intended to be the entry point
 * of a thread.
 */
void ble_write_thread(void);


#endif