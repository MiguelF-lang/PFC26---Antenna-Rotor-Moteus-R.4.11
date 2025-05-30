import asyncio
import moteus
import socket

###Plain Program that Allows Rotors Control via Gpredict - This allows the real-time tracking of satellites 

##Requirement: Starting neutral positions of the rotors must be True North.


##rotctld -m 1 -s 19200 #baudrate
#python -m moteus_gui.tview --target 2


HOST = "localhost"
PORT = 4533

MOTEUS_AZIMUTE_ID = 1
MOTEUS_ELEVACAO_ID = 2

azimute_motor = moteus.Controller(id=MOTEUS_AZIMUTE_ID)
elevacao_motor = moteus.Controller(id=MOTEUS_ELEVACAO_ID)

async def set_motor_position(controller, position):
    await controller.set_position(
        position=position,
        velocity=0.2,
        accel_limit=1.0,
        velocity_limit=3.0,
        query=False
    )
    


async def monitorar_e_mover():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
            client.connect((HOST, PORT))
            await azimute_motor.set_stop()
            await elevacao_motor.set_stop()

            while True:
                client.sendall(b"p\n")
                data = client.recv(1024).decode("utf-8").strip()

                if data:
                    #print("debug cenas", repr(data))
                    try:
                        values = data.split("\n")[0:2]  # Garante que processa apenas as duas primeiras linhas
                        azimute = float(values[0])
                        elevacao = float(values[1])

                        azimute_rotor = round(azimute / 360.0, 3)   # 0.0 a 1.0 voltas
                        #elevacao_rotor = round(elevacao / 90, 3)  # 0.0 a 1.0 voltas (ate 90 graus)
                        elevacao_rotor = -0.285 - (elevacao / 180.0) * 0.5

                        # Envia comandos para os dois motores sempre
                        await set_motor_position(azimute_motor, azimute_rotor)
                        await set_motor_position(elevacao_motor, elevacao_rotor)

                        print(f"Azimute: {azimute:.1f}° → {azimute_rotor:.3f} voltas | Elevação: {elevacao:.1f}° → {elevacao_rotor:.3f} voltas")

                    except (ValueError, IndexError) as e:
                        print("Erro ao interpretar os dados:", data)

                await asyncio.sleep(0.02)

    except Exception as e:
        print("Erro ao conectar ao rotctld:", e)

asyncio.run(monitorar_e_mover())
