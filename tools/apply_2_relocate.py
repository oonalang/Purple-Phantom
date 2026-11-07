#!/usr/bin/env python3
"""Authoritative relocation: HEAD (1.6.57 offsets) -> 1.6.59 RVAs.

Every hex constant is resolved through the 1.6.57 dump to a declared member,
then looked up in the 1.6.59 dump. Exact-signature matches win; a single
class+name match is accepted; anything ambiguous is left untouched and flagged.
"""
import re, sys, os, bisect, subprocess

def load(p):
    rows = []
    for line in open(p):
        q = line.rstrip("\n").split("\t")
        if len(q) == 3:
            rows.append((int(q[0], 16), q[1], q[2]))
    rows.sort()
    return rows

A = load("/tmp/idx57/methods.tsv")
B = load("/tmp/idx59/methods.tsv")
Arva = [r[0] for r in A]
Aex = {r[0]: (r[1], r[2]) for r in A}
B_exact, B_name = {}, {}
for rva, cls, sig in B:
    B_exact.setdefault((cls, sig), []).append(rva)
    B_name.setdefault((cls, sig.split("(")[0].split()[-1]), []).append((rva, sig))

stats = {"exact": 0, "byname": 0, "same": 0, "ambig": 0, "miss": 0, "inside": 0}
notes = []

def resolve(v):
    if v not in Aex:
        i = bisect.bisect_right(Arva, v) - 1
        if i < 0:
            return None, "unowned"
        rva, cls, sig = A[i]
        if v - rva > 0x100:
            return None, "unowned"
        stats["inside"] += 1
        notes.append("MID-FUNCTION 0x%X in %s::%s+0x%X" % (v, cls, sig.split("(")[0].split()[-1], v - rva))
        return None, "inside"
    cls, sig = Aex[v]
    name = sig.split("(")[0].split()[-1]
    if len(B_exact.get((cls, sig), [])) == 1:
        stats["exact"] += 1
        return B_exact[(cls, sig)][0], "exact"
    cands = B_name.get((cls, name), [])
    if len(cands) == 1:
        stats["byname"] += 1
        return cands[0][0], "byname"
    if len(cands) > 1:
        stats["ambig"] += 1
        notes.append("AMBIGUOUS 0x%X %s::%s -> %s" %
                     (v, cls, name, ", ".join("0x%X" % c[0] for c in cands)))
        return None, "ambiguous"
    stats["miss"] += 1
    notes.append("NO 1.6.59 MATCH 0x%X %s::%s" % (v, cls, name))
    return None, "missing"

def migrate(path, text):
    def sub(m):
        v = int(m.group(1), 16)
        if not (0x100000 <= v <= 0x10000000):
            return m.group(0)
        new, why = resolve(v)
        if new is None:
            if why == "unowned":
                stats["same"] += 1
            return m.group(0)
        if new == v:
            stats["same"] += 1
        return "0x%X" % new
    return re.sub(r"0x([0-9A-Fa-f]{6,8})\b", sub, text)

os.makedirs("/tmp/mig", exist_ok=True)
for path in sys.argv[1:]:
    txt = subprocess.run(["git", "show", "HEAD:" + path], capture_output=True, text=True).stdout
    out = migrate(path, txt)
    dst = os.path.join("/tmp/mig", os.path.basename(path))
    open(dst, "w").write(out)
    print("wrote %s" % dst)

print("\nstats: %s" % stats)
for n in notes:
    print("  " + n)
