import asyncio
import moteus
import socket
import threading
from time import sleep
from bno055_usb_stick_py import BnoUsbStick

##rotctld -m 1 -s 19200 #baudrate
#python -m moteus_gui.tview --target 2

HOST = "localhost"
PORT = 4533             #Rotctl by default Port

MOTEUS_AZIMUTE_ID = 1
MOTEUS_ELEVACAO_ID = 2

azimute_motor = moteus.Controller(id=MOTEUS_AZIMUTE_ID)
elevacao_motor = moteus.Controller(id=MOTEUS_ELEVACAO_ID)

# Estado partilhado
estado_bno = {
    "heading_offset": 0.0  # real heading (em voltas)
}

def graus_para_voltas_azimute(graus):
    return round(graus / 360.0, 3)                   #Moteus rotors receive unitary positions as in 1 = 360 deg.

def graus_para_voltas_elevacao(graus):
    return round(-0.285 - (graus / 180.0) * 0.5, 3)  #The Offset is required because of our personal assembly - it will be different with different Rotor assemblies

async def set_motor_position(controller, position):
    await controller.set_position(
        position=position,
        velocity=0.2,
        accel_limit=1.0,
        velocity_limit=3.0,
        query=False
    )

def iniciar_bno_thread():
    def bno_task():
        try:
            stick = BnoUsbStick(port="/dev/ttyACM1")  # Forcing the Port ACM1 (My personal use case)
            print("Using BNO port:", stick.port_name)
            stick.write_register(0x3D, 0b00001100)    # Setting the Operation Mode '0x3D' to NDOF '0b00001100' (Nine Deg. of Freedom)
            sleep(0.1)
            stick.activate_streaming()                

            for packet in stick.recv_streaming_generator(num_packets=-1):
                heading = packet.euler[0]  # 0–360°
                print(f"[BNO055] Heading atual: {heading:.2f}°")
                
                offset_voltas = graus_para_voltas_azimute(heading)
                estado_bno["heading_offset"] = offset_voltas
                sleep(0.2)
        except Exception as e:
            print("Erro na thread do BNO055:", e)

    threading.Thread(target=bno_task, daemon=True).start()

async def monitorar_e_mover():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:   # Connecting with Rotctl - Hamlib
            client.connect((HOST, PORT))
            await azimute_motor.set_stop()
            await elevacao_motor.set_stop()

            while True:
                client.sendall(b"p\n")
                data = client.recv(1024).decode("utf-8").strip()

                if data:
                    try:
                        values = data.split("\n")[0:2]
                        azimute = float(values[0])
                        elevacao = float(values[1])

                        # Fixing Azimuth Offset to receive valid coordinates in case the rotors base change position
                        azimute_voltas = graus_para_voltas_azimute(azimute)
                        heading_offset = estado_bno["heading_offset"]
                        azimute_corrigido = azimute_voltas - heading_offset

                        elevacao_corrigida = graus_para_voltas_elevacao(elevacao)

                        await set_motor_position(azimute_motor, azimute_corrigido)
                        await set_motor_position(elevacao_motor, elevacao_corrigida)

                        print(f"[Gpredict] Az: {azimute:.1f}° → {azimute_voltas:.3f}v | Corr: {azimute_corrigido:.3f}v | El: {elevacao:.1f}° → {elevacao_corrigida:.3f}v")

                    except (ValueError, IndexError) as e:
                        print("Erro ao interpretar os dados:", data)

                await asyncio.sleep(0.02)

    except Exception as e:
        print("Erro ao conectar ao rotctld:", e)

if __name__ == "__main__":
    iniciar_bno_thread()
    asyncio.run(monitorar_e_mover())

