---
source_url: https://book.hacktricks.xyz/linux-hardening/privilege-escalation
license: HackTricks license (CC BY-NC-SA 4.0 style; keep attribution, no commercial redistribution)
tags: [linux, privesc, suid, gtfobins]
---

# Linux SUID Binary Privilege Escalation

SUID binaries run with the file owner's permissions rather than the invoking
user's. If a SUID binary owned by root can be abused to read files, write
files, or spawn a shell, a low-privilege user can escalate to root.

Enumeration: `find / -perm -4000 -type f 2>/dev/null` lists all SUID binaries
on the system. Cross-reference each result against GTFOBins
(https://gtfobins.github.io/) for a known privilege-escalation technique.

Common abusable binaries: `find`, `vim`, `nmap` (older versions with
`--interactive`), `cp`, `python` with SUID set are all documented on
GTFOBins with ready-made one-liners.
