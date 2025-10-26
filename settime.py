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
                print("🆗 REG recibido. Respondiendo éxito y preparando ciclo settime...\n")

                # 1️⃣ Confirmar el registro
                response = {
                    "ret": "reg",
                    "result": True,
                    "cloudtime": now_str()
                }
                await ws.send(json.dumps(response))
                print(f"⬅️  Enviado REG OK con hora {response['cloudtime']}")

                # 2️⃣ Entrar en loop continuo de settime
                while True:
                    # settime 17:00
                    settime1 = {
                        "cmd": "settime",
                        "cloudtime": f"{datetime.now().strftime('%Y-%m-%d')} 17:00:00"
                    }
                    print("🕔 Enviando settime 17:00")
                    await ws.send(json.dumps(settime1))

                    await asyncio.sleep(5)

                    # settime 21:00
                    settime2 = {
                        "cmd": "settime",
                        "cloudtime": f"{datetime.now().strftime('%Y-%m-%d')} 21:00:00"
                    }
                    print("🌙 Enviando settime 21:00")
                    await ws.send(json.dumps(settime2))

                    await asyncio.sleep(5)

                    # Restaurar hora real
                    restore = {
                        "cmd": "settime",
                        "cloudtime": now_str()
                    }
                    print(f"🔄 Restaurando hora actual ({restore['cloudtime']})")
                    await ws.send(json.dumps(restore))

                    # Esperar antes del siguiente ciclo
                    await asyncio.sleep(10)

            elif ret == "settime":
                print(f"✅ ACK recibido del dispositivo por settime: {data}")

            else:
                print("📥 Otro mensaje recibido:", data)

    except websockets.ConnectionClosedError as e:
        print(f"⚠️ Conexión cerrada abruptamente: {e}")

    except Exception as e:
        print(f"💥 Error inesperado: {e}")

    finally:
        print("🔌 Conexión finalizada")


async def main():
    print(f"🚀 Servidor WS escuchando en ws://0.0.0.0:{PORT} (ciclo settime activo)")
    async with websockets.serve(handle_device, "0.0.0.0", PORT):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
