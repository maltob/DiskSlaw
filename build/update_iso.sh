cp src/DiskSlaw/diskslaw*.py diskslaw/opt/diskslaw/
cp src/DiskSlaw/diskslaw.sh diskslaw/usr/bin/
rm filesystem.squashfs && mksquashfs diskslaw filesystem.squashfs -e boot && cp filesystem.squashfs cd/casper/filesystem.squashfs
rm wipe.iso && genisoimage -D -r -V "cd" -cache-inodes -J -l -b isolinux/isolinux.bin -c isolinux/boot.cat -no-emul-boot -boot-load-size 4 -boot-info-table -o wipe.iso cd/