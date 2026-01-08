# Vivado project creation for emulator_wrapper
# Usage: vivado -mode batch -source scripts/vivado/create_project.tcl

set proj_dir "generated/vivado"
set proj_name "emulator_wrapper"
set part_name "xc7a200tsbg484-1"
set root_dir ""

if {[llength $argv] >= 1} {
    set proj_dir [lindex $argv 0]
}
if {[llength $argv] >= 2} {
    set proj_name [lindex $argv 1]
}
if {[llength $argv] >= 3} {
    set part_name [lindex $argv 2]
}
if {[llength $argv] >= 4} {
    set root_dir [lindex $argv 3]
}
if {$root_dir eq ""} {
    set root_dir [file normalize [file join [pwd] ".." ".."]]
}

file mkdir $proj_dir
create_project $proj_name $proj_dir -part $part_name -force

set rtl_file [file join $root_dir "generated/rtl/emulator_wrapper.sv"]
if {![file exists $rtl_file]} {
    puts "ERROR: RTL file not found: $rtl_file"
    exit 1
}

add_files -norecurse $rtl_file
set_property top emulator_wrapper [current_fileset]

# Elaborate RTL for schematic viewing.
synth_design -rtl -rtl_skip_mlo -name rtl_1

# No synthesis/implementation; project only.
puts "INFO: Project created at $proj_dir"
