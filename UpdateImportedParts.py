
import FreeCADGui
import Logging

class UpdateImportedPartsCommand():


    def updatePart(self, fileName, partName, doc_assembly):
        pass
#===============================================================================
#         if doc_assembly == None:
#             doc_assembly = FreeCAD.ActiveDocument
# 
#         updateExistingPart = partName != None
#         if updateExistingPart:
#             FreeCAD.Console.PrintMessage('Updating part {} from {}\n'.format(partName, fileName))
#         else:
#             FreeCAD.Console.PrintMessage('Importing part from {}\n'.format(fileName))
# 
#         partAlreadyOpened = fileName in [ d.FileName for d in FreeCAD.listDocuments().values() ]
#         FreeCAD.Console.PrintMessage('Part {} open already: {}\n'.format(fileName, partAlreadyOpened))
#         if partAlreadyOpened:
#             doc = [ d for d in FreeCAD.listDocuments().values() if d.FileName == fileName][0]
#         else:
#             if fileName.lower().endswith('.fcstd'):
#                 doc = FreeCAD.openDocument(fileName)
#                 FreeCAD.Console.PrintMessage('Succesfully opened {}\n'.format(fileName))
#             else: #trying shaping import http://forum.freecadweb.org/viewtopic.php?f=22&t=12434&p=99772#p99772x
#                 msg = 'ONLY *.fcstd files currently supported!'
#                 QtGui.QMessageBox.information(  QtGui.qApp.activeWindow(), "Value Error", msg )
#                 return
#                 #import ImportGui
#                 #doc = FreeCAD.newDocument( os.path.basename(filename) )
#                 #shapeobj=ImportGui.insert(filename,doc.Name)
# 
#         # Get the source object from the loaded document
#         visibleObjects = [ obj for obj in doc.Objects
#                            if hasattr(obj,'ViewObject') and obj.ViewObject.isVisible()
#                               and hasattr(obj,'Shape') 
#                               and len(obj.Shape.Faces) > 0 
#                               and 'Body' not in obj.Name] # len(obj.Shape.Faces) > 0 to avoid sketch
#         
#         if len(visibleObjects) == 1 and not any([ 'importPart' in obj.Content for obj in doc.Objects]):
#             subAssemblyImport = False
#             if len(visibleObjects) != 1:
#                 if not updateExistingPart:
#                     msg = 'A part can only be imported from a FreeCAD document with exactly one visible part. Aborting operation'
#                     QtGui.QMessageBox.information( QtGui.qApp.activeWindow(), "Value Error", msg )
#                 else:
#                     msg = 'Error updating part from %s: A part can only be imported from a FreeCAD document with exactly one visible part. Aborting update of %s'.format(partName, fileName)
#                     QtGui.QMessageBox.information( QtGui.qApp.activeWindow(), "Value Error", msg )
#                 return
# 
#             sourceObject = visibleObjects[0]
#         else:
#             subAssemblyImport = True
#             msg = 'Sub assembly import not yet implemented!'
#             QtGui.QMessageBox.information(  QtGui.qApp.activeWindow(), "Value Error", msg )
#             return
# 
#         FreeCAD.Console.PrintMessage("Source object: {}\n".format(sourceObject.Label))
# 
#         if updateExistingPart:
#             pass
#             #obj = doc_assembly.getObject(partName)
#             #prevPlacement = obj.Placement
#             #if not hasattr(obj, 'updateColors'):
#             #    obj.addProperty("App::PropertyBool","updateColors","importPart").updateColors = True
#             #importUpdateConstraintSubobjects( doc_assembly, obj, obj_to_copy )
#         else:
#             partName = AssemblyUtils.findUnusedObjectName( doc.Label + '_', document=doc_assembly )
#             try:
#                 obj = doc_assembly.addObject("Part::FeaturePython", partName)
#             except UnicodeEncodeError:
#                 safeName = AssemblyUtils.findUnusedObjectName('import_', document=doc_assembly)
#                 obj = doc_assembly.addObject("Part::FeaturePython", safeName)
#                 obj.Label = AssemblyUtils.findUnusedLabel( doc.Label + '_', document=doc_assembly )
# 
#             obj.addProperty("App::PropertyFile",  "sourceFile",    "importPart").sourceFile = fileName
#             obj.addProperty("App::PropertyFloat", "timeLastImport","importPart")
#             obj.setEditorMode("timeLastImport", 1)
#             obj.addProperty("App::PropertyBool","fixedPosition","importPart")
#             obj.fixedPosition = not any([i.fixedPosition for i in doc_assembly.Objects if hasattr(i, 'fixedPosition') ])
#             obj.addProperty("App::PropertyBool","updateColors","importPart").updateColors = True
# 
#         obj.Shape = sourceObject.Shape.copy()
# 
#         if updateExistingPart:
#             # obj.Placement = prevPlacement
#             pass
#         else:
#             for p in sourceObject.ViewObject.PropertiesList: #assuming that the user may change the appearance of parts differently depending on the assembly.
#                 if hasattr(obj.ViewObject, p) and p not in ['DiffuseColor']:
#                     setattr(obj.ViewObject, p, getattr(sourceObject.ViewObject, p))
#             obj.ViewObject.Proxy = ImportedPartViewProviderProxy()
# 
#         if getattr(obj,'updateColors', True):
#             obj.ViewObject.DiffuseColor = copy.copy( sourceObject.ViewObject.DiffuseColor )
#             #obj.ViewObject.Transparency = copy.copy( obj_to_copy.ViewObject.Transparency )   # .Transparency property
#             tsp = copy.copy( sourceObject.ViewObject.Transparency )   #  .Transparency workaround for FC 0.17 @ Nov 2016
#             if tsp < 100 and tsp != 0:
#                 obj.ViewObject.Transparency = tsp + 1
#             if tsp == 100:
#                 obj.ViewObject.Transparency = tsp - 1
#             obj.ViewObject.Transparency = tsp   # .Transparency workaround end
# 
#         obj.Proxy = Proxy_importPart()
#         obj.timeLastImport = os.path.getmtime( fileName )
# 
#         if subAssemblyImport:
#             #doc_assembly.removeObject(tempPartName)
#             pass
# 
#         if not partAlreadyOpened: #then close again
#             FreeCAD.closeDocument(doc.Name)
#             FreeCAD.setActiveDocument(doc_assembly.Name)
#             FreeCAD.ActiveDocument = doc_assembly
# 
#         FreeCAD.Console.PrintMessage('Import done.\n');
#         return obj
#===============================================================================

    def Activated(self):
        """This method is called when the command is activated, either 
           through the toolbar or through the menu bar.

        Args:
            self (ImportPartCommand): The reference to the object

        """

        print('UpdateImportedPartsCommand.Activated')


    def GetResources(self):
        """Returns the resources for this command object, like the icon, 
           the menu text or the tool tip.

        Returns:
            dict(str, str): a mapping with "Pixmap", "MenuText" and "ToolTip" 
                            as keys where the values represent the corresponding 
                            resources.
        """

        return {
            'Pixmap' : ':/assembly/icons/updateParts.svg',
            'MenuText': 'Update parts',
            'ToolTip': 'Update parts imported into the assembly'
            }
        

# This code is executed when the ImportPart module is imported (when the workbench is activated)
Logging.debug('UpdateImportedParts')
FreeCADGui.addCommand('updateImportedPartsCommand', UpdateImportedPartsCommand())
