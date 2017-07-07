
import FreeCADGui
import Logging


class MovePartCommand():

    def Activated(self):
        """This method is called when the command is activated, either 
           through the toolbar or through the menu bar.

        Args:
            self (ImportPartCommand): The reference to the object

        """

        print('MovePartCommand.Activated')


    def GetResources(self):
        """Returns the resources for this command object, like the icon, 
           the menu text or the tool tip.

        Returns:
            dict(str, str): a mapping with "Pixmap", "MenuText" and "ToolTip" 
                            as keys where the values represent the corresponding 
                            resources.
        """

        return {
            'Pixmap' : ':/assembly/icons/movePart.svg',
            'MenuText': 'Move Part',
            'ToolTip': 'Move Part  ( shift+click to copy )'
            }
# This code is executed when the ImportPart module is imported (when the workbench is activated)
Logging.debug('MovePart')
FreeCADGui.addCommand('assembly2_movePart', MovePartCommand())
