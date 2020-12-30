#!/bin/bash

# Remount filesystems as read only
mount / -o remount,rw
mount /boot -o remount,rw

# Save old disk ID
OLD_DISKID=$(fdisk -l /dev/mmcblk0 | sed -n 's/Disk identifier: 0x\([^ ]*\)/\1/p')

# Backup data partition
mkdir /tmp/tempdata
cp -a /mnt/data /tmp/tempdata
umount /mnt/data/

# Delete data partition
parted /dev/mmcblk0 rm 3

# Resize root partition to 90% of available space
parted -m /dev/mmcblk0 resizepart 2 90%

# Recreate data partition to the rest 10% of space
START=$(parted -m /dev/mmcblk0 print free|tail -n 1|cut -d : -f 2)
parted -m /dev/mmcblk0 mkpart primary ext4 $START 100%

# Reread data partition table
partprobe /dev/mmcblk0

# Recreate filesystem on data partition
mkfs.ext4 -F /dev/mmcblk0p3

# Grab new disk ID
DISKID=$(fdisk -l /dev/mmcblk0 | sed -n 's/Disk identifier: 0x\([^ ]*\)/\1/p')

# Replace new disk ID with old
sed -i "s/${OLD_DISKID}/${DISKID}/g" /etc/fstab
sed -i "s/${OLD_DISKID}/${DISKID}/" /boot/cmdline.txt

# Resize root filesystem to fill new partition size
resize2fs -f /dev/mmcblk0p2

