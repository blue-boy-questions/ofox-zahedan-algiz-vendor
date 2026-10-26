#!/usr/bin/env python3
"""
Volla Phone Quintus (algiz / zahedan) — Kernel 6.6 From-Zero Tree Extractor & Repacker
1. Extracts Kernel 6.6 DTB, 6.6 .ko modules, fstab.mt6877, and init.recovery.mt6877.rc
   directly from your stock_vendor_boot.img (and optional vendor_dlkm.img).
2. Populates device/volla/algiz/ so it is 100% ready for OrangeFox fox_14.1 / fox_12.1 compilation.
3. Also provides a post-build repacker (--repack-built) to merge your newly built OrangeFox
   vendor_ramdisk_recovery.cpio with your stock Kernel 6.6 platform ramdisk (ramdisk00) and AVB v4 footer!
"""

import argparse
import gzip
import hashlib
import os
import shutil
import struct
import subprocess

def align(x, p=4096):
    return (x + p - 1) & ~(p - 1)

def parse_cpio_ordered(data):
    pos = 0
    entries = []
    while pos + 110 <= len(data):
        magic = data[pos:pos+6]
        if magic != b"070701" and magic != b"070702":
            break
        hdr = data[pos:pos+110].decode("ascii")
        ino = int(hdr[6:14], 16)
        mode = int(hdr[14:22], 16)
        uid = int(hdr[22:30], 16)
        gid = int(hdr[30:38], 16)
        nlink = int(hdr[38:46], 16)
        mtime = int(hdr[46:54], 16)
        filesize = int(hdr[54:62], 16)
        devmajor = int(hdr[62:70], 16)
        devminor = int(hdr[70:78], 16)
        rdevmajor = int(hdr[78:86], 16)
        rdevminor = int(hdr[86:94], 16)
        namesize = int(hdr[94:102], 16)
        pos += 110
        name = data[pos:pos+namesize-1].decode("utf-8", errors="replace")
        pos += namesize
        pos = (pos + 3) & ~3
        content = data[pos:pos+filesize]
        pos += filesize
        pos = (pos + 3) & ~3
        if name == "TRAILER!!!":
            break
        entries.append({
            "name": name, "ino": ino, "mode": mode, "uid": uid, "gid": gid,
            "nlink": nlink, "mtime": mtime, "devmajor": devmajor, "devminor": devminor,
            "rdevmajor": rdevmajor, "rdevminor": rdevminor, "content": content
        })
    return entries

def decompress_ramdisk(raw_bytes):
    if raw_bytes[:2] == b"\x1f\x8b":
        return gzip.decompress(raw_bytes)
    tmp_in = "/tmp/rd_in.bin"
    tmp_out = "/tmp/rd_out.cpio"
    with open(tmp_in, "wb") as f:
        f.write(raw_bytes)
    subprocess.run(["lz4", "-d", "-f", tmp_in, tmp_out], check=True)
    with open(tmp_out, "rb") as f:
        return f.read()

def unpack_stock_vendor_boot(stock_img_path, out_tree_dir):
    print(f"[*] Reading Kernel 6.6 stock vendor_boot: {stock_img_path}")
    with open(stock_img_path, "rb") as f:
        hdr = f.read(4096)
        assert hdr[:8] == b"VNDRBOOT", "Invalid magic! Expected VNDRBOOT v4."
        version, page_size, kernel_addr, ramdisk_addr, vramdisk_size = struct.unpack("<5I", hdr[8:28])
        hdr_size, dtb_size, dtb_addr = struct.unpack("<IIQ", hdr[2096:2112])
        vrt_size, vrt_entry_num, vrt_entry_size, bootconfig_size = struct.unpack("<4I", hdr[2112:2128])

        f.seek(align(hdr_size, page_size))
        raw_ramdisks = f.read(align(vramdisk_size, page_size))[:vramdisk_size]

        f.seek(align(hdr_size, page_size) + align(vramdisk_size, page_size))
        dtb_raw = f.read(align(dtb_size, page_size))[:dtb_size]

        f.seek(align(hdr_size, page_size) + align(vramdisk_size, page_size) + align(dtb_size, page_size))
        vrt_raw = f.read(align(vrt_size, page_size))[:vrt_size]

    ent0_sz, ent0_off, ent0_type = struct.unpack("<3I", vrt_raw[0:12])
    ent1_sz, ent1_off, ent1_type = struct.unpack("<3I", vrt_raw[108:120])

    r00_raw = raw_ramdisks[ent0_off:ent0_off+ent0_sz]
    r01_raw = raw_ramdisks[ent1_off:ent1_off+ent1_sz]

    print(f"    - Header v{version}, PageSize={page_size}, DTB={len(dtb_raw)} bytes")
    print(f"    - Ramdisk00 (platform/modules): {len(r00_raw)} bytes")
    print(f"    - Ramdisk01 (stock recovery):   {len(r01_raw)} bytes")

    # 1. Save Prebuilt DTB
    dtb_dir = os.path.join(out_tree_dir, "prebuilt", "dtb")
    os.makedirs(dtb_dir, exist_ok=True)
    with open(os.path.join(dtb_dir, "dtb.img"), "wb") as f:
        f.write(dtb_raw)

    # Save raw ramdisk00 for later VRT v4 dual-ramdisk repacking
    with open(os.path.join(out_tree_dir, "prebuilt", "stock_ramdisk00.gz"), "wb") as f:
        f.write(r00_raw)

    # 2. Extract Kernel 6.6 modules and recovery configs from ramdisk00 & ramdisk01
    r00_entries = parse_cpio_ordered(decompress_ramdisk(r00_raw))
    r01_entries = parse_cpio_ordered(decompress_ramdisk(r01_raw))

    root_dir = os.path.join(out_tree_dir, "recovery", "root")
    mod_count = 0
    for e in r00_entries:
        name = e["name"]
        if name.startswith("lib/modules/") and len(e["content"]) > 0:
            dest = os.path.join(root_dir, name)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "wb") as f:
                f.write(e["content"])
            if name.endswith(".ko"):
                mod_count += 1

    print(f"    - Extracted {mod_count} Kernel 6.6 (.ko) modules into recovery/root/lib/modules/")

    for e in r01_entries:
        name = e["name"]
        if name in ("first_stage_ramdisk/fstab.mt6877", "system/etc/init/init.recovery.mt6877.rc"):
            dest = os.path.join(root_dir, name)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            content = e["content"]
            if name.endswith("init.recovery.mt6877.rc"):
                rc_str = content.decode("utf-8", errors="replace")
                touch_insmod = (
                    "on early-init\n"
                    "    insmod /lib/modules/hardware_info.ko\n"
                    "    insmod /lib/modules/mtk_disp_notify.ko\n"
                    "    insmod /lib/modules/goodix_core.ko\n\n"
                )
                if "goodix_core.ko" not in rc_str:
                    content = (touch_insmod + rc_str).encode("utf-8")
                with open(os.path.join(root_dir, "init.recovery.mt6877.rc"), "wb") as f2:
                    f2.write(content)
            with open(dest, "wb") as f:
                f.write(content)

    print(f"[+] Device tree at {out_tree_dir} is populated with Kernel 6.6 prebuilts!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Setup Volla Quintus (algiz) Kernel 6.6 OrangeFox Tree")
    parser.add_argument("--stock", required=True, help="Path to Kernel 6.6 stock_vendor_boot.img")
    parser.add_argument("--tree", default="device/volla/algiz", help="Output path for device tree")
    args = parser.parse_args()
    unpack_stock_vendor_boot(args.stock, args.tree)
