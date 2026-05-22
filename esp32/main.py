# main.py - Servidor web asíncrono y control UART
import uasyncio as asyncio
import machine
import time

# ==========================================
# CONFIGURACIÓN DE UART (COMUNICACIÓN SERIAL)
# ==========================================
# UART 2:
# - Baudrate: 9600 bps (debe coincidir con la grúa Arduino)
# - TX (Transmisión): GPIO 17 (Conectado al RX del Arduino Nano)
# - RX (Recepción): GPIO 16 (No utilizado para recibir datos en este proyecto)
uart = machine.UART(2, baudrate=9600, tx=17, rx=16)

# LED de estado (GPIO 2 es el LED integrado en la placa ESP32 DevKit V1)
led = machine.Pin(2, machine.Pin.OUT)

def send_command(cmd):
    """
    Envía un comando de un solo carácter por puerto Serial (UART) al Arduino Nano.
    Frenado por lista blanca de comandos seguros.
    """
    if cmd in ['F', 'B', 'U', 'D', 'L', 'R', 'S']:
        uart.write(cmd)
        print(f"UART TX: {cmd}")

def get_html():
    """
    Intenta abrir y leer el archivo index.html para retornar su contenido HTML/CSS/JS.
    Retorna un HTML con mensaje de error si no encuentra el archivo.
    """
    try:
        with open('index.html', 'r') as f:
            return f.read()
    except Exception as e:
        return "<html><body><h1>Error: index.html no encontrado en el sistema de archivos</h1></body></html>"

async def handle_client(reader, writer):
    """
    Manejador asíncrono para las conexiones HTTP entrantes de los clientes (navegadores).
    """
    try:
        # Lee la primera línea de la petición HTTP (ej: "GET /move?cmd=F HTTP/1.1")
        request_line = await reader.readline()
        if not request_line:
            writer.close()
            await writer.wait_closed()
            return
            
        request_str = request_line.decode('utf-8')
        
        # Ignorar peticiones malformadas o muy cortas
        if len(request_str) < 4:
            writer.close()
            await writer.wait_closed()
            return

        print("Request HTTP:", request_str.strip())
        
        # Consume/descarta el resto de las cabeceras HTTP para liberar el búfer de entrada
        while True:
            line = await reader.readline()
            if not line or line == b'\r\n':
                break
        
        # CASO 1: Servir la página web de control
        if request_str.startswith('GET / ') or request_str.startswith('GET /?'):
            html = get_html()
            response = 'HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n' + html
            writer.write(response.encode('utf-8'))
            
        # CASO 2: Procesar la acción de movimiento
        elif request_str.startswith('GET /move'):
            cmd = 'S' # Por seguridad, el comando por defecto es parar (Stop)
            idx = request_str.find('cmd=')
            if idx != -1:
                # Extrae el único caracter del comando (ej: 'F', 'B', etc.)
                cmd = request_str[idx+4:idx+5]
                
            # Parpadeo de control en el LED integrado del ESP32 para indicar actividad UART
            led.value(1)
            send_command(cmd)
            led.value(0)
            
            # Responder con un simple texto de confirmación al cliente JavaScript (Fetch API)
            response = 'HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nConnection: close\r\n\r\nOK'
            writer.write(response.encode('utf-8'))
            
        # CASO 3: Ruta desconocida (404 Not Found)
        else:
            response = 'HTTP/1.1 404 Not Found\r\nConnection: close\r\n\r\n'
            writer.write(response.encode('utf-8'))
            
        await writer.drain()
        
    except Exception as e:
        print("Error en handle_client:", e)
    finally:
        # Cerrar el socket del cliente adecuadamente
        writer.close()
        await writer.wait_closed()

async def main():
    """
    Función principal asíncrona que levanta el servidor TCP en el puerto 80.
    """
    print('Iniciando servidor web asíncrono en puerto 80...')
    server = await asyncio.start_server(handle_client, "0.0.0.0", 80)
    
    # Mantiene el bucle de eventos activo
    while True:
        await asyncio.sleep(1)

# ==========================================
# PUNTO DE ENTRADA (ENTRY POINT)
# ==========================================
try:
    # Lanza la ejecución del bucle de eventos asíncronos
    asyncio.run(main())
except KeyboardInterrupt:
    print("\nServidor web detenido desde el teclado.")
