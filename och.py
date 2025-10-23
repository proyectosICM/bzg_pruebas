import asyncio
import websockets
import json
from datetime import datetime

API_URL = "ws://192.168.0.204:7788/ws"
MESSAGE_DELAY = 3  # segundos entre mensajes

# Caché global: {device_id: [mensajes_pendientes]}
message_cache = {}

def log_message(device_id, direction, message, status):
    """Guarda cada mensaje con estado en la caché"""
    record = {
        "timestamp": datetime.now().isoformat(timespec='seconds'),
        "direction": direction,
        "message": message,
        "status": status
    }
    message_cache.setdefault(device_id, []).append(record)

async def resend_pending_messages(device_id, ws):
    """Reenvía mensajes pendientes para un dispositivo"""
    if device_id not in message_cache:
        return
    pending = [m for m in message_cache[device_id] if m["status"] == "pending"]
    if not pending:
        return

    print(f"🔁 Reintentando {len(pending)} mensajes pendientes para {device_id}...")
    for m in pending:
        try:
            await ws.send(m["message"])
            m["status"] = "resent"
            print(f"✅ Reenviado mensaje pendiente → {m['direction']}")
            await asyncio.sleep(MESSAGE_DELAY)
        except Exception as e:
            print(f"⚠️ Error reenviando mensaje pendiente: {e}")

async def safe_close(ws, label="socket"):
    """Cierra un websocket de forma segura"""
    try:
        if ws and not ws.closed:
            await ws.close()
        await ws.wait_closed()
        print(f"🔒 {label} cerrado correctamente")
    except Exception as e:
        print(f"⚠️ Error al cerrar {label}: {e}")

async def handle_device_connection(device_ws):
    print("📡 Nuevo dispositivo conectado")

    device_id = None
    try:
        # Conexión con la API
        api_ws = await websockets.connect(API_URL, ping_interval=10, ping_timeout=20)
        print("✅ Conectado con API Java")
    except Exception as e:
        print(f"❌ No se pudo conectar con API: {e}")
        await safe_close(device_ws, "Device")
        return

    async def device_to_api():
        nonlocal device_id
        try:
            async for message in device_ws:
                print(f"➡️ Dispositivo → API: {message}")
                data = json.loads(message)
                device_id = data.get("sn", "unknown_device")

                # Guardar en caché
                log_message(device_id, "device_to_api", message, "pending")

                # Si es registro exitoso, enviar a API y reintentar pendientes
                await api_ws.send(message)
                log_message(device_id, "device_to_api", message, "sent")
                await asyncio.sleep(MESSAGE_DELAY)

                # Si es cmd:reg → luego del registro confirmado reenvía pendientes
                if data.get("cmd") == "reg":
                    print(f"🪪 Registro detectado ({device_id}), esperando confirmación...")
                    await asyncio.sleep(2)
                    await resend_pending_messages(device_id, api_ws)

        except websockets.ConnectionClosedError as e:
            print(f"⚠️ Device→API cerrado con error: {e}")
        except Exception as e:
            print(f"💥 Error inesperado Device→API: {e}")
        finally:
            await safe_close(api_ws, "API")

    async def api_to_device():
        try:
            async for message in api_ws:
                print(f"⬅️ API → Dispositivo: {message}")
                await device_ws.send(message)
                if device_id:
                    log_message(device_id, "api_to_device", message, "sent")
                await asyncio.sleep(MESSAGE_DELAY)
        except websockets.ConnectionClosedError as e:
            print(f"⚠️ API→Device cerrado con error: {e}")
        except Exception as e:
            print(f"💥 Error inesperado API→Device: {e}")
        finally:
            await safe_close(device_ws, "Device")

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
    print(f"🚀 Servidor puente escuchando en ws://0.0.0.0:7789 (con delay={MESSAGE_DELAY}s y caché de mensajes)")
    async with websockets.serve(handle_device_connection, "0.0.0.0", 7789):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
