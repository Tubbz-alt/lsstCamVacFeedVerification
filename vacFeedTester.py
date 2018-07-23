#!/usr/bin/env python
import csv
import vxi11
from datetime import datetime
import argparse
import sys
import os


def preConfiguration():
    # Module 1 - 37 pins module
    # Module 2 - 44 pins module

    # Reset the 3700A to factory defaults
    instr.write('reset()')
    instr.write('channel.connectrule = channel.BREAK_BEFORE_MAKE')

    # Configure 37 pins module as a 96 channels device. Connect two halves of module 1 using backplane bank 3
    instr.write('channel.close("1913,1923")')
    # Configure 44 pins module as a 96 channels device. Connect two halves of module 2 using backplane bank 4
    instr.write('channel.close("2914,2924")')

    # Configure DMM
    instr.write('dmm.connect = dmm.CONNECT_TWO_WIRE')
    instr.write('dmm.autodelay = dmm.AUTODELAY_ONCE')
    instr.write('dmm.filter.count = 5')
    instr.write('dmm.filter.type = dmm.FILTER_REPEAT_AVG')
    instr.write('dmm.filter.enable = dmm.ON')

    instr.write('errorqueue.clear()')

    if not os.path.exists('reports'):
        os.makedirs('reports')

    instr.write('beeper.enable = 0')


def continuityLoadTest():
    i = datetime.now()
    with open("reports/continuity_load_" + i.strftime('%Y_%m_%d_%Hh%Mm%Ss') + f"_{name}.txt", 'w') as file:

        fileWrite(file, "LSST Camera Vacuum feedthrough Continuity and Load Test\n")
        fileWrite(file, name + "\n")
        fileWrite(file, i.strftime('%Y/%m/%d %H:%M:%S\n\n'))

        show("Cont. Load Test", "Preparing for test")

        preConfiguration()

        instr.write('dmm.func = "dcvolts"')
        instr.write('dmm.range = 7')

        # Setup common voltages
        # GND to HI on 37 pin module
        chClose(1, 89)
        # GND to LO on 37 pin module
        chClose(1, 93)
        # 5V to HI on 44 pin module
        chClose(2, 89)
        # GND to LO on 44 pin module
        chClose(2, 93)

        goodWires = []
        badWires = []

        n = 1
        for row in channelTable:
            s1 = f"Cont. Load ({n}/{len(channelTable)})"
            fileWrite(file, "\n" + s1 + "\n")
            pin44 = row[0]
            pin37A = row[1]
            pin37B = row[2]

            # Test wire A
            wireValid = True
            chClose(2, pin44)
            valid1, voltage1, expected1 = read(1, 0)
            valid2, voltage2, expected2 = read(2, 5)
            valid = 'Error'
            if (valid1 and valid2): valid = 'OK'
            s2 = f"    -- {pin44:02d}H {valid} {voltage1:.2f}|{voltage2:.2f} v      ({expected1:.2f}|{expected2:.2f})v"
            show(s1, s2)
            fileWrite(file, s2 + "\n")
            wireValid &= valid1 and valid2

            chClose(1, pin37A)
            valid1, voltage1, expected1 = read(1, 1.66)
            valid2, voltage2, expected2 = read(2, 1.66)
            valid = 'Error'
            if (valid1 and valid2): valid = 'OK'
            s2 = f"{pin37A:02d}H -- {pin44:02d}H {valid} {voltage1:.2f}|{voltage2:.2f} v      ({expected1:.2f}|{expected2:.2f})v"
            show(s1, s2)
            fileWrite(file, s2 + "\n")
            chOpen(1, pin37A)

            wireValid &= valid1 and valid2
            if wireValid:
                goodWires.append([pin37A, pin44])
            else:
                badWires.append([pin37A, pin44])

            # Test wire B
            wireValid = True
            valid1, voltage1, expected1 = read(1, 0)
            valid2, voltage2, expected2 = read(2, 5)
            valid = 'Error'
            if (valid1 and valid2): valid = 'OK'
            s2 = f"    -- {pin44:02d}H {valid} {voltage1:.2f}|{voltage2:.2f} v      ({expected1:.2f}|{expected2:.2f})v"
            show(s1, s2)
            fileWrite(file, s2 + "\n")
            wireValid &= valid1 and valid2

            chClose(1, pin37B)
            valid1, voltage1, expected1 = read(1, 1.66)
            valid2, voltage2, expected2 = read(2, 1.66)
            valid = 'Error'
            if (valid1 and valid2): valid = 'OK'
            s2 = f"{pin37B:02d}H -- {pin44:02d}H {valid} {voltage1:.2f}|{voltage2:.2f} v      ({expected1:.2f}|{expected2:.2f})v"
            show(s1, s2)
            fileWrite(file, s2 + "\n")
            chOpen(1, pin37B)

            wireValid &= valid1 and valid2
            if wireValid:
                goodWires.append([pin37B, pin44])
            else:
                badWires.append([pin37B, pin44])
                errorBeep()

            chOpen(2, pin44)
            n += 1

        fileWrite(file, "\n-----------------------------------------------------------------------------------\n")
        if len(badWires) > 0:
            show("$BCont. Load FAILED!", f"$B{len(badWires)} of {len(channelTable)*2} wires are bad")
            errorBeep()
            errorBeep()
            fileWrite(file, "\n---> Hi-Pot Test FAILED!\n\n")
            fileWrite(file, f"{len(goodWires)} of {len(channelTable)*2} wires passed the Hi-Pot Test\n")
            fileWrite(file, f"These wires failed:\n\n")
            fileWrite(file, f"pin37\t\tpin47\n")
            fileWrite(file, f"-----\t\t-----\n")
            for pair in badWires:
                fileWrite(file, f"CH{pair[0]}H\t\tCH{pair[1]}H\n")
        else:
            show("Cont. Load PASSED!", f"{len(goodWires)} of {len(channelTable)*2} wires are good")
            successBeep()
            fileWrite(file, "\n---> Hi-Pot Test PASSED!\n\n")
            fileWrite(file, f"{len(goodWires)} of {len(channelTable)*2} wires passed the Hi-Pot Test\n")


def hiPotTest():
    i = datetime.now()
    with open("reports/hi_pot_" + i.strftime('%Y_%m_%d_%Hh%Mm%Ss') + f"_{name}.txt", 'w') as file:
        fileWrite(file, "LSST Camera Vacuum feedthrough Hi-Pot Test\n")
        fileWrite(file, name + "\n")
        fileWrite(file, i.strftime('%Y/%m/%d %H:%M:%S\n\n'))

        show("HiPot. Test", "Preparing for test")
        preConfiguration()

        instr.write('dmm.func = "dcvolts"')
        instr.write('dmm.range = 260')

        # Setup common voltages
        # GND to HI on 37 pin module
        chClose(1, 90)
        # GND to LO on 37 pin module
        chClose(1, 93)
        # 5V to HI on 44 pin module
        chClose(2, 91)
        # GND to LO on 44 pin module
        chClose(2, 93)

        goodWires = []
        badWires = []

        n = 1
        for row in channelTable:
            s1 = f"HiPot ({n}/{len(channelTable)})"
            fileWrite(file, "\n" + s1 + "\n")

            pin44 = row[0]
            pin37A = row[1]
            pin37B = row[2]

            # Close all 37 pins module channels
            closeArray = []
            for row2 in channelTable:
                pin37A2 = row2[1]
                pin37B2 = row2[2]
                closeArray.append(pin37A2)
                closeArray.append(pin37B2)
            chClose(1, closeArray)

            # Open the 37 pins module channels that correspond to the pair of wires beeing tested
            chOpen(1, [pin37A, pin37B])

            # Close the 44 pins channel
            chClose(2, pin44)

            valid1, voltage1, expected1 = read(1, 0)
            valid2, voltage2, expected2 = read(2, 250)
            valid = 'Error'
            if (valid1 and valid2): valid = 'OK'
            s2 = f"{pin37A:02d}H,{pin37B:02d}H -/- {pin44:02d}H {valid} {voltage1:.1f}|{voltage2:.1f} v      ({expected1:.1f}|{expected2:.1f})v"
            fileWrite(file, s2 + "\n")
            show(s1, s2)

            chOpen(2, pin44)

            if valid1 and valid2:
                goodWires.append([pin37A, pin37B, pin44])
            else:
                badWires.append([pin37A, pin37B, pin44])
                errorBeep()

            n += 1

        fileWrite(file, "\n-----------------------------------------------------------------------------------\n")
        if len(badWires) > 0:
            show("$BHiPot. FAILED!", f"$B{len(badWires)} of {len(channelTable)} pairs are bad!")
            errorBeep()
            errorBeep()
            fileWrite(file, "\n---> Hi-Pot Test FAILED!\n\n")
            fileWrite(file, f"{len(goodWires)} of {len(channelTable)} pairs of wires passed the Hi-Pot Test\n")
            fileWrite(file, f"These pair of wires failed:\n\n")
            fileWrite(file, f"pin37A\tpin37B\t\tpin47\n")
            fileWrite(file, f"------\t------\t\t-----\n")
            for pair in badWires:
                fileWrite(file, f"CH{pair[0]}H\tCH{pair[1]}H\t\tCH{pair[2]}H\n")
        else:
            show("HiPot. PASSED!", f"{len(goodWires)} of {len(channelTable)} pairs are good")
            successBeep()
            fileWrite(file, "\n---> Hi-Pot Test PASSED!\n\n")
            fileWrite(file, f"{len(goodWires)} of {len(channelTable)} pairs of wires passed the Hi-Pot Test\n")


# Util functions

def connect(ip):
    global instr
    instr = vxi11.Instrument(ip)


def write(script):
    commands = script.split("\n")
    for command in commands:
        instr.write(command)


def readCsv(filePath):
    global rawTable, channelTable
    rawTable = []
    channelTable = []
    with open(filePath, 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for row in reader:
            if row[0] != '':
                rawTable.append(row)
                channelRow = [row[0], row[2], row[3]]
                for n, col in enumerate(channelRow):
                    channelRow[n] = int(col.replace("CH", "").replace("Ch", "").replace("H", ""))
                channelTable.append(channelRow)
        # print ((channelTable))


def read(slot, expected=None, tolerance=0.05):
    # expected = 0
    # tolerance = 1

    chClose(slot, 911)
    read = (instr.ask('print(dmm.measure())'))
    # instr.write("beeper.beep(0.1, 2400)")
    value = float(read)
    checkError()
    chOpen(slot, 911)
    valid = abs(expected - value) < tolerance
    return (valid, value, expected)
    return (valid, value, expected, value - expected)


def printClosed():
    print(instr.ask('print(channel.getclose("allslots"))'))


def checkError():
    error = float(instr.ask('print(errorqueue.count)'))
    while error > 0:
        print("\nERROR:")
        print(instr.ask('print(errorqueue.next())'))
        error = float(instr.ask('print(errorqueue.count)'))


def chClose(module, channels):
    if type(channels) is not list: channels = [channels]

    for n, ch in enumerate(channels):
        channels[n] = str(module * 1000 + ch)
    adds = ','.join(channels)
    instr.write(f'channel.close("{adds}")')


def chOpen(module, channels):
    if type(channels) is not list: channels = [channels]

    for n, ch in enumerate(channels):
        channels[n] = str(module * 1000 + ch)
    adds = ','.join(channels)

    instr.write(f'channel.open("{adds}")')


def show(string1, string2=''):
    string2 = string2.replace("Error", 'X').replace('OK', 'V')

    a = f'''display.clear()
    display.setcursor(1, 1)
    display.settext("{string1}")
    display.setcursor(2, 1)
    display.settext("{string2}")'''

    write(a)
    n1 = 20
    n2 = 32
    # print()
    # print(string1[0:n1-1])
    # if string2!='': print(string2[0:n2-1])


def fileWrite(file, string):
    file.write(string)
    print(string, end='')


def errorBeep():
    instr.write("beeper.beep(0.2, 3000)")
    instr.write("beeper.beep(0.2, 2600)")
    instr.write("beeper.beep(0.2, 2200)")


def successBeep():
    instr.write("beeper.beep(0.6, 2600)")
    instr.write("beeper.beep(0.6, 2800)")
    instr.write("beeper.beep(0.6, 3000)")


def parse_args(args):
    parser = argparse.ArgumentParser()
    parser.add_argument('-cl', dest='contLoad', help='Run Continuity and Load test', action="store_true")
    parser.add_argument('-hp', dest='hiPot', help='Run Hi-Pot test', action="store_true")
    parser.add_argument('-n', dest='name', help='Append a name to the report files')
    parser.add_argument('-ip', dest='ip', help='Keithley IP address')

    parsed_args, _unknown_args = parser.parse_known_args(args)

    return parsed_args


if __name__ == "__main__":
    args = parse_args(sys.argv)

    try:
        ip = "134.79.217.93"
        ip = "dmm-b084-test1"
        if args.ip is not None:
            ip = args.ip


        readCsv("channel_mapping.csv")
        connect(ip)
        preConfiguration()
        global name
        name = ''

        if args.name is not None:
            name = args.name

        if args.contLoad:
            continuityLoadTest()

        if args.hiPot:
            hiPotTest()

    except Exception as e:
        show("Error!", "Python script error")
        raise (e)
    finally:
        instr.close()
        print("Connection closed")
