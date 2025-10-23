import asyncio
import websockets
import json

API_URL = "ws://192.168.0.204:7788/ws"

# 🧩 Función de cierre seguro
async def safe_close(ws, name):
    if ws and not ws.closed:
        try:
            await ws.close(code=1000, reason=f"{name} normal closure")
            print(f"🔌 {name} cerrado correctamente (code=1000)")
        except Exception as e:
            print(f"⚠️  Error cerrando {name}: {e}")

# 🔁 Conexión con reintentos automáticos
async def connect_api():
    while True:
        try:
            api_ws = await websockets.connect(
                API_URL,
                ping_interval=30,  # menos agresivo
                ping_timeout=60
            )
            print("✅ Conectado con API Java")
            return api_ws
        except Exception as e:
            print(f"⚠️  No se pudo conectar con API ({e}), reintentando en 3s...")
            await asyncio.sleep(3)

# 🔌 Manejador principal de cada dispositivo
async def handle_device_connection(device_ws):
    print("📡 Nuevo dispositivo conectado")

    api_ws = await connect_api()

    # --- Función: mensajes desde el dispositivo hacia la API ---
    async def device_to_api():
        try:
            async for message in device_ws:
                print(f"➡️  Dispositivo → API: {message}")
                await api_ws.send(message)
        except websockets.ConnectionClosedOK:
            print("ℹ️  Device→API: conexión cerrada correctamente")
        except websockets.ConnectionClosedError as e:
            print(f"⚠️  Device→API closed with error: {e}")
        except Exception as e:
            print(f"❌ Error inesperado Device→API: {e}")
        finally:
            await asyncio.sleep(0.3)
            await safe_close(api_ws, "API")

    # --- Función: mensajes desde la API hacia el dispositivo ---
    async def api_to_device():
        try:
            async for message in api_ws:
                print(f"⬅️  API → Dispositivo: {message}")
                await device_ws.send(message)
        except websockets.ConnectionClosedOK:
            print("ℹ️  API→Device: conexión cerrada correctamente")
        except websockets.ConnectionClosedError as e:
            print(f"⚠️  API→Device closed with error: {e}")
        except Exception as e:
            print(f"❌ Error inesperado API→Device: {e}")
        finally:
            await asyncio.sleep(0.3)
            await safe_close(device_ws, "Device")

    # Ejecutar ambas tareas simultáneamente
    tasks = [
        asyncio.create_task(device_to_api()),
        asyncio.create_task(api_to_device())
    ]

    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

    # Cancelar las tareas que no hayan terminado
    for task in pending:
        task.cancel()

    await safe_close(api_ws, "API")
    await safe_close(device_ws, "Device")
    print("🔚 Conexión finalizada entre dispositivo y API\n")

# 🚀 Iniciar servidor WebSocket del puente
async def main():
    print("🚀 Servidor puente escuchando en ws://0.0.0.0:7789")
    async with websockets.serve(handle_device_connection, "0.0.0.0", 7789):
        await asyncio.Future()  # mantener el servidor corriendo

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Servidor detenido manualmente")
