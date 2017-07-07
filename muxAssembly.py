import Logging

import FreeCAD
import FreeCADGui
import Part


class Proxy_muxAssemblyObj:
    def execute(self, shape):
        pass


def faceMapKey(face):
    c = sum([ [ v.Point.x, v.Point.y, v.Point.z] for v in face.Vertexes ], [])
    return tuple(c)


def muxObjects(doc, mode=0):
    'combines all the imported shape object in doc into one shape'
    faces = []

    if mode == 1:
        objects = doc.getSelection()
    else:
        objects = doc.Objects

    for obj in objects:
        if 'importPart' in obj.Content:
            Logging.debug('  - parsing "%s"' % (obj.Name))
            faces = faces + obj.Shape.Faces
    return Part.makeShell(faces)



def muxMapColors(doc, muxedObj, mode=0):
    'call after muxedObj.Shape =  muxObjects(doc)'
    diffuseColors = []
    faceMap = {}

    if mode == 1:
        objects = doc.getSelection()
    else:
        objects = doc.Objects

    for obj in objects:
        if 'importPart' in obj.Content:
            for i, face in enumerate(obj.Shape.Faces):
                if i < len(obj.ViewObject.DiffuseColor):
                    clr = obj.ViewObject.DiffuseColor[i]
                else:
                    clr = obj.ViewObject.DiffuseColor[0]
                faceMap[faceMapKey(face)] = clr
    for f in muxedObj.Shape.Faces:
        try:
            key = faceMapKey(f)
            clr = faceMap[key]
            del faceMap[key]
        except KeyError:
            Logging.debug('muxMapColors: waring no faceMap entry for %s - key %s' % (f,faceMapKey(f)))
            clr = muxedObj.ViewObject.ShapeColor
        diffuseColors.append( clr )
    muxedObj.ViewObject.DiffuseColor = diffuseColors
    
    

def createMuxedAssembly(name=None):
        partName='muxedAssembly'
        if name != None:
            partName = name
        Logging.debug('creating assembly mux "%s"' % (partName))

        muxedObj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython",partName)
        muxedObj.Proxy = Proxy_muxAssemblyObj()
        muxedObj.ViewObject.Proxy = 0
        muxedObj.addProperty("App::PropertyString","type")
        muxedObj.type = 'muxedAssembly'
        muxedObj.addProperty("App::PropertyBool","ReadOnly")
        muxedObj.ReadOnly = False
        FreeCADGui.ActiveDocument.getObject(muxedObj.Name).Visibility = False
        muxedObj.addProperty("App::PropertyStringList","muxedObjectList")
        tmplist=[]
        for objlst in FreeCADGui.Selection.getSelection():
            if 'importPart' in objlst.Content:
                tmplist.append(objlst.Name)
        muxedObj.muxedObjectList=tmplist
        if len(tmplist)>0:
            #there are objects selected, mux them
            muxedObj.Shape = muxObjects(FreeCADGui.Selection, 1)
            muxMapColors(FreeCADGui.Selection, muxedObj, 1)
        else:
            #mux all objects (original behavior)
            for objlst in FreeCAD.ActiveDocument.Objects:
                if 'importPart' in objlst.Content:
                    tmplist.append(objlst.Name)
            muxedObj.muxedObjectList=tmplist
            if len(tmplist)>0:
                muxedObj.Shape = muxObjects(FreeCAD.ActiveDocument, 0)
                muxMapColors(FreeCAD.ActiveDocument, muxedObj, 0)
            else:
                Logging.debug('Nothing to Mux')



class MuxAssemblyCommand:

    def Activated(self):
        #we have to handle the mux name here
        createMuxedAssembly()
        FreeCAD.ActiveDocument.recompute()


    def GetResources(self):
        return {
            'Pixmap'  : ':/assembly/icons/muxAssembly.svg',
            'MenuText': 'Combine all parts',
            'ToolTip' : 'Combine all parts into a single object\nor combine all selected parts into a single object\n(for example to create a drawing of the whole or part of the assembly)'
            }

FreeCADGui.addCommand('muxAssembly', MuxAssemblyCommand())