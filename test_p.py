import asyncio
import websockets
import json
from datetime import datetime

PORT = 7789

def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

async def handle_device(ws):
    print("📡 Dispositivo conectado")

    try:
        async for message in ws:
            print(f"➡️  Recibido del dispositivo:\n{message}\n")

            data = json.loads(message)
            cmd = data.get("cmd")
            ret = data.get("ret")

            # --- REGISTRO ---
            if cmd == "reg":
                print("🆗 REG recibido. Enviando respuesta OK...\n")

                # Confirmar registro
                response = {
                    "ret": "reg",
                    "result": True,
                    "cloudtime": now_str()
                }
                await ws.send(json.dumps(response))
                print(f"⬅️  Enviado REG OK ({response['cloudtime']})")

                await asyncio.sleep(1)

                # 1️⃣ Usuario 1 con contraseña 12345678
                user1 = {
                    "cmd": "setuserinfo",
                    "enrollid": 1,
                    "name": "usuario1",
                    "backupnum": 10,   # 10 = password
                    "admin": 0,
                    "record": "12345678"
                }
                print("📨 Enviando setuserinfo (usuario1 / 12345678)...")
                await ws.send(json.dumps(user1))

                await asyncio.sleep(2)

                # 2️⃣ Usuario 2 con contraseña 12345
                user2 = {
                    "cmd": "setuserinfo",
                    "enrollid": 2,
                    "name": "usuario2",
                    "backupnum": 10,   # 10 = password
                    "admin": 0,
                    "record": "12345"
                }
                print("📨 Enviando setuserinfo (usuario2 / 12345)...")
                await ws.send(json.dumps(user2))

            # --- RESPUESTAS DE setuserinfo ---
            elif ret == "setuserinfo":
                print(f"✅ Dispositivo confirmó setuserinfo: {data}")

            else:
                print("📥 Otro mensaje recibido:", data)

    except websockets.ConnectionClosedError as e:
        print(f"⚠️ Conexión cerrada abruptamente: {e}")
    except Exception as e:
        print(f"💥 Error inesperado: {e}")
    finally:
        print("🔌 Conexión finalizada")

async def main():
    print(f"🚀 Servidor WS en ws://0.0.0.0:{PORT} (test setuserinfo)")
    async with websockets.serve(handle_device, "0.0.0.0", PORT):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
