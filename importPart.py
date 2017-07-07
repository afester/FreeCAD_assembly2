import os, copy
import FreeCADGui
import FreeCAD
import Logging

from PySide import QtGui
from PySide import QtCore

from ImportedPartViewProviderProxy import ImportedPartViewProviderProxy
import AssemblyUtils
from PartMover import PartMover

 
class Proxy_importPart:
    def execute(self, shape):
        pass

class ImportPartCommand():


    def importPart(self, fileName, partName=None, doc_assembly=None):
        if doc_assembly == None:
            doc_assembly = FreeCAD.ActiveDocument

        Logging.info('Importing part from {}'.format(fileName))

        partAlreadyOpened = fileName in [ d.FileName for d in FreeCAD.listDocuments().values() ]
        Logging.info('Part {} open already: {}'.format(fileName, partAlreadyOpened))
        if partAlreadyOpened:
            doc = [ d for d in FreeCAD.listDocuments().values() if d.FileName == fileName][0]
        else:
            if fileName.lower().endswith('.fcstd'):
                doc = FreeCAD.openDocument(fileName)
                Logging.info('Succesfully opened {}'.format(fileName))
            else: #trying shaping import http://forum.freecadweb.org/viewtopic.php?f=22&t=12434&p=99772#p99772x
                msg = 'ONLY *.fcstd files currently supported!'
                QtGui.QMessageBox.information(  QtGui.qApp.activeWindow(), "Value Error", msg )
                return
                #import ImportGui
                #doc = FreeCAD.newDocument( os.path.basename(filename) )
                #shapeobj=ImportGui.insert(filename,doc.Name)

        # Get the source object from the loaded document
        visibleObjects = [ obj for obj in doc.Objects
                           if hasattr(obj,'ViewObject') and obj.ViewObject.isVisible()
                              and hasattr(obj,'Shape') 
                              and len(obj.Shape.Faces) > 0 
                              and 'Body' not in obj.Name] # len(obj.Shape.Faces) > 0 to avoid sketch
        
        if len(visibleObjects) == 1 and not any([ 'importPart' in obj.Content for obj in doc.Objects]):
            subAssemblyImport = False
            if len(visibleObjects) != 1:
                msg = 'A part can only be imported from a FreeCAD document with exactly one visible part. Aborting operation'
                QtGui.QMessageBox.information( QtGui.qApp.activeWindow(), "Value Error", msg )
                return

            sourceObject = visibleObjects[0]
        else:
            subAssemblyImport = True
            msg = 'Sub assembly import not yet implemented!'
            QtGui.QMessageBox.information(  QtGui.qApp.activeWindow(), "Value Error", msg )
            return

        Logging.info('Source object: {}'.format(sourceObject.Label))

        partName = AssemblyUtils.findUnusedObjectName( doc.Label + '_', document=doc_assembly )
        try:
            obj = doc_assembly.addObject("Part::FeaturePython", partName)
        except UnicodeEncodeError:
            safeName = AssemblyUtils.findUnusedObjectName('import_', document=doc_assembly)
            obj = doc_assembly.addObject("Part::FeaturePython", safeName)
            obj.Label = AssemblyUtils.findUnusedLabel( doc.Label + '_', document=doc_assembly )

        obj.addProperty("App::PropertyFile",  "sourceFile",    "importPart").sourceFile = fileName
        obj.addProperty("App::PropertyFloat", "timeLastImport","importPart")
        obj.setEditorMode("timeLastImport", 1)
        obj.addProperty("App::PropertyBool","fixedPosition","importPart")
        obj.fixedPosition = not any([i.fixedPosition for i in doc_assembly.Objects if hasattr(i, 'fixedPosition') ])
        obj.addProperty("App::PropertyBool","updateColors","importPart").updateColors = True

        obj.Shape = sourceObject.Shape.copy()

        for p in sourceObject.ViewObject.PropertiesList: #assuming that the user may change the appearance of parts differently depending on the assembly.
            if hasattr(obj.ViewObject, p) and p not in ['DiffuseColor']:
                setattr(obj.ViewObject, p, getattr(sourceObject.ViewObject, p))
        obj.ViewObject.Proxy = ImportedPartViewProviderProxy()

        if getattr(obj,'updateColors', True):
            obj.ViewObject.DiffuseColor = copy.copy( sourceObject.ViewObject.DiffuseColor )
            #obj.ViewObject.Transparency = copy.copy( obj_to_copy.ViewObject.Transparency )   # .Transparency property
            tsp = copy.copy( sourceObject.ViewObject.Transparency )   #  .Transparency workaround for FC 0.17 @ Nov 2016
            if tsp < 100 and tsp != 0:
                obj.ViewObject.Transparency = tsp + 1
            if tsp == 100:
                obj.ViewObject.Transparency = tsp - 1
            obj.ViewObject.Transparency = tsp   # .Transparency workaround end

        obj.Proxy = Proxy_importPart()
        obj.timeLastImport = os.path.getmtime( fileName )

        if subAssemblyImport:
            #doc_assembly.removeObject(tempPartName)
            pass

        if not partAlreadyOpened: #then close again
            FreeCAD.closeDocument(doc.Name)
            FreeCAD.setActiveDocument(doc_assembly.Name)
            FreeCAD.ActiveDocument = doc_assembly

        Logging.info('Import done.');
        return obj


    def Activated(self):
        """This method is called when the command is activated, either 
           through the toolbar or through the menu bar.

        Args:
            self (ImportPartCommand): The reference to the object

        """

        print('ImportPartCommand.Activated')

        if FreeCADGui.ActiveDocument == None:
            FreeCAD.newDocument()

        dialog = QtGui.QFileDialog(
            QtGui.qApp.activeWindow(),
            "Select FreeCAD document to import part from"
            )
        dialog.setNameFilter("Supported Formats (*.FCStd *.brep *.brp *.imp *.iges *.igs *.obj *.step *.stp);;All files (*.*)")
        if dialog.exec_():
            fileName = dialog.selectedFiles()[0]
        else:
            return

        importedObject = self.importPart( fileName )

        FreeCAD.ActiveDocument.recompute()
        if not importedObject.fixedPosition: #will be true for the first imported part
            Logging.info('Activating part mover')
            view = FreeCADGui.activeDocument().activeView()
            PartMover( view, importedObject )
        else:
            from PySide import QtCore
            self.timer = QtCore.QTimer()
            QtCore.QObject.connect(self.timer, QtCore.SIGNAL("timeout()"), self.GuiViewFit)
            self.timer.start( 200 ) #0.2 seconds

        FreeCAD.ActiveDocument.recompute()


    def GuiViewFit(self):
        FreeCADGui.SendMsgToActiveView("ViewFit")
        self.timer.stop()


    def GetResources(self):
        """Returns the resources for this command object, like the icon, 
           the menu text or the tool tip.

        Returns:
            dict(str, str): a mapping with "Pixmap", "MenuText" and "ToolTip" 
                            as keys where the values represent the corresponding 
                            resources.
        """

        return {
            'Pixmap'   : ':/assembly/icons/importPart.svg',
            'MenuText' : QtCore.QObject.tr('Import Part ...'),
            'ToolTip'  : 'Import a part from another FreeCAD document'
            }
        

# This code is executed when the ImportPart module is imported (when the workbench is activated)
Logging.debug('ImportPart')
FreeCADGui.addCommand('importPart', ImportPartCommand())
