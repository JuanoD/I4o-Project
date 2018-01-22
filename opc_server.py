import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
import NamespaceOperators
# from datetime import datetime
import logging
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


class SubHandler(object):

    """
    Subscription Handler. To receive events from server for a subscription
    """


    def datachange_notification(self, node, val, data):
        print("Python: New data change event", node, val)

    def event_notification(self, event):
        print("Python: New event", event)


# method to be exposed through server

def func(parent, variant):
    ret = False
    if variant.Value % 2 == 0:
        ret = True
    return [ua.Variant(ret, ua.VariantType.Boolean)]


# method to be exposed through server
# uses a decorator to automatically convert to and from variants

@uamethod
def test(parent):
    print("My parent is: ", parent)
    return parent


if __name__ == "__main__":
    # optional: setup logging
    logging.basicConfig(level=logging.WARN)
    # logger = logging.getLogger("opcua.address_space")
    # logger.setLevel(logging.DEBUG)
    # logger = logging.getLogger("opcua.internal_server")
    # logger.setLevel(logging.DEBUG)
    # logger = logging.getLogger("opcua.binary_server_asyncio")
    # logger.setLevel(logging.DEBUG)
    # logger = logging.getLogger("opcua.uaprocessor")
    # logger.setLevel(logging.DEBUG)

    # now setup our server
    server = Server(
        # desired_uri="http://opcfoundation.org/UA/DI/",
        #  shelffile="shelf"
        )
    '''
    Se ha editado la libraría para pedir un uri en su __init__.
    Este uri debe ser el primero de la lista de importaciones si se van a importar xml.
    Después de realizar la importación, se cambia el uri por el deseado
    '''

    # import some nodes from xml
    xml_files = ["NodeSets/Opc.Ua.Di.NodeSet2.xml",
                 "NodeSets/Opc.Ua.Fdi5.NodeSet2.xml",
                 "NodeSets/Opc.Ua.Model.I.4.0.NodeSet2.xml",
                 # "NodeSets/Opc.Ua.Model.I.4.0.Mixer1.NodeSet2.xml",
                 # "NodeSets/Opc.Ua.Model.I.4.0.Mixer2.NodeSet2.xml",
                 ]

    NamespaceOperators.importer(xml_files, server)

    server.set_application_uri("http://juandavid.univalle/i4o/")
    # server.disable_clock()
    server.set_endpoint("opc.tcp://0.0.0.0:4840/UV/i4o/") # server.set_endpoint("opc.tcp://localhost:4840/freeopcua/server/")
    server.set_server_name("Proyecto Industria 4.0")
    ns1 = server.get_namespace_array()
    idx0 = ns1.index("http://opcfoundation.org/UA/")
    idx1 = ns1.index("http://opcfoundation.org/UA/DI/")
    idx2 = ns1.index("http://fdi-cooperation.com/OPCUA/FDI5/")
    idx3 = ns1.index("http://juandavid.univalle/i4o/")

    # server.link_method(server.get_root_node().get_child(
    #     [str(idx0) + ":Objects", str(idx1) + ":DeviceSet", str(idx3) + ":SistemaTransporte",
    #      str(idx3) + ":ActionSet", str(idx2) + ":InvokeAction" ]), test)
    #
    # server.link_method(server.get_root_node().get_child(
    #     [str(idx0) + ":Objects", str(idx1) + ":DeviceSet", str(idx3) + ":Mixer1",
    #      str(idx3) + ":ActionSet", str(idx2) + ":InvokeAction" ]), test)

    # starting!
    # print("Los namespace son:")
    # for nsn, nsu in enumerate(ns1):
    #     print("    {}: {}".format(nsn, nsu))

    server.start()

    #Initialize mirrored objects
    sistema_transporte_vars = NamespaceOperators.DiDevicesParameterSet(
        server,
        server.get_root_node().get_child([str(idx0)+":Objects", str(idx1)+":DeviceSet", str(idx3)+":SistemaTransporte", str(idx3)+":ParameterSet"]))
    # sistema_transporte_vars.DeviceClass = "Hola"
    # sistema_transporte_vars.write("DeviceClass")

    print("Available loggers are: ", logging.Logger.manager.loggerDict.keys())
    try:
        # enable following if you want to subscribe to nodes on server side
        # handler = NamespaceOperators.NodeTools.SubHandler()
        # sub = server.create_subscription(500, handler)
        # handle = sub.subscribe_data_change(sistema_transporte_vars)
        # trigger event, all subscribed clients wil receive it
        # THIS HAS BEEN COMMENTED DUE TO SUBSCRIPTION CREATED ON OBJECT INSTANTIATION

        # mydevice_var.set_value("Running")
        # myevgen.trigger(message="This is BaseEvent")

        embed()
    finally:
        server.stop()
