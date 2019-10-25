"""High-level API for modifying the Hardware tracking database
"""
from .orm import NodeItem, NodeMAC, NodeAssembled, NodeHistory, NodeRMA

from enum import Enum


# add to rack
# remove from rack

# add a component to node
# remove component from node (+ optional RMA)

# change location of thing

# add note to history with no changes

# component sent out for RMA
# component returned from RMA

# create new component
# discard component

# new node
