import FreeCAD
from pivy import coin

import Preferences

class ConstraintMirrorObjectProxy:
    def __init__(self, obj, constraintObj ):
        self.constraintObj_name = constraintObj.Name
        constraintObj.Proxy.mirror_name = obj.Name
        self.disable_onChanged = False
        obj.Proxy = self

    def execute(self, obj):
        return #no work required in onChanged causes touched in original constraint ...

    def onChanged(self, obj, prop):
        '''
        is triggered by Python code!
        And on document loading...
        '''
        #FreeCAD.Console.PrintMessage("%s.%s property changed\n" % (obj.Name, prop))
        if getattr( self, 'disable_onChanged', True):
            return
        if obj.getGroupOfProperty( prop ) == 'ConstraintNfo':
            if hasattr( self, 'constraintObj_name' ):
                constraintObj = obj.Document.getObject( self.constraintObj_name )
                try:
                    if getattr(constraintObj, prop) != getattr( obj, prop):
                        setattr( constraintObj, prop, getattr( obj, prop) )
                except AttributeError as e:
                    pass #loading issues...


def create_constraint_mirror( constraintObj, iconPath, origLabel= '', mirrorLabel='', extraLabel = '' ):
    #FreeCAD.Console.PrintMessage("creating constraint mirror\n")
    cName = constraintObj.Name + '_mirror'
    cMirror =  constraintObj.Document.addObject("App::FeaturePython", cName)
    if origLabel == '':
        cMirror.Label = constraintObj.Label + '_'
    else:
        cMirror.Label = constraintObj.Label + '__' + mirrorLabel
        constraintObj.Label = constraintObj.Label + '__' + origLabel
        if extraLabel != '':
            cMirror.Label += '__' + extraLabel
            constraintObj.Label += '__' + extraLabel
    for pName in constraintObj.PropertiesList:
        if constraintObj.getGroupOfProperty( pName ) == 'ConstraintInfo':
            #if constraintObj.getTypeIdOfProperty( pName ) == 'App::PropertyEnumeration':
            #    continue #App::Enumeration::contains(const char*) const: Assertion `_EnumArray' failed.
            cMirror.addProperty(
                constraintObj.getTypeIdOfProperty( pName ),
                pName,
                "ConstraintNfo" #instead of ConstraintInfo, as to not confuse the assembly2sovler
                )
            if pName == 'directionConstraint':
                v =  constraintObj.directionConstraint
                if v != "none": #then updating a document with mirrors
                    cMirror.directionConstraint =  ["aligned","opposed"]
                    cMirror.directionConstraint = v
                else:
                    cMirror.directionConstraint =  ["none","aligned","opposed"]
            else:
                setattr( cMirror, pName, getattr( constraintObj, pName) )
            if constraintObj.getEditorMode(pName) == ['ReadOnly']:
                cMirror.setEditorMode( pName, 1 )
    ConstraintMirrorObjectProxy( cMirror, constraintObj )
    cMirror.ViewObject.Proxy = ConstraintMirrorViewProviderProxy( constraintObj, iconPath )
    #cMirror.purgeTouched()
    return cMirror.Name


class ConstraintViewProviderProxy:
    def __init__( self, constraintObj, iconPath, createMirror=True, origLabel = '', mirrorLabel = '', extraLabel = '' ):
        self.iconPath = iconPath
        self.constraintObj_name = constraintObj.Name
        constraintObj.purgeTouched()
        if createMirror and Preferences.groupConstraintsUnderParts():
            part1 = constraintObj.Document.getObject( constraintObj.Object1 )
            part2 = constraintObj.Document.getObject( constraintObj.Object2 )
            if hasattr( getattr(part1.ViewObject,'Proxy',None),'claimChildren') \
               or hasattr( getattr(part2.ViewObject,'Proxy',None),'claimChildren'):
                self.mirror_name = create_constraint_mirror(  constraintObj, iconPath, origLabel, mirrorLabel, extraLabel )

    def getIcon(self):
        return self.iconPath

    def attach(self, vobj): #attach to what document?
        vobj.addDisplayMode( coin.SoGroup(),"Standard" )

    def getDisplayModes(self,obj):
        "'''Return a list of display modes.'''"
        return ["Standard"]

    def getDefaultDisplayMode(self):
        "'''Return the name of the default display mode. It must be defined in getDisplayModes.'''"
        return "Standard"

    def onDelete(self, viewObject, subelements): # subelements is a tuple of strings
        'does not seem to be called when an object is deleted pythonatically'
        if not Preferences.allowDeletionOfExternalDocuments() and FreeCAD.activeDocument() != viewObject.Object.Document:
            FreeCAD.Console.PrintMessage("preventing deletetion of %s since active document != %s. Disable behavior in assembly2 preferences.\n" % (viewObject.Object.Label, viewObject.Object.Document.Name) )
            return False
            #add code to delete constraint mirrors, or original
        obj = viewObject.Object
        doc = obj.Document
        if isinstance( obj.Proxy, ConstraintMirrorObjectProxy ):
            doc.removeObject(  obj.Proxy.constraintObj_name ) # also delete the original constraint which obj mirrors
        elif hasattr( obj.Proxy, 'mirror_name'): # the original constraint, #isinstance( obj.Proxy,  ConstraintObjectProxy ) not done since ConstraintObjectProxy not defined in namespace
            doc.removeObject( obj.Proxy.mirror_name ) # also delete mirror
        return True



class ConstraintMirrorViewProviderProxy( ConstraintViewProviderProxy ):
    def __init__( self, constraintObj, iconPath ):
        self.iconPath = iconPath
        self.constraintObj_name = constraintObj.Name

    def attach(self, vobj):
        vobj.addDisplayMode( coin.SoGroup(),"Standard" )
