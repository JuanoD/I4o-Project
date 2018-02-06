import sys
sys.path.insert(0, "..")
import logging
import threading
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


from opcua import Client
from opcua import ua
from Modules import crud, argstr


class SubHandler(object):

    """
    Subscription Handler. To receive events from server for a subscription
    data_change and event methods are called directly from receiving thread.
    Do not do expensive, slow or network operation there. Create another 
    thread if you need to do such a thing
    """

    def datachange_notification(self, node, val, var):
        print("Python: New data change event", node, val)

    def event_notification(self, event):
        print("Python: New event", event)


if __name__ == "__main__":
    time.sleep(1)  # Time must be set here, so you can run server first
    logging.basicConfig(level=logging.WARN)
    # logger = logging.getLogger("KeepAlive")
    # logger.setLevel(logging.DEBUG)

    client = Client("opc.tcp://localhost:4840/UV/i4o/")
    # client = Client("opc.tcp://admin@localhost:4840/freeopcua/server/") #connect using a user
    try:
        client.connect()

        # Get a specific node knowing its node id
        st_actions = client.get_node("ns=3;s=D.ST.O.ActionSet")
        mx1_actions = client.get_node("ns=4;s=D.Mx1.O.ActionSet")
        mx2_actions = client.get_node("ns=5;s=D.Mx2.O.ActionSet")

        st_services = client.get_node("ns=3;s=D.ST.O.PS.OfferedServices")
        mx1_services = client.get_node("ns=4;s=D.Mx1.O.PS.OfferedServices")
        mx2_services = client.get_node("ns=5;s=D.Mx2.O.PS.OfferedServices")

        st_attending = client.get_node("ns=3;s=D.ST.O.PS.NowAttending")
        mx1_attending = client.get_node("ns=4;s=D.Mx1.O.PS.NowAttending")
        mx2_attending = client.get_node("ns=5;s=D.Mx2.O.PS.NowAttending")
        # var.get_data_value() # get value of node as a DataValue object
        # var.get_value() # get value of node as a python builtin
        # var.set_value(ua.Variant([23], ua.VariantType.Int64)) #set node value using explicit data type
        # var.set_value(3.9) # set node value using implicit data type

        # subscribing to a variable node
        handler = SubHandler()
        sub = client.create_subscription(500, handler)
        handle = sub.subscribe_data_change(st_services)
        time.sleep(0.1)

        # we can also subscribe to events from server
        sub.subscribe_events()
        # sub.unsubscribe(handle)
        # sub.delete()

        # calling a method on server

        # print(st_services.get_value())

        def mx1_search():
            while True:
                if st_attending.get_value() == 0:
                    if mx1_attending.get_value() == 0:
                        arguments = crud.get_item("Mixer1")
                        if arguments:
                            args = argstr(arguments)
                            mx1_actions.call_method("4:InvokeAction", 'Called for Mixer1', args)

        def mx2_search():
            while True:
                if st_attending.get_value() == 0:
                    if mx2_attending.get_value() == 0:
                        arguments = crud.get_item("Mixer2")
                        if arguments:
                            args = argstr(arguments)
                            mx2_actions.call_method("5:InvokeAction", 'Called for Mixer2', args)

        mezcladora1 = threading.Thread(target=mx1_search,
                                       name='Mixing1',
                                       args=())
        mezcladora2 = threading.Thread(target=mx2_search,
                                       name='Mixing2',
                                       args=())
        mezcladora1.setDaemon(True)
        mezcladora2.setDaemon(True)
        mezcladora1.start()
        mezcladora2.start()
        embed()
    finally:
        client.disconnect()
