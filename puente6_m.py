import asyncio
import websockets
import json

API_URL = "ws://192.168.0.204:7788/ws"

# Memoria temporal de mensajes pendientes
pending_messages_to_api = []
pending_messages_to_device = []

# Función auxiliar para enviar con reintentos
async def safe_send(ws, message, direction_label, buffer_list):
    """Intenta enviar el mensaje; si falla, lo guarda para reintentar."""
    try:
        await ws.send(message)
        print(f"✅ {direction_label}: enviado correctamente")
    except Exception as e:
        print(f"⚠️ {direction_label}: fallo al enviar, guardando en buffer → {e}")
        buffer_list.append(message)

# Maneja un solo par: dispositivo <-> API
async def handle_device_connection(device_ws):
    print("📡 Nuevo dispositivo conectado")

    api_ws = None

    async def connect_api():
        """Conecta (o reconecta) con la API."""
        nonlocal api_ws
        try:
            api_ws = await websockets.connect(API_URL, ping_interval=10, ping_timeout=20)
            print("✅ Conectado con API Java")
        except Exception as e:
            print(f"❌ No se pudo conectar con API: {e}")
            api_ws = None

    # Primer intento de conexión con API
    await connect_api()

    async def resend_pending(buffer_list, ws, direction_label):
        """Reenvía los mensajes pendientes cuando se reconecta."""
        if buffer_list and ws:
            print(f"🔁 Reintentando enviar {len(buffer_list)} mensajes pendientes a {direction_label}")
            while buffer_list:
                msg = buffer_list.pop(0)
                await safe_send(ws, msg, direction_label, buffer_list)

    async def device_to_api():
        """Envía mensajes del dispositivo a la API."""
        while True:
            try:
                async for message in device_ws:
                    print(f"➡️  Dispositivo → API: {message}")

                    if not api_ws or api_ws.closed:
                        print("⚠️ API desconectada, guardando mensaje para reintentar.")
                        pending_messages_to_api.append(message)
                        await connect_api()
                        continue

                    await safe_send(api_ws, message, "Dispositivo → API", pending_messages_to_api)

            except websockets.ConnectionClosed:
                print("🔌 Dispositivo desconectado.")
                break
            except Exception as e:
                print(f"❌ Error en device_to_api: {e}")
                break

    async def api_to_device():
        """Envía mensajes de la API al dispositivo."""
        while True:
            try:
                if not api_ws:
                    await asyncio.sleep(2)
                    await connect_api()
                    continue

                async for message in api_ws:
                    print(f"⬅️  API → Dispositivo: {message}")

                    if device_ws.closed:
                        print("⚠️ Dispositivo desconectado, guardando mensaje para reintentar.")
                        pending_messages_to_device.append(message)
                        continue

                    await safe_send(device_ws, message, "API → Dispositivo", pending_messages_to_device)

            except websockets.ConnectionClosed:
                print("⚠️ API desconectada, intentando reconectar...")
                await connect_api()
                await resend_pending(pending_messages_to_api, api_ws, "API")
                continue
            except Exception as e:
                print(f"❌ Error en api_to_device: {e}")
                break

    # Lanzar ambas tareas
    tasks = [
        asyncio.create_task(device_to_api()),
        asyncio.create_task(api_to_device()),
    ]

    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    for task in pending:
        task.cancel()

    print("🔌 Conexión cerrada completamente.")

# Iniciar servidor WebSocket
async def main():
    print("🚀 Servidor puente escuchando en ws://0.0.0.0:7789")
    async with websockets.serve(handle_device_connection, "0.0.0.0", 7789):
        await asyncio.Future()  # Mantener servidor vivo

if __name__ == "__main__":
    asyncio.run(main())
