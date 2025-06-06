import asyncio
import threading
import tkinter as tk
from tkinter import ttk
import moteus
from time import sleep
from bno055_usb_stick_py import BnoUsbStick

###Program that Allows Rotors Control via a super basic GUI and Compensates directional changes of the Rotors base.

###Mainly used for testing, debugging, and fun motions... as it provides more speed and control of angles



# IDs dos motores
MOTEUS_AZIMUTE_ID = 1
MOTEUS_ELEVACAO_ID = 2

# Controladores
azimute_motor = moteus.Controller(id=MOTEUS_AZIMUTE_ID)
elevacao_motor = moteus.Controller(id=MOTEUS_ELEVACAO_ID)

# Queues para comunicação com os motores
queue_az = asyncio.Queue()
queue_el = asyncio.Queue()

# Estado global
estado_motores = {
    "az_enabled": False,
    "el_enabled": False,
    "az_pos": 0.0,
    "el_pos": -0.285,                                   #The Offset is required because of our personal assembly - it will be different for other Rotor assemblies
    "heading_ref": None,
}

def graus_para_voltas_azimute(graus):
    return round(graus / 360.0, 3)                      #Moteus rotors receive unitary positions as in 1 = 360 deg.

def graus_para_voltas_elevacao(graus):
    return round(-0.285 - (graus / 180.0) * 0.5, 3)     #The Offset is required because of our personal assembly - it will be different with different Rotor assemblies

async def loop_motor(controller, queue, enable_flag_name, pos_key):
    while True:
        try:
            estado_motores[pos_key] = queue.get_nowait()
        except asyncio.QueueEmpty:
            pass

        if estado_motores[enable_flag_name]:
            await controller.set_position(
                position=estado_motores[pos_key],
                velocity=0.2,
                accel_limit=1.0,
                velocity_limit=3.0,
                query=False
            )
        await asyncio.sleep(0.02)

def iniciar_interface(loop):
    def atualizar_azimute(val):
        graus = float(val)
        voltas = graus_para_voltas_azimute(graus)
        loop.call_soon_threadsafe(lambda: queue_az.put_nowait(voltas))

    def atualizar_elevacao(val):
        graus = float(val)
        voltas = graus_para_voltas_elevacao(graus)
        loop.call_soon_threadsafe(lambda: queue_el.put_nowait(voltas))

    def set_az_entry():
        try:
            val = float(az_entry.get())
            atualizar_azimute(val)
        except ValueError:
            pass

    def set_el_entry():
        try:
            val = float(el_entry.get())
            atualizar_elevacao(val)
        except ValueError:
            pass

    def parar():
        estado_motores["az_enabled"] = False
        estado_motores["el_enabled"] = False
        loop.create_task(azimute_motor.set_stop())
        loop.create_task(elevacao_motor.set_stop())
        print("Motores PARADOS")

    def retomar():
        estado_motores["az_enabled"] = True
        estado_motores["el_enabled"] = True

        loop.create_task(azimute_motor.set_position(
            position=estado_motores["az_pos"],
            velocity=0.2,
            accel_limit=1.0,
            velocity_limit=3.0,
            query=False
        ))
        loop.create_task(elevacao_motor.set_position(
            position=estado_motores["el_pos"],
            velocity=0.2,
            accel_limit=1.0,
            velocity_limit=3.0,
            query=False
        ))
        print("Motores RETOMADOS")

    root = tk.Tk()
    root.title("Controlo de Rotores Moteus")

    tk.Label(root, text="Azimute (°)").grid(row=0, column=0)
    az_slider = ttk.Scale(root, from_=0, to=360, orient="horizontal", command=atualizar_azimute)
    az_slider.grid(row=0, column=1)

    az_entry = ttk.Entry(root)
    az_entry.grid(row=0, column=2)
    ttk.Button(root, text="Set", command=set_az_entry).grid(row=0, column=3)

    tk.Label(root, text="Elevação (°)").grid(row=1, column=0)
    el_slider = ttk.Scale(root, from_=0, to=90, orient="horizontal", command=atualizar_elevacao)
    el_slider.grid(row=1, column=1)

    el_entry = ttk.Entry(root)
    el_entry.grid(row=1, column=2)
    ttk.Button(root, text="Set", command=set_el_entry).grid(row=1, column=3)

    ttk.Button(root, text="Parar Motores", command=parar).grid(row=2, column=1)
    ttk.Button(root, text="Retomar", command=retomar).grid(row=2, column=2)

    root.mainloop()

def iniciar_bno_loop(loop):
    def bno_task():
        stick = BnoUsbStick(port="/dev/ttyACM1")            # Forcing the Port ACM1 (My personal use case)
        print("Using BNO port:", stick.port_name)
        stick.write_register(0x3D, 0b00001100)              # Setting the Operation Mode '0x3D' to NDOF '0b00001100' (Nine Deg. of Freedom)
        sleep(0.1)
        stick.activate_streaming()

        for packet in stick.recv_streaming_generator(num_packets=-1):
            heading = packet.euler[0]  # 0-360°

            # Converting heading in 'laps' (to "fix" the direction change afterwards) 
            offset_voltas = graus_para_voltas_azimute(heading)

            # Updating azimuth position to compensate direction changes.
            nova_pos = -offset_voltas
            estado_motores["az_pos"] = nova_pos
            loop.call_soon_threadsafe(lambda: queue_az.put_nowait(nova_pos))

            sleep(0.2)

    # Iniciar a thread do BNO055
    threading.Thread(target=bno_task, daemon=True).start()



def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.create_task(loop_motor(azimute_motor, queue_az, "az_enabled", "az_pos"))
    loop.create_task(loop_motor(elevacao_motor, queue_el, "el_enabled", "el_pos"))

    iniciar_bno_loop(loop)
    threading.Thread(target=loop.run_forever, daemon=True).start()
    iniciar_interface(loop)

if __name__ == "__main__":
    main()
