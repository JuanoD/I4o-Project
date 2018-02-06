from .tools import ns_printer, importer, argstr, argget
from .node_classes import SistemaTransporte, Mixer
from .crud import get_item as crud_get_item
from .crud import update as crud_update
# from .pins import ttp
"""
Remember to use one of this ways for getting nodes:
    node = server.get_node('ns=%d;i=2' % idx)
    node = server.get_root_node().get_child(["0:Types", "0:ObjectTypes", "0:BaseObjectType", "%d:MyCustomObjectType" % idx])
    node = server.get_node(ua.ObjectIds.BaseObjectType).get_child(["%d:MyCustomObjectType" % idx])
"""