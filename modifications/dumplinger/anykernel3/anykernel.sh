# AnyKernel3 Ramdisk Mod Script
# osm0sis @ xda-developers

## AnyKernel setup
# begin properties
properties() { '
kernel.string=Nethunter Kernel for OnePlus5/5T by @seppzer0
do.devicecheck=1
do.modules=0
do.systemless=1
do.cleanup=0
do.cleanuponabort=0
device.name1=dumpling
device.name2=cheeseburger
supported.versions=12
supported.patchlevels=
'; } # end properties

# shell variables
block=/dev/block/bootdevice/by-name/boot;
is_slot_device=0;
ramdisk_compression=auto;

## AnyKernel methods (DO NOT CHANGE)
# import patching functions/variables - see for reference
. tools/ak3-core.sh;


## AnyKernel file attributes
# set permissions/ownership for included ramdisk files
set_perm_recursive 0 0 755 644 $ramdisk/*;
set_perm_recursive 0 0 750 750 $ramdisk/init* $ramdisk/sbin;


## AnyKernel boot install
dump_boot;

# patch dtbo.img
username="$(file_getprop /system/build.prop "ro.build.user")";
echo "Found user: $username";
case "$username" in
  "android-build") user=google;;
  *) user=custom;;
esac;
hostname="$(file_getprop /system/build.prop "ro.build.host")";
echo "Found host: $hostname";
case "$hostname" in
  *corp.google.com|abfarm*) host=google;;
  *) host=custom;;
esac;
if [ "$user" == "custom" -o "$host" == "custom" ]; then
  if [ ! -z /tmp/anykernel/dtbo.img ]; then
    ui_print " "; ui_print "You are on a custom ROM, patching kernel to remove verity...";
    $bin/magiskboot --dtb-patch /tmp/anykernel/dtbo.img;
    $bin/magiskboot --dtb-patch /tmp/anykernel/Image.lz4-dtb;
  fi;
else
  ui_print " "; ui_print "You are on stock, not patching kernel to remove verity!";
fi;

# begin ramdisk changes
backup_file init.rc;
insert_line init.rc "init.nethunter.rc" after "import /init.usb.configfs.rc" "import /init.nethunter.rc";

backup_file ueventd.rc;
insert_line ueventd.rc "/dev/hidg" after "/dev/pmsg0" "/dev/hidg*                0666   root       root";
# end ramdisk changes

write_boot;
## end install
