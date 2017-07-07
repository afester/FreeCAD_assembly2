
import FreeCAD
import FreeCADGui

import Logging

from MuxAssembly import createMuxedAssembly

class MuxAssemblyRefreshCommand:
    def Activated(self):

        #first list all muxes in active document
        allMuxesList=[]
        for objlst in FreeCAD.ActiveDocument.Objects:
            if hasattr(objlst,'type'):
                if 'muxedAssembly' in objlst.type:
                    if objlst.ReadOnly==False:
                        allMuxesList.append(objlst.Name)
        #Second, create a list of selected objects and check if there is a mux
        allSelMuxesList=[]
        for objlst in FreeCADGui.Selection.getSelection():
            tmpobj = FreeCAD.ActiveDocument.getObject(objlst.Name)
            if 'muxedAssembly' in tmpobj.type:
                if tmpobj.ReadOnly==False:
                    allSelMuxesList.append(objlst.Name)
        refreshMuxesList=[]
        if len(allSelMuxesList) > 0 :
            refreshMuxesList=allSelMuxesList
            Logging.debug('there are %d muxes in selected objects' % len(allSelMuxesList))
        else:
            if len(allMuxesList) > 0 :
                Logging.debug('there are %d muxes in Active Document' % len(allMuxesList))
                refreshMuxesList=allMuxesList
            #ok there are at least 1 mux to refresh, we have to retrieve the object list for each mux
        if len(refreshMuxesList)>0:
            FreeCADGui.Selection.clearSelection()
            for muxesobj in refreshMuxesList:
                for newselobjs in FreeCAD.ActiveDocument.getObject(muxesobj).muxedObjectList:
                    FreeCADGui.Selection.addSelection(FreeCAD.ActiveDocument.getObject(newselobjs))
                tmpstr=FreeCAD.ActiveDocument.getObject(muxesobj).Label
                FreeCAD.ActiveDocument.removeObject(muxesobj)
                Logging.debug('Refreshing Assembly Mux '+muxesobj)
                createMuxedAssembly(tmpstr)

        else:
            Logging.debug('there are no muxes in Active Document' )

        FreeCADGui.Selection.clearSelection()
        FreeCAD.ActiveDocument.recompute()


    def GetResources(self):

        return {
            'Pixmap'  : ':/assembly2/icons/muxAssemblyRefresh.svg',
            'MenuText': 'Refresh all combined objects',
            'ToolTip' : 'Refresh all muxedAssembly\nor refresh all selected muxedAssembly\nUse the ReadOnly property to avoid accidental refresh'
        }

FreeCADGui.addCommand('muxAssemblyRefresh', MuxAssemblyRefreshCommand())
