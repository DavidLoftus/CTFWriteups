# Nobody - Box - 400 points - 15 solves
> I made this cool terminal server that you can log on to with `netcat` on port 23.
> I keep my flag on the server too, but thanks to Unix permissions you won't be
> able to read it. :D
> 
> You can find the server at `192.168.144.1`.

In this challenge we have shell access to a machine but our user is nobody and as such we have no permissions to read the flag (at /flag.txt) which is owned by root. But we still have a shell, so lets start to investigate.

When we run `uname -a` we can see that we are running Alpine Linux, which is just a small linux disto used for lightweight containers like this. We can start looking at the available binaries, maybe there is a custom command we can run. If we `ls -l /bin` we see alot of the core files are just symbolic links to busybox, pretty sure we aren't meant to be hacking busybox so I can safely ignore these commands.

I found one single binary in /usr/local/bin called term_server. This is the program running the shell we are using. I base64 encoded the binary so I could copy it onto my machine, and then opened it up in Ghidra. The main file was simply listening for socket connections, once a socket connects it is passed to `handle_client`. The decompiled output looks pretty ugly so here is the cleaned up version of the important bits:
```c
fprintf(stderr,"connection from %s:%d\n",addr,port);
pid_t pid = fork();
if (pid == -1) {
    perror("fork()");
} else if (pid == 0) {
    if (setgroups(0,NULL) == -1) {
        perror("setgroups()");
    }
    if (setgid(0xfffe) == -1) {
        perror("setgid()");
    }
    if (seteuid(0xfffe) == -1) {
        perror("setuid()");
    }
    if (dup2(sock,0) == -1) {
        perror("stdin dup2()");
    } else {
        if (dup2(sock,1) == -1) {
        perror("stdout dup2()");
        } else {
            if (dup2(sock,2) == -1) {
                perror("stderr dup2()");
            } else {
                close(sock);
                execlp("/bin/sh","/bin/sh",&DAT_0010207e,0);
                perror("exec()");
            }
        }
    }
}
```

You might notice that there is a difference between the perror message and the called function for `setuid()`. Instead of calling setuid(0xfffe) it instead calls seteuid(0xfffe). This process is being run as root, so in order to remove our permissions it sets our **effective** UID to nobody but it never sets our **actual** uid to nobody. Thus we should still actually have root as our uid.

We can confirm this by typing the command `id` which says that `uid=0(root) euid=65534(nobody) gid=65534(nobody)`, perfect!
But what can we do with this? When you setuid to nobody, it is an irreversible action, you cannot use setuid to raise your privaledge level, only lower it. But thats not the same with euid, this is not meant to be used for security, instead its used for when you don't want to accidently overwrite any root files. seteuid can easily be reversed by calling seteuid(0)

Now maybe some Unix/Bash efficienado might know how to do seteuid purely from shell but I had no clue. So I had to resort to good old C syscalls. I wrote this [very small C file](seteuid.c) to call `setuid(0)` followed by whatever command I wrote in the arguments.

I did face some issues running this code on the machine though...
- There was no compiler, oof. No bother the architecture is amd64 so I can compile it on my machine and copy it over using the same base64 method.
- I can't write to the filesystem because my user is nobody. Drat! Oh wait I can still create files in /tmp/ since its temporary
- The shell won't execute files in /tmp. This is not going well.
Then after a bunch of trial and error, and alot of googling I found that you can actually execute ELF files using ld-linux.so, don't ask me how that works, I just accepted it and carried on.
`/lib/ld-linux.so /tmp/seteuid cat /flag.txt`

Oh if you were looking for the actual flag, sorry. The expensive servers running these instances were shutdown the day after the CTF ended. /: