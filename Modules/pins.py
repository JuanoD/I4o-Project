"""
This module translates the pin number from the device to WiringPi
"""
import logging
# import wiringpi2 as wiringpi  # I'll be using a fake wiringPi for testing
import time
import random

ttp = { # Terminal to pin dictionary
    'w01': 0,
    'w02': 1,  # PWM0
    'w03': 2,
    'w04': 3,
    'w05': 4,
    'w06': 5,
    'w07': 6,
    'w08': 10,
    'w09': 11,
    'w10': 12,
    'w11': 13,
    'w12': 14,
    'w13': 21,
    'w14': 22,
    'w15': 23,  # PWM1
    'w16': 24,  # PWM1?
    'w17': 25,
    'w18': 26,  # PWM0
    'w19': 27,
    'w20': 28,
    'w21': 29,
    'w22': 30,
    'w23': 31,
    'w24': 'GND',
    'w25': 'VCC',

    'in_m': 0,
    'out_m': 1,
    'alt_m': 2,
}

mx1pins = {
    'inputs': {'start': None, 'end': None, },
    'outputs': {'forward': None, 'backward': None, 'run': None, 'extend': None, 'contract': None, },
    'pwm': {'duty': None, },
}

mx2pins = {
    'inputs': {'start': None, 'end': None, },
    'outputs': {'forward': None, 'backward': None, 'run': None, 'extend': None, 'contract': None, },
    'pwm': {'duty': None, },
}


class wiringpi(object):
    @staticmethod
    def wiringPiSetup():
        logging.info('Setup for using wiringpi pin numbering')

    @staticmethod
    def digitalWrite(pin, state):
        logging.info('Set {} to {}.'.format(pin, state))

    @staticmethod
    def digitalRead(pin):
        read = random.choice([True, False])
        logging.info('Read {} from pin {}.'.format(read, pin))
        return read

    @staticmethod
    def pwmWrite(pin, duty):
        logging.info('Set pin {} duty to {}.'.format(pin, duty))

    @staticmethod
    def pinMode(pin, mode):
        logging.info('Set pin {} to mode {}.'.format(pin, mode))


# Everything beyond this point may be deleted


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


class ControlMezcladora(object):
    def __init__(self, **kwargs: 'Dictionary containing the pins for: '
                                 'forward, backward, extend, end, start,'
                                 'and if not needed contract, duty, and run may be None'):
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
        :param run: This should be a manual start. Will also be manual
        """
        # forward, backward, extend, end, start, contract=None, duty=None, run=None
        self.inputs = kwargs['inputs']
        self.outputs = kwargs['outputs']
        self.pwm = kwargs['pwm']
        self.forward_pin = self.outputs['forward']
        self.backward_pin = self.outputs['backward']
        self.extend = self.outputs['extend']
        self.end = self.inputs['end']
        self.start = self.inputs['start']
        self.contract = self.outputs['contract']
        self.duty = self.pwm['duty']
        self.run = self.outputs['run']

        for pin in self.inputs.values():  # Initialize inputs (I think this is not necessary
            if pin:
                wiringpi.pinMode(pin, ttp['in_m'])
        for pin in self.outputs.values():  # Initialize outputs
            if pin:
                wiringpi.pinMode(pin, ttp['out_m'])
        for pin in self.pwm.values():  # Initializing pwm output
            if pin:
                wiringpi.pinMode(pin, ttp['alt_m'])

    def clear_pins(self):  # Must be called when stopping server
        for pin in self.outputs.values():
            if pin:
                wiringpi.digitalWrite(pin, 0)
                wiringpi.pinMode(pin, ttp['in_m'])
        for pin in self.pwm.values():
            if pin:
                wiringpi.pwmWrite(pin, 0)
                wiringpi.pinMode(pin, ttp['alt_m'])

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
            while not wiringpi.digitalRead(self.start):
                # Wait for piston to reach start
                pass
            wiringpi.digitalWrite(self.contract, 0)  # In bistable valves, this must be set to 0
        if self.duty:
            # For security, set duty to 0 after process ends
            wiringpi.pwmWrite(self.duty, 0)
