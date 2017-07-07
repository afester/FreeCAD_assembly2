import FreeCAD
import FreeCADGui
import Logging
from PySide import QtGui
from AssemblyUtils import findUnusedObjectName, planeSelected, linearEdgeSelected, printSelection, SelectionExObject
from ConstraintObjectProxy import ConstraintObjectProxy
from ConstraintViewProviderProxy import ConstraintViewProviderProxy
from ConstraintSelectionObserver import ConstraintSelectionObserver
from solver.ConstraintTools import repair_tree_view, updateObjectProperties


class PlaneSelectionGate:
    def allow(self, doc, obj, sub):
        s = SelectionExObject(doc, obj, sub)
        return planeSelected(s) or linearEdgeSelected(s)


selection_text = '''Selection options:
  - plane surface
  - edge '''

class AngleConstraintCommand:
    
    def parseSelection(self, selection, objectToUpdate=None):
        validSelection = False
        if len(selection) == 2:
            s1, s2 = selection
            if s1.ObjectName != s2.ObjectName:
                if      ( planeSelected(s1) or linearEdgeSelected(s1)) \
                    and ( planeSelected(s2) or linearEdgeSelected(s2)):
                    validSelection = True
                    cParms = [ [s1.ObjectName, s1.SubElementNames[0], s1.Object.Label ],
                               [s2.ObjectName, s2.SubElementNames[0], s2.Object.Label ] ]
        if not validSelection:
            msg = '''Angle constraint requires a selection of 2 planes or two straight lines, each from different objects.Selection made: %s'''  % printSelection(selection)
            QtGui.QMessageBox.information(  QtGui.qApp.activeWindow(), "Incorrect Usage", msg)
            return
    
        if objectToUpdate == None:
            cName = findUnusedObjectName('angleConstraint')
            Logging.debug("creating %s" % cName )
            c = FreeCAD.ActiveDocument.addObject("App::FeaturePython", cName)
            c.addProperty("App::PropertyString","Type","ConstraintInfo").Type = 'angle_between_planes'
            c.addProperty("App::PropertyString","Object1","ConstraintInfo").Object1 = cParms[0][0]
            c.addProperty("App::PropertyString","SubElement1","ConstraintInfo").SubElement1 = cParms[0][1]
            c.addProperty("App::PropertyString","Object2","ConstraintInfo").Object2 = cParms[1][0]
            c.addProperty("App::PropertyString","SubElement2","ConstraintInfo").SubElement2 = cParms[1][1]
            c.addProperty("App::PropertyAngle","angle","ConstraintInfo")
            c.Object1 = cParms[0][0]
            c.SubElement1 = cParms[0][1]
            c.Object2 = cParms[1][0]
            c.SubElement2 = cParms[1][1]
            for prop in ["Object1","Object2","SubElement1","SubElement2","Type"]:
                c.setEditorMode(prop, 1)
            c.Proxy = ConstraintObjectProxy()
            c.ViewObject.Proxy = ConstraintViewProviderProxy( c, ':/assembly/icons/angleConstraint.svg', True, cParms[1][2], cParms[0][2])
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
                PlaneSelectionGate(),
                self.parseSelection,
                taskDialog_title ='Add angular constraint',
                taskDialog_iconPath = self.GetResources()['Pixmap'],
                taskDialog_text = selection_text )

    def GetResources(self):
        msg = 'Add Angular constraint'
        return {
            'Pixmap' : ':/assembly/icons/angleConstraint.svg',
            'MenuText': msg,
            'ToolTip': msg,
            }

FreeCADGui.addCommand('addAngleConstraint', AngleConstraintCommand())
