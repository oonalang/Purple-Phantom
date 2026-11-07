#pragma once

#define m_UNITYLIB OBFUSCATE("libunity.so")
#define m_ANOGSLIB OBFUSCATE("libanogs.so")
#define m_UNITYLIB "libunity.so"

#define SLEEP_TIME 1000LL / 60LL

// ---------------------------------------------------------------------------
// Offsets rebuilt from "Dump 1.6.59.cs" (Il2CppDumper output of the current
// arm64-v8a libunity.so). RVAs are relative to the libunity.so load base and
// every entry below was resolved against a named managed method of that dump.
//
// Managed -> native mapping used here:
//   UnityEngine.Input     -> get_touchCount / GetTouch / get_mousePosition
//   UnityEngine.Screen    -> get_width / get_height / get_dpi
//   UnityEngine.Camera    -> get_main / WorldToScreenPoint / aspect
//   GameEngine.GamePlay   -> get_MatchGame / get_LocalPawn
//   GameBase.Pawn         -> get_IsFiring / get_CurrentWeapon / IsAiming
//   GameBase.Weapon       -> GetWeaponId
//   UnityEngine.Time      -> timeScale
// ---------------------------------------------------------------------------
uintptr_t Class_Time_set_timeScale;
uintptr_t Class_Time_get_timeScale;



uintptr_t m_unity;
void UpdateAllOffset(){
#define Class_Input__get_touchCount (m_unity + 0x5307FDC ) // public static int get_touchCount() { };
#define Class_Input__GetTouch (m_unity + 0x5307FEC ) //public static Touch GetTouch(int index) { };
#define Class_Input__get_mousePosition (m_unity + 0x5307994 ) //public static Vector3 get_mousePosition() { };

#define Class_Screen__get_width (m_unity + 0x530005C ) //public static int get_width() { };
#define Class_Screen__get_height (m_unity + 0x53000C0 ) //public static int get_height() { };
#define Class_Screen__get_density (m_unity + 0x5339A00 ) //public static float get_dpi() { };

#define Class_Camera__get_main (m_unity + 0x52D5CDC ) //public static Camera get_main() { };
#define Class_Camera__WorldToScreenPoint (m_unity + 0x52D5820 ) //public Vector3 WorldToScreenPoint(Vector3 position) { };

#define Class_Component__get_transform (m_unity + 0x52DAEC4 ) //public Transform get_transform() { };
#define Class_Transform__get_position (m_unity + 0x532DF40 ) //public Vector3 get_position() { };

#define Class_Gameplay__get_MatchGame (m_unity + 0x801191C ) //public static MatchGame get_MatchGame() { };
#define Class_Gameplay__get_LocalPawn (m_unity + 0x8012814 ) //public static Pawn get_LocalPawn() { };
#define Class_Pawn_get_IsFiring (m_unity + 0x5379778 ) //public bool get_IsFiring() { };

#define Class_BaseGame__m_AllVehicles = 0x1A0;

#define Pawn_get_CurrentWeapon (m_unity + 0x535BE4C) //public Weapon get_CurrentWeapon()
#define Weapon_GetWeaponId (m_unity + 0x54A25F8) // public int GetWeaponId()

#define Class_Pawn_set_AimRotation (m_unity + 0x5386048 ) //public virtual void set_AimRotation(Quaternion value) { };
#define Class_Pawn_IsAiming (m_unity + 0x536BAE0 ) //public bool IsAiming() { };
#define Pawn_m_IsAlive (0x550 ) //protected bool m_IsAlive

#define Class_Pawn__m_Mesh (0x630 ) //protected Transform m_Mesh;
#define Class_Pawn__m_HeadBone (0x310 ) //protected Transform m_HeadBone
#define Class_Pawn__m_PlayerInfo (0x5C8 ) //protected PlayerInfo m_PlayerInfo
#define Class_Pawn__m_IsBot (0x5C1 ) //private bool m_IsBot

#define Class_BaseGame__EnemyPawns (0x178 ) //private readonly PawnList EnemyPawns;
#define Class_PlayerInfo__m_NickName (0x170 ) //protected string m_NickName

#define Class_AttackableTarget__m_AttackableInfo (0x78 ) //private AttackableTargetInfo m_AttackableInfo
#define Class_AttackableTarget__m_Health (0x34 ) //protected float m_Health
#define Class_AttackableTarget__m_MaxHealth (0x38 ) //protected float m_MaxHealth

#define m_IsInEM3Eye (0x198) //protected bool m_IsInEM3Eye
#define Class_Camera_get_aspect (m_unity + 0x52D4404)
#define Class_Camera_set_aspect (m_unity + 0x52D4420)
#define Class_Time_set_timeScale (m_unity + 0x534D984)
#define Class_Time_get_timeScale (m_unity + 0x52D2370)
}
