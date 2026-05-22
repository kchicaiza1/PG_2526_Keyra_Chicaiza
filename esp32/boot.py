# boot.py - Ejecutado en el arranque del ESP32
import network
import time
import sys
import uselect

# ==========================================
# CONFIGURACIÓN DE CREDENCIALES WIFI
# ==========================================
# Modifica estas variables con los datos de tu red local
SSID = 'MI_RED'
PASSWORD = 'MI_CLAVE'

def connect_wifi():
    """
    Establece la conexión a la red WiFi configurada.
    """
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    if not wlan.isconnected():
        print('Conectando a la red WiFi...')
        wlan.connect(SSID, PASSWORD)
        
        # Espera un máximo de 15 segundos para conectar
        timeout = 15
        while not wlan.isconnected() and timeout > 0:
            time.sleep(1)
            timeout -= 1
            print('.', end='')
    
    # Verificar el estado de la conexión
    if wlan.isconnected():
        print('\nConexión WiFi exitosa!')
        print('Configuración de red (IP, Subnet, Gateway, DNS):', wlan.ifconfig())
    else:
        print('\nFallo al conectar a WiFi. Revisa SSID y PASSWORD.')

def menu_inicio(timeout_segundos=5):
    """
    Muestra un menú interactivo en la consola serial (REPL).
    Permite detener el inicio automático para programar y subir archivos.
    Avanza automáticamente si se agota el tiempo de espera.
    """
    print("\n" + "="*40)
    print("      SISTEMA DE CONTROL - GRÚA TORRE")
    print("="*40)
    print("1. Iniciar sistema normalmente (Modo Ejecución)")
    print("2. Detener en modo programación (Liberar REPL)")
    print(f"Selecciona una opción (Avanza a opción 1 en {timeout_segundos}s)...")
    
    # Configurar la escucha del puerto serial (stdin) de forma no bloqueante
    poller = uselect.poll()
    poller.register(sys.stdin, uselect.POLLIN)
    
    tiempo_inicio = time.time()
    while (time.time() - tiempo_inicio) < timeout_segundos:
        # Monitorea la terminal durante 100ms en cada iteración del bucle
        if poller.poll(100):
            caracter = sys.stdin.read(1)
            if caracter == '1':
                print("\n-> Opción 1 seleccionada. Iniciando...")
                return True
            elif caracter == '2':
                print("\n-> Opción 2 seleccionada. Modo programación activo.")
                print("Consola REPL liberada. Puedes subir o modificar archivos.")
                return False
    
    # Si se agota el tiempo de espera, se asume que corre autónomamente en la grúa
    print("\n-> Tiempo de espera agotado. Iniciando de forma automática...")
    return True

# ==========================================
# FLUJO PRINCIPAL DE ARRANQUE (BOOTSTRAP)
# ==========================================

# Ejecutamos el menú de seguridad antes de iniciar cualquier servicio (WiFi o Servidor Web)
if menu_inicio(timeout_segundos=5):
    # Si el usuario selecciona la opción 1 o se agota el tiempo, conecta al WiFi
    # y permite que MicroPython pase a ejecutar el archivo main.py
    connect_wifi()
else:
    # Si el usuario selecciona la opción 2, detiene el script
    # Esto evita que MicroPython salte a ejecutar el main.py y libera la consola serial
    sys.exit()
