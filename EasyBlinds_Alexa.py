#EASY-BLINDS CODE

#IMPORTS
import RPi.GPIO as GPIO
from time import sleep
import time
import lirc
from multiprocessing import Process, Value
import fauxmo
import logging
from debounce_handler import debounce_handler

logging.basicConfig(level=logging.DEBUG)

#SET GPIO mode to BOARD
GPIO.setmode(GPIO.BOARD)

#Setup GPIO's for sensors
tempGPIO = 7
lightGPIO = 11
motorGPIO = 13
motionGPIO = 15
GPIO.setup(motionGPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)

#Setup GPIO's for LEDS
#green -> Auto State
#red -> Manual State
#blue -> Temp State
redLED = 40
greenLED = 38
blueLED = 36

GPIO.setup(redLED, GPIO.OUT)
GPIO.output(redLED, 0)
GPIO.setup(greenLED, GPIO.OUT)
GPIO.output(greenLED, 1)
GPIO.setup(blueLED, GPIO.OUT)
GPIO.output(blueLED, 0)

#This function get the current temperature
#value and returns it
def GET_TEMP(tempGPIO): 
    count = 0

    GPIO.setup(tempGPIO, GPIO.OUT)
    GPIO.output(tempGPIO, GPIO.LOW)
    sleep(0.1)

    #change GPIO back to input
    GPIO.setup(tempGPIO, GPIO.IN)

    #count until capacitor is 3/4 full
    while(GPIO.input(tempGPIO) == GPIO.LOW):
	count += 1

    return count

#This function gets the current light intensity
#value and returns it
def GET_LIGHT(lightGPIO):
    count = 0
	
    GPIO.setup(lightGPIO, GPIO.OUT)
    GPIO.output(lightGPIO, GPIO.LOW)
    sleep(0.1)

    #change GPIO back to input
    GPIO.setup(lightGPIO, GPIO.IN)

    #count until capacitor is 3/4 full
    while(GPIO.input(lightGPIO) == GPIO.LOW):
	count += 1

    return count

#This function takes in a direction (open or close)
#and opens or closes the blinds by moving the servo motor
def MOTOR(motorGPIO, direction):
    GPIO.setup(motorGPIO, GPIO.OUT)
    pwm=GPIO.PWM(motorGPIO, 50)
    pwm.start(5)
    if direction == "open":
	pwm.ChangeDutyCycle(1.5)
        sleep(.6)
    if direction == "close":
        pwm.ChangeDutyCycle(14.5)
        sleep(.75)

#This function takes in the current temperature and
#if the system is in the auto state it closes the blinds
#if the temperature is too high
def TEMP(tempGPIO):

    global current_state
    global blind_state
    global current_temp

    temp = GET_TEMP(tempGPIO)
    x = temp - 1800
    shift = x/41
    finalT = 60 - shift
    print("TEMP: ", finalT, " F")
    #If finalT gets above 90 close blinds
    if(time.time() > 3.5):
        if(finalT > 80 and blind_state == "open" and abs(finalT - current_temp) > 3 and current_state == "auto"): 
	    MOTOR(motorGPIO, "close")
	    print("tp close")
	    print(finalT)
	    blind_state = "closed"
            current_state = "temp"
            GPIO.output(redLED, 0)
	    current_temp = finalT
            GPIO.output(greenLED, 0)
            GPIO.output(blueLED, 1)
        if(finalT < 80 and blind_state == "closed" and abs(finalT - current_temp) > 3 and current_state == "temp"):
	    MOTOR(motorGPIO, "open")
	    print("tp open")
            blind_state = "open"
	    current_state = "auto"
	    current_temp = finalT
	    GPIO.output(redLED, 0)
            GPIO.output(greenLED, 1)
            GPIO.output(blueLED, 0)
    
#This function takes in the current light intensity and
#closes the blinds if it is dark outside and opens the
#blinds if it is light outside
def LIGHT(lightGPIO):

    global current_state
    global blind_state
    global current_light   

    light = GET_LIGHT(lightGPIO)
    #print(light)
    #if below 140 open blinds
    if(time.time() - time1 > 3.5):
    	if (light < 140 and blind_state == "closed" and abs(light-current_light) > 20 and current_state == "auto"):
            MOTOR(motorGPIO, "open")
	    print("lt open")
            blind_state = "open"
            current_light = light
    	if (light > 140 and blind_state == "open" and abs(light-current_light) > 20 and current_state == "auto"):
            MOTOR(motorGPIO, "close")
	    print("lt close")
            blind_state = "closed"
            current_light = light

def MOTION(motionGPIO):

    global current_state
    global blind_state

    if(0 == GPIO.input(motionGPIO) and blind_state == "closed"):
	MOTOR(motorGPIO, "open")
	print("mo open")
	blind_state = "open"
	current_state = "manual"
    	GPIO.output(redLED, 1)
        GPIO.output(greenLED, 0)
        GPIO.output(blueLED, 0)
    if(0 == GPIO.input(motionGPIO) and blind_state == "open"):
	MOTOR(motorGPIO, "close")
	print("mo close")
	blind_state = "closed"
	current_state = "manual"
	GPIO.output(redLED, 1)
        GPIO.output(greenLED, 0)
        GPIO.output(blueLED, 0)

#def GET_REMOTE(key):
#
#    while True:
#	sockid = lirc.init("myprogram")
#        try:
#	    code = lirc.nextcode()
#	    c = code[0]
#	    if c == 'up':
#		key.value = 1
#	    if c == 'down':
#		key.value = 2
#	    if c == 'reset':
#		key.value = 3
#	    if c == 'manual':
#		key.value = 4
#	    if c == 'auto':
#		key.value = 5
#
#	    lirc.deinit()
#        except IndexError:
# 	    key.value = 0
#	if(key.value == 3):
#	    break

#def REMOTE(button):
#    global current_state
#    global blind_state
#
#    if(current_state == 'auto' or current_state == 'temp'):
# 	if(button == 4):
#	    #send into manual mode
#	    print('MANUAL')
#	    current_state = 'manual'
#	    GPIO.output(redLED, 1)
#            GPIO.output(greenLED, 0)
#            GPIO.output(blueLED, 0)
#    if(current_state == 'manual'):
#	if(button == 5):
#	    #send into auto mode
#	    print('AUTO')
#	    current_state = 'auto'
#	    GPIO.output(redLED, 0)
#            GPIO.output(greenLED, 1)
#            GPIO.output(blueLED, 0)
#	if(button == 1 and blind_state == 'closed'):
#	    #open blinds
#	    MOTOR(motorGPIO, "open")
#	    blind_state = "open"
#	    print("key open")
#	if(button == 2 and blind_state == 'open'):
#	    #close blinds
#	    MOTOR(motorGPIO, "close")
#	    blind_state = "closed"
#	    print("Key close")

gpio_ports = {'state':23, 'blinds':27}
 
class device_handler(debounce_handler):
    global current_state
    global blind_state
    
    TRIGGERS = {"state":50023,
                "blinds":50027}

    def trigger(self,port,state):
        print('port: %d , state: %s', port, state)
        if state == True:
            MOTOR(motorGPIO, "open")
            current_state = "auto"
        else:
            MOTOR(motorGPIO, "close")
            current_state = "manual"
        
    def act(self, client_address, state, name):
        print "State", state, "on ", name, "from client @", client_address, "gpio port: ",gpio_ports[str(name)]
        self.trigger(gpio_ports[str(name)],state)
        return True

current_state = "auto"
blind_state = "closed"
current_temp = 0
current_light = 0
time1 = time.time()
key = Value('i', 0)

#MAIN LOOP
try:
    #p = Process(target = GET_REMOTE, args=(key,))
    #p.start()
    
    fauxmo.DEBUG = True
    x = fauxmo.poller()
    y = fauxmo.upnp_broadcast_responder()
    y.init_socket()
    x.add(y)
    z = device_handler()
    for trig, port in z.TRIGGERS.items():
        fauxmo.fauxmo(trig, y, x, None, port, z)
    logging.debug("Entering fauxmo polling loop")
    while True:


	#TEMP CHECK
        TEMP(tempGPIO)
        #LIGHT CHECK
        LIGHT(lightGPIO)
        #MOTION CHECK
        MOTION(motionGPIO)
        #REMOTE CHECK
	#if(key.value != 0 ):
        #       print(key.value)
	#REMOTE(key.value)
	#if(key.value == 3):
	#	GPIO.cleanup()
		#break

	key.value = 0
	
	x.poll(100)
        time.sleep(0.1)
	

except KeyboardInterrupt:
    GPIO.cleanup()
