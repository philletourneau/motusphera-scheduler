#define SYNC_REG_ADDR 99
#define POSITION_START_ADDR 100
#define BUFFER_MS 20  // 54 Define a buffer of 5.4ms
#define NUM_MOTORS 123
#define NUM_UNITS 31
#define MOTORS_PER_UNIT 4
#define BAUD_RATE 460800
#define MAX_POSITION 11000
#define MIN_POSITION 0
#define MAX_SPEED 7000
//#define MODBUS_TIMEOUT 720000
#define MODBUS_TIMEOUT_USEC 800000
#define MODBUS_TIMEOUT_SEC 0

//#define RESPONSE_BUFFER_SIZE 1024  //websocket server callback

#define SIMULATE 0  // Set to 1 to enable simulation, 0 to disable
#define DEBUG 0
#define MODBUS_DEBUG 0
#define FPS 2
#define USEBROADCAST 1

#if defined(__APPLE__)
#define USB_DEVICE "/dev/tty.usbserial-AC0134TM"
#else
#define USB_DEVICE "/dev/ttyUSB0"
#endif