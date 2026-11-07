#!/usr/bin/env python3
"""Apply the corrective edits on top of the 1.6.57->1.6.59 relocation."""
import re, sys

def must(cond, msg):
    if not cond:
        print("FAILED: " + msg); sys.exit(1)

# ---------------- Main.cpp ----------------
p = "/tmp/mig/Main.cpp"
s = open(p).read()
orig = s

# 1. stale "//AUTO ON" hooks: duplicates of the [System] block, wrong addresses in 1.6.57 too
for bad, intent in [("0x91BD4B4", "TutorialManager::IsTutorialEnabled"),
                    ("0x6BBD97C", "SystemSetting::get_EnableVulkan"),
                    ("0x4E75F58", "EmulatorManager::IsEmulator")]:
    line = [l for l in s.splitlines() if bad in l]
    must(len(line) == 1, "expected one line with " + bad)
    s = s.replace(line[0] + "\n", "")

s = s.replace("//AUTO ON",
              "// AUTO ON: the three stale hooks that used to sit here targeted the wrong\n"
              "\t// functions in 1.6.57 as well (UI/iterator bodies, not the intended\n"
              "\t// TutorialManager/SystemSetting/EmulatorManager members). The correct\n"
              "\t// equivalents live in the [System] block below.")

# 2. hooks whose 1.6.57 address was mid-function -> resolved by declared intent
must("0x904DD18" in s, "NeedDelayProcess hook missing")
s = s.replace("0x904DD18", "0x5366558")     # GameBase.ObserverDelayManager::NeedDelayProcess
must("0x9BDBBA8" in s, "slide tackle accel hook missing")
s = s.replace("0x9BDBBA8", "0x54F756C")     # GameBase.Weapon::get_SlideTackleAcclerationSpeed

# 3. Patches.outline: the old pair pointed inside TEDAct UI cell views (not IsEffectActive).
old_out = [l for l in s.splitlines() if "Patches.outline" in l]
must(len(old_out) == 2, "expected two Patches.outline lines, got %d" % len(old_out))
s = s.replace(old_out[0] + "\n", "")
s = s.replace(old_out[1],
              "\t// 1.6.57's outline pair pointed inside TEDAct.TEDActMainUIController::Init and\n"
              "\t// TEDAct.TEDActAwardFGCellView::SetData (+0x1E4/+0x5C), neither is IsEffectActive.\n"
              "\t// Intent (the old comment) is the see-front outline effect; only one field exists,\n"
              "\t// so the duplicate assignment is gone and the survivor is the real getter.\n"
              "\tPatches.outline = MemoryPatch::createWithHex(\"libunity.so\",0xB18EE4C,\"20 00 80 D2 C0 03 5F D6\");"
              "// EffectInstance_SeeFront::IsEffectActive")

# 4. patches that were inline writes inside a method: only StopShowEffect has a safe
#    entry-level equivalent (void -> skip body). The rest are dropped, not guessed.
repl = {
    'patchOffset("libunity.so", 0x8835A60, "00 00 80 D2 C0 03 5F D6", checkboxStates["extreme"]);':
    '\t// 1.6.57 wrote at StopShowEffect+0xC; the method is void, so skipping its body\n'
    '\t// from the entry is the same observable behaviour.\n'
    '\tpatchOffset("libunity.so", 0x758F0B4, "00 00 80 D2 C0 03 5F D6", checkboxStates["extreme"]);'
    ' // BRVehicleShowEffectBase::StopShowEffect',
    'patchOffset("libunity.so", 0x8847A40,"20 00 80 D2 C0 03 5F D6", checkboxStates["anti"]);':
    '\t// [1.6.59] was <GetPerk>c__Iterator0::MoveNext+0x78C - an inline write into a state\n'
    '\t// machine. No safe entry-level equivalent; needs a manual offset. Disabled.',
    'patchOffset("libunity.so", 0x91C3010, "1F 20 03 D5 E0 03 13 AA", checkboxStates["wallhack"]);':
    '\t// [1.6.59] was <PrintDialog>c__Iterator0::MoveNext+0x1A0 - not a visibility path at\n'
    '\t// all. ESP is served by the entity hooks; this inline write is dropped.',
    'patchOffset("libunity.so", 0x5CD8228, "20 00 80 D2 C0 03 5F D6", checkboxStates["BRTAGS"]);':
    '\t// [1.6.59] was OpenWorldDroppedPickUpUtil::.cctor+0x38. Returning from the middle of a\n'
    '\t// static ctor leaves the statics half-initialised; disabling is safer than guessing.',
    'patchOffset("libunity.so", 0x8839D08, "20 00 80 D2 C0 03 5F D6", checkboxStates["highend"]);':
    '\t// [1.6.59] was BrWeaponModsMainController::OnEasyListItemClick+0x58C (inline, inside a\n'
    '\t// UI click handler). Disabled rather than redirected.',
    'patchOffset("libunity.so", 0x883D084, "20 00 80 D2 C0 03 5F D6", checkboxStates["highend"]);':
    '\t// [1.6.59] was BTCrossHairPlayerInfoHUD::AimingDirectTarget+0x148. Forcing the return\n'
    '\t// value at entry would skip filling the ref AttackableTarget the caller reads. Disabled.',
}
for old, new in repl.items():
    must(old in s, "missing patch line: " + old[:48])
    s = s.replace(old, new)

must(s != orig, "Main.cpp unchanged")
open("src/main/jni/Main.cpp", "w").write(s)
print("Main.cpp written")

# ---------------- SkinHaxSystem.h ----------------
p = "/tmp/mig/SkinHaxSystem.h"
s = open(p).read()
fix = {
    # 1.6.57 address was FrontEndUIScene::RefreshNavigation, not the armor config ctor
    "static constexpr uintptr_t kMythicArmorCtor = 0x6C208A8;":
    "static constexpr uintptr_t kMythicArmorCtor = 0x8163400;   // Config.MythicArmorConfig::.ctor",
    "static constexpr uintptr_t kWeaponAssetCtor = 0x85D0488;":
    "static constexpr uintptr_t kWeaponAssetCtor = 0x85D0488;   // Config.WeaponAssetGroupConfConfig::.ctor",
    "static constexpr uintptr_t kWeaponNameGetter = 0x85D6744;":
    "static constexpr uintptr_t kWeaponNameGetter = 0x85D6744;  // Config.WeaponConfConfig::get_Name",
}
for old, new in fix.items():
    must(old in s, "SkinHax line missing: " + old)
    s = s.replace(old, new)
# guard: skip a zero RVA instead of hooking the library base
if "if (!rva) return false;" not in s:
    m = re.search(r"(static bool InstallOne\([^)]*\)\s*\{\n)", s)
    must(m is not None, "InstallOne signature not found")
    s = s[:m.end()] + "    // rva == 0 marks a symbol this build does not expose.\n    if (!rva) return false;\n" + s[m.end():]
open("src/main/jni/Hacks/Feature/SkinHaxSystem.h", "w").write(s)
print("SkinHaxSystem.h written")

# ---------------- MythicAttachmentSystem.h ----------------
p = "/tmp/mig/MythicAttachmentSystem.h"
s = open(p).read()
if "if (!rva) return false;" not in s:
    pat = re.compile(r"(auto hookRva = \[unityBase\]\([^)]*\)\s*\{\n)")
    must(pat.search(s) is not None, "hookRva lambda not found")
    s = pat.sub(lambda m: m.group(1) +
                "        // rva == 0 marks a symbol this build does not expose.\n"
                "        if (!rva) return false;\n", s)
open("src/main/jni/Hacks/Feature/MythicAttachmentSystem.h", "w").write(s)
print("MythicAttachmentSystem.h written")
