"""
Table definitions for the GPU node hardware tracker
"""
from chimedb.core.orm import base_model, name_table, EnumField

import logging
import datetime
import peewee as pw

from . import util

_logger = logging.getLogger("chimedb")
_logger.addHandler(logging.NullHandler())


class NodeComponent(base_model):
    """A hardware component

    Attributes
    ----------
    type : enum
        The component type:
        - 'CPU'
        - 'GPU'
        - 'MB': a motherboard
        - 'NIC'
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

    type = EnumField(["CPU", "GPU", "MB", "NIC"], default="CPU")
    model = pw.CharField(max_length=64, null=True)
    serial = pw.CharField(max_length=64, null=True)
    status = EnumField(["OK", "RMA", "GONE"], default="OK")
    location = pw.TextField()

    def uninstall(location=None, note=None):
        """Remove this component from a node.

        The location of a removed component is set to <location>, if given.

        The associated history entry uses <note>, if given."""
        if self.type == "MB":
            node = NodeAssembled.get_or_none(NodeAssembled.motherboard == self)
            field = "motherboard"
        elif self.type == "CPU":
            try:
                node = NodeAssembled.get(NodeAssembled.cpu0 == self)
                field = "cpu0"
            except DoesNotExist:
                node = NodeAssembled.get_or_none(NodeAssembled.cpu1 == self)
                field = "cpu1"
        elif self.type == "GPU":
            try:
                node = NodeAssembled.get(NodeAssembled.gpu0 == self)
                field = "gpu0"
            except DoesNotExist:
                node = NodeAssembled.get_or_none(NodeAssembled.gpu1 == self)
                field = "gpu1"
        elif self.type == "NIC":
            node = NodeAssembled.get_or_none(NodeAssembled.nic == self)
            field = "nic"
        else:
            node = None

        if not node:
            raise ValueError("component not installed in node.")

        node.save()

        setattr(node, field, None)
        if location:
            component.location = location
            component.save()

        history.del_(node=node, component=self, note=note)


class NodeMAC(base_model):
    """A MAC address record for a component.

    Attributes
    ----------
    value : integer
        The MAC address.  This is the primary key
    component : foreign key
        The component for the MAC address
    mac_type : enum
         The MAC address type:
         - 'NIC0', the first NIC
         - 'NIC1', the second NIC (motherboards only)
         - 'NIC2', the second NIC (motherboards only)
         - 'NIC3', the third NIC (motherboards only)
         - 'NIC4', the fourth NIC (motherboards only)
         - 'IPMI', the IPMI device (motherboards only)
    """

    value = pw.BigIntegerField(primary_key=True)
    component = pw.ForeignKeyField(NodeComponent, backref="mac")
    mac_type = EnumField(
        ["NIC0", "NIC1", "NIC2", "NIC3", "NIC4", "IPMI"], default="NIC0"
    )

    class Meta:
        indexes = (
            # component + type is unique
            (("component", "mac_type"), True),
        )


class NodeDIMM(base_model):
    """RAM installed in a node

    Attributes
    ----------
    value : integer
        The amount of RAM in GB
    slot : integer
        The DIMM slot
    node : foreign key
        Referent to the associated NodeAssembled
    """

    value = pw.IntegerField(default=0)
    slot = pw.IntegerField(default=0)
    node = pw.ForeignKeyField(NodeAssembled)

    class Meta:
        # Each node slot can only have one DIMM in it
        indexes = ((("slot", "node"), True),)


class NodeXEngine(base_model):
    """X-Engine node-specific data

    Attributes
    ----------
    base : foreign key
        A reference to the generic NodeAssembled record
    south : bool
        True if installed in GPU-S, False if installed in GPU-N, NULL/None if not installed.
    rack : integer
        The rack number of an installed node (0-14)
    slot : integer
        The rack slot number of an installed node (0-9)
    """

    south = BooleanField(null=True)
    rack = pw.Integer(null=True)
    slot = pw.Integer(null=True)
    base = pw.ForeignKeyField(NodeAssembled, backref="xengine", unique=True)

    class Meta:
        # Uniqueness of installed rack position
        indexes = ((("south", "rack", "slot"), True),)


class NodeL1(base_model):
    """FRB L1 node-specific data

    Attributes
    ----------
    base : foreign key
        A reference to the generic NodeAssembled record
    rack : integer
        The rack number of an installed node (0-14)
    slot : integer
        The rack slot number of an installed node (0-9)
    """

    rack = pw.Integer(null=True)
    slot = pw.Integer(null=True)
    base = pw.ForeignKeyField(NodeAssembled, backref="xengine", unique=True)

    class Meta:
        # Uniqueness of installed rack position
        indexes = ((("rack", "slot"), True),)


class NodeAssembled(base_model):
    """Common data for an assembled X-engine GPU node or FRB L1 node

    Attributes
    ----------
    serial : string
        The node serial number.
    location : text
        Location of node (if not in a rack)
    gone : bool
        True if this node no longer exists
    """

    serial = pw.CharField(max_length=64, unique=True)
    location = pw.TextField(null=True)
    gone = pw.BooleanField(default=False)

    def components(self):
        """A list of all components installed in this node."""
        return NodeComponent.select().where(
            NodeComponent.id.in_(
                self.motherboard, self.cpu0, self.cpu1, self.gpu0, self.gpu1, self.nic
            )
        )

    def empty(self, location=None, note=None):
        """Remove all components from node.

        The location of removed components are set to <location>
        """
        for item in ["motherboard", "cpu0", "cpu1", "gpu0", "gpu1", "nic"]:
            component = getattr(self, item)
            if component:
                setattr(self, item, None)
                component.location = location
                component.save()
                history.del_(node=self, component=component, note=note)

        self.save()


class NodeRMA(base_model):
    """RMA data for a node component

    Attributes
    ----------
    component : foreign key
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

    component = pw.ForeignKeyField(NodeComponent, backref="mac")
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
              = if `node` is NULL: create a new component
              = if `component` is NULL: create a new node
              = otherwise: insert an component into `node`, or `node` into a rack
        - 'DEL' :
              = if `node` is NULL: delete a component
              = if `component` is NULL: delete a node
              = otherwise: remove an component from `node`, or `node` from a rack
        - 'NOP' : no change, used to add notes without changing anything
    node : foreign key
        Referencing the NodeAssembled affected, if any
    component : foreign key
        Referencing the NodeComponent affected, if any
    rma : foreign key
        Referencing the NodeRMA record, if any
    author : string
        Who made the note
    timestamp : datetime
        The timestamp of the record
    autonote : boolean
        True if the contents of `note` were automatically generated
        because no note was explicitly specified.
    note : text
        The note accompanying this change.
    """

    operation = EnumField(["ADD", "DEL", "NOP"], default="NOP")
    node = pw.ForeignKeyField(NodeAssembled, backref="history", null=True)
    component = pw.ForeignKeyField(NodeComponent, backref="history", null=True)
    rma = pw.ForeignKeyField(NodeRMA, backref="history", null=True)
    author = pw.CharField(max_length=64)
    timestamp = pw.DateTimeField(default=datetime.datetime.now)
    autonote = pw.BooleanField(default=True)
    note = pw.TextField()
