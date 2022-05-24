# Reset Switch for Wifi/home assistant/internet

Cable modem and wifi are 12V, which is also arduino-compatible.  Plugs are all the same barrel style

## Current measurements

* cable modem: 0.45 - 0.52 A - wallwart rated to ?A
* dowstairs router: 0.3 - 0.6 A (testing with data send that peaked at a reasonable fraction of network capacity) - wallwart rated to 2.5A
* main router: 0.4 - 0.7 A (testing with data send that peaked at a reasonable fraction of network capacity, includes firmware flashing) - wallwart rated to ?A

Implies that 2.5A wallwart is fine with modem + router upstairs, 1.5A fine with downstairs router.

## Design

Use UNO I have lying around
```
  |------ GPIO7 pull-up input
-Sw 
  |----- GND
  
   GPIO8 output -- LED -- ~250 ohm~ -- GND
  
  |----V+- 5V from Uno
  Relay ---IN- output GPIO2
  |----V-- GND
  
  |-----NO- <disconnected>
  Relay --COM- Center of barrel jacks to router and modem
  |-----NC- 12V supply from center of input barrel socket
  
  
  Barrel jack V-/jacket: all connected together as gnd
 ```
 
## UNO firmware spec
 1. watch for switch to start (maybe with some debounding logic)
 2. If GPIO1 low, set GPIO 2 and 3 high. output serial message to turn off docker
 3. If GPIO1 low->high, set GPIO 3 low. Also send message to start looking for network/start docker
 4. Every 0.5 sec poll for network/docker up.  Toggle GPIO 2 if not up.
 5. If network up, switch to 0.25 sec poll. Once hass is up, GPIO2 off.

If "status" request does not reply within poll time, switch to .1 sec poll.

### s/w on device
Watch for a message from UNO:
1. If "off", docker compose homeassistant down
2. If "on", wait for network, then docker compose homeassistant up
3. If "status", reply with "0" for everything down, "1" for network up but hass not started, "2" for all up.
