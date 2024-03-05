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
- ROM;
- Magisk or KernelSU;
- TWRP, the special [build](https://sourceforge.net/projects/op5-5t/files/Android-12/TWRP/twrp-3.7.0_12-5-dyn-cheeseburger_dumpling.img/download) by faoliveira78 (supports operations with encrypted and dynamic partitions);
- DM-Verity and Force Encrypt disabler;
- Kali NetHunter + Kali NetHunter Terminal apps;
- Kali NetHunter Chroot (you can do this later, but it would be easier to download this beforehand);
- ~~`nhpatch.sh` script from this repo (fixes NetHunter permissions for Android 12+)~~ with recent NetHunter app versions, `nhpatch.sh` usage is no longer required.

Currently, all of the mentioned assets can be collected via the `assets` subcommand in the wrapper (use `full` option).

## **2. Flashing**

**Note:** Once again, this instruction is for <u>clean installation only</u>, meaning that you <u>will lose all your data</u>.

The installation process is done in the following order:

### **2.0 Some checks**

Before doing anything, please ensure that you have:

- an unlocked bootloader;
- an installed TWRP recovery;
- a <u>working</u> NANDroid backup of your device.

### **2.1 In TWRP**

- wipe your phone via `Wipe -> Advanced Wipe` menu, check all the shown boxes;
- wipe your device again via `Wipe -> Format Data` menu (this will remove any encryption that is present on your device);
- reboot into TWRP via `Reboot -> Recovery`;
- if using a Retrofit Dynamic Partitions ROM such as ParanoidAndoid -> untoggle `Unmount System before installing a ZIP` in the Settings;
- flash the ROM;
- flash the kernel;
- **if using Magisk** --> flash Magisk root manager (you must change the `.apk` extension into `.zip` for this);
- flash DM-Verity and Force Encrypt disabler zip;
- reboot into system via `Reboot -> System` .

### **2.2 In OS**

#### For Magisk users

- install Magisk apk, open it and do what the pop-up says (finish root installation, which will automatically reboot your device; if you don't see the pop-up, close the Magisk app and open it again);
- once booted back into OS, open Magisk app again and proceed with finishing the installation (when prompted with "Additional Setup", select the default `Patch vbmeta in boot image` in `Options` and `Direct install` in `Method` submenus);
- install NetHunter + NetHunter Terminal apps;
- open NetHunter app (if seeing a Busybox-related error, press "OK" and re-open the app);
- navigate to the `Kali Chroot Manager` submenu and install the chroot (if you downloaded it beforehand, use the "restore" option);
- make sure that your NetHunter and NetHunter Terminal apps are properly configured to see the installed chroot directory (by default it may be `/data/local/nhsystem/kalifs`; if you see it anywhere, change it to `/data/local/nhsystem/kali-arm64`);
- in NetHunter Terminal app open `Kali` shell (if it opens properly, then congratulations, you have a working Kali NetHunter on your device).

#### For KernelSU users

- install KernelSU Manager app, open it and verify that the `Superuser` tab works properly (should show the `Shell` item);
- install NetHunter and NetHunter Terminal apps, but do not open them yet;
- open KernelSU Manager app, grant SU permissions to both NetHunter and NetHunter Terminal apps via `Superuser` tab;
- open the NetHunter app (if seeing a Busybox-related error, press "OK" and re-open the app);
- navigate to the `Kali Chroot Manager` submenu and install the chroot (if you downloaded it beforehand, use the "restore" option);
- make sure that your NetHunter and NetHunter Terminal apps are properly configured to see the installed chroot directory (by default it may be `/data/local/nhsystem/kalifs`; if you see it anywhere, change it to `/data/local/nhsystem/kali-arm64`);
- in NetHunter Terminal app open `Kali` shell (if it opens properly, then congratulations, you have a working Kali NetHunter on your device).

#### For x_kernel-based kernel + ParanoidAndroid users

This is a small side-note for using x_kernel-based build with ParanoidAndroid ROM. When booting into OS, you will see a message that `There is an internal problem with this device. Please call manufacturer.`. This warning is essentially similar to the unlocked bootloader message and is completely harmless. Press "OK" and proceed.
