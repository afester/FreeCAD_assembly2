
import FreeCAD
import FreeCADGui

from solver.ConstraintSolver import solveConstraints
import Preferences 

class Assembly2SolveConstraintsCommand:
    def Activated(self):
        if Preferences.useCache():
            import solver.SolverCache
            solverCache = solver.SolverCache.defaultCache
        else:
            solverCache = None

        solveConstraints( FreeCAD.ActiveDocument, cache = solverCache )

    def GetResources(self):
        return {
            'Pixmap'  : ':/assembly/icons/solveConstraints.svg',
            'MenuText': 'Solve constraints',
            'ToolTip' : 'Solve all Assembly constraints'
            }

FreeCADGui.addCommand('assembly2SolveConstraints', Assembly2SolveConstraintsCommand())
