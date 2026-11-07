#!/usr/bin/env python3
"""Parse an Il2CppDumper dump.cs into searchable indexes.

Outputs (next to the dump):
  methods.tsv : rva \t class \t signature
  fields.tsv  : class \t offset \t declaration
"""
import re, sys, os

path = sys.argv[1]
outdir = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(path)

ns = ""
cls = ""
kind = ""
meth = open(os.path.join(outdir, "methods.tsv"), "w")
fld = open(os.path.join(outdir, "fields.tsv"), "w")

re_ns = re.compile(r"^// Namespace: (.*)$")
re_cls = re.compile(r"^(?:public |internal |private )?(?:sealed )?(?:abstract )?(?:static )?(?:partial )?(class|struct|interface|enum) ([A-Za-z0-9_<>.`,]+)")
re_kind = re.compile(r"^\s*// (Fields|Properties|Methods|Events)")
re_rva = re.compile(r"^\s*// RVA: (0x[0-9A-Fa-f]+)")
re_field = re.compile(r"^\s*(?:public|private|protected|internal|static|readonly|const|volatile|\s)+[^;{}=]+?\s([A-Za-z_][A-Za-z0-9_]*);\s*//\s*(0x[0-9A-Fa-f]+|-?\d+)")

pending_rva = None
cls_full = ""

with open(path, "r", errors="replace") as f:
    for line in f:
        m = re_ns.match(line)
        if m:
            ns = m.group(1).strip()
            if ns == "": ns = ""
            continue
        m = re_cls.match(line)
        if m:
            cls = m.group(2)
            cls_full = (ns + "." + cls) if ns else cls
            continue
        if re_kind.match(line):
            kind = re_kind.match(line).group(1)
            continue
        m = re_rva.match(line)
        if m:
            pending_rva = m.group(1)
            continue
        if pending_rva is not None:
            sig = line.strip()
            if sig:
                meth.write("%s\t%s\t%s\n" % (pending_rva, cls_full, sig))
                pending_rva = None
            continue
        if kind == "Fields":
            m = re_field.match(line)
            if m:
                fld.write("%s\t%s\t%s\n" % (cls_full, m.group(2), line.strip()))

meth.close(); fld.close()
print("done")
