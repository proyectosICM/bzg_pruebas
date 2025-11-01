import asyncio
import websockets
import json
import random
from datetime import datetime

PORT = 7789

def now_str():
    """Devuelve la hora actual del sistema en formato YYYY-MM-DD HH:mm:ss"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# --- Utilidades de nombres aleatorios (sin librerías externas) ---
FIRST_NAMES = ["Diego", "María", "Juan", "Lucía", "Carlos", "Elena", "Pedro", "Valeria", "Luis", "Ana"]
LAST_NAMES  = ["García", "Pérez", "Rodríguez", "Fernández", "López", "Martínez", "Gómez", "Díaz", "Torres", "Romero"]

def random_name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"

async def send_setuserinfo(ws, enrollid: int, name: str, password: int):
    """
    Envía un comando setuserinfo SOLO con contraseña (backupnum=10).
    El protocolo indica:
      cmd: "setuserinfo"
      enrollid: <int>
      name: <string>
      backupnum: 10   # Password
      admin: 0        # Usuario normal
      record: <int>   # La contraseña
    """
    payload = {
        "cmd": "setuserinfo",
        "enrollid": enrollid,
        "name": name,
        "backupnum": 10,   # 10 = password según el protocolo
        "admin": 0,        # 0 = no admin
        "record": password
    }
    msg = json.dumps(payload, ensure_ascii=False)
    print(f"⬅️  Enviando SETUSERINFO (enrollid={enrollid}, name='{name}', pwd={password})")
    await ws.send(msg)

async def handle_device(ws):
    print("📡 Dispositivo conectado")

    try:
        async for message in ws:
            print(f"➡️  Recibido del dispositivo:\n{message}\n")

            data = json.loads(message)
            cmd = data.get("cmd")
            ret = data.get("ret")

            # --- Registro inicial del terminal ---
            if cmd == "reg":
                print("🆗 REG recibido. Confirmando registro...\n")

                # 1️⃣ Confirmar el registro
                response = {
                    "ret": "reg",
                    "result": True,
                    "cloudtime": now_str()
                }
                await ws.send(json.dumps(response))
                print(f"⬅️  Enviado REG OK con hora {response['cloudtime']}")

                # 2️⃣ Enviar dos usuarios con contraseña
                #    - Usuario 1: enrollid=1, password=111
                #    - Usuario 2: enrollid=2, password=1234678
                name1 = random_name()
                name2 = random_name()

                await send_setuserinfo(ws, enrollid=1, name=name1, password=111)
                await asyncio.sleep(0.2)  # pequeña pausa para no saturar el buffer
                await send_setuserinfo(ws, enrollid=2, name=name2, password=1234678)

                print("📤 Solicitudes de creación de usuarios enviadas. Esperando ACKs del terminal...")

            # --- ACKs del terminal por setuserinfo ---
            elif ret == "setuserinfo":
                result = data.get("result")
                reason = data.get("reason")
                if result is True:
                    print("✅ ACK setuserinfo: éxito")
                else:
                    print(f"❌ ACK setuserinfo: fallo (reason={reason})")

            else:
                print("📥 Otro mensaje recibido:", data)

    except websockets.ConnectionClosedError as e:
        print(f"⚠️ Conexión cerrada abruptamente: {e}")

    except Exception as e:
        print(f"💥 Error inesperado: {e}")

    finally:
        print("🔌 Conexión finalizada")

async def main():
    print(f"🚀 Servidor WS escuchando en ws://0.0.0.0:{PORT} (envío de usuarios por contraseña)")
    async with websockets.serve(handle_device, "0.0.0.0", PORT):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
