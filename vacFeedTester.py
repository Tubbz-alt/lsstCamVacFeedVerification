#!/usr/bin/env python
import csv
import vxi11
from datetime import datetime
import argparse
import sys
import os
import time
from engineering_notation import EngNumber


maxWireR = 2 # Continuity test max acceptable wire impedance in ohms
minIsolationR = 1e6 # Hi-Pot Test min acceptable isolation impedance in ohms


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
    instr.write('dmm.filter.count = 3')
    instr.write('dmm.filter.type = dmm.FILTER_REPEAT_AVG')
    instr.write('dmm.filter.enable = dmm.ON')

    instr.write('errorqueue.clear()')

    if not os.path.exists('reports'):
        os.makedirs('reports')

    instr.write('beeper.enable = 1')


def continuityLoadTest():
    

    v0 = 0
    vHalf = 1.66

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
        # 5V to HI on 44 pin module
        chClose(2, 89)
        # GND to LO on 44 pin module
        chClose(2, 93)
        v5 = read(2)


        if v5<4.5:
            show("Cont. Load. FAILED!", f"$BPower supply not powered on (<4.5v)")
            errorBeep()
            errorBeep()
            errorBeep()
            errorBeep()
            fileWrite(file, "\n---> Cont. Load Test FAILED!\n\n")
            fileWrite(file, f"Power supply not powered on (<4.5v)\n")

            fileWrite(file, "\n\n")
            return False

        # GND to HI on 37 pin module
        chClose(1, 89)
        # GND to LO on 37 pin module
        chClose(1, 93)

        goodWires = []
        badWires = []

        R37 = 5.3
        R44 = 10.3


        s1 = f"Cont. Load Test (0/{2*len(channelTable)})"
        s2 = f"R37: {EngNumber(R37)}ohm"
        fileWrite(file, s2 + "\n")
        show(s1, s2)

        s2 = f"R44: {EngNumber(R37)}ohm"
        fileWrite(file, s2 + "\n")
        show(s1, s2)

        s2 = f"R cable threshold: {EngNumber(maxWireR)}ohm"
        fileWrite(file, s2 + "\n")
        show(s1, s2)


        s2 = f"Power Supply Voltage: {EngNumber(v5)}v"
        fileWrite(file, s2 + "\n")
        show(s1, s2)

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
            valid1, voltage1, expected1 = read(1, v0)
            valid2, voltage2, expected2 = read(2, v5)
            c1 = (voltage1) / R37
            c2 = (v5 - voltage2) / R44
            c = (c1 + c2) / 2.0
            r = abs(voltage2 - voltage1) / c

            valid = 'Error'
            if (valid1 and valid2): valid = 'OK'
            s2 = f"    -- {pin44:02d}H {valid}            {voltage1:.2f}|{voltage2:.2f} v  ({expected1:.2f}|{expected2:.2f})v"
            show(s1, s2)
            fileWrite(file, s2 + "\n")
            wireValid &= valid1 and valid2

            chClose(1, pin37A)
            valid1, voltage1, expected1 = read(1, vHalf,0.40)
            valid2, voltage2, expected2 = read(2, vHalf,0.40)

            c = (v5-voltage2)/R44
            r = abs(voltage2-voltage1)/c

            valid = 'Error'
            if (r<maxWireR and r>0): valid = 'OK'
            s2 = f"{pin37A:02d}H -- {pin44:02d}H {valid}  {EngNumber(r)}ohm   {voltage1:.2f}|{voltage2:.2f} v  ({expected1:.2f}|{expected2:.2f})v"
            show(s1, s2)
            fileWrite(file, s2 + "\n")
            chOpen(1, pin37A)

            wireValid &= r<maxWireR
            if wireValid:
                goodWires.append([pin37A, pin44,r])
            else:
                badWires.append([pin37A, pin44,r])
                errorBeep()

            # Test wire B
            wireValid = True
            valid1, voltage1, expected1 = read(1, v0)
            valid2, voltage2, expected2 = read(2, v5)
            c1 = (voltage1) / R37
            c2 = (v5 - voltage2) / R44
            c = (c1 + c2) / 2.0
            r = abs(voltage2 - voltage1) / c

            valid = 'Error'
            if (valid1 and valid2): valid = 'OK'
            s2 = f"    -- {pin44:02d}H {valid}            {voltage1:.2f}|{voltage2:.2f} v  ({expected1:.2f}|{expected2:.2f})v"
            show(s1, s2)
            fileWrite(file, s2 + "\n")
            wireValid &= valid1 and valid2

            chClose(1, pin37B)
            valid1, voltage1, expected1 = read(1, vHalf,0.4)
            valid2, voltage2, expected2 = read(2, vHalf,0.4)

            c1 = (voltage1) / R37
            c2 = (v5 - voltage2) / R44
            c = (c1 + c2) / 2.0
            r = abs(voltage2 - voltage1) / c

            valid = 'Error'
            if (r < maxWireR and r>0): valid = 'OK'
            s2 = f"{pin37B:02d}H -- {pin44:02d}H {valid}  {EngNumber(r)}ohm   {voltage1:.2f}|{voltage2:.2f} v  ({expected1:.2f}|{expected2:.2f})v"
            show(s1, s2)
            fileWrite(file, s2 + "\n")
            chOpen(1, pin37B)

            wireValid &= r<maxWireR
            if wireValid:
                goodWires.append([pin37B, pin44,r])
            else:
                badWires.append([pin37B, pin44,r])
                errorBeep()

            chOpen(2, pin44)
            n += 1

        fileWrite(file, "\n-----------------------------------------------------------------------------------\n")
        if len(badWires) > 0:
            show("$BCont. Load FAILED!", f"$B{len(badWires)} of {len(channelTable)*2} wires are bad")
            errorBeep()
            errorBeep()
            fileWrite(file, "\n---> Continuity and Load Test FAILED!\n\n")
            fileWrite(file, f"{len(goodWires)} of {len(channelTable)*2} wires passed the Continuity and Load Test\n\n")

            fileWrite(file, f"These wires passed:\n\n")
            fileWrite(file, f"pin37\t\tpin47\t\t\n")
            fileWrite(file, f"-----\t\t-----\t\t-----\n")
            for pair in goodWires:
                fileWrite(file, f"CH{pair[0]}H\t\tCH{pair[1]}H\t\t{EngNumber(pair[2])}ohm\n")

            fileWrite(file, f"\nThese wires failed:\n\n")
            fileWrite(file, f"pin37\t\tpin47\t\t\n")
            fileWrite(file, f"-----\t\t-----\t\t-----\n")
            for pair in badWires:
                fileWrite(file, f"CH{pair[0]}H\t\tCH{pair[1]}H\t\t{EngNumber(pair[2])}ohm\n")
            result = False
        else:
            show("Cont. Load PASSED!", f"{len(goodWires)} of {len(channelTable)*2} wires are good")
            successBeep()
            fileWrite(file, "\n---> Continuity and Load Test PASSED!\n\n")
            fileWrite(file, f"{len(goodWires)} of {len(channelTable)*2} wires passed the Continuity and Load Test\n\n")
            fileWrite(file, f"pin37\t\tpin47\t\t\n")
            fileWrite(file, f"-----\t\t-----\t\t-----\n")
            for pair in goodWires:
                fileWrite(file, f"CH{pair[0]}H\t\tCH{pair[1]}H\t\t{EngNumber(pair[2])}ohm\n")
            result = True

        fileWrite(file, "\n\n")
        return result


def hiPotTest():
  
    v0=0

    i = datetime.now()
    with open("reports/hi_pot_" + i.strftime('%Y_%m_%d_%Hh%Mm%Ss') + f"_{name}.txt", 'w') as file:
        fileWrite(file, "LSST Camera Vacuum feedthrough Hi-Pot Test\n")
        fileWrite(file, name + "\n")
        fileWrite(file, i.strftime('%Y/%m/%d %H:%M:%S\n\n'))

        show("HiPot. Test", "Preparing for test")
        preConfiguration()

        instr.write('dmm.func = "dcvolts"')
        instr.write('dmm.range = 260')

        Rtest = 100000



        s1 = f"HiPot (0/{len(channelTable)})"
        s2 = f"Rtest: {EngNumber(Rtest)}ohm"
        fileWrite(file, s2 + "\n")
        show(s1, s2)

        s2 = f"R Threshold : {EngNumber(minIsolationR)}ohm"
        fileWrite(file, s2 + "\n")
        show(s1, s2)



        # 250V to HI on 44 pin module
        chClose(2, 90)
        # GND to LO on 44 pin module
        chClose(2, 93)
        import time
        time.sleep(1)
        v250 = read(2)
        # 250V to HI on 44 pin module
        chOpen(2, 90)

        if v250<220:
            show("$BHiPot. FAILED!", f"$BPower supply not powered on (<220v)")
            errorBeep()
            errorBeep()
            errorBeep()
            errorBeep()
            fileWrite(file, "\n---> Hi-Pot Test FAILED!\n\n")
            fileWrite(file, f"Power supply not powered on (<220v)\n")

            fileWrite(file, "\n\n")
            return False


        s2 =  f"Power supply voltage: {v250:.3f} v"
        fileWrite(file, s2 + "\n")
        show(s1, s2)

        # Setup common voltages
        chClose(2, 91)
        # GND to LO on 44 pin module
        chClose(2, 93)
        Vdmm = read(2)
        Rdmm = -(Rtest * Vdmm) / ( Vdmm - v250)

        s2 = f"Rtest: {EngNumber(Rtest)}ohm"
        fileWrite(file, s2 + "\n")
        show(s1, s2)


        s2 =  f"Voltage after Rtest: {EngNumber(Vdmm)}v"
        fileWrite(file, s2 + "\n")
        show(s1, s2)


        s2 =  f"DMM input impedance: {EngNumber(Rdmm)}ohm"
        fileWrite(file, s2 + "\n")
        show(s1, s2)


        # GND to HI on 37 pin module
        chClose(1, 90)
        # GND to LO on 37 pin module
        chClose(1, 93)
        # 250V to HI on 44 pin module


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

            valid1, voltage1, expected1 = read(1, v0)
            valid2, voltage2, expected2 = read(2, v250)

            #input("Press Enter to continue...")

            R = -(Rtest * voltage2) / (voltage2 - v250)
            r = - (R * Rdmm) / ( R - Rdmm  )


            #print(v250,Vdmm,voltage2)
            #print(Rdmm,R,r)
            #print(voltage2/Rdmm*1000,voltage2/r*1000,voltage2/Rdmm*1000+voltage2/r*1000, (v250-voltage2)/Rtest*1000)


            valid = 'Error'
            if (valid1 and r>=minIsolationR): valid = 'OK'
            s2 = f"{pin37A:02d}H,{pin37B:02d}H -/- {pin44:02d}H {valid}   {EngNumber(r)}ohm   {EngNumber(voltage2/r)}A leakage  {voltage1:.2f}|{voltage2:.2f} v   ({expected1:.2f}|{expected2:.2f})v "
            fileWrite(file, s2 + "\n")
            show(s1, s2)

            chOpen(2, pin44)

            if valid1 and r>=minIsolationR:
                goodWires.append([pin37A, pin37B, pin44,r])
            else:
                badWires.append([pin37A, pin37B, pin44,r])
                errorBeep()

            n += 1

        fileWrite(file, "\n-----------------------------------------------------------------------------------\n")
        if len(badWires) > 0:
            show("$BHiPot. FAILED!", f"$B{len(badWires)} of {len(channelTable)} pairs are bad!")
            errorBeep()
            errorBeep()
            fileWrite(file, "\n---> Hi-Pot Test FAILED!\n\n")
            fileWrite(file, f"{len(goodWires)} of {len(channelTable)} pairs of wires passed the Hi-Pot Test\n")

            fileWrite(file, f"These pair of wires passed:\n\n")
            fileWrite(file, f"pin37A\tpin37B\t\tpin47\t\t \n")
            fileWrite(file, f"------\t------\t\t-----\t\t---------\n")
            for pair in goodWires:
                fileWrite(file, f"CH{pair[0]}H\tCH{pair[1]}H\t\tCH{pair[2]}H\t\t{EngNumber(pair[3])}ohm\n")

            fileWrite(file, f"\nThese pair of wires failed:\n\n")
            fileWrite(file, f"pin37A\tpin37B\t\tpin47\t\t \n")
            fileWrite(file, f"------\t------\t\t-----\t\t---------\n")
            for pair in badWires:
                fileWrite(file, f"CH{pair[0]}H\tCH{pair[1]}H\t\tCH{pair[2]}H\t\t{EngNumber(pair[3])}ohm\n")
            result = False
        else:
            show("HiPot. PASSED!", f"{len(goodWires)} of {len(channelTable)} pairs are good")
            successBeep()
            fileWrite(file, "\n---> Hi-Pot Test PASSED!\n\n")
            fileWrite(file, f"{len(goodWires)} of {len(channelTable)} pairs of wires passed the Hi-Pot Test\n\n")

            fileWrite(file, f"pin37A\tpin37B\t\tpin47\t\t \n")
            fileWrite(file, f"------\t------\t\t-----\t\t---------\n")
            for pair in goodWires:
                fileWrite(file, f"CH{pair[0]}H\tCH{pair[1]}H\t\tCH{pair[2]}H\t\t{EngNumber(pair[3])}ohm\n")

            result = True

        fileWrite(file, "\n\n")
        return result

def pinoutTest():
    i = datetime.now()
    with open("reports/pinout_" + i.strftime('%Y_%m_%d_%Hh%Mm%Ss') + f"_{name}.txt", 'w') as file:
        fileWrite(file, "LSST Camera Vacuum feedthrough Pinout Test\n")
        fileWrite(file, name + "\n")
        fileWrite(file, i.strftime('%Y/%m/%d %H:%M:%S\n\n'))

        show("Pinout Test", "Preparing for test")

        preConfiguration()

        instr.write('dmm.func = "dcvolts"')

        # Setup common voltages

        # GND to LO on 37 pin module
        chClose(1, 93) #TODO where is the ground?

        goodWires = []
        badWires = []

        tolerance=0.1 #v

        n = 1
        for row in channelTable:
            s1 = f"Pinout Test ({n}/{len(channelTable)})"
            fileWrite(file, "\n" + s1 + "\n")
            pin44 = row[0]
            pin37A = row[1]
            pin37B = row[2]
            expected = row[3]

            # Test wire A
            chClose(1, pin37A)
            validA, voltageA, expectedA = read(1, expected,tolerance)
            chOpen(1,pin37A)

            valid = 'Error'
            if (validA):
                valid = 'OK'
                goodWires.append([pin37B,expected,voltageA])
            else:
                badWires.append([pin37B,expected,voltageA])
            s2 = f"{pin37A:02d}H {valid}  {voltageA:.2f} v  ({expectedA:.2f}) v"
            show(s1, s2)
            fileWrite(file, s2 + "\n")

            # Test wire B
            chClose(1, pin37B)
            validB, voltageB, expectedB = read(1, expected,tolerance)
            chOpen(1,pin37B)
            valid = 'Error'
            if (validB):
                valid = 'OK'
                goodWires.append([pin37B,expected,voltageB])
            else:
                badWires.append([pin37B,expected,voltageB])
            s2 = f"{pin37B:02d}H {valid}  {voltageB:.2f} v  ({expectedB:.2f}) v"
            show(s1, s2)
            fileWrite(file, s2 + "\n")

            n+=1

        fileWrite(file, "\n-----------------------------------------------------------------------------------\n")
        if len(badWires) > 0:
            show("$BPinout FAILED!", f"$B{len(badWires)} of {len(channelTable)*2} wires are bad")
            errorBeep()
            errorBeep()
            fileWrite(file, "\n---> Pinout test FAILED!\n\n")
            fileWrite(file,
                      f"{len(goodWires)} of {len(channelTable)*2} wires passed the Pinout Test\n\n")

            fileWrite(file, f"These wires passed:\n\n")
            fileWrite(file, f"pin37\t\texpected\t\tread\n")
            fileWrite(file, f"-----\t\t--------\t\t----\n")
            for pair in goodWires:
                fileWrite(file, f"CH{pair[0]}H\t\t{EngNumber(pair[1])}v\t\t\t{EngNumber(pair[2])}v\n")

            fileWrite(file, f"\nThese wires failed:\n\n")
            fileWrite(file, f"pin37\t\texpected\t\tread\n")
            fileWrite(file, f"-----\t\t--------\t\t----\n")
            for pair in badWires:
                fileWrite(file, f"CH{pair[0]}H\t\t{EngNumber(pair[1])}v\t\t\t{EngNumber(pair[2])}v\n")
            result = False
        else:
            show("Pinout PASSED!", f"{len(goodWires)} of {len(channelTable)*2} wires are good")
            successBeep()
            fileWrite(file, "\n---> Pinout Test PASSED!\n\n")
            fileWrite(file,
                      f"{len(goodWires)} of {len(channelTable)*2} wires passed the Pinout  Test\n\n")
            fileWrite(file, f"pin37\t\texpected\t\tread\n")
            fileWrite(file, f"-----\t\t--------\t\t----\n")
            for pair in goodWires:
                fileWrite(file, f"CH{pair[0]}H\t\t{EngNumber(pair[1])}v\t\t{EngNumber(pair[2])}v\n")
            result = True

        fileWrite(file, "\n\n")
        return result

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
                channelRow = [row[0], row[2], row[3],row[5]]
                for n, col in enumerate(channelRow):
                    channelRow[n] = int(col.replace("CH", "").replace("Ch", "").replace("H", ""))
                channelTable.append(channelRow)
        # print ((channelTable))


def read(slot, expected=None, tolerance=0.05):
    # expected = 0
    # tolerance = 1


    chClose(slot, 911)


    #time.sleep(0.5)

    read = (instr.ask('print(dmm.measure())'))
    # instr.write("beeper.beep(0.1, 2400)")
    value = float(read)
    checkError()
    chOpen(slot, 911)

    if expected is not None:
        valid = abs(expected - value) < tolerance
        return (valid, value, expected)

    return value


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


def show(string1, string2='',c_print=False):
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

    if c_print:
        print(string1.replace("$B",""))
        print(string2.replace("$B",""))


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
    parser.add_argument('-t', dest='tests', help='Run Continuity and Load and Hi-Pot test', action="store_true")
    parser.add_argument('-p', dest='pinout', help='Run Pinout test', action="store_true")
    parser.add_argument('-n', dest='name', help='Append a name to the report files')
    parser.add_argument('-ip', dest='ip', help='Keithley IP address (DEFAULT: "134.79.217.93")')
    parser.add_argument('-m', dest='mapping', help='Channels mapping csv file (Overides --corner_raft and --science_raft)')
    parser.add_argument('--corner_raft', dest='corner', help='Use corner_raft_channel_mapping.csv mapping file')
    parser.add_argument('--science_raft', dest='science', help='Use science_raft_channel_mapping.csv mapping file (DEFAULT')


    parsed_args, _unknown_args = parser.parse_known_args(args)

    return parsed_args


if __name__ == "__main__":
    args = parse_args(sys.argv)

    try:
        ip = "134.79.217.93"
        #ip = "dmm-b084-test1"
        if args.ip is not None:
            ip = args.ip

        mapping = "science_raft_channel_mapping.csv"
        if args.corner:
            mapping = "corner_raft_channel_mapping.csv"
        if args.mapping is not None:
            mapping = args.mapping

        readCsv(mapping)
        print("Connecting to Keithley Tester...")
        connect(ip)
        preConfiguration()
        global name
        name = ''

        if args.name is not None:
            name = args.name
        else:
            name = input("\nName of the cable being tested:")

        if args.hiPot:
            hiPotTest()

        if args.contLoad:
            continuityLoadTest()

        if args.tests:
            hiPot = hiPotTest()
            contLoad = continuityLoadTest()

            if hiPot and contLoad:
                print("\n\n---------------------------------------------------------------------------------------------------\n")
                show("Both Tests PASSED!", "",True)
                successBeep()
                successBeep()
                successBeep()
            else:
                s = "Hi-Pot "
                if hiPot:
                    s+="PASSED"
                else:
                    s+= "$BFAILED"
                s+="    ContLoad "
                if contLoad:
                    s+="PASSED"
                else:
                    s+= "$BFAILED"
                show("$BTests FAILED!", s,True)
                errorBeep()
                errorBeep()
                errorBeep()
            print("---------------------------------------------------------------------------------------------------\n")



        if args.pinout:
            pinout = pinoutTest()

            print("\n\n---------------------------------------------------------------------------------------------------\n")
            if pinout:
                show("Pinout PASSED!","",True)
                successBeep()
                successBeep()
                successBeep()
            else:
                show("$BPinout FAILED!","",True)
                errorBeep()
                errorBeep()
                errorBeep()
            print("\n---------------------------------------------------------------------------------------------------\n")


    except Exception as e:
        show("Error!", "Python script error")
        raise (e)
    finally:
        instr.close()
        print("Connection closed")
