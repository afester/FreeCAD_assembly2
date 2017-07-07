import FreeCAD
import FreeCADGui

from PySide import QtGui
import Logging
from AssemblyUtils import SelectionExObject, linearEdgeSelected, axisOfPlaneSelected, cylindricalPlaneSelected, findUnusedObjectName, printSelection
from ConstraintObjectProxy import ConstraintObjectProxy
from ConstraintViewProviderProxy import ConstraintViewProviderProxy
from ConstraintSelectionObserver import ConstraintSelectionObserver
from solver.ConstraintTools import repair_tree_view, updateObjectProperties

class AxialSelectionGate:
    def allow(self, doc, obj, sub):
        return ValidSelection(SelectionExObject(doc, obj, sub))

def ValidSelection(selectionExObj):
    return cylindricalPlaneSelected(selectionExObj)\
        or linearEdgeSelected(selectionExObj)\
        or axisOfPlaneSelected(selectionExObj)


selection_text = '''Please select any two of
  - Cylindrical surface(s)
  - Edge(s)
  - Face(s)'''

class AxialConstraintCommand:


    def parseSelection(self, selection, objectToUpdate=None):
        validSelection = False
        if len(selection) == 2:
            s1, s2 = selection
            if s1.ObjectName != s2.ObjectName:
                if ValidSelection(s1) and ValidSelection(s2):
                    validSelection = True
                    cParms = [ [s1.ObjectName, s1.SubElementNames[0], s1.Object.Label ],
                               [s2.ObjectName, s2.SubElementNames[0], s2.Object.Label ] ]
                    Logging.debug('cParms = %s' % (cParms))
        if not validSelection:
            msg = '''To add an axial constraint select two cylindrical surfaces or two straight lines, each from a different part. Selection made: %s'''  % printSelection(selection)
            QtGui.QMessageBox.information(  QtGui.qApp.activeWindow(), "Incorrect Usage", msg)
            return
    
        if objectToUpdate == None:
            cName = findUnusedObjectName('axialConstraint')
            Logging.debug("creating %s" % cName )
            c = FreeCAD.ActiveDocument.addObject("App::FeaturePython", cName)
            c.addProperty("App::PropertyString","Type","ConstraintInfo","Object 1").Type = 'axial'
            c.addProperty("App::PropertyString","Object1","ConstraintInfo").Object1 = cParms[0][0]
            c.addProperty("App::PropertyString","SubElement1","ConstraintInfo").SubElement1 = cParms[0][1]
            c.addProperty("App::PropertyString","Object2","ConstraintInfo").Object2 = cParms[1][0]
            c.addProperty("App::PropertyString","SubElement2","ConstraintInfo").SubElement2 = cParms[1][1]
    
            c.addProperty("App::PropertyEnumeration","directionConstraint", "ConstraintInfo")
            c.directionConstraint = ["none","aligned","opposed"]
            c.addProperty("App::PropertyBool","lockRotation","ConstraintInfo")
    
            c.setEditorMode('Type',1)
            for prop in ["Object1","Object2","SubElement1","SubElement2"]:
                c.setEditorMode(prop, 1)
    
            c.Proxy = ConstraintObjectProxy()
            c.ViewObject.Proxy = ConstraintViewProviderProxy( c, ':/assembly/icons/axialConstraint.svg', True, cParms[1][2], cParms[0][2])
        else:
            Logging.debug("redefining %s" % objectToUpdate.Name )
            c = objectToUpdate
            c.Object1 = cParms[0][0]
            c.SubElement1 = cParms[0][1]
            c.Object2 = cParms[1][0]
            c.SubElement2 = cParms[1][1]
            updateObjectProperties(c)
    
        c.purgeTouched()
        c.Proxy.callSolveConstraints()
        repair_tree_view()

    def Activated(self):
        selection = FreeCADGui.Selection.getSelectionEx()
        if len(selection) == 2:
            self.parseSelection( selection )
        else:
            FreeCADGui.Selection.clearSelection()
            ConstraintSelectionObserver(
                AxialSelectionGate(),
                self.parseSelection,
                taskDialog_title ='Add axial constraint',
                taskDialog_iconPath = self.GetResources()['Pixmap'],
                taskDialog_text = selection_text
                )

    def GetResources(self):
        return {
            'Pixmap' : ':/assembly/icons/axialConstraint.svg',
            'MenuText': 'Add Axial constraint',
            'ToolTip': 'Add an axial constraint between two objects'
            }

FreeCADGui.addCommand('addAxialConstraint', AxialConstraintCommand())
