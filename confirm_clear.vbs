Option Explicit
Dim userInput
userInput = MsgBox("Are you sure you want to delete all memory files? The poor saps will never get their memory back!", vbYesNo + vbQuestion, "Confirm Delete")

If userInput = vbYes Then
    WScript.Quit 6  ' Exit with code 6 for Yes
Else
    WScript.Quit 7  ' Exit with code 7 for No
End If
