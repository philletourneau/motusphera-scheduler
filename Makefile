# Compiler
CC = gcc

# Compiler Flags
CFLAGS = -Wall -Wextra -std=c11 -pthread -fPIC

# Debugging Flags
DEBUG ?= 0
ifeq ($(DEBUG), 1)
    CFLAGS += -g
endif

DEPS = prebuilt/modbus_utils/include/modbus_utils.h

# Detect platform
UNAME_S := $(shell uname -s)

# Platform-specific settings
ifeq ($(UNAME_S), Darwin)
    # macOS settings
    CFLAGS += -I/opt/homebrew/include -Iprebuilt/libmodbus/include -Iprebuilt/modbus_utils/include
    LDFLAGS += -L/opt/homebrew/lib -Lprebuilt/libmodbus/darwin
    LIBMODBUS_LIB = prebuilt/libmodbus/darwin/libmodbus.dylib
    RPATH_FLAG = -Wl,-rpath,@loader_path/../../libmodbus/darwin
    SHARED_LIB_EXT = dylib
    SHARED_LIB_DIR = prebuilt/modbus_utils/darwin
else
    # Assume Linux (Raspberry Pi) settings
    CFLAGS += -I/usr/include -Iprebuilt/libmodbus/include -Iprebuilt/modbus_utils/include
    LDFLAGS += -L/usr/lib -Lprebuilt/libmodbus/linux
    LIBMODBUS_LIB = prebuilt/libmodbus/linux/libmodbus.so
    RPATH_FLAG = -Wl,-rpath=prebuilt/libmodbus/linux -Wl
    SHARED_LIB_EXT = so
    SHARED_LIB_DIR = prebuilt/modbus_utils/linux
endif

# Include Directories
INCLUDES = -I.

# Source Files
SRCS = modbus_utils.c

# Object Files
OBJS = $(SRCS:.c=.o)

# Shared Library Name
SHARED_LIB = $(SHARED_LIB_DIR)/libmodbus_utils.$(SHARED_LIB_EXT)

# Default target
all: $(SHARED_LIB_DIR) $(SHARED_LIB)

# Ensure the output directory exists
$(SHARED_LIB_DIR):
	mkdir -p $(SHARED_LIB_DIR)

# Build the shared library
$(SHARED_LIB): $(OBJS)
	$(CC) -shared -o $@ $(OBJS) $(LDFLAGS) $(RPATH_FLAG) -lmodbus -lm
ifeq ($(UNAME_S), Darwin)
	install_name_tool -change @rpath/libmodbus.dylib @loader_path/../../libmodbus/darwin/libmodbus.dylib $@
endif

# Compile source files into object files
%.o: %.c $(DEPS)
	$(CC) $(CFLAGS) $(INCLUDES) -c $< -o $@

# Clean up build files
.PHONY: clean
clean:
	rm -f *.o $(SHARED_LIB_DIR)/*.dylib $(SHARED_LIB_DIR)/*.so
