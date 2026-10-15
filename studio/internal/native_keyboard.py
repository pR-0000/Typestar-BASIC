"""Host keys -> S-70 matrix, default hardware locale 0.

This is a key-cap mapping, not a firmware translation/injection routine.
Regional variants and unmapped functions remain accessible through raw matrix.
"""
from PySide6.QtCore import Qt

TEXT_KEYS={chr(97+i):(i,False) for i in range(26)}
TEXT_KEYS.update({chr(65+i):(i,True) for i in range(26)})
TEXT_KEYS.update({c:(0x1a+i,False) for i,c in enumerate('0123456789')})
TEXT_KEYS.update({c:(0x1a+i,True) for i,c in enumerate(')!@#$%[&*(')})
for code,normal,shifted in ((0x24,'-',None),(0x26,';',':'),(0x27,"'",'"'),
                            (0x28,',',None),(0x29,'.',None),(0x2a,'/','?'),(0x2b,'_','~'),(0x2c,' ',None)):
    TEXT_KEYS[normal]=(code,False)
    if shifted:TEXT_KEYS[shifted]=(code,True)
SPECIAL={Qt.Key.Key_Return:0x2d,Qt.Key.Key_Enter:0x2d,Qt.Key.Key_Backspace:0x2f,
         Qt.Key.Key_Left:0x31,Qt.Key.Key_Right:0x32,Qt.Key.Key_Up:0x38,Qt.Key.Key_Down:0x39,
         Qt.Key.Key_Escape:0x36,Qt.Key.Key_Control:0x3b,
         Qt.Key.Key_F7:0x3b,Qt.Key.Key_F8:0x37,Qt.Key.Key_F9:0x3a}
# Existing Studio buttons use the BASIC logical key values.
BUTTON_KEYS={13:0x2d,8:0x2f,18:0x31,19:0x32,20:0x38,21:0x39,3:0x36}

def host_key(event):
    code=SPECIAL.get(event.key())
    if code is not None:return code,bool(event.modifiers()&Qt.KeyboardModifier.ShiftModifier)
    if event.modifiers()&Qt.KeyboardModifier.ControlModifier and Qt.Key.Key_A<=event.key()<=Qt.Key.Key_Z:
        return event.key()-Qt.Key.Key_A,bool(event.modifiers()&Qt.KeyboardModifier.ShiftModifier)
    return TEXT_KEYS.get(event.text())
