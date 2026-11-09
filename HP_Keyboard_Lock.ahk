#Requires AutoHotkey v2.0
#SingleInstance Force
Persistent

#Include "C:\AHI\Lib\AutoHotInterception.ahk"

AHI := AutoHotInterception()

; Built-in laptop keyboard
keyboardHandle := "ACPI\VEN_ATK&DEV_3001"
keyboardId := AHI.GetKeyboardIdFromHandle(keyboardHandle)
if (!keyboardId)
    ExitApp()

; Keys to block (blocking a physical key also blocks its Shift symbol:
; "0" -> 0 and ), "=" -> = and +, "'" -> ' and ", ";" -> ; and :, "," -> , and <, "." -> . and >, "/" -> / and ?)
blockedKeys := [
    "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m",
    "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z",
    "1", "2", "3", "4", "5", "6", "7", "8", "9", "0",
    ";", "'", "[", "]", "=", ",", ".", "/"
]

scanCodes := []
seenSC := Map()
for key in blockedKeys {
    sc := GetKeySC(key)
    if (!sc)
        ExitApp()
    if (!seenSC.Has(sc)) {
        seenSC[sc] := true
        scanCodes.Push(sc)
    }
}

activeScanCodes := []
locked := false

OnExit(UnlockKeys)

; Lock immediately when the script starts
ToggleBlocking()

; Ctrl + Alt toggle, either pressing order
~LCtrl & LAlt:: {
    ToggleBlocking()
    KeyWait("LAlt")
    KeyWait("LCtrl")
}

~LAlt & LCtrl:: {
    ToggleBlocking()
    KeyWait("LCtrl")
    KeyWait("LAlt")
}

ToggleBlocking() {
    global AHI, keyboardId, scanCodes
    global activeScanCodes, locked

    if (!locked) {
        activeScanCodes := []
        try {
            for sc in scanCodes {
                AHI.SubscribeKey(
                    keyboardId,
                    sc,
                    true,
                    IgnoreKey
                )
                activeScanCodes.Push(sc)
            }
            locked := true
        } catch {
            for sc in activeScanCodes {
                try AHI.UnsubscribeKey(keyboardId, sc)
            }
            activeScanCodes := []
            locked := false
        }
    } else {
        failed := []
        for sc in activeScanCodes {
            try {
                AHI.UnsubscribeKey(keyboardId, sc)
            } catch {
                failed.Push(sc)
            }
        }
        activeScanCodes := failed
        locked := failed.Length > 0
    }
}

; Discard selected key events
IgnoreKey(state) {
    return
}

; Restore keys when script exits
UnlockKeys(*) {
    global AHI, keyboardId, activeScanCodes
    for sc in activeScanCodes {
        try AHI.UnsubscribeKey(keyboardId, sc)
    }
}
