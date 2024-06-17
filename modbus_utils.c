#include "modbus_utils.h"
#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>    // For open flags
#include <errno.h>    // For errno and strerror
#include <unistd.h>   // For close
#include <string.h>   // For strerror
#include <time.h>
#include "config.h"

void check_usb_device(const char *device) {
#if SIMULATE 
    printf("skipping USB device check\n");
#else
    int fd = open(device, O_RDWR | O_NOCTTY | O_NONBLOCK);
    if (fd == -1) {
        fprintf(stderr, "Error opening %s: %s\n", device, strerror(errno));
        exit(EXIT_FAILURE);
    }
    close(fd);
#endif
}

modbus_t *initialize_modbus(const char *device, int baud_rate) {
    check_usb_device(device);  // Perform USB device check

    modbus_t *ctx = modbus_new_rtu(device, baud_rate, 'N', 8, 2);
    if (ctx == NULL) {
        fprintf(stderr, "Unable to create the libmodbus context\n");
        return NULL;
    }

    if (modbus_set_error_recovery(ctx, MODBUS_ERROR_RECOVERY_LINK | MODBUS_ERROR_RECOVERY_PROTOCOL) == -1) {
        fprintf(stderr, "Failed to set error recovery mode: %s\n", modbus_strerror(errno));
    }

    if (modbus_connect(ctx) == -1) {
        fprintf(stderr, "Connection failed: %s\n", modbus_strerror(errno));
        modbus_free(ctx);
        return NULL;
    }

    return ctx;
}

void configure_error_safe_modbus(modbus_t *ctx, int slave_id) {
    set_modbus_slave(ctx, slave_id);
    modbus_set_response_timeout(ctx, MODBUS_TIMEOUT_SEC, MODBUS_TIMEOUT_USEC);  //21000 = 21ms
    if (modbus_set_error_recovery(ctx, MODBUS_ERROR_RECOVERY_LINK | MODBUS_ERROR_RECOVERY_PROTOCOL) == -1) {
        fprintf(stderr, "Failed to set error recovery mode: %s\n", modbus_strerror(errno));
    }
}


void send_positions_over_modbus(modbus_t *ctx, uint16_t *positions, uint16_t time_delta_value) {
    struct timespec sleep_duration = {0, BUFFER_MS * 100000L};
    struct timespec longer_sleep_duration = {0, (BUFFER_MS+5) * 100000L};
    #if DEBUG
    struct timespec loop_start_time, loop_end_time, write_start_time, write_end_time;
    clock_gettime(CLOCK_MONOTONIC, &loop_start_time);
    #endif
    for (int unit_id = 1; unit_id <= NUM_UNITS; unit_id++) {
        #if DEBUG
        clock_gettime(CLOCK_MONOTONIC, &write_start_time);
        #endif
        
        uint16_t data[MOTORS_PER_UNIT];
        for (int i = 0; i < MOTORS_PER_UNIT; i++) {
            data[i] = positions[(unit_id - 1) * MOTORS_PER_UNIT + i];
        }
        // Calculate the starting address for this unit
        int start_address = POSITION_START_ADDR + (unit_id - 1) * MOTORS_PER_UNIT;

        set_modbus_slave(ctx, 0);
        //modbus_set_response_timeout(ctx, 0, 10000);  //21000 = 21ms
        //printf("data: %d %d %d %d \n", data[0], data[1], data[2], data[3]);

        int rc = modbus_write_registers(ctx, start_address, MOTORS_PER_UNIT, data);
        if (rc == -1) {
            fprintf(stderr, "Failed to write registers to unit %d: %s\n", unit_id, modbus_strerror(errno));
        }
        
        // Optional sleep to buffer between sending commands
        nanosleep(&sleep_duration, NULL);

        #if DEBUG
        clock_gettime(CLOCK_MONOTONIC, &write_end_time);

        // Calculate the time taken for modbus_write_registers
        double write_time_ms = (write_end_time.tv_sec - write_start_time.tv_sec) * 1000.0 +
                               (write_end_time.tv_nsec - write_start_time.tv_nsec) / 1e6;
        printf("Unit %d took %.2f ms", unit_id, write_time_ms);
        #endif
    }
    //set_modbus_slave(ctx, 1);
    //modbus_set_response_timeout(ctx, 0, 10000);  //21000 = 21ms

    // // TODO CLEANUP
    // char response[1024];
    // int slave_id = 1;
    // int start_address = 1;
    // int num_registers = 2;
    // uint16_t *registers = (uint16_t *)malloc(num_registers * sizeof(uint16_t));
    // int read = modbus_read_registers(ctx, slave_id, start_address, registers);
    // if (read == -1) {
    //     sprintf(response, "{\"error\": \"Failed to read registers: %s\"}", modbus_strerror(errno));
    // } else {
    //     for (int i = 0; i < num_registers; ++i) {
    //         printf("Register %d: %d\n", start_address + i, registers[i]);
    //     }
    // };

    nanosleep(&longer_sleep_duration, NULL);
    
    // Send Sync command 
    set_modbus_slave(ctx, 0); // Set to broadcast
    if (modbus_write_register(ctx, SYNC_REG_ADDR, time_delta_value) == -1) {
        fprintf(stderr, "Failed to send broadcast sync command: %s\n", modbus_strerror(errno));
    }
    nanosleep(&longer_sleep_duration, NULL);

    #if DEBUG
    clock_gettime(CLOCK_MONOTONIC, &loop_end_time);
    // Calculate the time taken for the entire loop iteration
    double loop_time_ms = (loop_end_time.tv_sec - loop_start_time.tv_sec) * 1000.0 +
                            (loop_end_time.tv_nsec - loop_start_time.tv_nsec) / 1e6;
    printf("Loop took %.2f ms", loop_time_ms);
    #endif
}

void write_coils(modbus_t *ctx, int slave_id, int motor_id, int start_address, uint8_t *coils, int num_coils) {
    // Calculate the full start address using motor_id and bit-shifting
    start_address = (motor_id << 8) + start_address;

    set_modbus_slave(ctx, slave_id);

    #if MODBUS_DEBUG
    modbus_set_debug(ctx, true);
    #endif

    configure_error_safe_modbus(ctx, slave_id);

    // Set the response timeout for the coil commands
    uint32_t timeout_sec = 0;  // seconds
    uint32_t timeout_usec = 221000;  // microseconds (221ms)
    modbus_set_response_timeout(ctx, timeout_sec, timeout_usec);

    int rc = modbus_write_bits(ctx, start_address, num_coils, coils);
    if (rc == -1) {
        fprintf(stderr, "Failed to write coils: %s\n", modbus_strerror(errno));
    } else {
        printf("Coils written successfully\n");
    }
}


void set_modbus_slave(modbus_t *ctx, int slave_id) {
    if (modbus_set_slave(ctx, slave_id) == -1) {
        fprintf(stderr, "Failed to set Modbus slave ID: %s\n", modbus_strerror(errno));
        modbus_free(ctx);
        exit(EXIT_FAILURE);
    }
}
void close_modbus(modbus_t *ctx) {
    modbus_close(ctx);
    modbus_free(ctx);
}

