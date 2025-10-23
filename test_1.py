# test_1.py
import asyncio
import websockets
import json
from datetime import datetime

async def handle_device(ws):
    print("📡 Dispositivo conectado")

    try:
        async for message in ws:
            print(f"➡️  Recibido del dispositivo:\n{message}\n")

            try:
                data = json.loads(message)
            except json.JSONDecodeError:
                print("⚠️ No es JSON válido")
                continue

            if data.get("cmd") == "reg":
                print("🆗 Comando REG recibido, respondiendo éxito...")
                response = {
                    "ret": "reg",
                    "result": True,
                    "cloudtime": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                await ws.send(json.dumps(response))
                print("⬅️  Respuesta enviada al dispositivo\n")
            else:
                print("📥 Comando no reconocido, ignorando...")

    except websockets.ConnectionClosedError as e:
        print(f"⚠️ Conexión cerrada abruptamente: {e}")
    except Exception as e:
        print(f"💥 Error inesperado: {e}")
    finally:
        print("🔌 Conexión finalizada")

async def main():
    print("🚀 Servidor WS escuchando en ws://0.0.0.0:7789 (solo REG)")
    async with websockets.serve(handle_device, "0.0.0.0", 7789):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
