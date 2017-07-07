import FreeCAD
import FreeCADGui
import Logging
from SelectionTaskDialog import SelectionTaskDialog

# This seems to be a workaround to be able to delete the ConstraintSelectionObserver, however not sure if that works at all
global wb_globals 
wb_globals = {}

class SelectionRecord:

    def __init__(self, docName, objName, sub):
        self.Document = FreeCAD.getDocument(docName)
        self.ObjectName = objName
        self.Object = self.Document.getObject(objName)
        self.SubElementNames = [sub]


class ConstraintSelectionObserver:

    def __init__(self, selectionGate, parseSelectionFunction,
                 taskDialog_title, taskDialog_iconPath, taskDialog_text,
                 secondSelectionGate=None):
        self.selections = []
        self.parseSelectionFunction = parseSelectionFunction
        self.secondSelectionGate = secondSelectionGate
        FreeCADGui.Selection.addObserver(self)
        FreeCADGui.Selection.removeSelectionGate()
        FreeCADGui.Selection.addSelectionGate( selectionGate )
        wb_globals['selectionObserver'] = self
        self.taskDialog = SelectionTaskDialog(taskDialog_title, taskDialog_iconPath, taskDialog_text)
        FreeCADGui.Control.showDialog( self.taskDialog )


    def addSelection( self, docName, objName, sub, pnt ):
        '''This method is called when an object is added to the set of currently selected objects.
        
        The method checks if two objects are now selected. If yes, then the parse callback function
        is called to process the selected objects. 
        '''
        obj = FreeCAD.ActiveDocument.getObject(objName)
        Logging.debug('addSelection: docName, objName, obj.Label, sub = %s, %s, %s, %s' % (docName, objName, obj.Label, sub)) # to print selection name

        self.selections.append( SelectionRecord( docName, objName, sub ))
        if len(self.selections) == 2:
            self.stopSelectionObservation()
            self.parseSelectionFunction( self.selections)
        elif self.secondSelectionGate != None and len(self.selections) == 1:
            FreeCADGui.Selection.removeSelectionGate()
            FreeCADGui.Selection.addSelectionGate( self.secondSelectionGate )


    def stopSelectionObservation(self):
        FreeCADGui.Selection.removeObserver(self)
        global wb_globals
        del wb_globals['selectionObserver']
        FreeCADGui.Selection.removeSelectionGate()
        FreeCADGui.Control.closeDialog()
