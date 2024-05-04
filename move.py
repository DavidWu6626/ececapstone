import serial
from serial import Serial
import json
import threading
from time import sleep

# msg = {"T":3,"lineNum":0,"Text":"pleaseworkrover"}
# {"T":143,"cmd":1}


def read_serial(ser):
    print('Testing read_serial')
    while True:
        print("sutck")
        data = ser.readline().decode('utf-8')
        if data:
            print(f"Received: {data}", end='')
            
# 172.26.171.155
def testMove():
    sendRoverMove({"T":71})
    data = ser.readline().decode()
    while(not data):
        if data:
            print(f"Received: {data}", end='')
            break
    dir = 'L'
    sendRoverMove(getJSONcmd(dir))
    sendRoverMove({"T":71})
    data = ser.readline().decode()
    while(not data):
        if data:
            print(f"Received: {data}", end='')
            break
        


def doBinary():
    while(True):
        print("Doing this Binary")
        ser.write(b'\xF0')
        ser.flush()
        sleep(0.5)

def fakeCamStream():
    while(True):
        print("doing camera streaming")
        sleep(2)

# Input: Movement ('L','R','F','B','N') (N for nothing)
# Output: JSON contents
def getJSONcmd(dir):
    if dir == 'L':
        msg = {"T":1,"L":-132,"R":135} #TODO JSON COMMANDS ARE RIGHT???
    elif dir == 'R':
        msg = {"T":1,"L":135,"R":-132}
    elif dir == 'F':
        msg = {"T":1,"L":132,"R":132}
    elif dir == 'B':
        msg = {"T":1,"L":-132,"R":-132}
    elif dir == 'N':   
        msg = {"T":1,"L":0,"R":0}
    return msg

personDetected = False
degreeOffset = 0
def doCreepingLine():
    num_creeps = 1 # CHANGE THIS
    movementPath = ['F','F','L','F','L','F','F','R','F','R']
    for _ in range(num_creeps): 
        for dir in movementPath:
            sendRoverMove(getJSONcmd(dir))
            if personDetected: # person found!
                break
        if personDetected: # person found!
            break 
    doTargetMove(degreeOffset) # degreeOffset should be set by here

# def doRandSearch():


def doTargetMove(degree):
    degRange = 45
    motorRange = 132
    while(personDetected):
        # degree comes in the range -45 to 45, change this if needed
        degree += range
        proportion = degree / (degRange*2)
        motor = round(proportion * (motorRange*2))
        msg = {"T":1,"L":-motor,"R":motor}
        sendRoverMove(msg)
        msg = {"T":1,"L":50,"R":50}
        sendRoverMove(msg)
    # doRandSearch()



def sendRoverMove(msg):
    data = json.dumps(msg).encode() + b'\n'
    print(data)

    ser.write(bytearray(data))
    ser.flush()
    try:
        data = ser.readline().decode()
        print("cow")
        if data:
            print(f"Received: {data}", end='')
    except Exception as e:
        print (e)
        pass
    sleep(1)

def main():
    global ser
    ser = Serial('/dev/serial0', baudrate=1000000, write_timeout=5, timeout=0) # should/can use /dev/ttyS0
    print(ser)
    ser.rts = False
    ser.dtr = False
    move_thread = threading.Thread(target=doCreepingLine)
    move_thread.daemon = True
    move_thread.start()
    while(True):
        print("doing camera streaming")
        sleep(2)
    # testMove()

    # doBinary()
    ser.close()


if __name__ == "__main__":
    main()

