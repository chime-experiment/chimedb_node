"""History management"""

import socket
import getpass
import peewee as pw

from . import orm

_author = None


def set_author(author):
    """Set the author for a history update"""
    global _author
    _author = author


def get_author():
    """Determine the author for a history update"""
    global _author
    if not _author:
        _author = getpass.getuser() + "@" + socket.gethostname()

    return _author


def new_history(op, node, component, rma, note, autonote):
    """Create a new record."""

    hist = orm.NodeHistory()
    hist.operation = op
    hist.node = node
    hist.component = component
    hist.rma = rma
    hist.note = note
    hist.autonote = autonote
    hist.author = get_author()

    hist.save()


def add(node=None, component=None, rma=None, note=None):
    """Create an ADD record.  The caller is responsible for starting a transaction."""

    if note:
        autonote = False
    else:
        if node is None:
            note = "Created component."
        elif component is None:
            note = "Created node."
        else:
            note = "Added component to node."
        autonote = True

    new_history("ADD", node, component, rma, note, autonote)


def del_(node=None, component=None, rma=None, note=None):
    """Create a DEL record.  The caller is responsible for starting a transaction."""

    if note:
        autonote = False
    else:
        if node is None:
            note = "Retired component."
        elif component is None:
            note = "Retired node."
        else:
            note = "Removed component from node."
        autonote = True

    new_history("DEL", node, component, rma, note, autonote)
