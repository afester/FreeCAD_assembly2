import Logging
import FreeCADGui
import FreeCAD
 
from PySide import QtGui
from ConstraintSelectionObserver import ConstraintSelectionObserver
from AssemblyUtils import circularEdgeSelected, SelectionExObject, axisOfPlaneSelected, findUnusedObjectName, printSelection
from solver.ConstraintTools import updateObjectProperties, repair_tree_view
from ConstraintObjectProxy import ConstraintObjectProxy
from ConstraintViewProviderProxy import ConstraintViewProviderProxy


class CircularEdgeSelectionGate:
    def allow(self, doc, obj, sub):
        return ValidSelectionFunct(SelectionExObject(doc, obj, sub),doc, obj, sub)


def ValidSelectionFunct(selectionExObj, doc, obj, sub):
    return circularEdgeSelected( SelectionExObject(doc, obj, sub) )\
           or axisOfPlaneSelected(selectionExObj)

selection_text = '''Select circular edges or faces'''
    
class CircularEdgeConstraintCommand:

    def parseSelection(self, selection, objectToUpdate=None, callSolveConstraints=True, lockRotation = False):
        validSelection = False
        if len(selection) == 2:
            s1, s2 = selection
            if s1.ObjectName != s2.ObjectName:
                validSelection = True
                cParms = [ [s1.ObjectName, s1.SubElementNames[0], s1.Object.Label ],
                           [s2.ObjectName, s2.SubElementNames[0], s2.Object.Label ] ]
                Logging.debug('cParms = %s' % (cParms))
        if not validSelection:
            msg = '''To add a circular edge constraint select two circular edges, each from a different part. Selection made:
    %s'''  % printSelection(selection)
            QtGui.QMessageBox.information(  QtGui.qApp.activeWindow(), "Incorrect Usage", msg)
            return
    
        if objectToUpdate == None:
            cName = findUnusedObjectName('circularEdgeConstraint')
            Logging.debug("creating %s" % cName )
            c = FreeCAD.ActiveDocument.addObject("App::FeaturePython", cName)
    
            c.addProperty("App::PropertyString", "Type", "ConstraintInfo").Type = 'circularEdge'
            c.addProperty("App::PropertyString", "Object1", "ConstraintInfo").Object1 = cParms[0][0]
            c.addProperty("App::PropertyString", "SubElement1", "ConstraintInfo").SubElement1 = cParms[0][1]
            c.addProperty("App::PropertyString", "Object2", "ConstraintInfo").Object2 = cParms[1][0]
            c.addProperty("App::PropertyString", "SubElement2", "ConstraintInfo").SubElement2 = cParms[1][1]
    
            c.addProperty("App::PropertyEnumeration","directionConstraint", "ConstraintInfo")
            c.directionConstraint = ["none","aligned","opposed"]
            c.addProperty("App::PropertyDistance","offset","ConstraintInfo")
            c.addProperty("App::PropertyBool","lockRotation","ConstraintInfo").lockRotation = lockRotation
    
            c.setEditorMode('Type',1)
            for prop in ["Object1","Object2","SubElement1","SubElement2"]:
                c.setEditorMode(prop, 1)
    
            c.Proxy = ConstraintObjectProxy()
            c.ViewObject.Proxy = ConstraintViewProviderProxy( c, ':/assembly/icons/circularEdgeConstraint.svg', True, cParms[1][2], cParms[0][2])
        else:
            Logging.debug("redefining %s" % objectToUpdate.Name )
            c = objectToUpdate
            c.Object1 = cParms[0][0]
            c.SubElement1 = cParms[0][1]
            c.Object2 = cParms[1][0]
            c.SubElement2 = cParms[1][1]
            updateObjectProperties(c)
    
        c.purgeTouched()
        if callSolveConstraints:
            c.Proxy.callSolveConstraints()
            repair_tree_view()
        #FreeCADGui.Selection.clearSelection()
        #FreeCADGui.Selection.addSelection(c)
        return c
    
    
    def Activated(self):
        selection = FreeCADGui.Selection.getSelectionEx()
        if len(selection) == 2:
            self.parseSelection( selection )
        else:
            FreeCADGui.Selection.clearSelection()
            ConstraintSelectionObserver(
                CircularEdgeSelectionGate(),
                self.parseSelection,
                taskDialog_title ='add circular edge constraint',
                taskDialog_iconPath = self.GetResources()['Pixmap'],
                taskDialog_text = selection_text
                )

    def GetResources(self):
        return {
            'Pixmap' : ':/assembly/icons/circularEdgeConstraint.svg' ,
            'MenuText': 'Add Circular Edge constraint',
            'ToolTip': 'Add a circular edge constraint between two objects'
            }

Logging.debug('CircularEdgeConstraint')
FreeCADGui.addCommand('addCircularEdgeConstraint', CircularEdgeConstraintCommand())
