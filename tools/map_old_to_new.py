#!/usr/bin/env python3
"""Map offsets from the 1.6.57 dump (what the old code targeted) to 1.6.59 RVAs.

old offset --(1.6.57 dump)--> class+method name --(1.6.59 dump)--> new RVA
"""
import re, sys, bisect, subprocess

def load(p):
    rows = []
    for line in open(p):
        q = line.rstrip("\n").split("\t")
        if len(q) == 3:
            rows.append((int(q[0], 16), q[1], q[2]))
    rows.sort()
    return rows

A = load("/tmp/idx57/methods.tsv")   # 1.6.57
B = load("/tmp/idx59/methods.tsv")   # 1.6.59
Arva = [r[0] for r in A]
Bname = {}
for rva, cls, sig in B:
    name = sig.split("(")[0].split()[-1]
    Bname.setdefault((cls, name), []).append((rva, sig))
Aexact = {}
for rva, cls, sig in A:
    Aexact.setdefault(rva, (cls, sig))

def owner(addr):
    """Return (class, signature, delta) for the method containing addr."""
    if addr in Aexact:
        return Aexact[addr][0], Aexact[addr][1], 0
    i = bisect.bisect_right(Arva, addr) - 1
    if i < 0:
        return None, None, None
    rva, cls, sig = A[i]
    return cls, sig, addr - rva

def consts(path):
    txt = subprocess.run(["git", "show", "HEAD:" + path], capture_output=True, text=True).stdout
    out = []
    for n, line in enumerate(txt.splitlines(), 1):
        for m in re.finditer(r"0x([0-9A-Fa-f]{6,8})", line):
            v = int(m.group(1), 16)
            if 0x100000 <= v <= 0x10000000:
                out.append((n, v, line.strip()))
    return out

for path in sys.argv[1:]:
    print("\n######## %s" % path)
    for n, v, line in consts(path):
        cls, sig, delta = owner(v)
        if cls is None:
            print("%-5d 0x%-9X (no 1.6.57 owner)  %s" % (n, v, line[:80]))
            continue
        name = sig.split("(")[0].split()[-1]
        cands = Bname.get((cls, name), [])
        where = "start" if delta == 0 else "+0x%X inside" % delta
        print("%-5d 0x%-9X %-58s %s" % (n, v, "%s::%s" % (cls, name), where))
        if not cands:
            print("        -> NO 1.6.59 MATCH for %s::%s" % (cls, name))
        for rva, s in cands:
            print("        -> 0x%-9X %s%s" % (rva, s, "" if len(cands) == 1 else "  [ambiguous]"))
