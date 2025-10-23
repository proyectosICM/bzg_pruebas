import asyncio
import websockets
import json

API_URL = "ws://192.168.0.204:7788/ws"

# Aumentamos tamaño máximo permitido: 5 MB
MAX_WS_SIZE = 5 * 1024 * 1024  # 5 MB

async def safe_close(ws, label="socket"):
    """Cierra un websocket sin lanzar excepción si ya está cerrado."""
    try:
        if ws is not None:
            if not ws.closed:
                await ws.close()
            await ws.wait_closed()
            print(f"{label} cerrado correctamente")
    except Exception as e:
        print(f"Error al cerrar {label}: {e}")

async def handle_device_connection(device_ws):
    print("📡 Nuevo dispositivo conectado")

    # Intentar conectar a la API Java
    try:
        api_ws = await websockets.connect(
            API_URL,
            ping_interval=10,
            ping_timeout=20,
            max_size=MAX_WS_SIZE  # <- buffer aumentado
        )
        print("✅ Conectado con API Java")
    except Exception as e:
        print(f"❌ No se pudo conectar con API: {e}")
        await safe_close(device_ws, "Device")
        return

    async def device_to_api():
        try:
            async for message in device_ws:
                print(f"➡️  Dispositivo → API: (longitud={len(message)} bytes)")
                await api_ws.send(message)
        except websockets.ConnectionClosedOK:
            print("ℹ️ Device→API: Conexión cerrada correctamente")
        except websockets.ConnectionClosedError as e:
            print(f"⚠️ Device→API cerrado con error: {e}")
        except Exception as e:
            print(f"💥 Error inesperado Device→API: {e}")
        finally:
            await safe_close(api_ws, "API")

    async def api_to_device():
        try:
            async for message in api_ws:
                print(f"⬅️ API → Dispositivo (longitud={len(message)} bytes)")
                await device_ws.send(message)
        except websockets.ConnectionClosedOK:
            print("ℹ️ API→Device: Conexión cerrada correctamente")
        except websockets.ConnectionClosedError as e:
            print(f"⚠️ API→Device cerrado con error: {e}")
        except Exception as e:
            print(f"💥 Error inesperado API→Device: {e}")
        finally:
            await safe_close(device_ws, "Device")

    # Ejecutar ambos flujos simultáneamente
    tasks = [
        asyncio.create_task(device_to_api()),
        asyncio.create_task(api_to_device())
    ]
    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

    # Cancelar el resto
    for task in pending:
        task.cancel()

    await safe_close(api_ws, "API")
    await safe_close(device_ws, "Device")

    print("🔌 Conexión cerrada correctamente")

async def main():
    print("🚀 Servidor puente escuchando en ws://0.0.0.0:7789 (max 5MB por mensaje)")
    async with websockets.serve(
        handle_device_connection,
        "0.0.0.0",
        7789,
        max_size=MAX_WS_SIZE  # <- también aquí
    ):
        await asyncio.Future()  # Mantener servidor vivo

if __name__ == "__main__":
    asyncio.run(main())
