# AnyKernel3 Ramdisk Mod Script
# osm0sis @ xda-developers

## AnyKernel setup
# begin properties
properties() { '
kernel.string=NetHunter Kernel for OnePlus 5/T by @seppzer0
do.devicecheck=1
do.modules=0
do.systemless=1
do.cleanup=1
do.cleanuponabort=0
device.name1=dumpling
device.name2=cheeseburger
supported.versions=14
supported.patchlevels=
'; } # end properties


### AnyKernel install
## boot files attributes
boot_attributes() {
set_perm_recursive 0 0 755 644 $RAMDISK/*;
set_perm_recursive 0 0 750 750 $RAMDISK/init* $RAMDISK/sbin;
} # end attributes

# boot shell variables
BLOCK=/dev/block/bootdevice/by-name/boot;
IS_SLOT_DEVICE=0;
RAMDISK_COMPRESSION=auto;
PATCH_VBMETA_FLAG=auto;

# import functions/variables and setup patching - see for reference (DO NOT REMOVE)
. tools/ak3-core.sh;

# boot install
dump_boot; # use split_boot to skip ramdisk unpack, e.g. for devices with init_boot ramdisk

# begin ramdisk changes
backup_file init.rc;
insert_line init.rc "init.nethunter.rc" after "import /init.usb.configfs.rc" "import /init.nethunter.rc";

#backup_file ueventd.rc;
#insert_line ueventd.rc "/dev/hidg" after "/dev/pmsg0" "/dev/hidg*                0666   root       root";
# end ramdisk changes

write_boot;
## end install
