import asyncio
import websockets
import queue
import threading

connected_clients = set()
data_queue = queue.Queue()
received_positions = None
positions_lock = threading.Lock()

async def handler(websocket, path):
    global received_positions
    # Register client
    connected_clients.add(websocket)
    try:
        async for message in websocket:
            # Assume the message is a list of positions in JSON format
            positions = json.loads(message)
            with positions_lock:
                received_positions = positions
            # Echo the received message back to the client
            await websocket.send(f"Received: {message}")
    except websockets.ConnectionClosed:
        pass
    finally:
        # Unregister client
        connected_clients.remove(websocket)

async def send_updates():
    while True:
        if not data_queue.empty():
            data = data_queue.get()
            for client in connected_clients:
                await client.send(f"Update: {data}")
        await asyncio.sleep(0.1)  # Adjust the sleep interval as needed

async def start_server():
    server = await websockets.serve(handler, "localhost", 8765)
    await asyncio.gather(server.wait_closed(), send_updates())

def run_websocket_server():
    asyncio.run(start_server())
