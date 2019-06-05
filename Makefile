OS = DEBIAN
DEBIAN_PACKAGE_INSTALL_COMMAND = sudo apt-get install syslinux squashfs-tools genisoimage debootstrap syslinux memtest86 -y 

ISONAME = wipedisk.iso
DEBOOTSTRAP_OS = bionic
DEBOOTSTRAP_SOURCE = http://archive.ubuntu.com/ubuntu/
CHROOT_DIR = build/ds_chroot
CD_BUILD_DIR = build/ds_iso_build
DEBOOTSTRAP_CACHE_DIR = /tmp/debootcache

DEBOOTSTRAP_OPTIONS?= --no-check-certificate --cache-dir=/tmp/debootcache

.RECIPEFIX =  

all: $(CHROOT_DIR)/opt/diskslaw $(ISONAME)

.PHONY: clean


pre_reqs: 
	$($(OS)_PACKAGE_INSTALL_COMMAND)

$(CHROOT_DIR) : pre_reqs
	mkdir -p $(CHROOT_DIR)

$(DEBOOTSTRAP_CACHE_DIR):
	mkdir $(DEBOOTSTRAP_CACHE_DIR)

$(CHROOT_DIR)/debootstrap/: $(CHROOT_DIR) $(DEBOOTSTRAP_CACHE_DIR)
	-debootstrap $(DEBOOTSTRAP_OPTIONS) $(DEBOOTSTRAP_OS) $(CHROOT_DIR) $(DEBOOTSTRAP_SOURCE) 

$(CHROOT_DIR)/sbin/hdparm: $(CHROOT_DIR)/debootstrap/
	cp build/build_chroot.sh $(CHROOT_DIR)/
	chmod +x $(CHROOT_DIR)/build_chroot.sh
	cp /etc/hosts $(CHROOT_DIR)/hosts
	cp /etc/resolv.conf $(CHROOT_DIR)/etc/resolv.conf
	chroot $(CHROOT_DIR) "/build_chroot.sh"
	rm $(CHROOT_DIR)/build_chroot.sh

$(CHROOT_DIR)/etc/systemd/system/getty@tty1.service.d/override.conf: $(CHROOT_DIR)/sbin/hdparm
	mkdir -p $(CHROOT_DIR)/etc/systemd/system/getty@tty1.service.d
	cp build/systemd/getty\@tty1.service $(CHROOT_DIR)/etc/systemd/system/getty@tty1.service.d/override.conf
	sed -i -e 's/root:\/bin\/bash/root:\/opt\/diskslaw\/diskslaw.sh/g' $(CHROOT_DIR)/etc/passwd
	sed -i -e 's/#NAutoVTs=6/NAutoVTs=2/g' $(CHROOT_DIR)/etc/systemd/logind.conf
	sed -i -e 's/#ReserveVT=6/#ReserveVT=2/g' $(CHROOT_DIR)/etc/systemd/logind.conf

$(CHROOT_DIR)/opt/diskslaw: $(CHROOT_DIR)/etc/systemd/system/getty@tty1.service.d/override.conf
	cp diskslaw/ $(CHROOT_DIR)/opt/diskslaw/ -r
	chmod +x $(CHROOT_DIR)/opt/diskslaw/diskslaw.sh



$(CD_BUILD_DIR):
	mkdir $(CD_BUILD_DIR)

$(CD_BUILD_DIR)/README.diskdefines: $(CD_BUILD_DIR)
	bash -c "mkdir -p $(CD_BUILD_DIR)/{casper,isolinux,install}"
	cp $(CHROOT_DIR)/boot/vmlinuz* $(CD_BUILD_DIR)/casper/vmlinuz
	cp $(CHROOT_DIR)/boot/initrd* $(CD_BUILD_DIR)/casper/initrd.lz
	cp /usr/lib/ISOLINUX/isolinux.bin $(CD_BUILD_DIR)/isolinux/
	cp /usr/lib/syslinux/modules/bios/ldlinux.c32 $(CD_BUILD_DIR)/isolinux/
	cp /boot/memtest86+.bin $(CD_BUILD_DIR)/install/memtest
	cp build/isolinux/isolinux.cfg $(CD_BUILD_DIR)/isolinux/
	cp build/.disk $(CD_BUILD_DIR) -r
	cp build/README.diskdefines $(CD_BUILD_DIR)/

$(CD_BUILD_DIR)/casper/filesystem.manifest-desktop: $(CHROOT_DIR)/opt/diskslaw
	chroot $(CHROOT_DIR) dpkg-query -W --showformat='${Package} ${Version}\n' | sudo tee $(CD_BUILD_DIR)/casper/filesystem.manifest
	sudo cp -v $(CD_BUILD_DIR)/casper/filesystem.manifest $(CD_BUILD_DIR)/casper/filesystem.manifest-desktop
	bash -c for i in 'ubiquity ubiquity-frontend-gtk ubiquity-frontend-kde casper lupin-casper live-initramfs user-setup discover1 xresprobe os-prober libdebian-installer4' \
	do \
		sudo sed -i "/$${i}/d" $(CD_BUILD_DIR)/casper/filesystem.manifest-desktop \
	done


$(CD_BUILD_DIR)/casper/filesystem.squashfs: $(CHROOT_DIR)/opt/diskslaw
	mksquashfs $(CHROOT_DIR) $(CD_BUILD_DIR)/casper/filesystem.squashfs -e boot -noappend

$(CD_BUILD_DIR)/md5sum.txt: $(CD_BUILD_DIR)/casper/filesystem.squashfs $(CD_BUILD_DIR)/casper/filesystem.manifest-desktop
	(cd $(CD_BUILD_DIR ) && find . -type f -print0 | xargs -0 md5sum | grep -v "\./md5sum.txt" > md5sum.txt)

$(ISONAME): $(CD_BUILD_DIR)/README.diskdefines $(CD_BUILD_DIR)/casper/filesystem.squashfs $(CD_BUILD_DIR)/casper/filesystem.manifest-desktop $(CD_BUILD_DIR)/md5sum.txt
	genisoimage -D -r -V "$(CD_BUILD_DIR)" -cache-inodes -J -l -b isolinux/isolinux.bin -c isolinux/boot.cat -no-emul-boot -boot-load-size 4 -boot-info-table -o $(ISONAME) $(CD_BUILD_DIR)/

clean:
	rm -rf $(CD_BUILD_DIR)
	rm -rf $(CHROOT_DIR)
	rm -f $(ISONAME)