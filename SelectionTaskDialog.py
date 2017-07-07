from PySide import QtGui

import Logging

global wb_globals

class SelectionTaskDialog:
    
    def __init__(self, title, iconPath, textLines ):
        self.form = SelectionTaskDialogForm( textLines )
        self.form.setWindowTitle( title )
        if iconPath != None:
            self.form.setWindowIcon( QtGui.QIcon( iconPath ) )

    def reject(self):
        Logging.debug('Cancelling selection observation')
        global wb_globals
        wb_globals['selectionObserver'].stopSelectionObservation()

    def getStandardButtons(self): #http://forum.freecadweb.org/viewtopic.php?f=10&t=11801
        return 0x00400000 #cancel button


class SelectionTaskDialogForm(QtGui.QWidget):
    
    def __init__(self, textLines ):
        super(SelectionTaskDialogForm, self).__init__()
        self.textLines = textLines
        self.initUI()

    def initUI(self):
        vbox = QtGui.QVBoxLayout()
        for line in self.textLines.split('\n'):
            vbox.addWidget( QtGui.QLabel(line) )
        self.setLayout(vbox)
