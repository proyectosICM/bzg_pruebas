# ws_server.py
import asyncio
import websockets

PORT = 7789

async def handler(ws):
    print(f"Conexión desde {ws.remote_address}")
    try:
        async for message in ws:
            print(f"[{ws.remote_address}] {message}")
            # opcional: responder al cliente
            await ws.send("Mensaje recibido")
    except websockets.exceptions.ConnectionClosed as e:
        print(f"Desconectado {ws.remote_address} ({e.code})")

async def main():
    async with websockets.serve(handler, "0.0.0.0", PORT):
        print(f"Escuchando WebSocket en 0.0.0.0:{PORT}")
        await asyncio.Future()  # para mantener el servidor corriendo

if __name__ == "__main__":
    asyncio.run(main())
