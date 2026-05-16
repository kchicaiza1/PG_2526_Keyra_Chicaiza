/*
 * Proyecto Grúa Torre - Firmware Arduino Nano
 * Control Dual: Joysticks (Manual) + ESP32/UART (Remoto Web)
 */

#include <AccelStepper.h>

// ==========================================
// 1. ASIGNACIÓN DE PINES (Según requirements.md)
// ==========================================

// --- Joysticks (Entradas Analógicas) ---
#define JOY_X A0 // Carro
#define JOY_Y A1 // Elevación
#define JOY_Z A2 // Rotación (Giro)

// --- Driver TB6612FNG (Motores DC N20) ---
// Motor A: Carro (Movimiento horizontal en la flecha)
#define AIN1 2
#define PWMA 3
#define AIN2 4

// Motor B: Elevación (Gancho)
#define PWMB 5
#define BIN1 7
#define BIN2 8

// --- Driver DRV8825 (Motor a Pasos Nema 17) ---
#define STEP_PIN 9
#define DIR_PIN 10

// Inicializar AccelStepper usando Driver (Step y Dir)
AccelStepper stepper(AccelStepper::DRIVER, STEP_PIN, DIR_PIN);

// ==========================================
// 2. VARIABLES DE CONTROL UART (Seguridad)
// ==========================================
char lastWebCmd = 'S';
unsigned long lastWebCmdTime = 0;
const unsigned long WEB_TIMEOUT_MS = 250; // Si no hay comandos en 250ms, forzar Stop

void setup() {
  // Comunicación Serial con el ESP32 (TX GPIO17 a RX D0 del Nano)
  Serial.begin(9600);
  
  // Pines Motor A (Carro)
  pinMode(AIN1, OUTPUT);
  pinMode(AIN2, OUTPUT);
  pinMode(PWMA, OUTPUT);
  
  // Pines Motor B (Elevación)
  pinMode(BIN1, OUTPUT);
  pinMode(BIN2, OUTPUT);
  pinMode(PWMB, OUTPUT);
  
  // Configuración de Motor Stepper
  stepper.setMaxSpeed(1500); // Pasos por segundo máximo
  stepper.setSpeed(0);
}

void loop() {
  // ----------------------------------------------------
  // 1. LEER COMANDOS WEB (UART)
  // ----------------------------------------------------
  if (Serial.available() > 0) {
    char c = Serial.read();
    // Validar si es un comando conocido
    if (c == 'F' || c == 'B' || c == 'U' || c == 'D' || c == 'L' || c == 'R' || c == 'S') {
      lastWebCmd = c;
      lastWebCmdTime = millis();
    }
  }

  // Timeout de Seguridad Web
  if (millis() - lastWebCmdTime > WEB_TIMEOUT_MS) {
    lastWebCmd = 'S';
  }

  // ----------------------------------------------------
  // 2. LEER COMANDOS MANUALES (JOYSTICKS)
  // ----------------------------------------------------
  int joyCarro = analogRead(JOY_X);
  int joyElev  = analogRead(JOY_Y);
  int joyRot   = analogRead(JOY_Z);

  int speedCarroJoy = mapWithDeadzone(joyCarro);
  int speedElevJoy  = mapWithDeadzone(joyElev);
  int speedRotJoy   = mapWithDeadzone(joyRot);

  // ----------------------------------------------------
  // 3. INTERPRETAR INTENCIÓN WEB
  // ----------------------------------------------------
  int speedCarroWeb = 0;
  int speedElevWeb  = 0;
  int speedRotWeb   = 0;
  
  const int WEB_DC_SPEED = 255;      // Max PWM
  const int WEB_STEP_SPEED = 800;    // Pasos/seg constantes para control web

  switch(lastWebCmd) {
    case 'F': speedCarroWeb = WEB_DC_SPEED; break;
    case 'B': speedCarroWeb = -WEB_DC_SPEED; break;
    case 'U': speedElevWeb  = WEB_DC_SPEED; break;
    case 'D': speedElevWeb  = -WEB_DC_SPEED; break;
    case 'L': speedRotWeb   = -WEB_STEP_SPEED; break;
    case 'R': speedRotWeb   = WEB_STEP_SPEED; break;
    case 'S': /* Todos en 0 */ break;
  }

  // ----------------------------------------------------
  // 4. LÓGICA DE CONTROL MIXTO (Suma Joysticks + Web)
  // ----------------------------------------------------
  int finalCarro = constrain(speedCarroJoy + speedCarroWeb, -255, 255);
  int finalElev  = constrain(speedElevJoy  + speedElevWeb,  -255, 255);
  
  // Escalar la velocidad del joystick (que va de -255 a 255) a pasos por segundo
  int speedRotJoyScaled = map(speedRotJoy, -255, 255, -WEB_STEP_SPEED, WEB_STEP_SPEED);
  int finalRot   = constrain(speedRotJoyScaled + speedRotWeb, -1500, 1500);

  // ----------------------------------------------------
  // 5. ACTUAR SOBRE LOS MOTORES
  // ----------------------------------------------------
  controlMotorA(finalCarro); // Carro (Horizontal)
  controlMotorB(finalElev);  // Gancho (Elevación)
  
  if (finalRot != 0) {
    stepper.setSpeed(finalRot);
    stepper.runSpeed();      // NO BLOQUEANTE: Se debe llamar frecuentemente
  } else {
    stepper.setSpeed(0);
  }
}

// ==========================================
// FUNCIONES AUXILIARES
// ==========================================

/*
 * mapWithDeadzone: Mapea la lectura analógica (0-1023) 
 * a un valor de velocidad (-255 a 255) ignorando el ruido central.
 */
int mapWithDeadzone(int val) {
  // Centro = ~512. Deadzone = 400 a 600
  if (val > 600) {
    // Mover hacia adelante/positivo
    return map(val, 600, 1023, 0, 255);
  } else if (val < 400) {
    // Mover hacia atrás/negativo
    return map(val, 400, 0, 0, -255);
  }
  return 0; // Dentro del Deadzone
}

/*
 * controlMotorA: Carro - Adelante/Atrás usando TB6612FNG
 */
void controlMotorA(int speed) {
  if (speed > 0) {
    digitalWrite(AIN1, HIGH);
    digitalWrite(AIN2, LOW);
    analogWrite(PWMA, speed);
  } else if (speed < 0) {
    digitalWrite(AIN1, LOW);
    digitalWrite(AIN2, HIGH);
    analogWrite(PWMA, -speed);
  } else {
    digitalWrite(AIN1, LOW);
    digitalWrite(AIN2, LOW);
    analogWrite(PWMA, 0); // Freno suave
  }
}

/*
 * controlMotorB: Elevación - Subir/Bajar usando TB6612FNG
 */
void controlMotorB(int speed) {
  if (speed > 0) {
    digitalWrite(BIN1, HIGH);
    digitalWrite(BIN2, LOW);
    analogWrite(PWMB, speed);
  } else if (speed < 0) {
    digitalWrite(BIN1, LOW);
    digitalWrite(BIN2, HIGH);
    analogWrite(PWMB, -speed);
  } else {
    digitalWrite(BIN1, LOW);
    digitalWrite(BIN2, LOW);
    analogWrite(PWMB, 0); // Freno suave
  }
}
