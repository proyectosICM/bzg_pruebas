# test_2_settime.py
import asyncio
import websockets
import json
from datetime import datetime

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
                print("🆗 Comando REG recibido. Respondiendo éxito y luego settime...")
                response = {
                    "ret": "reg",
                    "result": True,
                    "cloudtime": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                await ws.send(json.dumps(response))
                print("⬅️  Enviado REG OK")

                # Enviar comando settime
                settime = {
                    "cmd": "settime",
                    "cloudtime": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                await asyncio.sleep(1)  # pequeña pausa
                await ws.send(json.dumps(settime))
                print("🕓 Enviado comando settime")

            elif ret == "settime":
                print("✅ Dispositivo respondió al settime:", data)
            else:
                print("📥 Otro mensaje recibido:", data)

    except websockets.ConnectionClosedError as e:
        print(f"⚠️ Conexión cerrada abruptamente: {e}")
    except Exception as e:
        print(f"💥 Error inesperado: {e}")
    finally:
        print("🔌 Conexión finalizada")

async def main():
    print("🚀 Servidor WS escuchando en ws://0.0.0.0:7789 (REG + SETTIME)")
    async with websockets.serve(handle_device, "0.0.0.0", 7789):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())

