#!/usr/bin/env python3
"""Lookup helper for the 1.6.59 dump: method/field search + capstone disassembly.

RVA in dump.cs == ELF vaddr. Code sections are mapped with a uniform
file_offset = vaddr - 0x4000 (verified from readelf program headers).
"""
import os, re, sys
sys.path.insert(0, "/tmp/pylibs")

DUMP = "/tmp/dump"
SO = "/tmp/dump/apk/lib/arm64-v8a/libunity.so"
INDEX = os.path.join(DUMP, "methods.tsv")
FIELDS = os.path.join(DUMP, "fields.tsv")
DELTA = 0x4000

from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM

_md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
_md.detail = False

_so = open(SO, "rb")


def read(vaddr, n):
    off = vaddr - DELTA
    if off < 0 or off > os.path.getsize(SO):
        return None
    _so.seek(off)
    return _so.read(n)


def disasm(rva, n=10):
    if isinstance(rva, str):
        rva = int(rva, 16)
    data = read(rva, n * 4)
    if data is None:
        return "(out of range)"
    out = []
    for i in _md.disasm(data, rva):
        out.append("0x%X: %-8s %s" % (i.address, i.mnemonic, i.op_str))
    return "\n    ".join(out) if out else "(not code)"


def words(rva, n=4):
    if isinstance(rva, str):
        rva = int(rva, 16)
    data = read(rva, n * 4)
    return data.hex(" ") if data else ""


def load_methods():
    rows = []
    with open(INDEX) as f:
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) == 3:
                rows.append((int(p[0], 16), p[1], p[2]))
    return rows


ROWS = load_methods()


def find(pat, limit=40, cls=None, exact=False):
    rx = re.compile(pat, re.I)
    res = []
    for rva, c, s in ROWS:
        if (s == pat if exact else rx.search(s)) and (cls is None or re.search(cls, c, re.I)):
            res.append((rva, c, s))
            if limit and len(res) >= limit:
                break
    return res


def find_fields(pat, limit=40, cls=None):
    rx = re.compile(pat, re.I)
    res = []
    with open(FIELDS) as f:
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) == 3 and rx.search(p[2]) and (cls is None or re.search(cls, p[0], re.I)):
                res.append((p[0], p[1], p[2]))
                if limit and len(res) >= limit:
                    break
    return res


def show(rows, n=0):
    for rva, c, s in rows:
        print("0x%X\t%s\t%s" % (rva, c, s))
        if n:
            print("    " + disasm(rva, n).replace("\n", "\n    "))


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "m":
        pat = sys.argv[2]
        lim = int(sys.argv[3]) if len(sys.argv) > 3 else 40
        cls = sys.argv[4] if len(sys.argv) > 4 else None
        show(find(pat, lim, cls), int(sys.argv[5]) if len(sys.argv) > 5 else 0)
    elif mode == "exact":
        show(find(sys.argv[2], 20, sys.argv[3] if len(sys.argv) > 3 else None, exact=True),
             int(sys.argv[4]) if len(sys.argv) > 4 else 0)
    elif mode == "d":
        print(disasm(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 10))
    elif mode == "w":
        print(words(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 4))
    elif mode == "f":
        pat = sys.argv[2]
        lim = int(sys.argv[3]) if len(sys.argv) > 3 else 40
        cls = sys.argv[4] if len(sys.argv) > 4 else None
        for c, o, d in find_fields(pat, lim, cls):
            print("%s\t%s\t%s" % (c, o, d))
