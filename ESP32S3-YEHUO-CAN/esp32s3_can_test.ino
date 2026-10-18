/*
 * ESP32-S3 + 野火小智 CAN 收发器模块（SIT1042AQT/3）
 * 经典 CAN 500 kbit/s 收发测试
 *
 * 接线：
 *   模块 EN  -> 3.3V   （必须 3.3V，不能 5V）
 *   模块 5V  -> 5V
 *   模块 GND -> GND
 *   模块 TXD -> GPIO4
 *   模块 RXD -> GPIO5
 *   模块 CANH/CANL/GND -> 总线
 *
 * 功能：
 *   每秒发送一帧 0x123，8 字节 01..08
 *   同时接收并打印总线上的帧
 *
 * 注意：
 *   - ESP32-S3 TWAI 只支持经典 CAN，不支持 CAN FD
 *   - 总线上至少要有另一个节点 ACK；没有第二个节点时
 *     可临时改成 TWAI_MODE_NO_ACK 做自测
 */

#include "driver/twai.h"

#define CAN_TX 4
#define CAN_RX 5

// 正常总线用 TWAI_MODE_NORMAL；单节点自测可改 TWAI_MODE_NO_ACK
#define CAN_MODE TWAI_MODE_NORMAL

static uint32_t last_tx = 0;

void setup() {
  Serial.begin(115200);
  delay(300);

  twai_general_config_t g_config =
      TWAI_GENERAL_CONFIG_DEFAULT((gpio_num_t)CAN_TX, (gpio_num_t)CAN_RX, CAN_MODE);
  twai_timing_config_t t_config = TWAI_TIMING_CONFIG_500KBITS();
  twai_filter_config_t f_config = TWAI_FILTER_CONFIG_ACCEPT_ALL();

  if (twai_driver_install(&g_config, &t_config, &f_config) != ESP_OK) {
    Serial.println("TWAI install failed");
    return;
  }
  if (twai_start() != ESP_OK) {
    Serial.println("TWAI start failed");
    return;
  }

  Serial.println("TWAI started: 500 kbit/s, TX=GPIO4, RX=GPIO5");
}

void loop() {
  // 总线错误恢复：bus-off 后自动恢复，避免一直 INVALID_STATE
  twai_status_info_t status;
  if (twai_get_status_info(&status) == ESP_OK) {
    if (status.state == TWAI_STATE_BUS_OFF) {
      Serial.println("BUS-OFF, recovering...");
      twai_initiate_recovery();
    } else if (status.state == TWAI_STATE_STOPPED) {
      Serial.println("TWAI stopped, restarting...");
      twai_start();
    }
  }

  // 每秒发一帧
  if (millis() - last_tx >= 1000) {
    last_tx = millis();

    twai_message_t msg = {};
    msg.identifier = 0x123;
    msg.extd = 0;
    msg.rtr = 0;
    msg.data_length_code = 8;
    for (int i = 0; i < 8; i++) {
      msg.data[i] = i + 1;
    }

    esp_err_t ret = twai_transmit(&msg, pdMS_TO_TICKS(100));
    if (ret == ESP_OK) {
      Serial.println("TX 0x123 01 02 03 04 05 06 07 08");
    } else {
      Serial.printf("TX failed: %s\n", esp_err_to_name(ret));
    }
  }

  // 接收
  twai_message_t rx;
  if (twai_receive(&rx, pdMS_TO_TICKS(10)) == ESP_OK) {
    Serial.printf("RX id=0x%X dlc=%d data=", rx.identifier, rx.data_length_code);
    for (int i = 0; i < rx.data_length_code; i++) {
      Serial.printf("%02X ", rx.data[i]);
    }
    Serial.println();
  }
}
