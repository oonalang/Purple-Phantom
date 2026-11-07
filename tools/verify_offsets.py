#!/usr/bin/env python3
"""Verify every relocated RVA against Dump 1.6.59.cs method index."""
import re, bisect, os

INDEX = os.environ.get("METHODS_TSV", "/tmp/idx59/methods.tsv")
rows = []
with open(INDEX) as f:
    for line in f:
        p = line.rstrip("\n").split("\t")
        if len(p) == 3:
            rows.append((int(p[0], 16), p[1], p[2]))
RVAS = sorted(r[0] for r in rows)
NAME = {}
for rva, cls, sig in rows:
    NAME.setdefault(rva, "%s::%s" % (cls, sig))

FILES = [
    "src/main/jni/Hacks/StructGame/Defines.h",
    "src/main/jni/Main.cpp",
    "src/main/jni/Hacks/Feature/SkinHaxSystem.h",
    "src/main/jni/Hacks/Feature/MythicAttachmentSystem.h",
]
hexre = re.compile(r"0x([0-9A-Fa-f]{5,})")
ok = missing = 0
print("== offsets that are NOT a method start in the 1.6.59 dump ==")
for path in FILES:
    for n, line in enumerate(open(path, encoding="utf-8", errors="replace"), 1):
        for m in hexre.finditer(line):
            v = int(m.group(1), 16)
            if v < 0x10000 or v > 0xF710000:
                continue
            if v in NAME:
                ok += 1
            else:
                missing += 1
                print("%-52s:%-4d 0x%X  | %s" % (path.split("/")[-1], n, v, line.strip()[:110]))

print("\n== patch sites: bytes available before the next method ==")
patchre = re.compile(r'createWithHex\(\s*"libunity.so"\s*,\s*(0x[0-9A-Fa-f]+)\s*,\s*"([0-9A-Fa-f ]+)"')
for n, line in enumerate(open("src/main/jni/Main.cpp", encoding="utf-8", errors="replace"), 1):
    m = patchre.search(line)
    if not m:
        continue
    addr = int(m.group(1), 16)
    nbytes = len(m.group(2).split())
    i = bisect.bisect_left(RVAS, addr)
    nxt = RVAS[i] if i < len(RVAS) and RVAS[i] != addr else (RVAS[i + 1] if i + 1 < len(RVAS) else addr + 0x100)
    gap = nxt - addr
    flag = "OK " if gap >= nbytes else "SHORT"
    print("%s line %-5d 0x%-8X writes %2d bytes, %3d available -> %s" %
          (flag, n, addr, nbytes, gap, NAME.get(addr, "(not a method start)")))

print("\nchecked ok=%d not-a-method-start=%d" % (ok, missing))
