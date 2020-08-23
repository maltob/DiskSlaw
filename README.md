# DiskSlaw
DiskSlaw is a tool for mass wiping of disks whether they be mechanical or solid state.

#### This project is archived, I no longer have the hardware to maintain and test the various hardware configurations.
#### If the drive secure erase fails, you may end up with a difficult to boot system that will ask for a password.

### Motivation
I wanted a solution that would: 
 * Use the most appropriate wiping method for a media
 * Worked across manufacturers
 * Could be booted from USB and not wipe its own USB
 * Once setup was relatively easy to use
 * Was customizable to allow automated reporting

 Existing solutions forced either :
  * Only wrote random data to the drive, this is not the preferred method to wipe solid state media
  * Only worked on drives made by the same manufacturer
  * Required booting into a Linux distro and running the commands manually

#### Features
 * Parallel wiping if multiple disks exist
 * Quick validation that the disk was wiped by placing a string on the disk thrice and ensuring it was removed
 * ISO Built on Ubuntu 18.04 Bionic for hardware support
 * Selects the correct wipe type for a disk
   * NVMe Secure Erase using nvme-cli on NVMe disks
   * SATA Secure Erase on Disks that support it (Typically SSDs)
     * Detects if the drive is "frozen" by the OS and will enter sleep mode to unfreeze it
   * Shred using Random or Zeros if none of the above are supported
 * Configurable
    * Skip certain devices - Defaults to skipping USB and removable devices
    * Erase type can be changed
    * Can launch custom wrapper script over http/https using CUSTOM_SCRIPT kernel argument
      * Requires use of the custom_script ISO
      * Custom script can inject CSV report to send along to documentation system or notification
 

### Screenshots
##### Wiping Screen
![Screenshot of wiping progress bar](https://github.com/maltob/DiskSlaw/raw/master/img/Wiping_Progress.png)
##### Results Screen - With Fallback
 The NVMe drive shows a warning because VirtualBox doesn't emulate NVMe format so it fell back to using shred
![Screenshot of results panel](https://github.com/maltob/DiskSlaw/raw/master/img/VirtualBox_TestWipe.png)

## Quick Start
Overview of use

#### ISO
 1) Download ISO from releases
 2) Burn ISO to disk
 3) Boot the flash drive by using F12/F10 to select it from the boot menu on the PC you would like to wipe

#### USB
 1) Download the ISO from releases
 2) Use a tool such as [RUFUS](https://rufus.ie/) or [YUMI](https://www.pendrivelinux.com/yumi-multiboot-usb-creator/) to create a bootable flash drive by pointing to the ISO
 3) Boot the flash drive by using F12/F10 to select it from the boot menu on the PC you would like to wipe

 #### Network - iPXE
 Using iPXE is recommended due to the download being over half a gigabit.
 See [Setting Up Network boot on a Linux Server](https://github.com/maltob/DiskSlaw/wiki/Setting-up-network-boot-on-a-Linux-Server) on the Wiki for a step by step guide
  1) Configure the DHCP scope to boot ipxe - See instructions from ipxe.org [Chainloading iPXE on ipxe.org](https://ipxe.org/howto/chainloading)
  2) Download the ISO from releases
  3) Extract or mount the ISO
  4) Copy the filesystem.squashfs vmlinuz, and initrd from our disk (v0.3-alpha) or higher
    4.1. If you use Microsoft IIS as your web server you will need to add ".squashfs" and "." as a MIME type of "application/octet-stream" 
   5) Create an iPXE script like below to boot the disk 
   (WARNING : It will autoamtically wipe without further input unless there is a frozen SSD)
   ```
    #!ipxe
    kernel http://<WEBSERVER>/vmlinuz
    initrd http://<WEBSERVER>/initrd.lz
    imgargs vmlinuz boot=live dhcp fetch=http://<WEBSERVER>/casper/filesystem.squashfs nouveau.modeset=0 nomodeset --
    boot
   ```
