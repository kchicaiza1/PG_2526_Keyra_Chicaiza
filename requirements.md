
# Proyecto Grúa Torre: Requerimientos Técnicos para Generación de Código (v2)
## Contexto del Proyecto
Este documento está optimizado para su procesamiento por agentes de IA en **Antigravity** o **Codex**. El objetivo es generar el firmware para una grúa torre con control dual (Manual vía Joysticks y Remoto vía Web) utilizando comunicación serial entre un ESP32 y un Arduino Nano.

---

## 1. Arquitectura de Hardware y Pines
### Controlador A: Arduino Nano (Actuador Principal)
- **Framework:** Arduino / C++
- **Responsabilidad:** Controlar motores y leer entradas analógicas. Escuchar comandos Serial desde ESP32.
- **Asignación de Pines:**
  - **Joysticks:** X (Carro) -> A0, Y (Elevación) -> A1, Giro -> A2.
  - **Driver TB6612FNG (Motores DC N20):** 
    - Motor A (Carro): AIN1(D2), AIN2(D4), PWMA(D3).
    - Motor B (Elevación): BIN1(D7), BIN2(D8), PWMB(D5).
    - STBY -> VCC (5V).
  - **Driver DRV8825 (Motor a Pasos Nema 17):** 
    - STEP -> D9, DIR -> D10.
  - **Comunicación:** RX(D0) desde el TX del ESP32.

### Controlador B: ESP32 DevKit V1 (Interfaz Web)
- **Framework:** MicroPython (Thonny IDE)
- **Responsabilidad:** Levantar un servidor web asíncrono, gestionar conexión WiFi y enviar comandos UART.
- **Asignación de Pines:**
  - **UART TX:** GPIO 17 (Conectado a RX del Nano).
  - **LED Status:** GPIO 2.

---

## 2. Requerimientos de Software (Backlog para Agente)

### Tarea 1: Firmware Arduino (main.ino)
- **Lógica de Control Mixto:** Crear una función que sume la intención del Joystick y la intención de la Web.
- **Protocolo Serial:** Implementar un parser simple para comandos UART (Ej: 'F'=Adelante, 'B'=Atrás, 'U'=Subir, 'D'=Bajar, 'L'=Giro Izq, 'R'=Giro Der, 'S'=Stop).
- **Control de Velocidad:** Utilizar PWM para los motores N20.
- **Control Stepper:** Implementar movimiento suave para el Nema 17 usando la librería `AccelStepper` o lógica de retardos no bloqueante.

### Tarea 2: Firmware ESP32 (boot.py y main.py)
- **Conexión WiFi:** Implementar función robusta de conexión a SSID/Password.
- **Servidor Web:**
  - Endpoint `/` que entregue un HTML con botones (Adelante, Atrás, Izquierda, Derecha, Subir, Bajar, Parar).
  - Uso de JavaScript (Fetch API) en el cliente para enviar peticiones al servidor sin recargar la página.
- **Transmisión UART:** Al recibir una petición web, enviar el carácter correspondiente por el puerto serial a 9600 baudios.

### Tarea 3: Interfaz Web (HTML/CSS)
- Diseño minimalista tipo "Control Remoto".
- Botones grandes y responsivos para uso en móvil.

---

## 3. Instrucciones de Generación para Codex/Antigravity
1. **Archivo 1:** Generar `grúa_arduino.ino` integrando el driver TB6612FNG y AccelStepper.
2. **Archivo 2:** Generar `boot.py` para la configuración de red en MicroPython.
3. **Archivo 3:** Generar `main.py` con el servidor web (uasyncio) y la lógica de envío serial.
4. **Archivo 4:** Generar `index.html` integrado como string dentro de `main.py` o como archivo independiente si el agente lo prefiere.

---

## 4. Consideraciones Técnicas
- **Baudrate:** Configurar ambos dispositivos a 9600 bps.
- **Seguridad:** Los comandos web deben tener un "timeout" de seguridad; si no se recibe un comando de movimiento continuo, los motores deben detenerse.
