# NS ICMm displays

These comprise at least the following devices:
- Focon 800313-02 ("External Side Display (ESD)"): default configuration for reference in `ns-icmm.esd.config.bin`

Supported displays will have a single [Harting Han 24DD](https://www.harting.com/en-PE/p/Han-24DD-HMC-M-c-09162243001) connector on top, with the following pin-out:

```
   _/-----------\_
 _/  21 22 23 24  \_
/    17 18 19 20    \
|    13 14 15 16    |
|     9 10 11 12    |
\_    5  6  7  8   _/
  \_  1  2  3  4 _/
    \-----------/

 1: power Vcc
 2: power GND
 3: N/C [no pin]
 4: N/C [no pin]
 5: N/C [no pin]
 6: N/C [no pin]
 7: N/C [no pin]
 8: N/C [no pin]
 9: address bit 0
10: address bit 1 [no pin]
11: address bit 2 [no pin]
12: address bit 3 [no pin]
13: address bit 0 GND
14: address bit 1 GND [no pin]
15: address bit 2 GND [no pin]
16: address bit 3 GND [no pin]
17: RS-485 in-
18: RS-485 in-  [no pin]
19: RS-485 out-
20: (debug RX?) [no pin]
21: RS-485 in+
22: RS-485 in+  [no pin]
23: RS-485 out+
24: (debug TX?) [no pin]
```

Connect a 90-140V DC power supply to pins 1 and 2, and bridge the address pin pairs as desired (or leave them all unbridged for ID 0).

Connect a RS-485 transceiver to pins 13, 17, and 21.
Connect pins 13, 19, and 23 to pins 13, 17, and 21 of the next device if you're setting up a daisy chain,
or put a 120 ohm termination resistor between pins 19 and 23 if this is the last device.

Testing so far indicates it also works without this termination resistor at reasonable distances.
