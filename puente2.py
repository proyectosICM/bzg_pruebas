import asyncio
import websockets
import json

API_WS_URL = "ws://192.168.0.204:7788/ws"  # WebSocket de la API

async def handle_device(websocket):
    print(f"🔌 Dispositivo conectado: {websocket.remote_address}")
    try:
        api_ws = await websockets.connect(API_WS_URL)

        async def forward_to_api():
            try:
                async for msg in websocket:
                    await api_ws.send(msg)
                    print(f"➡️  Dispositivo → API: {msg}")
            except websockets.exceptions.ConnectionClosed:
                print("⚠️ Conexión con dispositivo cerrada.")

        async def forward_to_device():
            try:
                async for msg in api_ws:
                    await websocket.send(msg)
                    print(f"⬅️  API → Dispositivo: {msg}")
            except websockets.exceptions.ConnectionClosed:
                print("⚠️ Conexión con API cerrada.")

        await asyncio.gather(forward_to_api(), forward_to_device())

    except Exception as e:
        print(f"❌ Error manejando dispositivo: {e}")

    finally:
        await websocket.close()
        try:
            await api_ws.close()
        except:
            pass
        print(f"🔌 Conexión finalizada: {websocket.remote_address}")


async def main():
    server = await websockets.serve(handle_device, "0.0.0.0", 7789)
    print("🚀 Servidor puente Python escuchando en puerto 7789")
    await server.wait_closed()

asyncio.run(main())
