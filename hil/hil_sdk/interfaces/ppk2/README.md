# PPK2 Interface Documentation

The PPK2 device is produced by Nordic and comes with open-source interface software, located [here](https://github.com/NordicSemiconductor/pc-nrfconnect-ppk). This software source code, especially the device interface code in `src/device`, was the source (pun intended) of the information for my Python library, along with some trial and error and experimentation. This file contains what I learned about the PPK2's operation and how it influenced the creation of this interface code.

## USB Serial Interface

The PPK2 interfaces with a host via serial communication over USB as a virtual COM port. Once the device has been connected to the nRF Connect App (which I believe flashes the firmware) the device also has "PPK2" in the name which makes it easy to auto-detect. The PPK2 receives commands over the serial port (the file `src/constants.ts` has the values of these commands). Some commands also take arguments, but this is hard to determine without manually inspecting the source. Almost all commands are send-only; there is no response. From what I've seen, the PPK2 only sends serial data back in two situations: First, when metadata is requested (command 0x19), and second, when data collection is started. Otherwise, no responses are given.

There is a reset command (0x20) which appears to do a hard-reset on the PPK2's processor. This means that after sending a reset, you have to basically create a new serial connection. This is helpful, because if the PPK2 gets into a weird state, it is almost impossible to get it to work correctly without doing a reset.

## Metadata

The Get Metadata Command will cause the PPK2 to send back a string of metadata information, which is basically coefficients used for calculating the current values. I'm guessing these are programmed at the factory and can be changed via a calibration process. After sending the command, the data is sent back immediately. The metadata has kind of an interesting format:

NAME:VALUE\n \
NAME:VALUE\n \
... \
NAME:VALUE\n \
END\n

Essentially, it's name/value pairs, with the name and value separated by a colon. Each pair is separated by a newline. The entire dataset ends with the word `END`. I find it helpful to collect this metadata immediately after opening the port, that way in the future you know that all bytes received are sample bytes.

## Sampling

The PPK2 has a fixed sample rate of 100 KS/s. Each sample is 4 bytes. This is a lot of data. That's why the interface uses a child process, because without it, it's almost impossible to keep up with the data rate. The nRF Connect app does have a sample rate selection, but this only does decimation at the software level. Each sample contains four values: A raw ADC value, a sample counter sequence number, range level, and a "bits" field that I don't fully understand. The measurement ranges correspond to different sensitivities that the PPK2 auto-selects to get the best resolution.

The calculation of current values was taken from Nordic's code. I don't really understand it but it seems to work. It's worth noting that Nordic's code has some spike filtering and rolling averages which I didn't implemented. It's unclear how this affects the accuracy.