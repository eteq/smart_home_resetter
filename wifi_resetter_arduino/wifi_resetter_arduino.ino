#define LED_PIN 8
#define SWITCH_PIN 7
#define RELAY_PIN 2

bool wasoff = false;

void setup() {
    digitalWrite(LED_BUILTIN, LOW);

    pinMode(SWITCH_PIN, INPUT_PULLUP);  

    pinMode(LED_PIN, OUTPUT);  
    digitalWrite(LED_PIN, LOW);

    pinMode(RELAY_PIN, OUTPUT);  
    digitalWrite(RELAY_PIN, LOW);

    Serial.begin(9600);    
}

void loop() {
    if (digitalRead(SWITCH_PIN) == LOW) {
        digitalWrite(LED_PIN, HIGH);
        digitalWrite(RELAY_PIN, HIGH);
        if (!wasoff) {
            Serial.println("off");
            wasoff = true;
        }
    } else {
        digitalWrite(LED_PIN, LOW);
        digitalWrite(RELAY_PIN, LOW);
        if (wasoff) {
            Serial.println("on");
            wasoff = false;
        }
    }
    delay(10);
}
