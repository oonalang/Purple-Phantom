# 1.6.59 offset refresh

## Sources

| file | role |
|---|---|
| `dump-1.6.57/dump 1.6.57.cs` | **reference build** — the dump the old offsets were built on (469,242 methods) |
| `jeudhehs/dump/Dump 1.6.59.cs` | target build (484,908 methods, 280,127 fields) |
| `split_config.arm64_v8a.apk` | `libunity.so` arm64-v8a — IL2CPP is linked into it, so RVAs are library-relative |
| `base.apk` | `assets/bin/Data/Managed/Metadata/global-metadata.dat` |
| `5_6296463175952900842.txt` | libanogs (Tencent ACE) name/offset table |

RVA → file offset is `vaddr - 0x4000` (from `readelf -lW`), which is what `tools/lookup.py`
uses for Capstone checks.

## Method

1. `tools/dump_index.py <dump.cs>` → `methods.tsv` (rva, class, signature) for **both** builds.
2. Every constant in the old code is resolved in the 1.6.57 dump to a declared member.
3. That member's **exact signature** is looked up in the 1.6.59 dump (`tools/apply_2_relocate.py`):
   **103 exact matches, 0 ambiguous, 0 missing.**
4. `tools/verify_offsets.py` re-checks the result: every RVA must be a method start in the
   1.6.59 dump, and every byte patch must have at least as many bytes before the next
   method as it writes.

Current state: **128 offsets verified as method starts**, 17 `createWithHex` + 18
`patchOffset` sites all `OK`, no two patches writing the same address.

## Bugs that were already in the old code

The 1.6.57 dump is what makes these provable — each was verified against that build, not guessed:

* **`// AUTO ON` block** — three hooks (`IsTutorialEnabled`, `get_EnableVulkan`,
  `IsEmulator`) pointed at `BRContractTask::RefreshIndication+0x16C`,
  `TouchInputModule::ShouldActivateModule+0x100` and `XLua.DelegateBridge` internals.
  They duplicated the correct `[System]` block below them, so they are gone.
* **`kMythicArmorCtor`** — pointed at `FrontEndUIScene::RefreshNavigation`, but is used as a
  `void(*)(void*)` constructor hook. Now `Config.MythicArmorConfig::.ctor`.
* **`Patches.outline`** (two assignments) — both addresses sat inside
  `TEDActMainUIController::Init` and `TEDActAwardFGCellView::SetData`, never in
  `IsEffectActive`. Collapsed into one patch on `EffectInstance_SeeFront::IsEffectActive`.
* **`NeedDelayProcess`** — pointed inside `LoadoutWeaponProficiencyAwardController::UpdateAvatarShow`;
  now `ObserverDelayManager.NeedDelayProcess`.
* **`h_get_SlideTackleAcclerationSpeed`** — pointed inside `PropHuntLockViewController::OnOpen`;
  now `Weapon.get_SlideTackleAcclerationSpeed`.
* **`UNLI AMMO`** — the target is `GameInfo.IsNoCostAmmo`, but the payload was `mov w0,#0`
  (return false = vanilla path). Corrected to return true.

## Feature headers, fully resolved

All 15 `SkinHaxSystem.h` and all 15 `MythicAttachmentSystem.h` constants now map to real
1.6.59 members — no `0x0` placeholders remain:

* `Item2InventoryConfig`, `WeaponConfConfig`, `WeaponConfExtraConfig`,
  `WeaponFireEffectConfigConfig`, `WeaponAssetGroupConfConfig`, `MythicArmorConfig`,
  `MythicSightConfig`, `KillEffectItemConfConfig`, `WeaponSkinConfig`,
  `ItemResourceConfig` constructors + `WeaponConfConfig.get_Name`
* `WeaponPromotionInfo.GetCurrentWeaponKillEffect / FireEffect / BulletTrackEffect / WeaponBrocast`
* `AttachmentGroupNew` (both overloads + `GetColorId`), `BRWeaponAttachItemData`,
  `Squad.AttachItem` (ctor, `SetData`, `SetMythicSkinID`, `CopyFromEquippedItem`,
  `GetModelAttachId`), `AttachSkinData`,
  `LoadoutWeaponsAttachmentItemController.SetData`, `Weapon.InitOneWeaponPart`

`if (!rva) return false;` guards remain in both install paths as a cheap defence.

## Disabled — 5 inline patches with no safe equivalent

These were writes *inside* a method body in 1.6.57, so their address cannot be relocated by
name. Each is commented in place with the containing method named:

| feature | old site |
|---|---|
| anti FPS drop | `<GetPerk>c__Iterator0::MoveNext +0x78C` |
| wallhack | `<PrintDialog>c__Iterator0::MoveNext +0x1A0` |
| BR tags | `OpenWorldDroppedPickUpUtil::.cctor +0x38` |
| higher end | `BrWeaponModsMainController::OnEasyListItemClick +0x58C` |
| higher end | `BTCrossHairPlayerInfoHUD::AimingDirectTarget +0x148` |

`StopShowEffect +0xC` was also inline but the method is `void`, so it is now patched at its
entry (skipping the body is the same observable behaviour).

## Still open

* **libanogs bypass** — `0x1F8408` matches the supplied table; `0x1F87B0`, `0x204100`,
  `0x41BA40` are absent from it and were left untouched.
* **`Patches.revive` and `Patches.fire` are assigned twice** in `Init_Thread`, so only the
  second target (`get_ReviveTime`, `get_FireInterval`) is ever installed. Pre-existing
  (identical in 1.6.57); splitting them needs new fields/toggles instead of a silent overwrite.
* **`Fields.h`** C++ struct layouts were not re-diffed field by field against 1.6.59.
* **Not compiled or run** — no NDK in this environment, so this is static verification
  against both dumps only.

## Re-running

```bash
python3 tools/dump_index.py "/tmp/dump/Dump 1.6.57.cs" /tmp/idx57
python3 tools/dump_index.py "/tmp/dump/Dump 1.6.59.cs" /tmp/idx59
python3 tools/apply_2_relocate.py <file>     # HEAD -> /tmp/mig, reports ambiguity
python3 tools/finalize_1_6_59.py             # intent fixes + guards
python3 tools/verify_offsets.py              # membership + patch headroom
```
