/** ble.c - BLE routines
 * Copyright 2023 Dojo Five
 **/

#include <inttypes.h>
#include <zephyr/types.h>
#include <stddef.h>
#include <string.h>
#include <errno.h>
#include <zephyr/device.h>
#include <zephyr/drivers/uart.h>
#include <zephyr/sys/ring_buffer.h>
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>

#include "ble.h"

#define LOG_MODULE_NAME EO_HIL_SERIAL
LOG_MODULE_REGISTER(LOG_MODULE_NAME);

#define RING_BUF_SIZE 1024
uint8_t ring_buffer[RING_BUF_SIZE];

struct ring_buf ringbuf;

/* change this to any other UART peripheral if desired */
#define UART_DEVICE_NODE DT_CHOSEN(zephyr_shell_uart)

#define MSG_SIZE 32

/* queue to store up to 10 messages (aligned to 4-byte boundary) */
K_MSGQ_DEFINE(uart_msgq, MSG_SIZE, 10, 4);

static const struct device *uart_dev = DEVICE_DT_GET(UART_DEVICE_NODE);

/* receive buffer used in UART ISR callback */
static char rx_buf[1024];
static int rx_buf_pos;
/*
 * Read characters from UART until line end is detected. Afterwards push the
 * data to the message queue.
 */
void serial_cb(const struct device *dev, void *user_data)
{
    uint8_t data[256];
    uint32_t bytes_read;

    if (!uart_irq_update(uart_dev)) {
        return;
    }

    while (uart_irq_rx_ready(uart_dev)) {

        bytes_read = uart_fifo_read(uart_dev, data, 256);

        for(uint32_t i = 0; i < bytes_read; i++)
        {
            uint8_t c = data[i];

            if ((c == '\n' || c == '\r') && rx_buf_pos > 0) {
            /* terminate string */
            rx_buf[rx_buf_pos] = '\0';

            LOG_INF("%s\n", rx_buf);

            /* if queue is full, message is silently dropped */
            k_msgq_put(&uart_msgq, &rx_buf, K_NO_WAIT);

            /* reset the buffer (it was copied to the msgq) */
            rx_buf_pos = 0;
            } else if (rx_buf_pos < (sizeof(rx_buf) - 1)) {
                rx_buf[rx_buf_pos++] = c;
            }
            /* else: characters beyond buffer size are dropped */
        }
    }
}

/*
 * Print a null-terminated string character by character to the UART interface
 */
void print_uart(char *buf)
{
    int msg_len = strlen(buf);

    for (int i = 0; i < msg_len; i++) {
        uart_poll_out(uart_dev, buf[i]);
    }
}

void serial_echo_thread(void)
{
    char tx_buf[MSG_SIZE];

    if (!device_is_ready(uart_dev)) {
        LOG_ERR("UART device not found!");
        return;
    }

    /* configure interrupt and callback to receive data */
    uart_irq_callback_user_data_set(uart_dev, serial_cb, NULL);
    uart_irq_rx_enable(uart_dev);

    /* indefinitely wait for input from the user */
    while (k_msgq_get(&uart_msgq, &tx_buf, K_FOREVER) == 0) {

        if(strcmp("mac_address", tx_buf) == 0)
        {
            LOG_INF("Received MAC address command!");

            uint8_t addr[BLE_ADDR_LEN];
            ble_get_address(addr);

            char device_id_string[30] = {0};

            sprintf(device_id_string, "%02X:%02X:%02X:%02X:%02X:%02X\r\n", addr[5], addr[4], addr[3], addr[2], addr[1], addr[0]);
            print_uart(device_id_string);
        }
        else
        {
            print_uart(tx_buf);
            print_uart("\r\n");
        }
    }
}
