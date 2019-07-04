CS 456 Assignment 2

To run the GBN protocol, run

./nEmulator-linux386 <emulator receiving UDP port from sender> <receiver hostname> <receiver UDP port> <emulator receiving UDP port> <sender hostname> <sender UDP port> <max delay in ms> <packet discard probability> <verbose-mode>

java receiver <emulator hostname> <emulator receiving UDP port> <receiver UDP port> <output file>

java sender <emulator hostname> <emulator receiving UDP port from sender> <sender UDP port> <input file>

For example:
nEmulator 9991 host2 9994 9993 host3 9992 1 0.2 0
java receiver host1 9993 9994 <output file>
java sender host1 9991 9992 <input file>

Built on ubuntu1804-004, tested on ubuntu1804-008, ubuntu1804-004 (), ubuntu1804-002

Used java
