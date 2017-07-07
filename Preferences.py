import FreeCAD


def groupConstraintsUnderParts():
    preferences = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Assembly2")
    return preferences.GetBool('groupConstraintsUnderParts', True)


def allowDeletionOfExternalDocuments():
    preferences = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Assembly2")
    return preferences.GetBool('allowDeletionOfExternalDocuments', False)


def promptUserForAxisConstraintLabel():
    preferences = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Assembly2")
    return preferences.GetBool('promptUserForAxisConstraintLabel', False)


def autoSolveConstraintAttributesChanged():
    preferences = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Assembly2")
    return preferences.GetBool('autoSolveConstraintAttributesChanged', True)


def useCache():
    preferences = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Assembly2")
    return preferences.GetBool('useCache', False)
