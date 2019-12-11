"""High-level API for modifying the Hardware tracking database
"""
from .orm import NodeItem, NodeMAC, NodeAssembled, NodeHistory, NodeRMA
from enum import Enum


"""
add
    component
    ram
change
    nic
create/new
    component
    node
delete
    component
install
    node
move
    component
    node
note
rma
    out
    in
remove
    component
    node

show
    history
    operations
    node
    component

create_comp <type> <serial> --model=<model> --location=<location> -nic0=AA:AA:AA:AA:AA:AA:AA --nic1= --nic2= --nic3= --ipmi= --note=<text>
delete_comp <serial>

change_nic <serial> <which> <value>

add_comp <serial> <rack_slot> --slot=<#> --note=<text>
add_ram <rack_slot> <ram_slot> <amount> --note=<text>
remove_comp <rack_slot> <type> <serial> --note=<text>

new_node <type> <serial>
install_node <serial> <rack_slot> --note=<text>
remove_node <rack_slot> --location=<location> -note=<text>

move_comp <serial> <new_location> -note=<text>
move_node <serial> <new_location> -note=<text>

note <text> --node=<serial|rack_slot> --comp=<serial>

rma_out <serial> --number=<rma_number> --company=<company> --send-time=<datetime> --note=<text>
rma_in  :q<serial|rma_number> --recv-time=<datetime>

get_history --node= --component= --start= --end=
count_operations --start= --end=
    <component-type> <operation>
get_node <node>
get_component <serial>
"""
