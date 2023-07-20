# Kernel Flashing Instructions

For this kernel to work properly, there are some steps that need to be done.

Please also note that the instructions provided are made for a <u>clean installation</u>.

*As for now*, dirty installations (==with data preservation) are not tested nor researched.

Also keep in mind that after executing all of the documented steps, <u>**your device will have disabled DM-Verity and Force Encrypt, which can be seen as (and actually is) a security risk.**</u>

## **0. Backup**

Before doing anything to your device, **make a backup**.

It is highly recommended to do a NANDroid backup via TWRP.

Backup should be made with removed lockscreen passwords/fingerprints/PINs. Otherwise there might be some issues during the flashing process.

## **1. Download assets**

Listed below files are required:

- compiled kernel, obviously;
- LineageOS ROM;
- Magisk + some modules;
- TWRP, the official 3.7.0 version (supports operations with encrypted partitions);
- DM-Verity and Force Encrypt disabler;
- Kali NetHunter + Kali NetHunter Terminal apps;
- Kali NetHunter Chroot (you can do this later, but it would be easier to download this beforehand);
- `nhpatch.sh` script from this repo (fixes NetHunter permissions for Android 12+).

Currently, all of the mentioned assets can be collected via the `assets` subcommand in the wrapper (use `full` option).

## **2. Flashing**

**Note:** Once again, this instruction is for <u>clean installation only</u>, meaning that you <u>will lose all your data</u>.

The installation process is done in the following order:

### **2.0 Some checks**

Before doing anything, please ensure that you have:

- an unlocked bootloader;
- an installed TWRP blu_spark recovery;
- a <u>working</u> NANDroid backup of your device.

### **2.1 In TWRP**

- wipe your phone via `Wipe -> Advanced Wipe` menu, check all the shown boxes;
- wipe your device again via the `Wipe -> Format Data` menu (this will remove any encryption that is present on your device);
- reboot into TWRP via `Reboot -> Recovery`;
- flash the ROM;
- flash the kernel;
- flash the root manager (Magisk; you must change the `.apk` extension into `.zip` for this);
- flash the DM-Verity and Force Encrypt disabler zip (*?; requires further testing, there is a chance this is not actually needed*);
- reboot into system via `Reboot -> System` .

### **2.2 In OS**

- install Magisk apk, open it and do what the pop-up says (finish root installation, which will automatically reboot your device; if you don't see the pop-up, close the Magisk app and open it again);
- once booted back into OS, open Magisk app again and proceed with finishing the installation (when prompted with "Additional Setup", select the default `Patch vbmeta in boot image` in `Options` and `Direct install` in `Method` submenus);
- install NetHunter + NetHunter Terminal apps;
- open the NetHunter app and grant all the permissions (at some point you will see an error indicating that some permissions are not granted; that's normal, the next step will fix that);
- open the NetHunter Terminal app, select `AndroidSu` option, navigate through your storage and launch the `nhpatch.sh`;
- open the NetHunter app (permissions should be fixed now);
- navigate to the `Kali Chroot Manager` submenu and install the chroot (if you downloaded it beforehand, use the "restore" option);
- open Nethunter Terminal app with the `kali` option (if it opens properly, then congratulations, you have a working Kali NetHunter on your device).
