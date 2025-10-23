import asyncio
import websockets
import json

API_URL = "ws://192.168.0.204:7788/ws"

# Maneja un solo par: dispositivo <-> API
async def handle_device_connection(device_ws):
    print("📡 Nuevo dispositivo conectado")

    # Conectar con la API (nuevo socket) con keepalive
    try:
        api_ws = await websockets.connect(API_URL, ping_interval=10, ping_timeout=20)
        print("✅ Conectado con API Java")
    except Exception as e:
        print(f"❌ No se pudo conectar con API: {e}")
        await device_ws.close()
        return

    async def device_to_api():
        try:
            async for message in device_ws:
                print(f"➡️  Dispositivo → API: {message}")
                await api_ws.send(message)
        except websockets.ConnectionClosedOK:
            print("ℹ️ Device→API: Conexión cerrada correctamente")
        except websockets.ConnectionClosedError as e:
            print(f"⚠️ Device→API closed with error: {e}")
        finally:
            await api_ws.close()

    async def api_to_device():
        try:
            async for message in api_ws:
                print(f"⬅️  API → Dispositivo: {message}")
                await device_ws.send(message)
        except websockets.ConnectionClosedOK:
            print("ℹ️ API→Device: Conexión cerrada correctamente")
        except websockets.ConnectionClosedError as e:
            print(f"⚠️ API→Device closed with error: {e}")
        finally:
            await device_ws.close()

    # Ejecutar ambos bucles y cancelar si uno termina
    tasks = [asyncio.create_task(device_to_api()), asyncio.create_task(api_to_device())]
    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

    for task in pending:
        task.cancel()

    print("🔌 Conexión cerrada correctamente")

# Iniciar servidor WebSocket (puerto 7789)
async def main():
    print("🚀 Servidor puente escuchando en ws://0.0.0.0:7789")
    async with websockets.serve(handle_device_connection, "0.0.0.0", 7789):
        await asyncio.Future()  # mantener servidor vivo

if __name__ == "__main__":
    asyncio.run(main())
