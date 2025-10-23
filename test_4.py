import asyncio
import websockets
import json
from datetime import datetime

PORT = 7789

def now_str():
    """Devuelve la hora actual del sistema en formato YYYY-MM-DD HH:mm:ss"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

async def handle_device(ws):
    print("📡 Dispositivo conectado")

    try:
        async for message in ws:
            print(f"➡️  Recibido del dispositivo:\n{message}\n")

            data = json.loads(message)
            cmd = data.get("cmd")
            ret = data.get("ret")

            # --- Registro inicial ---
            if cmd == "reg":
                print("🆗 REG recibido. Respondiendo éxito y preparando secuencia settime...\n")

                # 1️⃣ Confirmar el registro
                response = {
                    "ret": "reg",
                    "result": True,
                    "cloudtime": now_str()
                }
                await ws.send(json.dumps(response))
                print(f"⬅️  Enviado REG OK con hora {response['cloudtime']}")

                await asyncio.sleep(1)

                # 2️⃣ Primer settime - 5 PM
                settime1 = {
                    "cmd": "settime",
                    "cloudtime": f"{datetime.now().strftime('%Y-%m-%d')} 17:00:00"
                }
                print(f"🕔 Enviando primer settime (17:00)...")
                await ws.send(json.dumps(settime1))

                await asyncio.sleep(5)

                # 3️⃣ Segundo settime - 9 PM
                settime2 = {
                    "cmd": "settime",
                    "cloudtime": f"{datetime.now().strftime('%Y-%m-%d')} 21:00:00"
                }
                print(f"🌙 Enviando segundo settime (21:00)...")
                await ws.send(json.dumps(settime2))

                await asyncio.sleep(5)

                # 4️⃣ Restaurar hora actual
                restore = {
                    "cmd": "settime",
                    "cloudtime": now_str()
                }
                print(f"🔄 Restaurando hora actual ({restore['cloudtime']})...")
                await ws.send(json.dumps(restore))

            elif ret == "settime":
                print(f"✅ Respuesta del dispositivo al settime: {data}")
            else:
                print("📥 Otro mensaje recibido:", data)

    except websockets.ConnectionClosedError as e:
        print(f"⚠️ Conexión cerrada abruptamente: {e}")
    except Exception as e:
        print(f"💥 Error inesperado: {e}")
    finally:
        print("🔌 Conexión finalizada")

async def main():
    print(f"🚀 Servidor WS escuchando en ws://0.0.0.0:{PORT} (triple settime con restauración)")
    async with websockets.serve(handle_device, "0.0.0.0", PORT):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
