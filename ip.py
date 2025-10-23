# ws_client.py
import asyncio
import websockets

URI = "ws://190.43.106.49:7788"   # o "ws://190.43.106.49:7788/ws" si tu servidor usa /ws

async def main():
    try:
        async with websockets.connect(URI, ping_interval=20) as ws:
            print(f"Conectado a {URI}")
            # ejemplo: enviar un mensaje y esperar respuesta
            await ws.send("Hola desde el cliente Python")
            resp = await ws.recv()
            print("Respuesta del servidor:", resp)

            # mantener leyendo mensajes (si los hay)
            async for msg in ws:
                print("->", msg)

    except Exception as e:
        print("Error de conexión:", e)

if __name__ == "__main__":
    asyncio.run(main())
