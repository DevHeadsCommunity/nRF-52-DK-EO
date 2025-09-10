#include "ble.h"
#include "bme280.h"

#include <zephyr/bluetooth/bluetooth.h>
#include <zephyr/bluetooth/conn.h>
#include <zephyr/bluetooth/gatt.h>
#include <zephyr/bluetooth/hci.h>
#include <zephyr/bluetooth/services/nus.h>
#include <zephyr/bluetooth/uuid.h>

#include <zephyr/logging/log.h>
LOG_MODULE_REGISTER(nrf52dk_eo_ble);

#define DEVICE_NAME CONFIG_BT_DEVICE_NAME
#define DEVICE_NAME_LEN (sizeof(DEVICE_NAME) - 1)

// BLE service e177af9e-e1f0-4f65-8206-29507e994416
#define BT_UUID_CUSTOM_SERVICE_VAL                                             \
  BT_UUID_128_ENCODE(0xe177af9e, 0xe1f0, 0x4f65, 0x8206, 0x29507e994416)

static struct bt_uuid_128 service_uuid =
    BT_UUID_INIT_128(BT_UUID_CUSTOM_SERVICE_VAL);

// BLE characteristic e177af9e-e1f0-4f65-8206-29507e994417
static struct bt_uuid_128 characteristic_uuid = BT_UUID_INIT_128(
    BT_UUID_128_ENCODE(0xe177af9e, 0xe1f0, 0x4f65, 0x8206, 0x29507e994417));

// temperature, pressure, humidity
static uint8_t sensor_values[6] = {0, 0, 0, 0, 0, 0};
static uint8_t indicate;
static uint8_t indicating;
static struct bt_gatt_indicate_params indicate_params;

static void ccc_cfg_changed(const struct bt_gatt_attr *attr, uint16_t value) {
  ARG_UNUSED(attr);

  indicate = 0U;
  switch (value) {
  case BT_GATT_CCC_NOTIFY:
    LOG_DBG("CMD RX/TX CCCD subscribed");
    break;
  case BT_GATT_CCC_INDICATE:
    indicate = 1U;
    break;
  case 0:
    LOG_DBG("CMD RX/TX CCCD unsubscribed");
    break;

  default:
    LOG_DBG("failed CCCD has invalid value");
  }
}

static bool sensor_values_updated(void) {
  uint8_t current_buffer[6];
  int16_t temp;
  uint16_t humid, press;

  temp = bme280_get_temperature();
  press = bme280_get_pressure();
  humid = bme280_get_humidity();

  current_buffer[0] = temp & 0xFF;
  current_buffer[1] = temp >> 8;
  current_buffer[2] = press & 0xFF;
  current_buffer[3] = press >> 8;
  current_buffer[4] = humid & 0xFF;
  current_buffer[5] = humid >> 8;

  if (memcmp(sensor_values, current_buffer, sizeof(current_buffer)) != 0) {
    memcpy(sensor_values, current_buffer, sizeof(current_buffer));
    return true;
  }

  return false;
}

static ssize_t read_characteristic(struct bt_conn *conn,
                                   const struct bt_gatt_attr *attr, void *buf,
                                   uint16_t len, uint16_t offset) {
  if (sensor_values_updated()) {
    // we should do something ?
  }
  const char *value = attr->user_data;

  return bt_gatt_attr_read(conn, attr, buf, len, offset, value,
                           sizeof(sensor_values));
}

// primary service def.
BT_GATT_SERVICE_DEFINE(
    service, BT_GATT_PRIMARY_SERVICE(&service_uuid),
    BT_GATT_CHARACTERISTIC(&characteristic_uuid.uuid,
                           BT_GATT_CHRC_READ | BT_GATT_CHRC_INDICATE,
                           BT_GATT_PERM_READ, read_characteristic, NULL,
                           sensor_values),
    BT_GATT_CCC(ccc_cfg_changed, BT_GATT_PERM_READ | BT_GATT_PERM_WRITE), );

// advertising data
static const struct bt_data advert_data[] = {
    BT_DATA_BYTES(BT_DATA_FLAGS, (BT_LE_AD_GENERAL | BT_LE_AD_NO_BREDR)),
    BT_DATA_BYTES(BT_DATA_UUID128_ALL, BT_UUID_CUSTOM_SERVICE_VAL),
};

static const struct bt_data scan_data[] = {
    BT_DATA(BT_DATA_NAME_COMPLETE, CONFIG_BT_DEVICE_NAME,
            sizeof(CONFIG_BT_DEVICE_NAME) - 1),
};

static void bt_ready(int err) {
  int ret;

  if (err) {
    LOG_ERR("ble not initialized %d", err);
    return;
  }

  LOG_INF("ble initialized");
  ret = bt_le_adv_start(BT_LE_ADV_CONN_FAST_1, advert_data,
                        ARRAY_SIZE(advert_data), scan_data,
                        ARRAY_SIZE(scan_data));
  if (ret != 0) {
    LOG_ERR("advertising failed to start %d", ret);
    return;
  }

  LOG_INF("advertising started");
}

static void indicate_cb(struct bt_conn *conn,
                        struct bt_gatt_indicate_params *params, uint8_t err) {
  LOG_INF("indication %s", err != 0U ? "failed" : "success");
}

static void indicate_destroy(struct bt_gatt_indicate_params *params) {
  LOG_INF("indication complete");
  indicating = 0U;
}

static void connected(struct bt_conn *conn, uint8_t err) {
  char addr[BT_ADDR_LE_STR_LEN];

  bt_addr_le_to_str(bt_conn_get_dst(conn), addr, sizeof(addr));
  if (err) {
    LOG_ERR("failed to connect to %s, err 0x%02x %s", addr, err,
            bt_hci_err_to_str(err));
    return;
  }

  LOG_INF("connected to %s", addr);
}

static void disconnected(struct bt_conn *conn, uint8_t reason) {
  char addr[BT_ADDR_LE_STR_LEN];

  bt_addr_le_to_str(bt_conn_get_dst(conn), addr, sizeof(addr));

  LOG_INF("disconnected from %s, reason 0x%02x %s", addr, reason,
          bt_hci_err_to_str(reason));
}

BT_CONN_CB_DEFINE(conn_callbacks) = {
    .connected = connected,
    .disconnected = disconnected,
};

static void nus_notif_enabled(bool enabled, void *ctx) {
  ARG_UNUSED(ctx);

  LOG_INF("nus notification - %s", (enabled ? "enabled" : "disabled"));
}

static void nus_received(struct bt_conn *conn, const void *data, uint16_t len,
                         void *ctx) {
  ARG_UNUSED(ctx);

  int ret;

  LOG_INF("nus received - Len: %d, Message: %s", len, (char *)data);

  ret = bt_nus_send(conn, (char *)data, len);
  if (ret) {
    LOG_ERR("failed to send NUS %d", ret);
  }
}

struct bt_nus_cb nus_listener = {
    .notif_enabled = nus_notif_enabled,
    .received = nus_received,
};

void ble_update_indication(void) {
  int ret;

  if (sensor_values_updated() && indicate == 0) {
    indicate_params.attr = &service.attrs[2];
    indicate_params.func = indicate_cb;
    indicate_params.destroy = indicate_destroy;
    indicate_params.data = sensor_values;
    indicate_params.len = sizeof(sensor_values);

    ret = bt_gatt_indicate(NULL, &indicate_params);
    if (ret != 0) {
      LOG_ERR("indicate failed %d", ret);
    }
  }
}

int ble_initialize(void) {
  int ret;

  ret = bt_nus_cb_register(&nus_listener, NULL);
  if (ret) {
    LOG_ERR("failed to register NUS callback: %d", ret);
    return -1;
  }

  ret = bt_enable(bt_ready);
  if (ret != 0) {
    LOG_ERR("ble initialization failure %d", ret);
    return -1;
  }

  return 0;
}
