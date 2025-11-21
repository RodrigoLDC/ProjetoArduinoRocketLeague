#include <SoftwareSerial.h>
SoftwareSerial bluetooth(2, 3); // RX=2 (HC-06 TX), TX=3 (HC-06 RX)

const int ENA = 9;   // PWM motor A
const int ENB = 10;  // PWM motor B
const int IN1 = 4;
const int IN2 = 5;
const int IN3 = 6;
const int IN4 = 7;

int baseSpeed = 0;
const int MIN_PWM = 90; // mínimo para vencer inércia

char lineBuf[16];
uint8_t idx = 0;

void setup() {
  Serial.begin(9600);
  bluetooth.begin(9600);

  pinMode(ENA, OUTPUT);
  pinMode(ENB, OUTPUT);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);

  stopAll();
  Serial.println("Pronto (protocolo #SSSD\\n).");
}

void loop() {
  while (bluetooth.available()) {
    char ch = bluetooth.read();

    if (ch == '\n') {
      lineBuf[idx] = '\0';
      processLine(lineBuf);
      idx = 0;
    } else {
      if (idx < sizeof(lineBuf) - 1) {
        lineBuf[idx++] = ch;
      } else {
        // overflow: descarta
        idx = 0;
      }
    }
  }
}

void processLine(const char* s) {
  // Esperado: #SSSD (ex: "#120f")
  if (s[0] != '#') return;
  if (!isDigit(s[1]) || !isDigit(s[2]) || !isDigit(s[3])) return;

  char d = s[4];
  if (d == '\0') return;

  int v = (s[1] - '0') * 100 + (s[2] - '0') * 10 + (s[3] - '0');
  if (v < 0) v = 0;
  if (v > 255) v = 255;
  baseSpeed = v;

  // aplica PWM imediatamente
  int spd = (baseSpeed > 0) ? max(baseSpeed, MIN_PWM) : 0;
  analogWrite(ENA, spd);
  analogWrite(ENB, spd);

  // Direção
  switch (d) {
    case 'f': frente(); break;
    case 'b': tras(); break;
    case 'l': esquerda(); break;
    case 'r': direita(); break;
    case 'h': diagFrenteDir(); break;
    case 'g': diagFrenteEsq(); break;
    case 'j': diagTrasDir(); break;
    case 'i': diagTrasEsq(); break;
    case 's': stopAll(); break;
    default: break;
  }

  Serial.print("Cmd: ");
  Serial.print(d);
  Serial.print("  V=");
  Serial.println(baseSpeed);
}

// ================= MOVIMENTOS =================

void frente() {
  digitalWrite(IN1, HIGH); digitalWrite(IN2, LOW);
  digitalWrite(IN3, HIGH); digitalWrite(IN4, LOW);
}

void tras() {
  digitalWrite(IN1, LOW);  digitalWrite(IN2, HIGH);
  digitalWrite(IN3, LOW);  digitalWrite(IN4, HIGH);
}

void esquerda() {
  digitalWrite(IN1, LOW);  digitalWrite(IN2, HIGH);
  digitalWrite(IN3, HIGH); digitalWrite(IN4, LOW);
}

void direita() {
  digitalWrite(IN1, HIGH); digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);  digitalWrite(IN4, HIGH);
}

void diagFrenteDir() { frente(); }
void diagFrenteEsq() { frente(); }
void diagTrasDir()   { tras();   }
void diagTrasEsq()   { tras();   }

void stopAll() {
  analogWrite(ENA, 0);
  analogWrite(ENB, 0);
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);
}
