
#Create mounts so things work
mount none -t proc /proc
mount none -t sysfs /sys
mount none -t devpts /dev/pts

#Required variables to make other things work
export HOME=/root
export LC_ALL=C

#Setup our apt repos to include universe for nvme-cli, python3-dialog
echo "deb http://archive.ubuntu.com/ubuntu bionic main universe" > /etc/apt/sources.list

#Install requirements
export DEBIAN_FRONTEND=noninteractive 
apt-get update -y
apt-get install hdparm pm-utils python3 python3-dialog nvme-cli python3-yaml linux-image-generic linux-firmware dbus casper lupin-casper discover laptop-detect ubuntu-standard linux-generic live-boot live-boot-initramfs-tools live-tools extlinux -y 

#Items we use just in the wrapper script
apt-get install curl dmidecode dstat chntpw -y 

useradd monitoring -s /opt/diskslaw/diskslaw.sh

# Set the root password?
echo 'root:pass' | chpasswd

#Make sure the initramfs is up to date
update-initramfs -u

#Hush the motd
touch /root/.hushlogin
touch /home/monitoring/.hushlogin

#Clean up
apt-get clean
rm -rf /tmp/*
umount /proc
umount /sys
umount /dev/pts

