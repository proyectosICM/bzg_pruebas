import asyncio
import websockets
import json

API_URL = "ws://192.168.0.204:7788/ws"


async def safe_close(ws, label="socket"):
    """Cierra un websocket de forma segura, compatible con websockets >=13."""
    try:
        if ws is not None:
            # Comprobamos si el websocket sigue abierto
            if hasattr(ws, "state"):
                if ws.state.name not in ("CLOSING", "CLOSED"):
                    await ws.close()
                    print(f"🔒 {label}: cierre solicitado (estado {ws.state.name})")
            else:
                # fallback para versiones anteriores
                await ws.close()
            await ws.wait_closed()
            print(f"✅ {label} cerrado correctamente")
    except Exception as e:
        print(f"⚠️ Error al cerrar {label}: {e}")


async def handle_device_connection(device_ws):
    print("📡 Nuevo dispositivo conectado")

    # Intentar conectar con la API Java
    try:
        api_ws = await websockets.connect(API_URL, ping_interval=None)
        print("✅ Conectado con API Java")
    except Exception as e:
        print(f"❌ No se pudo conectar con API: {e}")
        await safe_close(device_ws, "Device")
        return

    async def device_to_api():
        try:
            async for message in device_ws:
                print(f"➡️  Dispositivo → API: {message}")
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
                print(f"⬅️  API → Dispositivo: {message}")
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

    for task in pending:
        task.cancel()

    await safe_close(api_ws, "API")
    await safe_close(device_ws, "Device")

    print("🔌 Conexión cerrada correctamente")


async def main():
    print("🚀 Servidor puente escuchando en ws://0.0.0.0:7789")
    async with websockets.serve(handle_device_connection, "0.0.0.0", 7789):
        await asyncio.Future()  # Mantener servidor vivo


if __name__ == "__main__":
    asyncio.run(main())
