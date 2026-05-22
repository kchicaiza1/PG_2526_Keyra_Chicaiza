# boot.py - Ejecutado en el arranque del ESP32
import network
import time

# Placeholders para credenciales WiFi
SSID = 'MI_RED'
PASSWORD = 'MI_CLAVE'

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('Conectando a la red WiFi...')
        wlan.connect(SSID, PASSWORD)
        timeout = 15
        while not wlan.isconnected() and timeout > 0:
            time.sleep(1)
            timeout -= 1
            print('.', end='')
    
    if wlan.isconnected():
        print('\nConexión WiFi exitosa!')
        print('Configuración de red (IP, Subnet, Gateway, DNS):', wlan.ifconfig())
    else:
        print('\nFallo al conectar a WiFi. Revisa SSID y PASSWORD.')

connect_wifi()
