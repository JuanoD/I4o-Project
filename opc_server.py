import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
import Modules
import threading
import logging
import time
try:
    from IPython import embed
except ImportError:
    import code

    def embed():
        vars = globals()
        vars.update(locals())
        shell = code.InteractiveConsole(vars)
        shell.interact()

from opcua import ua, uamethod, Server
from Modules.pins import wiringpi, ttp, mx1pins, mx2pins
# import wiringpi2 as wiringpi
# from opcua.server.history_sql import HistorySQLite # Import for history


class SubHandler(object):

    """
    Subscription Handler. To receive events from server for a subscription
    """

    def datachange_notification(self, node, val, data):
        print("Python: New data change event", node, val)

    def event_notification(self, event):
        print("Python: New event", event)


# ==============================[ METHOD DEFINITION STARTS HERE ]==============================

# This one was impossible to modularize since I need globals

class Methods(object):
    global sistran

    @staticmethod
    @uamethod
    def test(parent, action_name, method_arguments):
        logging.info("Iniciado test, con parent='{}', action_name='{}',"
                     " y method_arguments='{}'".format(parent.to_string(), action_name, method_arguments))

        method = threading.Thread(target=Methods.change_transport_values, name='CTV', args=(15, 'Mover', 'Mixer'))
        method.setDaemon(True)
        method.start()
        time.sleep(1)
        logging.info("Terminado test")
        return ["2", "OK"]

    @staticmethod
    @uamethod
    def execute(parent, action_name, method_arguments):
        ps = parent.to_string()
        logging.info("Iniciando execute con parent='{}', action_name='{}', y method_arguments='{}'"
                     .format(ps, action_name, method_arguments))
        args = Modules.argget(method_arguments)

        if 'D.ST.O.ActionSet' in ps:
            method = threading.Thread(target=Methods.change_transport_values,
                                      name='ctv',
                                      args=(action_name, args))
        elif 'D.Mx1.O.ActionSet' in ps:
            method = threading.Thread(target=Methods.mixing1,
                                      name='Mixing1',
                                      args=(action_name, args,))
        elif 'D.Mx2.O.ActionSet' in ps:
            method = threading.Thread(target=Methods.mixing2,
                                      name='Mixing2',
                                      args=(action_name, args))
        method.setDaemon(True)
        method.start()
        time.sleep(1)
        logging.info("Terminando execute")
        return 'OK'

    @staticmethod
    def change_transport_values(action_name, *args):
        logging.info("Iniciado change_transport_values con args={} y action_name='{}'".format(args[0], action_name))
        id, action, target = args[0]
        sistran.ParameterSet.NowAttending, sistran.ParameterSet.Action, sistran.ParameterSet.Target = args[0]
        sistran.ParameterSet.write()
        logging.info("Terminado change_transport_values")

    @staticmethod
    def mixing1(action_name, *args):
        logging.info("Iniciando mixing1 con argumentos action_name={} y args={}".format(action_name, args))
        id, action, ptime, target = args[0]
        logging.info("Se obtuvo {} de la base de datos".format((id, action, ptime, target)))

        Methods.change_transport_values('From mixing1', [id, action, target])
        if action == 'Mixing':
            mixer1.mix(id, ptime)
        logging.info("Terminando mixing1")

    @staticmethod
    def mixing2(action_name, *args):
        logging.info("Iniciando mixing2 con argumentos action_name={} y args={}".format(action_name, args))
        id, action, ptime, target = args[0]
        logging.info("Se obtuvo {} de la base de datos".format((id, action, ptime, target)))

        Methods.change_transport_values('From mixing2', [id, action, target])
        if action == 'Mixing':
            mixer2.mix(id, ptime)
        elif action == 'SlowMixing':
            mixer2.mix(id, ptime, duty=614)
        logging.info("Terminando mixing2")


# ===================================[ PINS MODULE ]===================================

# This one was impossible to modularize since I need globals

class ControlMezcladora(object):

    global sistran

    def __init__(self, the_mixer, name, pin_dict: 'Dictionary containing the pins for: '
                                 'forward, backward, extend, end, start,'
                                 'and if not needed contract, duty, and run may be None'):
        """
        ControlMotor(forward_pin, backward_pin)

        Use class P to convert pins from our device connectors to wiringPi
        forward: Pin for running motor forward
        backward: Pin for running motor backwards
        extend: Pin for piston extension  # This can be a light or sound if piston works manually.
        end: Pin for the limit switch at the end of the piston
        start: Pin for the limit switch at the start of the piston
        contract: If valve is bistable, this pin must be assigned  # This can be a light or sound if piston works
            manually.
        duty: If motor is PWM controllable, set this pin to the PWM output. Must be between 0 and 1023
        run: This should be a manual start. Will also be manual end
        """
        # forward, backward, extend, end, start, contract=None, duty=None, run=None
        self.inputs = pin_dict['inputs']
        self.outputs = pin_dict['outputs']
        self.pwm = pin_dict['pwm']
        self.forward = self.outputs['forward']
        self.backward = self.outputs['backward']
        self.extend = self.outputs['extend']
        self.end = self.inputs['end']
        self.start = self.inputs['start']
        self.contract = self.outputs['contract']
        self.duty = self.pwm['duty']
        self.run = self.outputs['run']

        self.name = name
        self.oua = the_mixer

        for pin in self.inputs.values():  # Initialize inputs (I think this is not necessary)
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

    def mix(self, id, total_time, alternating_time=2, duty=1023):
        """
        alternate(id, total_time, alternating_time, duty)
        :param total_time: Total mixing time
        :param alternating_time: Time between mixing orientation changes
        :param duty: Percentage of max output (Default is one, so it may only output PWM on PWM supported pins)
        """
        self.oua.ParameterSet.NowAttending = id
        self.oua.ParameterSet.write('NowAttending')
        tl = self.cl(total_time, alternating_time)
        if self.run:
            while not wiringpi.digitalRead(self.run):
                            # Run pin should be set if the machine piston valve runs automatically, so
                            # it can wait for product to reach the machine before process starts.
                pass
        Methods.change_transport_values('Freeing from mixing', [0, '', ''])
        if self.duty:
            # Set duty for this process
            wiringpi.pwmWrite(self.duty, duty)
            self.oua.SubDevices.Motor.ParameterSet.Duty = duty
            self.oua.SubDevices.Motor.ParameterSet.write('Duty')
        while not wiringpi.digitalRead(self.start):
            # Check for piston in initial position
            pass
        wiringpi.digitalWrite(self.extend, 1)                   # extend piston
        while not wiringpi.digitalRead(self.end):
                                                                # Wait for piston to reach end
            pass
        self.oua.SubDevices.Piston.ParameterSet.IsExtended = True
        self.oua.SubDevices.Piston.ParameterSet.write('IsExtended')
        self.oua.SubDevices.Motor.ParameterSet.IsRunning = True
        self.oua.SubDevices.Motor.ParameterSet.write('IsRunning')
        for i in range(0, len(tl), 2):                          # Motor cycle
            wiringpi.digitalWrite(self.forward, 1)              # Go forward
            wiringpi.digitalWrite(self.backward, 0)
            self.oua.SubDevices.Motor.ParameterSet.IsRunningForward = False
            self.oua.SubDevices.Motor.ParameterSet.write('IsRunningForward')
            time.sleep(tl[i])                                   # Wait
            wiringpi.digitalWrite(self.forward, 0)              # Go backwards
            wiringpi.digitalWrite(self.backward, 1)
            self.oua.SubDevices.Motor.ParameterSet.IsRunningForward = True
            self.oua.SubDevices.Motor.ParameterSet.write('IsRunningForward')
            time.sleep(tl[i+1])                                 # Wait
        wiringpi.digitalWrite(self.forward, 0)                  # Shut down motor
        wiringpi.digitalWrite(self.backward, 0)                 # Shut down motor
        self.oua.SubDevices.Motor.ParameterSet.IsRunning = False
        self.oua.SubDevices.Motor.ParameterSet.write('IsRunning')
        while sistran.ParameterSet.NowAttending != 0:            # Wait for worker to be free
            pass
        Methods.change_transport_values('Retrieving', [id, 'FinishedProduct', self.name])
        while not wiringpi.digitalRead(self.run):              # Wait for worker to push run button
            pass
        wiringpi.digitalWrite(self.extend, 0)                   # This contracts if piston uses monostable valve
        if self.contract:
            wiringpi.digitalWrite(self.contract, 1)             # This contracts if piston uses bistable valve
            while not wiringpi.digitalRead(self.start):
                pass                                            # Wait for piston to reach start
            wiringpi.digitalWrite(self.contract, 0)             # For bistable valves, this must be set to 0
        self.oua.SubDevices.Piston.ParameterSet.IsExtended = False
        self.oua.SubDevices.Piston.ParameterSet.write('IsExtended')
        if self.duty:
                                                                # For security, set duty to 0 after process ends
            wiringpi.pwmWrite(self.duty, 0)
            self.oua.SubDevices.Motor.ParameterSet.Duty = 0
            self.oua.SubDevices.Motor.ParameterSet.write('Duty')
        Modules.crud_update('Terminado', id)
        self.oua.ParameterSet.NowAttending = 0
        self.oua.ParameterSet.write('NowAttending')
        Methods.change_transport_values('Freeing from mixing', [0, '', ''])

# ===================================[ MAIN STARTS HERE ]===================================
if __name__ == "__main__":
    # optional: setup logging
    # Disable all loggers so they can be set manually one by one
    for i in logging.Logger.manager.loggerDict.keys():
        logger = logging.getLogger(i)
        logger.setLevel(logging.WARNING)
    # logger = logging.getLogger("opcua.address_space")
    # logger.setLevel(logging.DEBUG)
    # logger = logging.getLogger("opcua.internal_server")
    # logger.setLevel(logging.DEBUG)
    # logger = logging.getLogger("opcua.binary_server_asyncio")
    # logger.setLevel(logging.DEBUG)
    # logger = logging.getLogger("opcua.uaprocessor")
    # logger.setLevel(logging.DEBUG)
    # Enable next lines if you want to debug xml import:
    # logger = logging.getLogger("opcua.common.xmlimporter")
    # logger.setLevel(logging.DEBUG)
    # logger = logging.getLogger("opcua.common.xmlparser")
    # logger.setLevel(logging.DEBUG)
    logger = logging.basicConfig(level=logging.INFO,
                                 format='[{levelname:s}] - {asctime:s} {threadName:10s} : {message:s}',
                                 style='{',)

    # now setup our server
    server = Server(
        #  shelffile="shelf",
        )

    # import some nodes from xml
    xml_files = ["NodeSets/Opc.Ua.Di.NodeSet2.xml",
                 "NodeSets/Opc.Ua.Fdi5.NodeSet2.xml",
                 "NodeSets/Opc.Ua.Model.I.4.0.NodeSet2.xml",
                 "NodeSets/Opc.Ua.Model.I.4.0.Mixer1.NodeSet2.xml",
                 "NodeSets/Opc.Ua.Model.I.4.0.Mixer2.NodeSet2.xml",
                 ]

    Modules.importer(xml_files, server)

    server.set_application_uri("http://juandavid.univalle/i4o/")
    # server.disable_clock()
    server.set_endpoint("opc.tcp://0.0.0.0:4840/UV/i4o/")  # server.set_endpoint("opc.tcp://localhost:4840/freeopcua/server/")
    server.set_server_name("Proyecto Industria 4.0")
    # load server certificate and private key. This enables endpoints
    # with signing and encryption.
    # server.load_certificate("certificate-example.der")
    # server.load_private_key("private-key-example.pem")

    ns = server.get_namespace_array()
    uax = str(ns.index("http://opcfoundation.org/UA/"))
    dix = str(ns.index("http://opcfoundation.org/UA/DI/"))
    fdix = str(ns.index("http://fdi-cooperation.com/OPCUA/FDI5/"))
    i4ox = str(ns.index("http://juandavid.univalle/i4o/"))
    m1x = str(ns.index("http://juandavid.univalle/i4o/Mixer1/"))
    m2x = str(ns.index("http://juandavid.univalle/i4o/Mixer2/"))

    server.link_method(server.get_node("ns="+i4ox+";s=D.ST.O.AS.InvokeAction"), Methods.execute)
    server.link_method(server.get_node("ns="+m1x+";s=D.Mx1.O.AS.InvokeAction"), Methods.execute)
    server.link_method(server.get_node("ns="+m2x+";s=D.Mx2.O.AS.InvokeAction"), Methods.execute)

    Modules.ns_printer(ns)

    # Server conf for using sqlite for history
    # server.iserver.history_manager.set_storage(HistorySQLite("my_datavalue_history.sql"))

    # starting!
    server.start()

    # Initialize mirrored objects
    sistran = Modules.SistemaTransporte(server, server.get_node("ns="+i4ox+";s=D.ST.Online"))

    wiringpi.wiringPiSetup()  # Needed so the mixers control work

    mixer1 = ControlMezcladora(
        Modules.Mixer(server, server.get_node("ns="+m1x+";s=D.Mx1.Online")),
        'Mixer1',
        mx1pins
    )
    mixer2 = ControlMezcladora(
        Modules.Mixer(server, server.get_node("ns="+m2x+";s=D.Mx2.Online")),
        'Mixer2',
        mx2pins
    )

    # print("Available loggers are: ", logging.Logger.manager.loggerDict.keys())
    try:
        # enable following if you want to subscribe to nodes on server side
        # handler = Modules.NodeTools.SubHandler()
        # sub = server.create_subscription(500, handler)
        # handle = sub.subscribe_data_change(sistema_transporte_vars)
        # trigger event, all subscribed clients wil receive it
        # THIS HAS BEEN COMMENTED DUE TO SUBSCRIPTION CREATED ON OBJECT INSTANTIATION

        # mydevice_var.set_value("Running")
        # myevgen.trigger(message="This is BaseEvent")

        embed()
    finally:
        logging.info("Stopping server...")
        mixer1.clear_pins()
        mixer2.clear_pins()
        server.stop()
        logging.info("Server has stopped.")
