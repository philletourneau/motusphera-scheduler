#ifndef MODBUS_UTILS_H
#define MODBUS_UTILS_H

#include "modbus.h"

modbus_t *initialize_modbus(const char *device, int baud_rate);
void configure_error_safe_modbus(modbus_t *ctx, int slave_id);
void set_modbus_slave(modbus_t *ctx, int slave_id); 
void close_modbus(modbus_t *ctx);
void check_usb_device(const char *device);
void write_coils(modbus_t *ctx, int slave_id, int motor_id, int start_address, uint8_t *coils, int num_coils);

#endif // MODBUS_UTILS_H
