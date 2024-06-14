# Compiler
CC = gcc

# Compiler Flags
CFLAGS = -Wall -Wextra -std=c11 -pthread -fPIC

# Debugging Flags
DEBUG ?= 0
ifeq ($(DEBUG), 1)
    CFLAGS += -g
endif

DEPS = config.h

# Detect platform
UNAME_S := $(shell uname -s)

# Platform-specific settings
ifeq ($(UNAME_S), Darwin)
    # macOS settings
    CFLAGS += -I/opt/homebrew/include -Iprebuilt/libmodbus/include
    LDFLAGS += -L/opt/homebrew/lib -Lprebuilt/libmodbus/darwin
    LIBMODBUS_LIB = prebuilt/libmodbus/darwin/libmodbus.dylib
    RPATH_FLAG = -Wl,-rpath,lib/libmodbus/src/.libs -Wl
    SHARED_LIB_EXT = dylib
else
    # Assume Linux (Raspberry Pi) settings
    CFLAGS += -I/usr/include -Iprebuilt/libmodbus/include
    LDFLAGS += -L/usr/lib -Lprebuilt/libmodbus/linux
    LIBMODBUS_LIB = prebuilt/libmodbus/linux/libmodbus.so
    RPATH_FLAG = -Wl,-rpath=prebuilt/libmodbus/linux -Wl
    SHARED_LIB_EXT = so
endif

# Include Directories
INCLUDES = -I.

# Source Files
SRCS = modbus_utils.c

# Object Files
OBJS = $(SRCS:.c=.o)

# Shared Library Name
SHARED_LIB = libmodbus_utils.$(SHARED_LIB_EXT)

# Default target
all: $(SHARED_LIB)

# Build the shared library
$(SHARED_LIB): $(OBJS)
	$(CC) -shared -o $@ $(OBJS) $(LDFLAGS) $(RPATH_FLAG) -lmodbus -lm

# Compile source files into object files
%.o: %.c $(DEPS)
	$(CC) $(CFLAGS) $(INCLUDES) -c $< -o $@

# Clean up build files
.PHONY: clean
clean:
	rm -f *.o $(SHARED_LIB)
