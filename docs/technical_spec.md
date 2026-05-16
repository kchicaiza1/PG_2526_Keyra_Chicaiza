openapi: 3.0.0
info:
  title: Grúa Torre API (ESP32)
  description: Especificación técnica para el control remoto de una grúa torre. Documenta los endpoints del servidor web del ESP32 y el protocolo de mensajería UART entre el ESP32 y el Arduino Nano.
  version: 1.0.0
servers:
  - url: http://<ESP32_IP_ADDRESS>
    description: Servidor Web del ESP32

paths:
  /:
    get:
      summary: Interfaz Web
      description: Devuelve el archivo index.html que contiene la interfaz de usuario para el control de la grúa.
      responses:
        '200':
          description: Documento HTML
          content:
            text/html:
              schema:
                type: string
  
  /move:
    get:
      summary: Enviar comando de movimiento
      description: Recibe el comando de movimiento desde la interfaz web e instruye al ESP32 para enviarlo vía UART al Arduino.
      parameters:
        - name: cmd
          in: query
          required: true
          description: Carácter que representa la acción a realizar.
          schema:
            type: string
            enum: ['F', 'B', 'U', 'D', 'L', 'R', 'S']
      responses:
        '200':
          description: Comando recibido y enviado por UART
          content:
            text/plain:
              schema:
                type: string
                example: OK

components:
  description: |
    # Protocolo de Mensajería UART
    La comunicación entre el ESP32 (Controlador B) y el Arduino Nano (Controlador A) se realiza mediante un enlace serial estándar.
    
    ## Especificaciones Físicas
    - **Baudrate:** 9600 bps
    - **Data bits:** 8
    - **Stop bits:** 1
    - **Paridad:** Ninguna
    - **Conexión Hardware:** ESP32 TX (GPIO 17) -> Arduino RX (D0)
    
    ## Estructura de Mensajes
    El protocolo es basado en caracteres simples en código ASCII. Se envía exactamente 1 byte (1 carácter) por cada comando.
    
    ### Comandos Soportados:
    | Carácter | Acción | Subsistema Afectado |
    | :---: | :--- | :--- |
    | **`F`** | Forward (Adelante) | Carro (TB6612FNG - Motor A) |
    | **`B`** | Backward (Atrás) | Carro (TB6612FNG - Motor A) |
    | **`U`** | Up (Subir) | Elevación (TB6612FNG - Motor B) |
    | **`D`** | Down (Bajar) | Elevación (TB6612FNG - Motor B) |
    | **`L`** | Left (Izquierda) | Rotación (DRV8825 - Motor Pasos) |
    | **`R`** | Right (Derecha) | Rotación (DRV8825 - Motor Pasos) |
    | **`S`** | Stop (Detener) | Todos los motores |
    
    ## Flujo de Trabajo y Seguridad
    - El cliente web envía una petición `/move?cmd=X` repetidamente mientras se mantiene presionado un botón en la interfaz.
    - El ESP32 retransmite inmediatamente el carácter recibido por UART al Arduino.
    - El Arduino cuenta con un mecanismo de **Timeout de Seguridad**. Si el Arduino deja de recibir el carácter correspondiente a un movimiento por un período superior a un umbral (ej. 200 ms), forzará un estado de parada (equivalente a recibir 'S') deteniendo los motores instantáneamente para evitar daños o accidentes en caso de desconexión WiFi.
