unset SKIPFS
unset REMOVEALL
unset USECUSTOMSCRIPT

while getopts "s:c::v:" opt; do
 case ${opt} in 
     s )
       SKIPFS=1
        ;;
     c )
       USECUSTOMSCRIPT=$OPTARG
       ;;
     v )
       VARIANT=$OPTARG
    esac
done

#Install prerequisites
sudo apt-get install syslinux squashfs-tools genisoimage debootstrap syslinux memtest86 -y

#Install base OS
if [ ! -d ds_root ]; then
    mkdir ds_root
    debootstrap bionic ds_root http://archive.ubuntu.com/ubuntu/
fi

#Chroot install script
cp build_chroot.sh ds_root/
chmod +x ds_root/build_chroot.sh

#Prepare networking in the chroot
cp /etc/hosts ds_root/hosts
cp /etc/resolv.conf ds_root/etc/resolv.conf


#Setup autologin on TTY1 and 2
mkdir -p ds_root/etc/systemd/system/getty@tty{1,2,3}.service.d
cp systemd/getty\@tty1.service ds_root/etc/systemd/system/getty@tty1.service.d/override.conf
cp systemd/getty\@tty1.service ds_root/etc/systemd/system/getty@tty2.service.d/override.conf
cp systemd/getty\@tty1.service ds_root/etc/systemd/system/getty@tty3.service.d/override.conf

#Enter chroot and build it
chroot ds_root bash "/build_chroot.sh"
rm ds_root/build_chroot.sh

#Setup root to autolaunch our diskslaw script
sed -i -e 's/root:\/bin\/bash/root:\/opt\/diskslaw\/diskslaw.sh/g' ds_root/etc/passwd
sed -i -e 's/#\?NAutoVTs=[0-9]\+/NAutoVTs=3/g' ds_root/etc/systemd/logind.conf
sed -i -e 's/#\?ReserveVT=[0-9]\+/#ReserveVT=3/g' ds_root/etc/systemd/logind.conf

#Disable lid switch action
sed -i -e 's/#\?HandleLidSwitch=[a-zA-Z]\+/HandleLidSwitch=ignore/g' ds_root/etc/systemd/logind.conf

#Copy over the scripts
cp ../diskslaw/ ds_root/opt/ -f -r

#If they want to provide their own script via network or use a variant script
if [ $USECUSTOMSCRIPT ]; then
    mv ds_root/opt/diskslaw/scripts/custom/diskslaw_custom.sh ds_root/opt/diskslaw/diskslaw.sh
elif [ $VARIANT ]; then
    cp ds_root/opt/diskslaw/scripts/${VARIANT}/* ds_root/opt/diskslaw/ -r
fi

chmod +x ds_root/opt/diskslaw/diskslaw.sh



#If we don't have the cd base, build it
if [ ! -e ds_cd_base/isolinux/isolinux.cfg ]; then
    mkdir ds_cd_base
    mkdir -p ds_cd_base/{casper,isolinux,install}
    cp ds_root/boot/vmlinuz* ds_cd_base/casper/vmlinuz
    cp ds_root/boot/initrd* ds_cd_base/casper/initrd.lz
    cp /usr/lib/ISOLINUX/isolinux.bin ds_cd_base/isolinux/
    cp /usr/lib/syslinux/modules/bios/ldlinux.c32 ds_cd_base/isolinux/
    cp /boot/memtest86+.bin ds_cd_base/install/memtest
    cp .disk ds_cd_base -r
    cp README.diskdefines ds_cd_base/
fi

#Always make sure we overwrite this in case we were dirty runs
cp isolinux/isolinux.cfg ds_cd_base/isolinux/

#Set the script it runs
if [ $USECUSTOMSCRIPT ]; then
    sed -i -e "s~casper initrd=~casper CUSTOM_SCRIPT=$USECUSTOMSCRIPT initrd=~g" ds_cd_base/isolinux/isolinux.cfg
fi

#Create the manifest
chroot ds_root dpkg-query -W --showformat='${Package} ${Version}\n' > ds_cd_base/casper/filesystem.manifest
sudo cp -v ds_cd_base/casper/filesystem.manifest ds_cd_base/casper/filesystem.manifest-desktop
REMOVE='ubiquity ubiquity-frontend-gtk ubiquity-frontend-kde casper lupin-casper live-initramfs user-setup discover1 xresprobe os-prober libdebian-installer4'
for i in $REMOVE
do
        sudo sed -i "/${i}/d" ds_cd_base/casper/filesystem.manifest-desktop
done


#Build the squashfs
if [ ! $SKIPFS ]; then 
    if [ -f ds_cd_base/casper/filesystem.squashfs ]; then
     rm ds_cd_base/casper/filesystem.squashfs
    fi
    mksquashfs ds_root ds_cd_base/casper/filesystem.squashfs -e boot
fi

(cd ds_cd_base && find . -type f -print0 | xargs -0 md5sum | grep -v "\./md5sum.txt" > md5sum.txt)


#Build the iso
if [ -f diskslaw.iso ]; then
    rm diskslaw.iso
fi
genisoimage -D -r -V "ds_cd_base" -cache-inodes -J -l -b isolinux/isolinux.bin -c isolinux/boot.cat -no-emul-boot -boot-load-size 4 -boot-info-table -o diskslaw.iso ds_cd_base/