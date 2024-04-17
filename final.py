# for streaming
#!/usr/bin/python3

# Mostly copied from https://picamera.readthedocs.io/en/release-1.13/recipes2.html
# Run this script, then point a web browser at http:<this-ip-address>:8000
# Note: needs simplejpeg to be installed (pip3 install simplejpeg).

import io
import logging
import socketserver
from http import server
from threading import Condition

from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput

# for moving
from serial import Serial
import json

# for laser
import RPi.GPIO as gpio

# general libraries
from time import sleep
import threading

PAGE = """\
<html>
<head>
<title>picamera2 MJPEG streaming demo</title>
</head>
<body>
<h1>Picamera2 MJPEG Streaming Demo</h1>
<img src="stream.mjpg" width="640" height="480" />
</body>
</html>
"""

class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()


class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        else:
            self.send_error(404)
            self.end_headers()

class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

def doStreaming():
    picam2.start_recording(JpegEncoder(), FileOutput(output))
    address = ('', 8000)
    server = StreamingServer(address, StreamingHandler)
    server.serve_forever()        


# Output: True if person is found
# Sets personDetected var to True if person is found
def checkForPerson():
    personDetected = False
    # check if person is found using first line of info.txt
    status = infofile.readline().rstrip('\n')
    print(status)
    if status == 'Person Not Found':
        personDetected = False
    elif status == 'Person Found':
        personDetected = True
    else:
        print("Error: Invalid first line in info.txt")
    return personDetected

# Input: Movement ('L','R','F','B','N') (N for nothing)
# Output: JSON contents
# Translates direction to JSON cmd
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
        msg = {"T":0}
    return msg

# Input: JSON contents
# Output: None
# Sends the rover JSON cmd for movement through UART
def sendRoverMove(msg):
    data = json.dumps(msg).encode() + b'\n'
    ser.write(bytearray(data))
    ser.flush()
    try:
        data = ser.readline().decode()
        if data:
            print(f"Received: {data}", end='')
    except Exception as e:
        print (e)
        pass

# Performs targeted movement based off of txt file from CV
def doTargetMove():
    print("Found Target!")
    degRange = 45 # change these if needed
    motorRange = 132
    personDetected = True
    while(personDetected):
        # get the degree offset of the person using second line of info.txt
        degree = float(infofile.readline().rstrip('\n'))
        infofile.seek(0)
        if (abs(degree) < 2): # person is in the center! FIREEEE!
            gpio.output(17, gpio.HIGH)
        else:
            gpio.output(17, gpio.LOW)
        proportion = degree / degRange # scale motor movement proportionally to degree
        motor = round(proportion * motorRange)
        msg = {"T":1,"L":motor,"R":-motor}
        sendRoverMove(msg)
        sleep(0.5)
        personDetected = checkForPerson()
    # what to do if person not found anymore??????
    sendRoverMove(getJSONcmd('N'))
    infofile.seek(0)

def doMove():
    personDetected = False
    num_creeps = 1_000_000 # CHANGE THIS
    movementPath = ['F','F','F','F','F']
    for _ in range(num_creeps): 
        for dir in movementPath:
            personDetected = checkForPerson()
            if personDetected: # person found!
                break
            infofile.seek(0)
            sendRoverMove(getJSONcmd(dir))
            sleep(0.5)
        if personDetected: # person found!
            sendRoverMove(getJSONcmd('N'))
            doTargetMove()
            break 

# main function
def main():
    # moving
    global ser
    ser = Serial('/dev/serial0', baudrate=1000000, write_timeout=5, timeout=0) # should/can use /dev/ttyS0
    print(ser)
    ser.rts = False
    ser.dtr = False
    global infofile
    infofile = open("info.txt", "r")
    gpio.setmode(gpio.BCM)
    gpio.setup(17, gpio.OUT)

    # streaming
    global picam2
    picam2 = Picamera2()
    picam2.configure(picam2.create_video_configuration(main={"size": (640, 480)}))
    global output
    output = StreamingOutput()

    try:
        move_thread = threading.Thread(target=doMove)
        move_thread.daemon = True
        move_thread.start()
        doStreaming()
    finally:
        ser.close()
        infofile.close()
        gpio.cleanup()
        picam2.stop_recording()

if __name__ == "__main__":
    main()