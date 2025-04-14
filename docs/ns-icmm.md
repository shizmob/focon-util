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

## Firmware modifications

### Baudrate increase

The firmware programs a clock divisor in the communication chip (UART transceiver) to obtain the standard 57.6 kbaud/s communication speed.
By tweaking this divisor, it's possible to bump the communication speed, and thus the maximum framerate, to 115.2 kbaud/s.

A [binary patch for application version 1.31](ns-icmm.app.131-baud115k.xd3) is available. Given the application extracted from a flash dump (using `focon-util flash unpack`), it can be applied using `xdelta3`:

```sh
xdelta3 -d -s ns-icmm.app.131.bin ns-icmm.app.131-baud115k.xd3 ns-icmm.app.131-baud115k.bin
```

The modified application can then be flashed through `focon-util`:

```sh
focon-util display selfdestruct                     # erase existing application
focon-util info                                     # ensure the device is now in bootloader mode
focon-util boot flash ns-icmm.app.131-baud115k.bin  # flash new application
focon-util boot launch                              # boot into new application
focon-util -b 115200 info                           # ensure the device is in application mode and responding at 115.2 kbaud/s
```

Once successful, the `-b <BAUDRATE>` argument can be used (*before any subcommand*) to communicate with the device.
Note that if the device is in bootloader mode, it will still use the original 57.6 kbaud/s speed.

## Hardware modifications

### UART crystal

The communication chip (UART transceiver) is paired to a dedicated clock crystal, which by default resonates at 1.8432 MHz.
It can be replaced to increase the effective communication speed, and thus the maximum framerate, to up to a theoretical 1 Mbaud as follows:

`new_baudrate = orig_baudrate * (new_frequency / 1.8432)`

The stock baudrate is 57.6 kb/s, but can be increased to 115.2 kbaud/s through [a firmware modification](#baudrate-increase).
The [https://www.ti.com/lit/ds/symlink/tl16c550c.pdf](datasheet) for the chip claims compatibility with up to 16 MHz.
A 7.15909 MHz crystal on 115.2 kbaud/s firmware has been tested successfully, resulting in an effective baudrate of ~447 kbaud/s
and framerate of ~20 frames per second.

If you replace the crystal, the `-x <FREQ>` argument can be used (*before any subcommand*) to have `focon-util` adjust the baudrate automatically.

### SoC crystal

The main processor (SoC) is paired to a clock crystal running at 16 MHz. Even though the [manual](https://www.renesas.com/en/document/mah/h83003-hardware-manual) claims this is the maximum frequency, practice shows it can be replaced with a higher-frequency crystal for a modest bump in performance.

A 20 MHz crystal has been verified to work and give a ~8% speed increase on top of the other modifications, bumping the framerate from ~20 to ~21.5 frames per second.