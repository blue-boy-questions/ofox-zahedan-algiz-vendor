#!/usr/bin/env bash
#
# Copyright (C) 2026 The OrangeFox Recovery Project
# OrangeFox Build Variables for Volla Phone Quintus (algiz) - Kernel 6.6
#

FDEVICE="algiz"

fox_get_target_device() {
    local chkdev=$(echo "$BASH_SOURCE" | grep -w "$FDEVICE")
    if [ -n "$chkdev" ]; then
        FOX_BUILD_DEVICE="$FDEVICE"
    else
        chkdev=$(set | grep BASH_ARGV | grep -w "$FDEVICE")
        [ -n "$chkdev" ] && FOX_BUILD_DEVICE="$FDEVICE"
    fi
}

if [ -z "$1" -a -z "$FOX_BUILD_DEVICE" ]; then
    fox_get_target_device
fi

if [ "$1" = "$FDEVICE" -o "$FOX_BUILD_DEVICE" = "$FDEVICE" ]; then
    export TARGET_DEVICE_ALT="zahedan,Quintus,algiz"
    export FOX_TARGET_DEVICES="algiz,zahedan,Quintus"

    # Vendor Boot Recovery & Virtual A/B (Kernel 6.6 GKI)
    export FOX_VENDOR_BOOT_RECOVERY=1
    export FOX_VIRTUAL_AB_DEVICE=1
    export FOX_RECOVERY_VENDOR_BOOT_PARTITION="/dev/block/by-name/vendor_boot"
    export FOX_RECOVERY_SYSTEM_PARTITION="/dev/block/mapper/system"
    export FOX_RECOVERY_VENDOR_PARTITION="/dev/block/mapper/vendor"
    export FOX_RECOVERY_BOOT_PARTITION="/dev/block/by-name/boot"

    # Screen Geometry (20:9 - 1080x2400)
    export OF_SCREEN_H=2400
    export OF_STATUS_H=100
    export OF_STATUS_INDENT_LEFT=48
    export OF_STATUS_INDENT_RIGHT=48
    export OF_HIDE_NOTCH=1
    export OF_CLOCK_POS=1

    # Features & Addons
    export FOX_USE_BASH_SHELL=1
    export FOX_ASH_IS_BASH=1
    export FOX_USE_TAR_BINARY=1
    export FOX_USE_SED_BINARY=1
    export FOX_USE_XZ_UTILS=1
    export FOX_USE_NANO_EDITOR=1
    export FOX_ENABLE_APP_MANAGER=1
    export FOX_DELETE_AROMAFM=1
    export OF_ENABLE_LPTOOLS=1
    export OF_NO_TREBLE_COMPATIBILITY_CHECK=1
    export OF_NO_REFLASH_CURRENT_ORANGEFOX=1
    export OF_KEEP_DM_VERITY=1
    export OF_SUPPORT_ALL_BLOCK_OTA_UPDATES=0
    export OF_FIX_OTA_UPDATE_MANUAL_FLASH_ERROR=1

    # Maintainer & Versioning
    export OF_MAINTAINER="Volla-6.6-Builder"
    export FOX_MAINTAINER_PATCH_VERSION="1"
    export FOX_VARIANT="Kernel-6.6"
fi
