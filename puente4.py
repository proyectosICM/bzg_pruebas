import asyncio
import websockets
import json
import socket

API_URL = "ws://102.168.0.204:7788"  # la dirección pública o LAN de tu API

async def handle_device(reader, writer):
    addr = writer.get_extra_info('peername')
    print(f"🔌 Nuevo dispositivo conectado desde {addr}")

    # Crear conexión WebSocket individual con la API para este dispositivo
    async with websockets.connect(API_URL) as ws_api:
        print("🌐 Conectado a la API")

        async def device_to_api():
            while True:
                data = await reader.read(4096)
                if not data:
                    break
                try:
                    msg = data.decode().strip()
                    print(f"➡️ Dispositivo → API: {msg}")
                    await ws_api.send(msg)
                except Exception as e:
                    print(f"⚠️ Error al reenviar al API: {e}")
                    break

        async def api_to_device():
            async for message in ws_api:
                print(f"⬅️ API → Dispositivo: {message}")
                try:
                    writer.write((message + "\r\n").encode())
                    await writer.drain()
                except Exception as e:
                    print(f"⚠️ Error enviando al dispositivo: {e}")
                    break

        await asyncio.gather(device_to_api(), api_to_device())

    print(f"❌ Dispositivo desconectado: {addr}")
    writer.close()
    await writer.wait_closed()


async def start_bridge():
    server = await asyncio.start_server(handle_device, "0.0.0.0", 7789)
    print("🚀 Puente escuchando en puerto 7789 (modo clásico)")
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    try:
        asyncio.run(start_bridge())
    except KeyboardInterrupt:
        print("🛑 Puente detenido manualmente")
