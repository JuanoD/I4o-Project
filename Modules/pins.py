"""
This module translates the pin number from the device to WiringPi
"""
import wiringpi2 as wiringpi
import time


class P(object):
    w01 = 0
    w02 = 1  # PWM0
    w03 = 2
    w04 = 3
    w05 = 4
    w06 = 5
    w07 = 6
    w08 = 10
    w09 = 11
    w10 = 12
    w11 = 13
    w12 = 14
    w13 = 21
    w14 = 22
    w15 = 23  # PWM1
    w16 = 24  # PWM1?
    w17 = 25
    w18 = 26  # PWM0
    w19 = 27
    w20 = 28
    w21 = 29
    w22 = 30
    w23 = 31
    w24 = "GND"
    w25 = "VCC"

    in_m = 0
    out_m = 1
    alt_m = 2

    @staticmethod
    def initial_setup():
        """
        Here you should put your initialization for pins
        """
        wiringpi.wiringPiSetup()
        wiringpi.pinMode(P.w15, P.out_m)

    @staticmethod
    def final_cleanup():
        """
        Here, you should perform pin cleanup
        """
        wiringpi.digitalWrite(P.w15, 0)
        wiringpi.pinMode(P.w15, 0)


class ControlMezcladora(object):
    def __init__(self, forward, backward, extend, end, start, contract=None, duty=None, run=None):
        """
        ControlMotor(forward_pin, backward_pin)

        Use class P to convert pins from our device connectors to wiringPi
        :param forward: Pin for running motor forward
        :param backward: Pin for running motor backwards
        :param extend: Pin for piston extension  # This can be a light or sound if piston works manually.
        :param end: Pin for the limit switch at the end of the piston
        :param start: Pin for the limit switch at the start of the piston
        :param contract: If valve is bistable, this pin must be assigned  # This can be a light or sound if piston works
            manually.
        :param duty: If motor is PWM controllable, set this pin to the PWM output. Must be between 0 and 1023
        """
        self.forward_pin = forward
        self.backward_pin = backward
        self.extend = extend
        self.end = end
        self.start = start
        self.contract = contract
        self.duty = duty
        self.run = run

    @staticmethod
    def cl(total_time, alternating_time):
        """
        Sum of the generated list equals the total time.
        Used for time.sleep so it fulfills the entire time
        """
        tt = total_time
        at = alternating_time
        tl = list()
        while tt > at:
            tl.append(at)
            tt -= at
        tl.append(tt)
        if len(tl) % 2:
            tl.append(0)
        return tl

    def mix(self, total_time, alternating_time=2, duty=1):
        """
        alternate(alternating_time, total_time)
        :param total_time: Total mixing time
        :param alternating_time: Time between mixing orientation changes
        :param duty: Percentage of max output (Default is one, so it may only output PWM on PWM supported pins)
        """
        tl = self.cl(total_time, alternating_time)
        if self.run:
            while not wiringpi.digitalRead(self.run):
                # Run pin should be set if the machine piston valve runs automatically, so
                # it can wait for product to reach the machine before process starts.
                pass
        if self.duty:
            # Set duty for this process
            wiringpi.pwmWrite(self.duty, duty)
        while not wiringpi.digitalRead(self.start):
            # Check for piston in initial position
            pass
        wiringpi.digitalWrite(self.extend, 1)  # extend piston
        while not wiringpi.digitalRead(self.end):
            # Wait for piston to reach end
            pass
        for i in range(0, len(tl), 2):
            wiringpi.digitalWrite(self.forward, 1)  # Go forward
            wiringpi.digitalWrite(self.backwards, 0)
            time.sleep(tl[i])            # Wait
            wiringpi.digitalWrite(self.forward, 0)  # Go backwards
            wiringpi.digitalWrite(self.backwards, 1)
            time.sleep(tl[i+1])            # Wait
        wiringpi.digitalWrite(self.forward, 0)  # Shut down motor
        wiringpi.digitalWrite(self.backwards, 0)  # Shut down motor
        wiringpi.digitalWrite(self.extend, 0)  # This contracts if piston uses monostable valve
        if self.contract:
            wiringpi.digitalWrite(self.contract, 1)  # This contracts if piston uses bistable valve
            while wiringpi.digitalRead(self.start):
                # Wait for piston to reach start
                pass
            wiringpi.digitalWrite(self.contract, 0)  # In bistable valves, this must be set to 0
        if self.duty:
            # For security, set duty to 0 after process ends
            wiringpi.pwmWrite(self.duty, 0)
