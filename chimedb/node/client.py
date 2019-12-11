"""CLI client for hardware node database"""

import click
import peewee as pw
import chimedb.core as db

from . import orm, history, util, __version__

import logging

_logger = logging.getLogger("chimedb")
logging.basicConfig(level=logging.DEBUG)

_MAC_TYPE = {0: "NIC0", 1: "NIC1", 2: "NIC2", 3: "NIC3", -1: "IPMI"}

# ============== click type definitions
class macaddr(click.ParamType):
    """MAC address values.

A MAC addresses is a 48-bit number, typically expressed as twelve hexadecimal
digits.  We accept any 12-digit hexadecimal number, optionally broken up
by colons, dots or hyphens into 6, 4, 3 or 2 equally-sized groups.
Separator characters cannot be mixed.

    * AA:AA:AA:AA:AA:AA
    * AA-AA-AA-AA-AA-AA
    * AAA.AAA.AAA.AAA
    * AAAA.AAAA.AAAA
    * AAAAAA-AAAAAA

Hexdigits are case insensitive.
"""

    name = "MAC_ADDR"

    def convert(self, value, param, ctx):
        if value is None:
            return None

        # a click.ParamType needs to be idempotent
        if isinstance(value, int):
            return value

        # Otherwise, validate and strip separators, if any
        separator = None
        if ":" in value:
            separator = ":"
        elif "-" in value:
            separator = "-"
        elif "." in value:
            separator = "."

        if separator is None:
            pass
        elif (
            value.count(separator) == 5
            and value[2] == separator
            and value[5] == separator
            and value[8] == separator
            and value[11] == separator
            and value[14] == separator
        ):
            value = value.replace(separator, "")
        elif (
            value.count(separator) == 3
            and value[3] == separator
            and value[7] == separator
            and value[11] == separator
        ):
            value = value.replace(separator, "")
        elif (
            value.count(separator) == 2
            and value[4] == separator
            and value[9] == separator
        ):
            value = value.replace(separator, "")
        elif value.count(separator) == 1 and value[7] == separator:
            value = value.replace(separator, "")
        else:
            self.fail(
                "Expected MAC address, got "
                f"{value!r} of type {type(value).__name__}",
                param,
                ctx,
            )

        # Verify
        if len(value) != 12:
            self.fail(
                "Bad length for MAC address: "
                f"{value!r} of type {type(value).__name__}",
                param,
                ctx,
            )

        # Convert to integer
        try:
            return int(value, 16)
        except TypeError:
            self.fail(
                f"Invalid MAC address: {value!r} of type {type(value).__name__}",
                param,
                ctx,
            )


class node_assembled(click.ParamType):
    """NodeAssembled specifiers."""

    name = "NODE"

    def convert(self, value, param, ctx):
        return util.node_from_userid(value, from_cli=True)


class node_component(click.ParamType):
    """NodeComponent specifiers ."""

    name = "COMPONENT"

    def convert(self, value, param, ctx):
        return util.component_from_userid(value, from_cli=True)


_mac_addr = macaddr()
_node_assembled = node_assembled()
_node_component = node_component()

# ============================= Common parameters


def component_argument(func):
    return click.argument(
        "COMPONENT", type=_node_component, default=None, required=False
    )(func)


def node_argument(func):
    return click.argument("NODE", type=_node_assembled, default=None, required=False)(
        func
    )


def serial_argument(func):
    return click.argument("SERIAL", type=str, default=None, required=False)(func)


def force_option(func):
    return click.option(
        "--force", help="don't ask for confirmation", is_flag=True, default=False
    )(func)


def location_option(_func=None, *, help="location information"):
    def decorator(_func):
        return click.option(
            "--location",
            "--loc",
            "-l",
            help=help,
            metavar="TEXT",
            type=str,
            default=None,
        )(_func)

    if _func is None:
        return decorator
    return decorator(_func)


def model_option(func):
    return click.option(
        "--model", "-M", help="model of the component", type=str, default=None
    )(func)


def mac_option(_func=None, *, multiple=False):
    if multiple:
        help = (
            "MAC address(es) of the component.  Depending on TYPE, up to "
            "four may be specified by using this option multiple times.  An "
            "IPMI MAC address is specified separately using --ipmi"
        )
    else:
        help = "MAC address of the component"

    def decorator(_func):
        return click.option(
            "--mac", "-m", type=_mac_addr, default=None, multiple=multiple, help=help
        )(_func)

    if _func is None:
        return decorator
    return decorator(_func)


def note_option(func):
    return click.option(
        "--note",
        "-n",
        type=str,
        default=None,
        help="a note to attach to this change in the history",
    )(func)


# ======== CLI entry point


def param_help(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return

    click.echo(
        "\n"
        + click.wrap_text("Several parameter values have special syntax:")
        + "\n\n"
        + click.wrap_text(
            "Record numbers can be used to refer to any nodedb object. "
            "A record number starts with a (case-insensitive) character "
            "indicating the object type, followed by a number sign (#), "
            "followed by one or more digits.  Use the `show` or `history`"
            "commands to find record numbers.  Record numbers printed "
            "by these commands often have leading zeros after the number "
            "sign.  These may be omitted.",
            initial_indent="* ",
            subsequent_indent="  ",
        )
        + "\n\n  Examples:\n"
        "    C#332   c#000332   -  C is the prefix for components\n"
        "    H#20432 h#00020432 -  H is the prefix for history entries\n"
        "    N#1987  n#01987    -  N is the prefix for nodes\n"
        "    R#101   r#0101     -  R is the prefix for RMA records\n"
        + "\n\n"
        + click.wrap_text(
            "A MAC address is expressed as a twelve-hexdigit number.  The "
            "twelve hexdigits may optionally be broken up into six, four, "
            "three, or two equally-sized groups separated by a separator "
            "character.  Three separator characters are supported "
            '(":", "-", and "."), but only one of these may be used '
            "in a single address.  Hexdigits are not case sensitive.",
            initial_indent="* ",
            subsequent_indent="  ",
        )
        + "\n\n  Examples:\n"
        "    AA:AA:AA:AA:AA:AA\n"
        "    aa-aa-aa-aa-aa-aa\n"
        "    AAA.AAA.AAA.AAA\n"
        "    aaaa.aaaa.aaaa\n"
        "    AAAAAA:AAAAAA\n\n"
        + click.wrap_text(
            "Rack slot designations should follow the standard "
            "c[ns][0-E]g[0-9] or cf[0-E]n[0-9] formats.  They "
            'are not case sensitive and the initial "c" may be omitted.',
            initial_indent="* ",
            subsequent_indent="  ",
        )
        + "\n\n  Examples:\n"
        "    cnEg4 cneg4 CFEN4 fEn4\n"
    )
    ctx.exit(0)


def show_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return

    click.echo(
        "{0} {1}\nCopyright © 2019 D. V. Wiebe\n\n".format(
            ctx.find_root().info_name, __version__
        )
        + click.wrap_text(
            """
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but without any warranty; without even the implied warranty of
merchantability or fitness for a particular purpose.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
""",
            preserve_paragraphs=True,
        )
    )

    ctx.exit(0)


@click.group()
@click.option(
    "--help-params",
    is_eager=True,
    expose_value=False,
    callback=param_help,
    is_flag=True,
    help="show help for parameter values",
)
@click.option(
    "--user",
    "-u",
    metavar="USER",
    nargs=1,
    default=None,
    help="username for history entries.  Currently: {0}".format(history.get_author()),
)
@click.option(
    "---version",
    "-v",
    is_eager=True,
    expose_value=False,
    callback=show_version,
    is_flag=True,
    help="show version and licensing information",
)
def entry(user):
    """CHIME hardware node tracker."""

    if user:
        history.set_author(user)


# ========= CREATE


def _new_mac(comp, value, num=0):
    """Create MAC address <value> for NodeComponent <comp>.  <num> is 0-3 for NIC0-NIC3 or -1 for IPMI."""

    mac = orm.NodeMac()
    mac.value = addr
    mac.type = _MAC_TYPE[num]
    mac.component = comp

    return mac


def create_component(type_, serial, location, note, model, ipmi=None, macs=[]):
    """Common handler for NodeComponent creation"""

    # If the serial number is missing, assume the user wanted --help
    if serial is None:
        ctx = click.get_current_context()
        click.echo(ctx.get_help())
        ctx.exit(0)

    component = orm.NodeComponent()
    component.type = type_.upper()
    component.model = model
    component.serial = serial
    component.status = "OK"
    component.location = location

    component.save()

    # Create and save all the MAC addresses
    [_new_mac(component, addr, num).save() for num, addr in enumerate(macs)]

    # Also the IPMI address
    if ipmi is not None:
        _new_mac(component, ipmi, -1).save()

    # Update History
    history.add(component=component, note=note)


@db.atomic(read_write=True)
@entry.group()
def create():
    """Create a new node or component."""
    pass


@create.command("node", short_help="create a node")
@serial_argument
@click.option("--frb/--gpu", "-f/-g", help="node type [default: GPU]")
@location_option(
    help="location information for an uninstalled node.  "
    "Mutually exclusive with --slot."
)
@note_option
@click.option(
    "--slot",
    "-s",
    metavar="RACK_SLOT",
    default=None,
    help="location of an installed node.  Mutually exclusive with --location.",
)
def create_node(serial, frb, location, note, slot):
    """Create a new node with serial number SERIAL."""

    # If the serial number is missing, assume the user wanted --help
    if serial is None:
        ctx = click.get_current_context()
        click.echo(ctx.get_help())
        ctx.exit(0)

    if location and slot:
        ctx = click.get_current_context()
        ctx.fail("Cannot specify both --location and --slot")

    node = orm.NodeAssembled()
    node.frb = frb
    node.serial = serial
    node.location = location
    node.rack_slot = util.valid_rack_slot(slot, from_cli=True)

    node.save()

    history.add(node=node, note=note)

    click.echo("Created Node N#{0}".format(node.id))


@create.command("cpu", short_help="create a new CPU")
@serial_argument
@location_option
@model_option
@note_option
def create_cpu(serial, location, note, model):
    """Create a new CPU with serial number SERIAL."""
    create_component("cpu", serial, location, note, model)


@create.command("gpu", short_help="create a new GPU")
@serial_argument
@location_option
@model_option
@note_option
def create_gpu(serial, location, note, model):
    """Create a new GPU with serial number SERIAL."""
    create_component("gpu", serial, location, note, model)


@create.command("mb", short_help="create a new motherboard")
@serial_argument
@click.option(
    "--ipmi", "-i", type=_mac_addr, default=None, help="MAC address of the IPMI device."
)
@location_option
@model_option
@mac_option(multiple=True)
@note_option
def create_mb(serial, location, note, model, ipmi, mac):
    """Create a new motherboard with serial number SERIAL."""
    create_component("mb", serial, location, note, model, ipmi=ipmi, macs=[mac])


@create.command("nic", short_help="create a new NIC")
@serial_argument
@location_option
@model_option
@mac_option
@note_option
def create_nic(serial, location, note, model, mac):
    """Create a new NIC with serial number SERIAL."""
    create_component("mb", serial, location, note, model, macs=mac)


# ========= DISCARD


@db.atomic(read_write=True)
@entry.group()
def discard():
    """Discard a node or component."""
    pass


@discard.command("node", short_help="discard a node")
@node_argument
@location_option(
    help="location of removed components, if any.  "
    "Ignored if --remove-all is not specified."
)
@note_option
@click.option(
    "--remove-all",
    is_flag=True,
    default=False,
    help="remove all installed components.  If this option is not specified, "
    "and the node to be discarded still has components installed in it, the "
    "operation will fail.",
)
@click.pass_context
def discard_node(ctx, node, location, remove_all, note):
    """Discards the node specified by NODE.

    NODE may either be a serial number or else a node record number.

    (NB: this doesn't remove the node from the database, just marks it as gone.)
    """

    if node is None:
        # Show click help if node is missing
        click.echo(ctx.get_help())
        ctx.exit(0)

    if node.gone:
        click.fail("ERROR: node has already been discarded.")

    if not remove_all:
        if node.components():
            click.fail("ERROR: node contains components.")
    else:
        node.empty(location=location, note=note)

    node.gone = True
    node.save()

    history.del_(node=node, note=note)


@discard.command("component", short_help="discard a component")
@component_argument
@note_option
@click.option(
    "--uninstall",
    "-u",
    is_flag=True,
    default=False,
    help="if the component is installed in a node, remove it first. "
    "Without this option, attempting to discard an installed component "
    "will fail",
)
@click.pass_context
def discard_component(ctx, component, uninstall, note):
    """Discards the component specified by COMPONENT.

    COMPONENT may either be a serial number or else a component record number.

    (NB: this doesn't remove the component from the database, just marks it as gone.)
    """
    if component is None:
        # Show click help if component is missing
        click.echo(ctx.get_help())
        ctx.exit(0)

    if component.status == "GONE":
        click.fail("ERROR: component has already been discarded.")
    elif component.status == "RMA":
        click.fail("ERROR: component is out for RMA.")

    if component.node:
        if uninstall:
            component.uninstall(location=None, note=note)
        else:
            click.fail("ERROR: component installed in node")

    component.status = "GONE"
    component.save()

    history.del_(component=component, note=note)
