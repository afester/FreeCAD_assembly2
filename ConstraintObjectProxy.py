import FreeCAD

import Logging
import Preferences


class ConstraintObjectProxy:

    def execute(self, obj):
        Logging.debug('ConstraintObjectProxy.execute()')
        if Preferences.autoSolveConstraintAttributesChanged():
            self.callSolveConstraints()
            #obj.touch()


    def onChanged(self, obj, prop):
        Logging.debug('ConstraintObjectProxy.onChanged()')

        if hasattr(self, 'mirror_name'):
            cMirror = obj.Document.getObject( self.mirror_name )
            if cMirror.Proxy == None:
                return #this occurs during document loading ...
            if obj.getGroupOfProperty( prop ) == 'ConstraintInfo':
                cMirror.Proxy.disable_onChanged = True
                setattr( cMirror, prop, getattr( obj, prop) )
                cMirror.Proxy.disable_onChanged = False


    def reduceDirectionChoices( self, obj, value):
        Logging.debug('ConstraintObjectProxy.reduceDirectionChoices()')
        if hasattr(self, 'mirror_name'):
            cMirror = obj.Document.getObject( self.mirror_name )
            cMirror.directionConstraint = ["aligned","opposed"] #value should be updated in onChanged call due to assignment in 2 lines
        obj.directionConstraint = ["aligned","opposed"]
        obj.directionConstraint = value


    def callSolveConstraints(self):
        Logging.debug('ConstraintObjectProxy.callSolveConstraints()')

        from solver.ConstraintSolver import solveConstraints

        if Preferences.useCache():
            import solver.SolverCache
            solverCache = solver.SolverCache.defaultCache
        else:
            solverCache = None

        solveConstraints( FreeCAD.ActiveDocument, cache = solverCache )
