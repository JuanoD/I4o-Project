import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
import Modules
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
# from opcua.server.history_sql import HistorySQLite # Import for history


class SubHandler(object):

    """
    Subscription Handler. To receive events from server for a subscription
    """

    def datachange_notification(self, node, val, data):
        print("Python: New data change event", node, val)

    def event_notification(self, event):
        print("Python: New event", event)


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
    # Enable next lines if you want to debug xml import:
    # logger = logging.getLogger("opcua.common.xmlimporter")
    # logger.setLevel(logging.DEBUG)
    # logger = logging.getLogger("opcua.common.xmlparser")
    # logger.setLevel(logging.DEBUG)

    # now setup our server
    server = Server(
        #  shelffile="shelf"
        )

    # import some nodes from xml
    xml_files = ["NodeSets/Opc.Ua.Di.NodeSet2.xml",
                 "NodeSets/Opc.Ua.Fdi5.NodeSet2.xml",
                 "NodeSets/Opc.Ua.Model.I.4.0.NodeSet2.xml",
                 # "NodeSets/Opc.Ua.Model.I.4.0.Mixer1.NodeSet2.xml",
                 # "NodeSets/Opc.Ua.Model.I.4.0.Mixer2.NodeSet2.xml",
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
    idx0 = ns.index("http://opcfoundation.org/UA/")
    idx1 = ns.index("http://opcfoundation.org/UA/DI/")
    idx2 = ns.index("http://fdi-cooperation.com/OPCUA/FDI5/")
    idx3 = ns.index("http://juandavid.univalle/i4o/")

    # server.link_method(server.get_root_node().get_child(
    #     [str(idx0) + ":Objects", str(idx1) + ":DeviceSet", str(idx3) + ":SistemaTransporte",
    #      str(idx3) + ":ActionSet", str(idx2) + ":InvokeAction" ]), test)
    #
    server.link_method(server.get_root_node().get_child(
        [str(idx0) + ":Objects", str(idx1) + ":DeviceSet", str(idx3) + ":Mixer1",
         str(idx3) + ":ActionSet", str(idx3) + ":InvokeAction"]), Modules.test)

    Modules.ns_printer(ns)

    # Server conf for using sqlite for history
    # server.iserver.history_manager.set_storage(HistorySQLite("my_datavalue_history.sql"))

    # starting!
    server.start()

    # Initialize mirrored objects
    sistran = Modules.DeviceDi(
        server,
        server.get_root_node().get_child(["0:Objects", "1:DeviceSet", "3:SistemaTransporte", "3:Online"]),
        "ST"
    )

    # method = ua.NodeId.from_string('ns=%d;i=2' % idx)
    # self.server.link_method(method, definedmethodonpython)
    # server.historize_node_data_change(myvar, period=None, count=100) # Historize var

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
        server.stop()
