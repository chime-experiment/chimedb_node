import pytest
import peewee as pw

from chimedb.node.client import create_node
from chimedb.node.orm import NodeAssembled
from playhouse.shortcuts import model_to_dict


def _node_dict(
    id=None,
    frb=False,
    serial=None,
    rack_slot=None,
    motherboard=None,
    cpu0=None,
    cpu1=None,
    gpu0=None,
    gpu1=None,
    nic=None,
    ram0=0,
    ram1=0,
    ram2=0,
    ram3=0,
    ram4=0,
    ram5=0,
    ram6=0,
    ram7=0,
    gone=False,
):
    return dict(
        id=id,
        frb=frb,
        serial=serial,
        rack_slot=rack_slot,
        motherboard=motherboard,
        cpu0=cpu0,
        cpu1=cpu1,
        gpu0=gpu0,
        gpu1=gpu1,
        nic=nic,
        ram0=ram0,
        ram1=ram1,
        ram2=ram2,
        ram3=ram3,
        ram4=ram4,
        ram5=ram5,
        ram6=ram6,
        ram7=ram7,
        gone=gone,
    )


def _id_from_output(result):
    """Get the node id mentioned in command output"""
    import re

    match = re.search(r"N#(\d+)", result.output)
    return int(match.group(1), 10)


def test_create_node_help(start_db, click_runner):
    """Check that running "create node" returns usage if no serial number given"""
    result = click_runner.invoke(create_node)
    assert result.exit_code == 0
    assert "usage" in result.output.lower()


def test_create_node_defaults(start_db, click_runner):
    """Check default parameter values"""
    result = click_runner.invoke(create_node, ["cn_defaults"])
    assert result.exit_code == 0
    assert "created node" in result.output.lower()

    id_ = _id_from_output(result)
    node = NodeAssembled.get(NodeAssembled.id == id_)
    assert model_to_dict(node) == _node_dict(id=id_, serial="cn_defaults")


def test_create_node_frb(start_db, click_runner):
    result = click_runner.invoke(create_node, ["cn_frb", "--frb"])
    assert result.exit_code == 0
    assert "created node" in result.output.lower()

    id_ = _id_from_output(result)
    node = NodeAssembled.get(NodeAssembled.id == id_)
    assert model_to_dict(node) == _node_dict(id=id_, serial="cn_frb", frb=True)


def test_create_node_duplicate(start_db, click_runner):
    result = click_runner.invoke(create_node, ["cn_duplicate"])
    assert result.exit_code == 0
    assert "created node" in result.output.lower()

    result = click_runner.invoke(create_node, ["cn_duplicate"])
    assert result.exit_code == 1
    assert result.exception.__class__ == pw.IntegrityError


def test_create_node_gpu_forbidden(start_db, click_runner):
    pass


#    result = click_runner.invoke(create_node, ["cn_gpu_forbidden",
