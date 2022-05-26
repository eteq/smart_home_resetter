#define LED_PIN 8
#define SWITCH_PIN 7
#define HASS_SWITCH_PIN 14 // 14 = A0
#define RELAY_PIN 2

#define DELAY_INET_MS 500
#define DELAY_HASS_MS 150

//#define SKIP_RELAY

bool wasoff = false;
bool wasoff_hass = false;

void setup() {
    digitalWrite(LED_BUILTIN, LOW);

    pinMode(SWITCH_PIN, INPUT_PULLUP);
    pinMode(HASS_SWITCH_PIN, INPUT_PULLUP);

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
    
    if (digitalRead(HASS_SWITCH_PIN) == LOW) {
        digitalWrite(LED_PIN, HIGH);

        if (!wasoff_hass) {
            Serial.println("off");
            wasoff_hass = true;
        }
    } else {
        digitalWrite(LED_PIN, LOW);

        if (wasoff_hass) {
            hass_startup();
            wasoff_hass = false;
        }
    }
    delay(10);
}

void net_then_hass_startup_sequence() {
    String read_result;
    bool netup = false;

    Serial.setTimeout(DELAY_INET_MS);

    while (!netup) {
        unsigned long loopstart = millis();

        digitalWrite(LED_PIN, !digitalRead(LED_PIN));

        Serial.println("inet_status");
        read_result = Serial.readStringUntil('\n');
        
        if (read_result == "1") {
            // internet is up!
            netup = true;
        } else if (read_result == "0") {
            //not up
            netup = false;
        } else {
            //ambiguous, just try again, although maybe this should try a longer delay?
            netup = false;
        }
        
        unsigned long dt = (millis() - loopstart);
        if (dt < DELAY_INET_MS) {
            delay(DELAY_INET_MS - dt);
        }
    }

    hass_startup();
}

void hass_startup() {
    String read_result;
    bool hassup = false;

    // start hass
    Serial.println("on");
    Serial.setTimeout(DELAY_HASS_MS);
    
    while (!hassup) {
        unsigned long loopstart = millis();

        digitalWrite(LED_PIN, !digitalRead(LED_PIN));
        Serial.println("hass_status");
        read_result = Serial.readStringUntil('\n');

        if (read_result == "1") {
            // hass is up!
            hassup = true;
        } else if (read_result == "0") {
            //not up
            hassup = false;
        } else {
            //ambiguous, just try again, although maybe this should try a longer delay?
            hassup = false;
        }

        unsigned long dt = (millis() - loopstart);
        if (dt < DELAY_HASS_MS) {
            delay(DELAY_HASS_MS - dt);
        }
    }
    digitalWrite(LED_PIN, LOW);
}