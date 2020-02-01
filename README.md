# Radio Recorder

This script helps to record analog audio streams (a line-in audio output of an airband radio station in this case) with two parallel channels.

Channel 1: Signal controlled transmission recording (every tx will be an ogg or mp3 file on the disk). The signal is a TTL level output of the radio device (for example: the squelch status output). Recording starts when LPT port pin13 (SELECT) goes to HIGH state, and stops when the pin goes to LOW.

Channel 2: Continuous daily recording. File rotated at 00:00.

The script has been developed especially for a Rohde und Schwarz XU251 (Series 200 rack) airband radio and a PC with LPT port, but it's easy to implement on a Raspberry PI or any other device (audio input and gpio required!).
