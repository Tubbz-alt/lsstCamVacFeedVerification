import csv
import vxi11
import time


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
            if row[0]!='':
                rawTable.append(row)

                channelRow = [row[0],row[2],row[3]]

                for n,col in enumerate(channelRow):
                    channelRow[n] = int(col.replace("CH","").replace("Ch","").replace("H",""))

                channelTable.append(channelRow)

        #print ((channelTable))


def preConfiguration():
    print(instr.ask("print(os.time())"))

    # Module 1 - 37 pins module
    # Module 2 - 44 pins module

    # Reset the 3700A to factory defaults
    instr.write('reset()')
    instr.write('channel.connectrule = channel.BREAK_BEFORE_MAKE')

    # Configure module 1 as 96 channels device. Connect two halves of module 1 using backplane bank 3
    instr.write('channel.close("1913,1923")')

    # Configure module 2 as 96 channels device. Connect two halves of module 2 using backplane bank 4
    instr.write('channel.close("2913,2923")')

    printClosed()

    instr.write('dmm.connect = dmm.CONNECT_TWO_WIRE')
    instr.write('dmm.autodelay = dmm.AUTODELAY_ONCE')
    instr.write('dmm.filter.count = 5')
    instr.write('dmm.filter.type = dmm.FILTER_REPEAT_AVG')
    instr.write('dmm.filter.enable = dmm.ON')

    instr.write('errorqueue.clear()')



    #instr.write('')

    print("done")

def continuityLoadTest():
    preConfiguration()

    instr.write('dmm.func = "dcvolts"')
    instr.write('dmm.range = 7')

    # Setup common voltages
    # GND to HI on 37 pin module
    chClose(1,89)

    # GND to LO on 37 pin module
    chClose(1,93)

    # 5V to HI on 44 pin module
    chClose(2,89)

    # GND to LO on 44 pin module
    chClose(2,93)

    printClosed()

    n = 1
    for row in channelTable:
        s1 = f"Cont. Load test ({n}/{len(channelTable)})"
        pin44 = row[0]
        pin37A = row[1]
        pin37B = row[2]

        chClose(2,pin44)
        s2 = f"CH{pin44}L ->"
        show(s1,s2)
        read(1,0)
        read(2,5)

        chClose(1,pin37A)
        s2 = f"CH{pin44}L -> CH{pin37A}L "
        show(s1, s2)
        read(1,1.66)
        read(2,1.66)
        chOpen(1, pin37A)

        s2 = f"CH{pin44}L -> "
        show(s1, s2)
        read(1,0)
        read(2,5)

        chClose(1, pin37B)
        s2 = f"CH{pin44}L -> CH{pin37B}L"
        show(s1, s2)
        read(1,1.66)
        read(2,1.66)
        chOpen(1, pin37B)

        chOpen(2,pin44)

        n+=1





def hiPotTest():



    if True:

        #preConfiguration()

        #instr.write('dmm.func = "dcvolts"')
        #instr.write('dmm.range = 260')

        # Setup common voltages
        # GND to HI on 37 pin module
        chClose(1, 90)
        # GND to LO on 37 pin module
        chClose(1,93)
        # 5V to HI on 44 pin module
        chClose(2,2091)
        # GND to LO on 44 pin module
        chClose(2,93)


    error = int(instr.ask('print(errorqueue.count)')[0]) #getting -350 que overflow error
    print(error)
    if error>0:
        print(instr.ask('print(errorqueue.next())'))  # getting -350 que overflow error


    print("---------------------")


    n = 1
    for row in channelTable:
        s1 = f"HiPot test ({n}/{len(channelTable)})"
        pin44 = row[0]
        pin37A = row[1]
        pin37B = row[2]

        chClose(2,pin44)

        s2 = f"CH{pin44}L -> "
        show(s1, s2)
        read(2,250)
        read(1,0)

        closeArray = []
        for row2 in channelTable:
            pin37A2 = row2[1]
            pin37B2 = row2[2]

            if row2!=row:
                closeArray.append(pin37A2)
                closeArray.append(pin37B2)

       #     if len(closeArray)>=1:
       #         chClose(1, closeArray)
       #         closeArray = []

        #if len(closeArray)>0:
        chClose(1, closeArray)


        s2 = f"CH{pin44}L -> CH{pin37A}L, CH{pin37B}L"
        show(s1, s2)
        read(1,0)
        read(2,250)

        openArray=[]
        for row2 in channelTable:
            pin37A2 = row2[1]
            pin37B2 = row2[2]

            openArray.append(pin37A2)
            openArray.append(pin37B2)

         #   if len(openArray) >= 1:
         #       chOpen(1, openArray)
         #       openArray = []

        #if len(openArray) > 0:
        chOpen(1, openArray)


        chOpen(2,pin44)

        n+=1





def read(slot,expected=None,tolerance=0.05):

#    dmm.measurecount = 10
#    ReadingBufferTwo = dmm.makebuffer(1000)
#    dmm.measure(ReadingBufferTwo)


    chClose(slot, 911)
    #print(f"Read slot {slot} ({expected} v) : ")
    #printClosed()


    print(instr.ask('print(dmm.measure())')) #getting -350 que overflow error
    error = int(instr.ask('print(errorqueue.count)')[0]) #getting -350 que overflow error
    print(error)
    if error>0:
        print(instr.ask('print(errorqueue.next())'))  # getting -350 que overflow error

#    time.sleep(0.2)

    chOpen(slot, 911)



    #instr.write("beeper.beep(0.1, 2400)")


def printClosed():
    print(instr.ask('print(channel.getclose("allslots"))'))



def chClose(module,channels):

    if type(channels) is not list: channels = [channels]

    for n,ch in enumerate(channels):
        channels[n] = str(module*1000+ch)
    adds = ','.join(channels)
    instr.write(f'channel.close("{adds}")')

def chOpen(module, channels):

    if type(channels) is not list: channels = [channels]

    for n, ch in enumerate(channels):
        channels[n] = str(module * 1000 + ch)
    adds = ','.join(channels)

    instr.write(f'channel.open("{adds}")')

def show(string1,string2=''):

    n1 = 20
    n2 = 32


    a = f'''display.clear()
    display.setcursor(1, 1)
    display.settext("{string1}")
    display.setcursor(2, 1)
    display.settext("{string2}")'''

    write(a)

    print()
    print(string1)
    if string2!='': print(string2)




def beep():
    n=0

    while True:
        connect("134.79.217.93")
        print(n)

        instr.write("beeper.beep(0.1, 2400)")
        print(instr.ask("print(os.time())"))
        print(instr.ask("print(localnode.description)"))

        a = f'''display.clear()
        display.setcursor(1, 4)
        display.settext("Hello Hoang")
        display.setcursor(2, 14)
        display.settext("{n}")'''

        write(a)



        n+=1
        instr.close()
        time.sleep(.5)


def main():


    readCsv("channel_mapping.csv")


    #beep()

    connect("134.79.217.93")
    preConfiguration()

    #continuityLoadTest()
    hiPotTest()

    show("Success!","Tests Finished!")




try:
    main()
finally:
    instr.close()
    print("closed")



