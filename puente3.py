import asyncio
import websockets
import json

API_WS_URL = "ws://192.168.0.204:7788/ws"

connected_devices = {}  # SN -> WebSocket
api_ws = None  # conexión persistente con la API

async def forward_device_to_api(device_ws, sn):
    """Reenvía mensajes desde un dispositivo hacia la API."""
    try:
        async for msg in device_ws:
            data = json.loads(msg)
            # Asegura que incluya el SN
            if "sn" not in data:
                data["sn"] = sn
            await api_ws.send(json.dumps(data))
            print(f"➡️  [{sn}] Dispositivo → API: {data}")
    except websockets.exceptions.ConnectionClosed:
        print(f"⚠️  Dispositivo {sn} desconectado.")
    finally:
        del connected_devices[sn]


async def handle_device(websocket):
    """Acepta conexiones de dispositivos (puerto 7789)."""
    print(f"🔌 Nuevo dispositivo conectado: {websocket.remote_address}")

    # Espera el primer mensaje (debe contener el SN)
    msg = await websocket.recv()
    data = json.loads(msg)
    sn = data.get("sn") or data.get("devinfo", {}).get("sn") or "unknown"

    connected_devices[sn] = websocket
    print(f"✅ Dispositivo registrado: SN={sn}")

    # Reenvía el primer mensaje (registro) a la API
    if api_ws:
        await api_ws.send(json.dumps(data))

    # Sigue escuchando mensajes del dispositivo
    await forward_device_to_api(websocket, sn)


async def handle_api_messages():
    """Escucha mensajes que vienen desde la API."""
    global api_ws
    async for msg in api_ws:
        data = json.loads(msg)
        sn = data.get("sn")
        if sn and sn in connected_devices:
            ws = connected_devices[sn]
            await ws.send(json.dumps(data))
            print(f"⬅️  API → [{sn}] Dispositivo: {data}")
        else:
            print(f"⚠️  API envió comando para SN desconocido: {sn}")


async def main():
    global api_ws
    # Conectar al WebSocket de la API
    api_ws = await websockets.connect(API_WS_URL)
    print("🌐 Conectado al WebSocket de la API")

    # Correr el servidor de dispositivos y la escucha de la API en paralelo
    device_server = await websockets.serve(handle_device, "0.0.0.0", 7789)
    print("🚀 Puente escuchando en puerto 7789 para dispositivos")

    await asyncio.gather(
        handle_api_messages(),
        device_server.wait_closed(),
    )

asyncio.run(main())
