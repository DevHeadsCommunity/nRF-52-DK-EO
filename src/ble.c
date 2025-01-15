/** ble.c - BLE routines
 * Copyright 2023 Dojo Five
 **/

#include <zephyr/types.h>
#include <stddef.h>
#include <string.h>
#include <errno.h>
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <zephyr/bluetooth/bluetooth.h>
#include <zephyr/bluetooth/hci.h>
#include <zephyr/bluetooth/conn.h>
#include <zephyr/bluetooth/uuid.h>
#include <zephyr/bluetooth/gatt.h>
#include <bluetooth/services/nus.h>
#include <zephyr/settings/settings.h>

#include "ble.h"

#define LOG_MODULE_NAME EO_HIL_BLE
LOG_MODULE_REGISTER(LOG_MODULE_NAME);

#define BT_LE_ADV_SETTINGS BT_LE_ADV_PARAM(BT_LE_ADV_OPT_CONNECTABLE | \
                           BT_LE_ADV_OPT_USE_NAME, \
                           BT_GAP_ADV_FAST_INT_MIN_1, \
                           BT_GAP_ADV_FAST_INT_MAX_1, NULL)

#define RX_BUF_SIZE   64
#define MAX_RX_MSGS   16
#define RX_SIZE_ALIGN 4

static const struct bt_data ad[] =
{
    BT_DATA_BYTES(BT_DATA_FLAGS, (BT_LE_AD_GENERAL | BT_LE_AD_NO_BREDR)),
    BT_DATA_BYTES(BT_DATA_UUID16_ALL, BT_UUID_16_ENCODE(BT_UUID_DIS_VAL)),
};

typedef struct
{
    uint8_t size;
    uint8_t data[RX_BUF_SIZE];
} rx_buf;

K_MSGQ_DEFINE(rx_msg_queue, sizeof(rx_buf), MAX_RX_MSGS, RX_SIZE_ALIGN);

static bool ble_connected = false;
static struct bt_conn *default_conn;
static uint8_t ble_local_address[BLE_ADDR_LEN] = {0};

static void connected(struct bt_conn *conn, uint8_t err)
{
    if (err)
    {
        LOG_ERR("Connection failed (err 0x%02x)\n", err);
    } else
    {
        ble_connected = true;
        LOG_INF("Connected\n");

        /* Active connection exists, disconnect this client to prevent two simultaneous connections. */
        if (default_conn)
        {
            LOG_INF("Connection exists, disconnect second connection\n");
            bt_conn_disconnect(conn, BT_HCI_ERR_REMOTE_USER_TERM_CONN);
            return;
        }

        default_conn = bt_conn_ref(conn);
    }
}

static void disconnected(struct bt_conn *conn, uint8_t reason)
{
    if (default_conn)
    {
        /* Calling unref will restart advertising */
        bt_conn_unref(default_conn);

        /* Reset to NULL indicating we no longer have an active connection */
        default_conn = NULL;
    }

    ble_connected = false;
}

BT_CONN_CB_DEFINE(conn_callbacks) =
{
    .connected = connected,
    .disconnected = disconnected,
};

static void bt_receive_cb(struct bt_conn *conn, const uint8_t *const data, uint16_t len)
{
    rx_buf buf = {0};

    LOG_INF("Data received: %u bytes\n", len);

    buf.size = (uint8_t)len;
    memcpy(&buf.data[0], data, len);
    k_msgq_put(&rx_msg_queue, &buf, K_NO_WAIT);
}

static struct bt_nus_cb nus_cb =
{
    .received = bt_receive_cb,
};

bool ble_init()
{
    int err = bt_enable(NULL);
    if (err)
    {
        LOG_ERR("Bluetooth init failed (err %d)\n", err);
        return false;
    }

    LOG_INF("Bluetooth initialized\n");

    err = bt_nus_init(&nus_cb);
    if (err)
    {
        LOG_ERR("Failed to initialize UART service (err: %d)", err);
        return false;
    }

    size_t num_ids;
    bt_addr_le_t addrs[CONFIG_BT_ID_MAX];
    bt_id_get(addrs, &num_ids);

    if(num_ids != 1)
    {
        LOG_ERR("Number of BT identities (%d) was not 1!", num_ids);
        return false;
    }

    memcpy(ble_local_address, addrs[0].a.val, BLE_ADDR_LEN);

    err = bt_le_adv_start(BT_LE_ADV_SETTINGS, ad, ARRAY_SIZE(ad), NULL, 0);
    if (err)
    {
        LOG_ERR("Advertising failed to start (err %d)\n", err);
        return false;
    }

    LOG_INF("Advertising successfully started\n");

    return true;
}

bool ble_is_connected()
{
    return ble_connected;
}

void ble_get_address(uint8_t *addr_out)
{
    memcpy(addr_out, &ble_local_address, BLE_ADDR_LEN);
}

void ble_write_thread(void)
{
    rx_buf buf;

    while (1)
    {
        /* get a data item */
        k_msgq_get(&rx_msg_queue, &buf, K_FOREVER);

        LOG_INF("Sending data of length %u\n", buf.size);

        bt_nus_send(NULL, buf.data, buf.size);
    }
}
