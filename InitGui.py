

from PySide import QtCore
import AssemblyUtils
import Logging


class AssemblyWorkbench(Workbench):
    MenuText = 'Assembly 3'
    Icon = ':/assembly/icons/workBenchIcon.svg'

    def Initialize(self):
        import Logging  # otherwise "global name Logging undefined" !!?!
        Logging.debug('AssemblyWorkbench.Initialize()')

        import ImportPart, UpdateImportedParts, MovePart
        import PlaneConstraint, CircularEdgeConstraint, AxialConstraint, AngleConstraint, SphericalSurfaceConstraint
        import DegreesOfFreedomAnimation, SolveConstraints, MuxAssembly, MuxAssemblyRefresh, AddPartsList, CheckAssembly

        commandslist = [
            'importPart',
            'updateImportedPartsCommand',
            'assembly2_movePart',
            'Separator',
            'addPlaneConstraint',
            'addCircularEdgeConstraint',
            'addAxialConstraint',
            'addAngleConstraint',
            'addSphericalSurfaceConstraint',
            'Separator',
            'degreesOfFreedomAnimation',
            'assembly2SolveConstraints',
            'muxAssembly',
            'muxAssemblyRefresh',
            'addPartsList',
            'assembly2_checkAssembly'
            ]
        self.appendToolbar(self.MenuText, commandslist)

        #shortcut_commandslist = [
        #    'flipLastConstraintsDirection',
        #    'lockLastConstraintsRotation',
        #    'boltMultipleCircularEdges',
        #    ]
        #self.appendToolbar('Assembly 2 shortcuts', shortcut_commandslist )
        #self.treecmdList = ['importPart', 'updateImportedPartsCommand']

        # Add icon search path for implicit icons, like preferences-assembly
        FreeCADGui.addIconPath( ':/assembly/icons' )

        FreeCADGui.addPreferencePage(':/assembly/ui/PreferencesPage.ui', 'Assembly')
        self.appendMenu(self.MenuText, commandslist)

    def Activated(self):
        import Logging # otherwise "global name Logging undefined" !!?!
        Logging.debug('AssemblyWorkbench.Activated')
        
# This code is called when the module is detected by FreeCAD
resourceFile = AssemblyUtils.getResourceFilePath()
Logging.info('Resource file: {}'.format(resourceFile))
resourcesLoaded = QtCore.QResource.registerResource(resourceFile)
Logging.info('Resources loaded: {}'.format(resourcesLoaded))

Gui.addWorkbench(AssemblyWorkbench())
