import FreeCADGui
import FreeCAD
from PySide import QtGui

import Logging
import Preferences 

from ConstraintSelectionObserver import ConstraintSelectionObserver
from AssemblyUtils import SelectionExObject, planeSelected, vertexSelected, printSelection, findUnusedObjectName
from solver.ConstraintTools import updateObjectProperties, repair_tree_view
from ConstraintObjectProxy import ConstraintObjectProxy
from ConstraintViewProviderProxy import ConstraintViewProviderProxy



class PlaneSelectionGate:

    def allow(self, doc, obj, sub):
        return planeSelected( SelectionExObject(doc, obj, sub) )


class PlaneSelectionGate2:
    
    def allow(self, doc, obj, sub):
        s2 = SelectionExObject(doc, obj, sub)
        return planeSelected(s2) or vertexSelected(s2)


selection_text = '''Please select either
  - 2 Planes

or

  - Plane
  - Vertex '''

class PlaneConstraintCommand():


    def parseSelection(self, selection, objectToUpdate=None):
        Logging.debug('PlaneConstraintCommand.parseSelection()')
        validSelection = False

        if len(selection) == 2:
            s1, s2 = selection
            if s1.ObjectName != s2.ObjectName:
                if not planeSelected(s1):
                    s2, s1 = s1, s2
                if planeSelected(s1) and (planeSelected(s2) or vertexSelected(s2)):
                    validSelection = True
                    cParms = [ [s1.ObjectName, s1.SubElementNames[0], s1.Object.Label ],
                               [s2.ObjectName, s2.SubElementNames[0], s2.Object.Label ] ]

        if not validSelection:
            msg = '''Plane constraint requires a selection of either
- 2 planes, or
- 1 plane and 1 vertex

Selection made:
%s'''  % printSelection(selection)

            QtGui.QMessageBox.information(  QtGui.qApp.activeWindow(), "Incorrect Usage", msg)
            return

        if objectToUpdate == None:
            if Preferences.promptUserForAxisConstraintLabel():
                extraText, extraOk = QtGui.QInputDialog.getText(QtGui.qApp.activeWindow(), "Axis", 
                                                                "Axis for constraint Label", QtGui.QLineEdit.Normal, "0")
                if not extraOk:
                    return
            else:
                extraText = ''

            cName = findUnusedObjectName('planeConstraint')
            Logging.info("creating %s" % cName )

            c = FreeCAD.ActiveDocument.addObject("App::FeaturePython", cName)
            c.addProperty("App::PropertyString","Type","ConstraintInfo").Type = 'plane'
            c.addProperty("App::PropertyString","Object1","ConstraintInfo").Object1 = cParms[0][0]
            c.addProperty("App::PropertyString","SubElement1","ConstraintInfo").SubElement1 = cParms[0][1]
            c.addProperty("App::PropertyString","Object2","ConstraintInfo").Object2 = cParms[1][0]
            c.addProperty("App::PropertyString","SubElement2","ConstraintInfo").SubElement2 = cParms[1][1]
            c.addProperty('App::PropertyDistance','offset',"ConstraintInfo")
    
            c.addProperty("App::PropertyEnumeration","directionConstraint", "ConstraintInfo")
            c.directionConstraint = ["none","aligned","opposed"]
    
            c.setEditorMode('Type',1)
            for prop in ["Object1","Object2","SubElement1","SubElement2"]:
                c.setEditorMode(prop, 1)

            c.Proxy = ConstraintObjectProxy()
            c.ViewObject.Proxy = ConstraintViewProviderProxy( c, ':/assembly/icons/planeConstraint.svg', 
                                                              True, cParms[1][2], cParms[0][2], extraText)
        else:
            Logging.info("redefining %s" % objectToUpdate.Name )

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
        """This method is called when the command is activated, either 
           through the toolbar or through the menu bar.

        Args:
            self (ImportPartCommand): The reference to the object

        """

        Logging.debug('PlaneConstraintCommand.Activated')

        selection = FreeCADGui.Selection.getSelectionEx()
        if len(selection) == 2:
            Logging.info('Two objects selected, can immediately attach the constraints')
            self.parseSelection( selection )
        else:
            FreeCADGui.Selection.clearSelection()
            Logging.info('User needs to select two objects to proceed')

            ConstraintSelectionObserver(
                    PlaneSelectionGate(),
                    self.parseSelection,
                    taskDialog_title ='add plane constraint',
                    taskDialog_iconPath = self.GetResources()['Pixmap'],
                    taskDialog_text = selection_text,
                    secondSelectionGate = PlaneSelectionGate2() )

    def GetResources(self):
        return {
            'Pixmap'  : ':/assembly/icons/planeConstraint.svg',
            'MenuText': 'Add Plane constraint',
            'ToolTip' : 'Add a Plane constraint between two objects'
            }


# This code is executed when the ImportPart module is imported (when the workbench is activated)
Logging.debug('PlaneConstraint')
FreeCADGui.addCommand('addPlaneConstraint', PlaneConstraintCommand())
