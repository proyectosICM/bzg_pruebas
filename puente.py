import asyncio
import websockets
import json

API_WS_URL = "ws://192.168.0.204:7788/ws"  # WebSocket de la API
connected_devices = {}

async def handle_device(websocket):
    print(f"🔌 Dispositivo conectado: {websocket.remote_address}")
    api_ws = await websockets.connect(API_WS_URL)

    async def forward_to_api():
        async for msg in websocket:
            await api_ws.send(msg)
            print(f"➡️ Dispositivo → API: {msg}")

    async def forward_to_device():
        async for msg in api_ws:
            await websocket.send(msg)
            print(f"⬅️ API → Dispositivo: {msg}")

    await asyncio.gather(forward_to_api(), forward_to_device())

async def main():
    server = await websockets.serve(handle_device, "0.0.0.0", 7789)
    print("🚀 Servidor puente Python escuchando en puerto 7789")
    await server.wait_closed()

asyncio.run(main())
