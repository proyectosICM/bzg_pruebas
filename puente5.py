import asyncio
import websockets
import json

API_URL = "ws://192.168.0.204:7788/ws"

# Maneja un solo par: dispositivo <-> API
async def handle_device_connection(device_ws):
    print("📡 Nuevo dispositivo conectado")

    # Conectar con la API (nuevo socket)
    try:
        api_ws = await websockets.connect(API_URL)
        print("✅ Conectado con API Java")
    except Exception as e:
        print(f"❌ No se pudo conectar con API: {e}")
        await device_ws.close()
        return

    async def device_to_api():
        try:
            async for message in device_ws:
                print(f"➡️ Dispositivo → API: {message}")
                await api_ws.send(message)
        except Exception as e:
            print(f"⚠️ Error envío Dispositivo→API: {e}")

    async def api_to_device():
        try:
            async for message in api_ws:
                print(f"⬅️ API → Dispositivo: {message}")
                await device_ws.send(message)
        except Exception as e:
            print(f"⚠️ Error envío API→Dispositivo: {e}")

    # Ejecutar ambos bucles simultáneamente
    await asyncio.gather(device_to_api(), api_to_device())

    # Cerrar conexiones al terminar
    await api_ws.close()
    await device_ws.close()
    print("🔌 Conexión cerrada")

# Iniciar servidor WebSocket (puerto 7789)
async def main():
    print("🚀 Servidor puente escuchando en ws://0.0.0.0:7789")
    async with websockets.serve(handle_device_connection, "0.0.0.0", 7789):
        await asyncio.Future()  # mantener servidor vivo

if __name__ == "__main__":
    asyncio.run(main())
