---
source_url: https://book.hacktricks.xyz/network-services-pentesting/pentesting-smb
license: HackTricks license (CC BY-NC-SA 4.0 style; keep attribution, no commercial redistribution)
tags: [smb, ms17-010, eternalblue, windows, remote-exploit]
---

# SMB / MS17-010 (EternalBlue)

MS17-010 is a remote code execution vulnerability in Microsoft's SMBv1 server,
exploited by the EternalBlue tool. It affects unpatched Windows systems from
Windows XP through Server 2016 (the most commonly targeted lab builds are
Windows 7 SP1 x64 and Server 2008 R2, since SMBv1 is enabled by default on
those).

Detection: scan with `nmap -p445 --script smb-vuln-ms17-010 <target>` or use
the Metasploit auxiliary scanner `auxiliary/scanner/smb/smb_ms17_010`.

Exploitation: `exploit/windows/smb/ms17_010_eternalblue` in Metasploit, or the
standalone EternalBlue/DoublePulsar tooling. A successful exploit yields a
SYSTEM-level shell with no authentication required.

Mitigation / patch: MS17-010 (March 2017); disable SMBv1 entirely where not
needed.
