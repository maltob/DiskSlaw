# DiskSlaw
DiskSlaw is a tool for mass wiping of disks whether they be mechanical or solid state.

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
 TODO : Clean up below
  1) Configure the DHCP scope to boot ipxe - See instructions from ipxe.org [Chainloading iPXE on ipxe.org](https://ipxe.org/howto/chainloading)
  2) Download the ISO from releases
  3) Extract or mount the ISO
  4) Copy the filesystem.squashfs, vmlinuz, and initrd to a web server
    4.1. If you use Microsoft IIS as your web server you will need to add ".squashfs" and "." as a MIME type of "application/octet-stream" 
   5) Create an iPXE script like below to boot the disk 
   (WARNING : It will autoamtically wipe without further input unless there is a frozen SSD)
   ```
    #!ipxe
    dhcp
    kernel http://<WEBSERVER>/vmlinuz dhcp boot=live fetch=http://<WEBSERVER>/webserver.squashfs
    initrd http://<WEBSERVER>/initrd
    boot
   ```
