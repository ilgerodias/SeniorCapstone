# Lab targets

Owner: Andres · Status: shortlist drafted, needs your download + checksum
verification (see "still on you" below) and a team decision on the
EternalBlue fallback.

## Shortlist — 3 Linux VulnHub VMs, increasing difficulty

| # | VM | Exposes | Vuln → path | Difficulty |
|---|---|---|---|---|
| 1 | **Kioptrix: Level 1** | SSH 22 (OpenSSH 2.9p2), HTTP 80 / HTTPS 443 (Apache 1.3.20 + mod_ssl 2.8.4), Samba 139 (Samba 2.2.1a), rpcbind 111 | Two independent root paths: (a) Samba `trans2open` buffer overflow on 139 → direct root shell (Metasploit `exploit/linux/samba/trans2open`), or (b) mod_ssl 2.8.4 OpenFuck exploit on 443 → root via ptrace. Good "recon → vuln-ID → suggested module" case because there are two valid modules to choose between. | Beginner — classic first VulnHub box, all-service-version-based, no web-app logic needed. |
| 2 | **DC: 1** | SSH 22, HTTP 80, RPC 111 | Outdated Drupal (7.22–7.26) → Drupalgeddon2 RCE (CVE-2018-7600) → shell as `www-data` → SUID `find` binary (GTFOBins) → root. Good case for the agent chaining a web-CVE step into a classic Linux-privesc step. | Easy, one step up from Kioptrix — needs CVE identification from a CMS version, not just a stock Metasploit module. |
| 3 | **VulnOS v2** | SSH 22, HTTP 80, IRC 6667 | Hidden path exposes OpenDocMan; version is SQL-injectable → sqlmap dumps `odm_user` → recovered `webmin` credential hash → SSH login → overlayfs kernel exploit → root. | Intermediate — multi-stage (web recon → SQLi → credential cracking → kernel exploit), good test of whether the agent can chain 3+ distinct vuln classes instead of hitting one obvious hole. |

Recon → vuln → module mapping for each is in the table above; expand into
your own doc per-target once you've actually run each box, since the real
value for the eval is the agent's actual recon output vs. this expected path.

**Still on you:** VulnHub serves downloads from a site my tools can't fetch
(robots-disallowed), so I can't pull the exact current image filenames/MD5s
myself. When you download each VM from vulnhub.com, copy the filename and
the MD5/SHA1 hash VulnHub lists on the entry page into this table — that's
the "record exact image names, checksums" part of your ticket.

## EternalBlue / MS17-010 target — the critical-path item

**Finding: there is no current, actively-hosted VulnHub VM built specifically
around MS17-010/EternalBlue.** I searched VulnHub-focused sources
specifically for this and found nothing — the well-known "exploit MS17-010
for practice" boxes (e.g. "Blue") are **HackTheBox/TryHackMe**, not VulnHub,
and those platforms are outside your locked lab stack (VulnHub + Kali,
self-hosted). I did not find a VulnHub entry that ships SMBv1/MS17-010
out of the box.

**Recommendation: don't spend more time hunting for a VulnHub image — go
straight to the fallback build**, which the task list already anticipated:

1. **Source a Windows 7 SP1 x64 (or Server 2008 R2) ISO legitimately** — a
   licensed copy you/the team already has access to (e.g. a university
   MSDN/Azure Dev Tools subscription, if your program has one) is the clean
   path; avoid pulling an ISO from an untrusted third-party mirror for a lab
   machine that will run unpatched and network-exposed.
2. **Install it and do not apply Windows Update** — SMBv1 is enabled by
   default on Windows 7/Server 2008 R2 and MS17-010 (the March 2017 patch)
   must specifically be withheld. Disconnect the install VM from any network
   with internet access before first boot, or disable Windows Update
   immediately after install, to avoid auto-patching.
3. **Confirm vulnerability before building the rest of the lab around it:**
   from the Kali host, `nmap -p445 --script smb-vuln-ms17-010 <target>` or
   Metasploit's `auxiliary/scanner/smb/smb_ms17_010` should report
   vulnerable. If the box doesn't fire, don't dig into obscure manual-patch
   registry tricks — that's a sign to pull a different Win7 build rather
   than lose time debugging one.
4. **Snapshot immediately once confirmed vulnerable**, before any further
   changes — this is Joshua's "add the EternalBlue target once Andres
   confirms the image or build; snapshot it" step, so hand this off to him
   right after step 3 passes.
5. Keep SMBv1 enabled (default) and open 445 in Windows Firewall inbound;
   you do **not** need to disable the firewall/Defender entirely for the
   exploit to work.

This gates only the exploit-chain demo — per the task list, recon and
vuln-ID development on the Linux targets above are not blocked on this, so
it doesn't need to happen before everything else, just before the final
week.
