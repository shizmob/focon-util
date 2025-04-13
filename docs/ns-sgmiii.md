# NS SGMIII/SGMm displays

These comprise at least the following devices:
- Focon 800222-01 ("INTERNAL DISPLAY SGMIII")
- Focon 800224-01 ("EXTERNAL DISPLAY SGMIII")

Supported displays will have two connectors on the side, labeled `X1` and `X2`, with the following pin-out:

X1:
```
  /-------------------\
A | 1  -  3  4  5  6  |
B | 1  2  3  4  5  6  |
  ---------------------

A1: power GND
B1: power Vcc
B2: N/C
 3: address bit 0
 4: address bit 1
 5: address bit 2
 6: address bit 3
```

Connect a 60-140V DC power supply to pins B1 and A1, and bridge the address pin pairs as desired (or leave them all unbridged for ID 0).

X2:
```
  /-------\
Y | 1 2 3 |
  |-------|
X | 1 2 3 |
  ---------

X1: RS-485 in-
X2: RS-485 in+
Y1: RS-485 out-
Y2: RS-485 out+
 3: RS-485 GND
```

Connect a RS-485 transceiver to pins X1, X2, and X3.
Connect Y1, Y2, and Y3 through to X1, X2, and X3 of the next device if you're setting up a daisy chain,
or put a 120 ohm termination resistor between Y1 and Y2 if this is the last device.

Testing so far indicates it also works without this termination resistor at reasonable distances.