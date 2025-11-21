import serial
import pygame
import time

# ============================
PORTA = 'COM5'
BAUDRATE = 9600
DEADZONE = 0.2
INTERVALO = 0.08
# ============================

bt = serial.Serial(PORTA, BAUDRATE)
time.sleep(2)

pygame.init()
pygame.joystick.init()

if pygame.joystick.get_count() == 0:
    print("Nenhum controle detectado!")
    raise SystemExit

joy = pygame.joystick.Joystick(0)
joy.init()
id_controle = joy.get_instance_id()
print(f"Controle 1 detectado: {joy.get_name()} (ID: {id_controle})")

ultimo_comando = None

while True:
    for event in pygame.event.get():
        # Ignora eventos de outros controles
        if not hasattr(event, 'instance_id') or event.instance_id != id_controle:
            continue

    x = joy.get_axis(0)
    y = joy.get_axis(1)

    cmd = 's'
    vel = 0
    mag = (x*x + y*y) ** 0.5

    if mag > DEADZONE:
        vel = int(min(255, mag * 255))
        if y < -DEADZONE:
            if x > DEADZONE:   cmd = 'h'
            elif x < -DEADZONE:cmd = 'g'
            else:               cmd = 'f'
        elif y > DEADZONE:
            if x > DEADZONE:   cmd = 'j'
            elif x < -DEADZONE:cmd = 'i'
            else:               cmd = 'b'
        else:
            if x < -DEADZONE:  cmd = 'l'
            elif x > DEADZONE: cmd = 'r'
    else:
        cmd = 's'
        vel = 0

    pacote = f"#{vel:03d}{cmd}\n"
    bt.write(pacote.encode())
    if cmd != ultimo_comando:
        print(f"[CARRINHO 1] {cmd}  Vel={vel}")
        ultimo_comando = cmd

    time.sleep(INTERVALO)
