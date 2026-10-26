#
# Copyright (C) 2026 The OrangeFox Recovery Project
# SPDX-License-Identifier: Apache-2.0
#

# Inherit standard 64-bit AOSP & TWRP common configs
$(call inherit-product, $(SRC_TARGET_DIR)/product/core_64_bit.mk)
$(call inherit-product, $(SRC_TARGET_DIR)/product/base.mk)
$(call inherit-product, vendor/twrp/config/common.mk)

# Inherit device configurations
$(call inherit-product, device/volla/algiz/device.mk)

PRODUCT_NAME := twrp_algiz
PRODUCT_DEVICE := algiz
PRODUCT_BRAND := Volla
PRODUCT_MODEL := Volla Phone Quintus
PRODUCT_MANUFACTURER := Hallo Welt Systeme UG

PRODUCT_GMS_CLIENTID_BASE := android-volla
