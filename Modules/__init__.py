from .NSO import ns_printer, importer
from .NodeClasses import DiDevicesParameterSet, DeviceDi
from .Methods import test
"""
Remember to use one of this ways for getting nodes:
    myobject1_type_nodeid = ua.NodeId.from_string('ns=%d;i=2' % idx)
    myobject2_type_nodeid = server.get_root_node().get_child(["0:Types", "0:ObjectTypes", "0:BaseObjectType", "%d:MyCustomObjectType" % idx]).nodeid
    myobject3_type_nodeid = server.get_node(ua.ObjectIds.BaseObjectType).get_child(["%d:MyCustomObjectType" % idx]).nodeid
"""