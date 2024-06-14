import asyncio
import logging
import platform
from pymodbus.client import AsyncModbusSerialClient
from pymodbus.exceptions import ModbusException, ConnectionException
from pymodbus.framer import ModbusRtuFramer
from constants import MODBUS_MULTIPLIER, TIMER_INTERVAL, START_ADDRESS, SYNC_REGISTER

RETRY_DELAY = 1  # Delay in seconds before retrying connection
MAX_RETRIES = 3  # Maximum number of retries
WRITE_DELAY = 0.007  # Delay of 10 ms between each Modbus register write

logging.basicConfig(level=logging.DEBUG)  # Set logging level to debug

async def async_modbus_connect():
    print("--- Starting async Modbus")

    # Determine the port based on the operating system
    if platform.system() == 'Darwin':  # MacOS
        port = '/dev/tty.usbserial-AC0134TM'
    else:
        port = '/dev/ttyUSB0'
    
    client = AsyncModbusSerialClient(
        port=port,  
        framer=ModbusRtuFramer,
        baudrate=460800,
        bytesize=8,
        parity="N",
        stopbits=1,
        timeout=0.4,  # Increased timeout for better stability
        retries=1,
        retry_on_empty=False,
        broadcast_enable=True,
    )
    retries = 0
    while retries < MAX_RETRIES:
        await client.connect()
        if client.connected:
            logging.debug("Connected to Modbus")
            return client
        else:
            logging.warning(f"Failed to connect to Modbus. Retrying in {RETRY_DELAY} seconds...")
            await asyncio.sleep(RETRY_DELAY)
            retries += 1
    logging.error("Failed to connect to Modbus after multiple retries.")
    return None

async def write_coil(client, slave_id, motor_id, coil_address, coil_value):
    """Write to a coil for a given slave ID, motor ID, and coil address."""
    start_address = (motor_id << 8) + coil_address  # Bit shifting to combine motor_id and coil_address

    try:
        if not client.connected:
            logging.debug("Client not connected. Attempting to reconnect.")
            await client.connect()
            if not client.connected:
                raise ConnectionException("Failed to reconnect to Modbus")
        
        logging.debug(f"Writing to coil {coil_address} (start_address {start_address}) at slave {slave_id}")
        await client.write_coil(start_address, coil_value, unit=slave_id)
        await asyncio.sleep(WRITE_DELAY)  # Add delay between writes
        logging.debug("Coil written successfully")
    except (ModbusException, ConnectionException) as e:
        logging.error(f"Error writing to coil: {e}")

async def sync_modbus_register(client):
    """Write to the SYNC_REGISTER with a value of TIMER_INTERVAL * 1000."""
    sync_value = int((TIMER_INTERVAL * 1000)+50)
    try:
        await client.write_register(SYNC_REGISTER, sync_value, unit=0)
        logging.debug(f"Sync register {SYNC_REGISTER} set to {sync_value}")
    except (ModbusException, ConnectionException) as e:
        logging.error(f"Error writing to sync register: {e}")

async def send_positions_modbus(client, positions):
    # Multiply each position by MODBUS_MULTIPLIER and convert to int
    processed_positions = [int(pos * MODBUS_MULTIPLIER) for pos in positions]
    logging.debug("Sending positions: {}".format(processed_positions))
    
    try:
        if not client.connected:
            logging.debug("Client not connected. Attempting to reconnect.")
            await client.connect()
            if not client.connected:
                raise ConnectionException("Failed to reconnect to Modbus")
        
        address = START_ADDRESS
        for i in range(0, len(processed_positions), 4):
            batch = processed_positions[i:i+4]
            logging.debug(f"Writing batch to address {address}: {batch}")
            await client.write_registers(address, batch, unit=0)
            await asyncio.sleep(WRITE_DELAY)  # Add delay between writes
            address += len(batch)
        
        # Call sync_modbus_register after sending all positions
        await asyncio.sleep(WRITE_DELAY)  # Add delay between writes
        await sync_modbus_register(client)
        await asyncio.sleep(WRITE_DELAY)  # Add delay between writes
    except (ModbusException, ConnectionException) as e:
        logging.error(f"Error sending positions: {e}")

async def main():
    client = await async_modbus_connect()
    if client:
        try:
            positions = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]  # Example positions
            await send_positions_modbus(client, positions)
        finally:
            await client.close()
            logging.debug("Client connection closed.")

if __name__ == "__main__":
    asyncio.run(main())
