#define LED_PIN 8
#define SWITCH_PIN 7
#define RELAY_PIN 2

#define DELAY_INET_MS 500
#define DELAY_HASS_MS 200

//#define SKIP_RELAY

bool wasoff = false;

void setup() {
    digitalWrite(LED_BUILTIN, LOW);

    pinMode(SWITCH_PIN, INPUT_PULLUP);  

    pinMode(LED_PIN, OUTPUT);  
    digitalWrite(LED_PIN, LOW);

    pinMode(RELAY_PIN, OUTPUT);  
    digitalWrite(RELAY_PIN, LOW);

    Serial.begin(115200);    
}

void loop() {
    if (digitalRead(SWITCH_PIN) == LOW) {
        digitalWrite(LED_PIN, HIGH);
        #ifndef SKIP_RELAY
        digitalWrite(RELAY_PIN, HIGH);
        #endif

        if (!wasoff) {
            Serial.println("off");
            wasoff = true;
        }
    } else {
        digitalWrite(LED_PIN, LOW);
        #ifndef SKIP_RELAY
        digitalWrite(RELAY_PIN, LOW);
        #endif

        if (wasoff) {
            net_then_hass_startup_sequence();
            wasoff = false;
        }
    }
    delay(10);
}

void net_then_hass_startup_sequence() {
    bool netup = false;

    Serial.setTimeout(DELAY_INET_MS);

    while (!netup) {

        digitalWrite(LED_PIN, !digitalRead(LED_PIN));

        Serial.println("inet_status");
        String res = Serial.readStringUntil('\n');
        
        if (res == "1") {
            // internet is up!
            netup = true;
        } else if (res == "0") {
            //not up
            netup = false;
        } else {
            //ambiguous, just try again, although maybe this should try a longer delay?
            netup = false;
        }
    }
    Serial.println("on");
    for (int i=0; i < 3; i++) {
         digitalWrite(LED_PIN, HIGH);
        delay(DELAY_HASS_MS/2);
         digitalWrite(LED_PIN, LOW);
        delay(DELAY_HASS_MS/2);
    }
}