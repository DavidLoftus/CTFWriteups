# pfSenseless - Box - 600 points - 2 solves
> So I found this prototype router. It doesn't do much besides to connect to the
> local network on a static IP (`192.168.147.1`). Makes sense given it's a
> prototype. However, I suspect there might be a flag hidden inside somewhere...
> 
> I've opened it up and connected a debugger to the serial port, when you connect
> to `192.168.147.2` on port `23` the debugger will release the reset line and
> boot the router. If for any reason the router resets, re-connect to the debugger
> and the router will boot back up.
> 
> The box it came in had a CD with a firmware upgrade tool and a sample firmware,
> maybe they'll be of some use.
> 
> _Note: You will need to set the MTU of the OpenVPN TAP interface to `1300` for
> this challenge to work correctly! If you're on Linux, OpenVPN will do this
> automatically. For Windows instructions, click
> [here](https://hamy.io/post/0004/openvpn-tap-adapter-mtu-in-windows/)_.

### Files
- [firmtool.exe](firmtool.exe)
- [pf_senseless_93c5c19e.fw](pf_senseless_93c5c19e.fw)

So I was one of 2 people to get this problem, yay for me.
We were given firmtool to perform the upgrade process but some mad man decided to give the tool to us as a python scripted packed into a PE file.
Rather than trying to extract the pyc file I simply ran the executable in a Windows VM and had Wireshark open to check what it was sending.
Turns out it sends a null byte followed by the selected file to the router at port 6969 (nice).
Great, I can do away with this firmtool and just do `(echo -ne "\x00" && cat file) | ncat 192.168.147.1 6969` when I want to trigger an upgrade.

So when I open up the serial debugger, I can see the OS start and all the logs. There's no shell this time. I can see what services it starts, avertiser (which I found is just so firmtool can find the ipadresss), dropbear (ssh server but can't login I never figured out why this was on it), and upgrade_server. When I trigger an upgrade the system shuts down and when I restart it, it begins the upgrade process. The logs tell me what its doing, it is unzipping some file upgrade.f2fs.gz and writing that to the raw storage device.

Lets divert our attention to the actual pf_senseless_93c5c19e.fw file. If we run `binwalk pf_senseless_93c5c19e.fw` we get this output
```
DECIMAL       HEXADECIMAL     DESCRIPTION
--------------------------------------------------------------------------------
12            0xC             gzip compressed data, maximum compression, from Unix, NULL date (1970-01-01 00:00:00)
9960121       0x97FAB9        gzip compressed data, maximum compression, from Unix, NULL date (1970-01-01 00:00:00)
```

So we have a 12 byte header and 2 gzip'd data. We can split the file into 3 chunks then: header, fw_1.gz, fw_2.gz
So lets unzip both of these `gzip -d fw_1.gz && gzip -d fw_2.gz`

We do some more binwalks and find fw_1 and fw_2 contain alot of files, if we run strings on fw_2 we can see alot of scripts though. The `upgrade.f2fs.gz` gives us a hint of what kind of file one of these is, f2fs is a kind of filesystem, so lets try mount them.

```sh
$ mkdir upgrade/
$ sudo mount -t f2fs fw_1 upgrade/
mount: pfsense/upgrade: wrong fs type, bad option, bad superblock on /dev/loop1, missing codepage or helper program, or other error.
$ sudo mount -t f2fs fw_2 upgrade/
```

Ok so fw_2 is upgrade.f2fs, hurray for better names, I was getting sick of those non-descriptive names anyway.

So now we have this filesystem mounted and we can see it pretty much contains an entire OS. Lets find that upgrade_server service:

```sh
upgrade$ ls
bin  dev  etc  lib  opt  proc  root  run  sbin  sys  tmp  usr  var
upgrade$ find . -name upgrade_server
find: ‘./root’: Permission denied
./usr/local/bin/upgrade_server
```

Alright more Ghidra time. Similar to `term_server` in [Nobody](../nobody/README.md) we have some socket code in main but the actual code is in handle_client. Here's the cleaned up decompiled output:

```c
fprintf(stderr, "connection from %s:%d\n", ip, port >> 0x10 & 0xffff);
msgIdBytesRead = recv(sock, &msgId, 1, 0);
if (msgIdBytesRead == 1) {
    if (msgId == 0) {
        magicBytesRead = recv(sock, &magic, 4, 0x100);
        if (magicBytesRead == 4) {
            magic = ntohl(magic);
            if (magic == 0x69420) {
                sizesBytesRead = recv(sock, sizes, 8, 0x100);
                if (sizesBytesRead == 8) {
                    initCodeSz = ntohl(sizes[0]);
                    upgradeCodeSz = ntohl(sizes[1]);
                    if ((initCodeSz < 0x4000001) && (upgradeCodeSz < 0x4000001)) {
                        if (initCodeSz != 0) {
                            initCode = malloc(initCodeSz);
                            initCodeBytesRead = recv(sock, initCode, initCodeSz, 0x100);
                            if (initCodeBytesRead != initCodeSz) {
                                perror("recv()");
                                goto LAB_001014b4;
                            }
                        }
                        if (upgradeCodeSz != 0) {
                            upgradeCode = malloc(upgradeCodeSz);
                            upgradeCodeBytesRead = recv(sock, upgradeCode, upgradeCodeSz, 0x100);
                            if (upgradeCodeBytesRead != upgradeCodeSz) {
                                perror("recv()");
                                goto LAB_001014b4;
                            }
                        }
                        if (initCode == (void *)0x0) {
                        LAB_001013d0:
                            if (upgradeCode == (void *)0x0) {
                            LAB_00101450:
                                fprintf(stderr, "%s:%d issued an upgrade, rebooting...\n", ip,
                                        port >> 0x10 & 0xffff);
                                free(upgradeCode);
                                free(initCode);
                                res_client(sock, '\0');
                                close(sock);
                                system("poweroff");
                                goto LAB_001014cc;
                            }
                            upgrade_fp = creat("/upgrade.f2fs.gz", 2);
                            if (upgrade_fp == 0xffffffff) {
                                perror("open()");
                                res_client(sock, '\x06');
                            }
                            else {
                                success = chunk_write(upgrade_fp, upgradeCode, (ulonglong)upgradeCodeSz);
                                if (success == true)
                                    goto LAB_00101450;
                                res_client(sock, '\x06');
                            }
                        }
                        else {
                            mmcblk0_fp = open("/dev/mmcblk0", 2);
                            if (mmcblk0_fp == 0xffffffff) {
                                perror("open()");
                                res_client(sock, '\x05');
                            }
                            else {
                                _success = chunk_write(mmcblk0_fp, initCode, (ulonglong)initCodeSz);
                                if (_success == true)
                                    goto LAB_001013d0;
                                res_client(sock, '\x05');
                            }
                        }
                    }
                    // Rest is just error handling
```

So the format of the file is: a 4 byte magic number 0x69420, the sizes of the 2 gzip files, then the two gzip files.
The second file is written to upgrade.f2fs but the first file is written directly to the start of the filesystem. So this part is actually executed when the machine boots.

Initially I tried just inserting a tcp reverse shell inside upgrade.f2fs, but at the point where the code in upgrade.f2fs is unpacked and executed, the upgrade code has already wiped all previous data from the sdcard. So we need to get the flag before the upgrade completes. That means tinkering with the first file, lets call it initram.

So we can see in the serial debugger that the upgrader is running some commands. Specifically ```sh
cp /newroot/upgrade.f2fs /tmp/
umount /newroot 
dd if=/dev/zero of=/dev/mmcblk1 bs=4k count=5096
zcat /tmp/upgrade.f2fs | dd of=/dev/mmcblk1
```

These scripts must be somewhere in the firmware, lets go exploring. We can try grep for it but we don't see it in plain text. If we binwalk initram we see a few compressed archives. We can extract them using `binwalk --dd 'gzip' initram`. The noteworthy archive is the one at the end of the file, `_initram.extracted/129CA48`, if we unzip this file we find an archive (specifically an ASCII cpio archive) of files including a file /init which contains our upgrade code, found it!

So now we just need to modify /init to run our code before the upgrade process occurs. After doing enough of these challenges it is pretty obvious the flag is either in /flag.txt or /run/secrets/flag.txt so I just modified the file to print both files out.

Then go back through the process of repacking the file, be careful to make sure the files are all the same. I had to remove code from the script to make space for my new code. These archives are heavily sensitive to changes in offset and if you forget to pad out your data to the original archive size you'll get kernel panicks before your code is even run.

But after many kernel panicks I managed to properly repack the firmware, (or atleast well enough such that it only panicked **after** it printed the flag!) Woo!

Oh if you were looking for the actual flag, sorry. The expensive servers running these instances were shutdown the day after the CTF ended. /:
There's plans of releasing the images of these instances, so if I can get them running on my local machine I can get some screenshots.