# lsstCamVacFeedVerification

Script to run the Vacuum feedthrough tests using a Keithley 3700A with two 3722 boards on slot 1 and 2.

Module on slot 1 must be connected to Test Board 1 (37 pins connectors).
Module on slot 2 must be connected to Test Board 2 (44 pins connectors).

Tests reports are generated in the reports directory.

# Requirements

- Python >3.6
- python-vxi11
- engineering_notation


# Usage

usage: vacFeedTester.py [-h] [-cl] [-hp] [-t] [-p] [-n NAME] [-ip IP]

optional arguments:
  -h, --help  show this help message and exit
  -cl         Run Continuity and Load test
  -hp         Run Hi-Pot test
  -t          Run Continuity and Load and Hi-Pot test
  -p          Run Pinout test
  -n NAME     Append a name to the report files
  -ip IP      Keithley IP address
  ```
