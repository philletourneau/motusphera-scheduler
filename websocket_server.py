import asyncio
import websockets
import queue
import json
import threading

connected_clients = set()
data_queue = queue.Queue()
received_positions = None
positions_lock = threading.Lock()
scheduler = None  # This will be set from the main application

async def handler(websocket, path):
    global received_positions
    # Register client
    connected_clients.add(websocket)
    try:
        async for message in websocket:
            try:
                # Parse the received message as JSON
                command = json.loads(message)
                response = await process_command(command)
            except json.JSONDecodeError:
                response = {"status": "error", "message": "Invalid JSON format"}
            # Send the response back to the client
            await websocket.send(json.dumps(response))
    except websockets.ConnectionClosed:
        pass
    finally:
        # Unregister client
        connected_clients.remove(websocket)

async def process_command(command):
    global received_positions
    response = {"status": "error", "message": "Unknown command"}
    
    if "action" not in command:
        return response

    action = command["action"]

    if action == "list_animations":
        response = {
            "status": "success",
            "animations": scheduler.getAnimationDetails()
        }
    elif action == "append_animation":
        animation_type = command.get("type")
        starttime = command.get("starttime", 0)
        params = command.get("params", {})
        animation = create_animation(animation_type, starttime, params)
        if animation:
            scheduler.appendToQueue(animation)
            response = {"status": "success", "message": "Animation appended"}
        else:
            response = {"status": "error", "message": "Invalid animation type"}
    elif action == "delete_animation":
        scheduler.deleteFromQueue()
        response = {"status": "success", "message": "Animation deleted"}
    elif action == "update_animation":
        index = command.get("index")
        params = command.get("params", {})
        if scheduler.updateAnimation(index, params):
            response = {"status": "success", "message": "Animation updated"}
        else:
            response = {"status": "error", "message": "Invalid animation index or parameters"}
    elif action == "send_positions":
        positions = command.get("positions")
        with positions_lock:
            received_positions = positions
        response = {"status": "success", "message": "Positions received"}

    return response

def create_animation(animation_type, starttime, params):
    from animations import SineWaveAnimation, LinearAnimation, AnimationGroupAdditive

    if animation_type == "sine_wave":
        return SineWaveAnimation(starttime=starttime, **params)
    elif animation_type == "linear":
        return LinearAnimation(starttime=starttime, **params)
    elif animation_type == "group_additive":
        animations = [create_animation(anim["type"], anim["starttime"], anim["params"]) for anim in params.get("animations", [])]
        return AnimationGroupAdditive(starttime=starttime, animations=animations)
    return None

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
