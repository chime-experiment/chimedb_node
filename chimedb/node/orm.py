"""
Table definitions for the GPU node hardware tracker
"""
from chimedb.core.orm import base_model, name_table, EnumField

import peewee as pw
import datetime

import logging
_logger = logging.getLogger("chimedb")
_logger.addHandler(logging.NullHandler())

class NodeItem(base_model):
    """A hardware component

    Attributes
    ----------
    type : enum
        The component type:
        - 'CPU'
        - 'GPU'
        - 'MB': a motherboard
        - 'NIC'
        - 'RAM'
        - 'slot': a rack slot
    model : string
        The model of the component
    serial : string
        The serial number of the component
    status : enum
        The status of the component:
            - 'OK': the component is in use (or available for use)
            - 'RMA': the component has been sent out for RMA
            - 'GONE': the component has been discarded
    location : text
        Location of component (if not in a node)
    """
    type = EnumField(['CPU', 'GPU', 'MB', 'NIC', 'RAM'], default='CPU')
    model = pw.CharField(max_length=64, null=True)
    serial = pw.CharField(max_length=64, null=True)
    status = EnumField(['OK', 'RMA', 'GONE'], default='OK')
    location = pw.TextField()

class NodeMAC(base_model):
    """A MAC address record for a component.

    Attributes
    ----------
    value : integer
        The MAC address.  This is the primary key
    item : foreign key
        The component for the MAC address
    mac_type : enum
         The MAC address type:
         - 'NIC0', the first NIC
         - 'NIC1', the second NIC (motherboards only)
         - 'NIC2', the third NIC (motherboards only)
         - 'NIC3', the fourth NIC (motherboards only)
         - 'IPMI', the IPMI device (motherboards only)
    """
    value = pw.BigIntegerField(primary_key=True)
    item = pw.ForeignKeyField(NodeItem, backref='mac')
    mac_type = EnumField(['NIC0', 'NIC1', 'NIC2', 'NIC3', 'IPMI'], default='NIC0')

    class Meta:
        indexes = (
                # item + type is unique
                (('item', 'node_type'), True),
                )


class NodeAssembled(base_model):
    """Data for an assembled X-engine GPU node or FRB L1 node

    Attributes
    ----------
    node_type : enum
        - 'FRB' for a FRB L1 node
        - 'GPU' for a X-Engine GPU node
    serial : string
        The node serial number.
    rack_slot : foreign key
        Reference to a NodeRackSlock: the location of the node,
        if installed
    motherboard : foreign key
        Reference to the installed NodeMotherboard
    cpu0 : foreign key
        Reference to the first installed NodeCPU
    cpu1 : foreign key
        Reference to the second installed NodeCPU (FRB L1 node only)
    gpu0 : foreign key
        Reference to the first installed NodeGPUBoard (X-Engine GPU node only)
    gpu1 : foreign key
        Reference to the second installed NodeGPUBoard (X-Engine GPU node only)
    nic : foreign key
        Reference to the installed NodeNIC (X-Engine GPU node only)
    ram0 : foreign key
        Reference to the first installed NodeRAM module
    ram1 : foreign key
        Reference to the second installed NodeRAM module
    ram2 : foreign key
        Reference to the third installed NodeRAM module
    ram3 : foreign key
        Reference to the fourth installed NodeRAM module
    ram4 : foreign key
        Reference to the fifth installed NodeRAM module
    ram5 : foreign key
        Reference to the sixth installed NodeRAM module
    ram6 : foreign key
        Reference to the seventh installed NodeRAM module
    ram7 : foreign key
        Reference to the eighth installed NodeRAM module
    location : text
        Location of node (if not in a rack)
    """
    node_type = EnumField(['FRB', 'GPU'], default='GPU')
    serial = pw.CharField(max_length=64)
    rack_slot = pw.ForeignKeyField(NodeItem, backref='node', unique=True, null=True)
    motherboard = pw.ForeignKeyField(NodeItem, backref='node', unique=True, null=True)
    cpu0 = pw.ForeignKeyField(NodeItem, backref='node', unique=True, null=True)
    cpu1 = pw.ForeignKeyField(NodeItem, backref='node', unique=True, null=True)
    gpu0 = pw.ForeignKeyField(NodeItem, backref='node', unique=True, null=True)
    gpu1 = pw.ForeignKeyField(NodeItem, backref='node', unique=True, null=True)
    nic = pw.ForeignKeyField(NodeItem, backref='node', unique=True, null=True)
    ram0 = pw.ForeignKeyField(NodeItem, backref='node', unique=True, null=True)
    ram1 = pw.ForeignKeyField(NodeItem, backref='node', unique=True, null=True)
    ram2 = pw.ForeignKeyField(NodeItem, backref='node', unique=True, null=True)
    ram3 = pw.ForeignKeyField(NodeItem, backref='node', unique=True, null=True)
    ram4 = pw.ForeignKeyField(NodeItem, backref='node', unique=True, null=True)
    ram5 = pw.ForeignKeyField(NodeItem, backref='node', unique=True, null=True)
    ram6 = pw.ForeignKeyField(NodeItem, backref='node', unique=True, null=True)
    ram7 = pw.ForeignKeyField(NodeItem, backref='node', unique=True, null=True)

class NodeRMA(base_model):
    """RMA data for a node component

    Attributes
    ----------
    item : foreign key
        The RMA'd component
    number : string
        The RMA number
    company : string
        The company for the return
    send_time : datetime
        The time the RMA'd component was sent out
    recv_time : datetime
        The time the RMA'd component was returned
    """
    item = pw.ForeignKeyField(NodeItem, backref='mac')
    number = pw.CharField(max_length=64, null=True)
    company = pw.CharField(max_length=64, null=True)
    send_time = pw.DateTimeField(default=datetime.datetime.now)
    recv_time = pw.DateTimeField(null=True)

class NodeHistory(base_model):
    """Notes and history for the node hardware tracker

    Attributes
    ----------
    operation : enum
        The operation performed:
        - 'ADD' :
              = if `node` is NULL: add a new component
              = otherwise: insert a component into `node`, or `node` into a rack
        - 'DEL' : remove a component from a node, or a node from a rack
              = if `node` is NULL: delete a component
              = otherwise: remove a component from `node`, or `node` from a rack
        - 'NOP' : no change, used to add notes without changing anything
    node : foreign key
        Referencing the NodeAssembled affected, if any
    item : foreign key
        Referencing the NodeItem affected, if any
    rma : foreign key
        Referencing the NodeRMA record, if any
    timestamp : datetime
        The timestamp of the record
    autonote : boolean
        True if the contents of `note` were automatically generated
        because no note was explicitly specified.
    note : text
        The note accompanying this change.
    """
    operation = EnumField(['ADD', 'DEL', 'NOP'], default='NOP')
    node = pw.ForeignKeyField(NodeAssembled, backref="history", null=True)
    item = pw.ForeignKeyField(NodeItem, backref="history", null=True)
    rma = pw.ForeignKeyField(NodeRMA, backref="history", null=True)
    timestamp = pw.DateTimeField(default=datetime.datetime.now)
    autonote = pw.BooleanField(default=True)
    note = pw.TextField()
