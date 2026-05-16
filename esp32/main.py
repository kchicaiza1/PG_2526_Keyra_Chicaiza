# main.py - Servidor web asíncrono y control UART
import uasyncio as asyncio
import machine
import time

# Configuración de UART
# UART TX: GPIO 17 (conectado al RX del Nano)
# UART RX: GPIO 16 (no se usa para recibir en este proyecto)
uart = machine.UART(2, baudrate=9600, tx=17, rx=16)

# LED de status (GPIO 2 es el LED integrado en la mayoría de DevKit V1)
led = machine.Pin(2, machine.Pin.OUT)

def send_command(cmd):
    """Envía un comando de 1 carácter por UART al Arduino"""
    if cmd in ['F', 'B', 'U', 'D', 'L', 'R', 'S']:
        uart.write(cmd)
        print(f"UART TX: {cmd}")

def get_html():
    """Lee y retorna el contenido de index.html"""
    try:
        with open('index.html', 'r') as f:
            return f.read()
    except Exception as e:
        return "<html><body><h1>Error: index.html no encontrado en el sistema de archivos</h1></body></html>"

async def handle_client(reader, writer):
    """Maneja las peticiones HTTP entrantes"""
    try:
        request_line = await reader.readline()
        if not request_line:
            writer.close()
            await writer.wait_closed()
            return
            
        request_str = request_line.decode('utf-8')
        
        # Ignorar peticiones vacías o demasiado cortas
        if len(request_str) < 4:
            writer.close()
            await writer.wait_closed()
            return

        print("Request HTTP:", request_str.strip())
        
        # Consumir el resto de las cabeceras HTTP para liberar el buffer
        while True:
            line = await reader.readline()
            if not line or line == b'\r\n':
                break
        
        # Analizar la ruta solicitada
        if request_str.startswith('GET / ') or request_str.startswith('GET /?'):
            # Servir la interfaz web (index.html)
            html = get_html()
            response = 'HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n' + html
            writer.write(response.encode('utf-8'))
            
        elif request_str.startswith('GET /move'):
            # Buscar el comando en los parámetros de la URL
            cmd = 'S' # Parada por defecto (Stop)
            idx = request_str.find('cmd=')
            if idx != -1:
                cmd = request_str[idx+4:idx+5] # Extraer el carácter (F,B,U,D,L,R,S)
                
            # Parpadeo rápido del LED indicando actividad
            led.value(1)
            send_command(cmd)
            led.value(0)
            
            # Responder al cliente
            response = 'HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nConnection: close\r\n\r\nOK'
            writer.write(response.encode('utf-8'))
            
        else:
            # 404 Not Found para cualquier otra ruta
            response = 'HTTP/1.1 404 Not Found\r\nConnection: close\r\n\r\n'
            writer.write(response.encode('utf-8'))
            
        await writer.drain()
        
    except Exception as e:
        print("Error en handle_client:", e)
    finally:
        writer.close()
        await writer.wait_closed()

async def main():
    print('Iniciando servidor web asíncrono en puerto 80...')
    server = await asyncio.start_server(handle_client, "0.0.0.0", 80)
    
    # Mantener el loop principal vivo para permitir que el servidor corra en el background
    while True:
        await asyncio.sleep(1)

# Entry point
try:
    asyncio.run(main())
except KeyboardInterrupt:
    print('Servidor web detenido por el usuario.')
