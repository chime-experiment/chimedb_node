"""Utility functions"""

import click
import peewee as pw
from . import orm


def node_from_userid(id_, from_cli=False):
    """Given a string (id_) record number or serial number, return a NodeAssembled object"""

    if id_ is None:
        return None

    # This function is idempotent
    if isinstance(id_, orm.NodeAssembled):
        return id_

    # Is this a record number
    if id_.startswith("N#"):
        try:
            return orm.NodeAssembled.get(orm.NodeAssembled.id == int(id_[2:], 10))
        except TypeError:
            if from_cli:
                ctx = click.get_current_context()
                ctx.fail("Bad record number.")
            else:
                raise
        except pw.DoesNotExist:
            if from_cli:
                ctx = click.get_current_context()
                ctx.fail("NODE not found.")
            else:
                raise

    # Now try serial number
    try:
        return orm.NodeAssembled.get(orm.NodeAssembled.serial == id_)
    except pw.DoesNotExist:
        if from_cli:
            ctx = click.get_current_context()
            ctx.fail("NODE not found.")
        else:
            return None


def component_from_userid(id_, from_cli=False):
    """Given a record number or serial number, return a NodeComponent object"""

    if id_ is None:
        return None

    # This function is idempotent
    if isinstance(id_, orm.NodeAssembled):
        return id_

    if id_.startswith("C#"):
        try:
            return orm.NodeComponent.get(
                orm.NodeComponent.id == id_, orm.NodeComponent.type != "slot"
            )
        except TypeError:
            if from_cli:
                ctx = click.get_current_context()
                ctx.fail("Bad record number.")
            else:
                raise
        except pw.DoesNotExist:
            if from_cli:
                ctx = click.get_current_context()
                ctx.fail("COMPONENT not found.")
            else:
                raise

    # Now try serial number
    try:
        return orm.NodeComponent.get(
            orm.NodeAssembled.serial == id_, orm.NodeComponent.type != "slot"
        )
    except pw.DoesNotExist:
        if from_cli:
            ctx = click.get_current_context()
            ctx.fail("COMPONENT not found.")
        else:
            raise


def valid_rack_slot(slot_name, from_cli=False):
    """Return a canonical rack slot designation if `slot_name` is a valid
    rack slot designator.  If `slot_name` is None, this function returns None.

    A rack slot must be specified like this, disregarding case:

    * an optional inital 'c'
    * a character indicating hut.  One of: F, N, S
    * a hexadecimal rack number, 0 through E
    * for hut "F", the character 'n'; for other huts, the character 'g'
    * a decimal slot number, 0 through 9

    Parameters
    ----------
    slot_name : str
        The slot name to validate, or None
    from_cli : bool
        If True, a syntax error will result in click.context.fail() being
        called.  If False, a syntax error will result in ValueError being raised
    """

    if slot_name is None:
        return None

    class RackSlotError(RuntimeError):
        pass

    # Canonicalise the slot name
    slot_name = slot_name.lower()
    try:
        try:
            offset = 1 if slot_name[0] == "c" else 0
        except IndexError:
            # We were passed the empty string
            raise RackSlotError

        if len(slot_name) != 4 + offset:
            raise RackSlotError

        hut = slot_name[offset]
        if hut not in "fns":
            raise RackSlotError

        rack = slot_name[offset + 1]
        if rack not in "0123456789abcde":
            raise RackSlotError

        if (hut == "f" and slot_name[offset + 2] != "n") or (
            hut != "f" and slot_name[offset + 2] != "g"
        ):
            raise RackSlotError
        slot = slot_name[offset + 3]
        if slot not in "0123456789":
            raise RackSlotError
    except RackSlotError:
        if from_cli:
            ctx = click.get_current_context()
            ctx.fail("Invalid rack slot designation.")
        else:
            raise ValueError("Invalid rack slot designation.")

    return "c" + hut + rack.upper() + ("n" if hut == "f" else "g") + slot
