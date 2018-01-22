from opcua import ua

class SubHandler(object):
    """
    Subscription Handler. To receive events from server for a subscription.
    The handler forwards updates to it's referenced python object
    """

    def __init__(self, obj):
        self.obj = obj


    def datachange_notification(self, node, val, data):
        # print("Python: New data change event", node, val, data)

        _node_name = node.get_browse_name()
        setattr(self.obj, _node_name.Name, data.monitored_item.Value.Value.Value)


class UaObject(object):
    """
    Python object which mirrors an OPC UA object
    Child UA variables/properties are auto subscribed to to synchronize python with UA server
    Python can write to children via write method, which will trigger an update for UA clients
    """
    def __init__(self, opcua_server, ua_node):
        self.opcua_server = opcua_server
        self.nodes = {}
        self.b_name = ua_node.get_browse_name().Name

        # keep track of the children of this object (in case python needs to write, or get more info from UA server)
        for _child in ua_node.get_children():
            _child_name = _child.get_browse_name()
            self.nodes[_child_name.Name] = _child

        # find all children which can be subscribed to (python object is kept up to date via subscription)
        sub_children = ua_node.get_properties()
        sub_children.extend(ua_node.get_variables())

        # subscribe to properties/variables
        handler = SubHandler(self)
        sub = opcua_server.create_subscription(500, handler)
        handle = sub.subscribe_data_change(sub_children)

    def write(self, attr=None):
        # if a specific attr isn't passed to write, write all OPC UA children
        if attr is None:
            for k, node in self.nodes.items():
                node_class = node.get_node_class()
                if node_class == ua.NodeClass.Variable:
                    node.set_value(getattr(self, k))
        # only update a specific attr
        else:
            self.nodes[attr].set_value(getattr(self, attr))


class DiDevicesParameterSet(UaObject):
    """
    Definition of OPC UA object which represents a object to be mirrored in python
    This class mirrors it's UA counterpart and semi-configures itself according to the UA model (generally from XML)
    """
    def __init__(self, opcua_server, ua_node):

        # properties and variables; must mirror UA model (based on browsename!)
        self.DeviceClass = 0
        self.DeviceHealth = 0
        self.DeviceManual = 0
        self.DeviceRevision = 0
        self.HardwareRevision = 0
        self.Manufacturer = 0
        self.Model = 0
        self.RevisionCounter = 0
        self.SerialNumber = 0
        self.SoftwareRevision = 0

        # init the UaObject super class to connect the python object to the UA object
        super().__init__(opcua_server, ua_node)

        # local values only for use inside python
        self.testval = 'python only'

        # If the object has other objects as children it is best to search by type and instantiate more
        # mirrored python classes so that your UA object tree matches your python object tree

        # ADD CUSTOM OBJECT INITIALIZATION BELOW
        # find children by type and instantiate them as sub-objects of this class
        # NOT PART OF THIS EXAMPLE
