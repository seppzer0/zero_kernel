# FAQ

This page contains answers to popular questions when working with this kernel.

## Q: How to TURN ON monitor mode on internal Wi-Fi card?

There are two options to switch internal Wi-Fi card to monitor mode:

- in Kali chroot environment, launch `airmon-ng start wlan0`;
- in NetHunter app, navigate to the `Custom Commands` menu and launch the `Start wlan0 in monitor mode`.

Be aware that while in monitor mode, you won't be able to connect to a Wi-Fi like you'd normally do in an Android device.

## Q: How to TURN OFF monitor mode on internal Wi-Fi card?

Similarly, depending on which approach you chose to turn on the monitor way, the are two options:

- in Kali chroot environment ->`airmon-ng stop wlan0`;
- in NetHunter app -> `Custom Commands` -> `Start wlan0 in monitor mode`.

## Q: Why is there an unused wlan1 interface?

**TL;DR**: Because it's a ~~bug~~ feature of Android 13.

Initially, when launching `airmon-ng` in Kali chroot environment without any of the interfaces in monitor mode and no external adapters plugged in, you will see two wlan interfaces: `wlan0` and `wlan1`.

This is most likely caused by the way [Wi-Fi STA/STA Concurrency](https://source.android.com/docs/core/connect/wifi-sta-sta-concurrency) mechanism. Disabling this seems dangerous, so a workaround is required.

Switching `wlan0` to monitor mode disables `wlan1` completely. However, when restoring `wlan0` to "normal" mode, `wlan1` appears back.

## Q: How to TURN ON and OFF monitor mode on external Wi-Fi card?

For an external card, you would have to use `airmon-ng start <interface>` and `airmon-ng stop <interface>` commands only.
