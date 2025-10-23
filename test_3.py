import asyncio
import websockets
import json

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
                print("🆗 Comando REG recibido. Respondiendo éxito y luego settime doble...")

                # Respuesta al reg
                response = {
                    "ret": "reg",
                    "result": True,
                    "cloudtime": "2025-10-22 17:00:00"
                }
                await ws.send(json.dumps(response))
                print("⬅️  Enviado REG OK")

                # Espera breve antes del primer settime
                await asyncio.sleep(1)

                # Primer settime (5 PM)
                settime1 = {
                    "cmd": "settime",
                    "cloudtime": "2025-10-22 17:00:00"
                }
                print("🕓 Enviando primer settime (17:00)...")
                await ws.send(json.dumps(settime1))

                # Esperar 5 segundos
                await asyncio.sleep(5)

                # Segundo settime (9 PM)
                settime2 = {
                    "cmd": "settime",
                    "cloudtime": "2025-10-22 21:00:00"
                }
                print("🌙 Enviando segundo settime (21:00)...")
                await ws.send(json.dumps(settime2))

            elif ret == "settime":
                print(f"✅ Dispositivo respondió al settime: {data}")
            else:
                print("📥 Otro mensaje recibido:", data)

    except websockets.ConnectionClosedError as e:
        print(f"⚠️ Conexión cerrada abruptamente: {e}")
    except Exception as e:
        print(f"💥 Error inesperado: {e}")
    finally:
        print("🔌 Conexión finalizada")

async def main():
    print("🚀 Servidor WS escuchando en ws://0.0.0.0:7789 (doble settime)")
    async with websockets.serve(handle_device, "0.0.0.0", 7789):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
