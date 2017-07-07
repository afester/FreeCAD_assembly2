
import time
import traceback

from PySide import QtGui
import Logging
from AssemblyUtils import removeConstraint
from ConstraintTools import updateOldStyleConstraintProperties
from VariableManager import VariableManager
from ConstraintSystems import Assembly2SolverError, FixedObjectSystem, AddFreeObjectsUnion, AxisAlignmentUnion, VertexUnion, LockRelativeAxialRotationUnion, AxisDistanceUnion, PlaneOffsetUnion, AngleUnion
from numpy import pi

def constraintsObjectsAllExist( doc ):
    Logging.debug("constraintsObjectsAllExist")

    objectNames = [ obj.Name for obj in doc.Objects if not 'ConstraintInfo' in obj.Content ]
    for obj in doc.Objects:
        if 'ConstraintInfo' in obj.Content:
            if not (obj.Object1 in objectNames and obj.Object2 in objectNames):
                flags = QtGui.QMessageBox.StandardButton.Yes | QtGui.QMessageBox.StandardButton.Abort
                message = "%s is refering to an object no longer in the assembly. Delete constraint? otherwise abort solving." % obj.Name
                response = QtGui.QMessageBox.critical(QtGui.qApp.activeWindow(), "Broken Constraint", message, flags )
                if response == QtGui.QMessageBox.Yes:
                    Logging.info("removing constraint %s" % obj.Name)
                    doc.removeObject(obj.Name)
                else:
                    missingObject = obj.Object2 if obj.Object1 in objectNames else obj.Object1
                    Logging.info("aborted solving constraints due to %s refering the non-existent object %s" % (obj.Name, missingObject))
                    return False
    return True


def findBaseObject( doc, objectNames  ):
    Logging.debug('solveConstraints: searching for fixed object to begin solving constraints from.' )
    fixed = [ getattr( doc.getObject( name ), 'fixedPosition', False ) for name in objectNames ]
    if sum(fixed) > 0:
        return objectNames[ fixed.index(True) ]
    if sum(fixed) == 0:
        Logging.warning('It is recommended that the assembly 2 module is used with parts imported using the assembly 2 module.')
        Logging.warning('This allows for part updating, parts list support, object copying (shift + assembly2 move) and also tells the solver which objects to treat as fixed.')
        Logging.warning('since no objects have the fixedPosition attribute, fixing the postion of the first object in the first constraint')
        Logging.warning('assembly 2 solver: assigning %s a fixed position' % objectNames[0])
        Logging.warning('assembly 2 solver: assigning %s, %s a fixed position' % (objectNames[0], doc.getObject(objectNames[0]).Label))
        return objectNames[0]


def solveConstraints( doc, showFailureErrorDialog=True, printErrors=True, cache=None ):
    Logging.debug('solveConstraints')

    if not constraintsObjectsAllExist(doc):
        return

    T_start = time.time()
    updateOldStyleConstraintProperties(doc)
    constraintObjectQue = [ obj for obj in doc.Objects if 'ConstraintInfo' in obj.Content ]
    #doc.Objects already in tree order so no additional sorting / order checking required for constraints.
    objectNames = []
    for c in constraintObjectQue:
        for attr in ['Object1','Object2']:
            objectName = getattr(c, attr, None)
            if objectName != None and not objectName in objectNames:
                objectNames.append( objectName )
    variableManager = VariableManager( doc, objectNames )
    Logging.debug(' variableManager.X0 %s' % variableManager.X0 )
    constraintSystem = FixedObjectSystem( variableManager, findBaseObject(doc, objectNames) )
    Logging.debug('solveConstraints base system: %s' % constraintSystem.str() )

    solved = True
    if cache != None:
        t_cache_start = time.time()
        constraintSystem, que_start = cache.retrieve( constraintSystem, constraintObjectQue)
        Logging.debug("~cached solution available for first %i out-off %i constraints (retrieved in %3.2fs)" % (que_start, len(constraintObjectQue), time.time() - t_cache_start ) )
    else:
        que_start = 0

    for constraintObj in constraintObjectQue[que_start:]:
        Logging.debug('  parsing %s, type:%s' % (constraintObj.Name, constraintObj.Type ))
        try:
            cArgs = [variableManager, constraintObj]
            if not constraintSystem.containtsObject( constraintObj.Object1) and not constraintSystem.containtsObject( constraintObj.Object2):
                constraintSystem = AddFreeObjectsUnion(constraintSystem, *cArgs)

            if constraintObj.Type == 'plane':
                if constraintObj.SubElement2.startswith('Face'): #otherwise vertex
                    constraintSystem = AxisAlignmentUnion(constraintSystem, *cArgs,  constraintValue = constraintObj.directionConstraint )
                constraintSystem = PlaneOffsetUnion(constraintSystem,  *cArgs, constraintValue = constraintObj.offset.Value)
            elif constraintObj.Type == 'angle_between_planes':
                constraintSystem = AngleUnion(constraintSystem,  *cArgs, constraintValue = constraintObj.angle.Value*pi/180 )
            elif constraintObj.Type == 'axial':
                constraintSystem = AxisAlignmentUnion(constraintSystem,  *cArgs, constraintValue = constraintObj.directionConstraint)
                constraintSystem =  AxisDistanceUnion(constraintSystem,  *cArgs, constraintValue = 0)
                if constraintObj.lockRotation: constraintSystem =  LockRelativeAxialRotationUnion(constraintSystem,  *cArgs, constraintValue = 0)
            elif constraintObj.Type == 'circularEdge':
                constraintSystem = AxisAlignmentUnion(constraintSystem,  *cArgs, constraintValue=constraintObj.directionConstraint)
                constraintSystem = AxisDistanceUnion(constraintSystem,  *cArgs, constraintValue=0)
                constraintSystem = PlaneOffsetUnion(constraintSystem,  *cArgs, constraintValue=constraintObj.offset.Value)
                if constraintObj.lockRotation: constraintSystem =  LockRelativeAxialRotationUnion(constraintSystem,  *cArgs, constraintValue = 0)
            elif constraintObj.Type == 'sphericalSurface':
                constraintSystem = VertexUnion(constraintSystem,  *cArgs, constraintValue=0)
            else:
                raise NotImplementedError('constraintType %s not supported yet' % constraintObj.Type)

            if cache:
                cache.record_levels.append( constraintSystem.numberOfParentSystems() )
        except Assembly2SolverError as e:
            if printErrors:
                Logging.error('UNABLE TO SOLVE CONSTRAINTS! info:')
                Logging.error(e)
            solved = False
            break
        except:
            if printErrors:
                Logging.error('UNABLE TO SOLVE CONSTRAINTS! info:')
                Logging.error( traceback.format_exc())
            solved = False
            break
        
    if solved:
        Logging.debug('placement X %s' % constraintSystem.variableManager.X )

        t_cache_record_start = time.time()
        if cache:
            cache.record( constraintSystem, constraintObjectQue, que_start)
        Logging.debug('  time cache.record %3.2fs' % (time.time()-t_cache_record_start) )

        t_update_freecad_start = time.time()
        variableManager.updateFreeCADValues( constraintSystem.variableManager.X )
        Logging.debug('  time to update FreeCAD placement variables %3.2fs' % (time.time()-t_update_freecad_start) )

        Logging.debug('Constraint system solved in %2.2fs; resulting system has %i degrees-of-freedom' % (time.time()-T_start, len( constraintSystem.degreesOfFreedom)))
    elif showFailureErrorDialog and  QtGui.qApp != None: #i.e. GUI active
        # http://www.blog.pythonlibrary.org/2013/04/16/pyside-standard-dialogs-and-message-boxes/
        flags = QtGui.QMessageBox.StandardButton.Yes
        flags |= QtGui.QMessageBox.StandardButton.No
        #flags |= QtGui.QMessageBox.Ignore
        message = """The assembly2 solver failed to satisfy the constraint "%s".

possible causes
  - impossible/contridictorary constraints have be specified, or
  - the contraint problem is too difficult for the solver, or
  - a bug in the assembly 2 workbench

potential solutions
  - redefine the constraint (popup menu item in the treeView)
  - delete constraint, and try again using a different constraint scheme.

Delete constraint "%s"?
""" % (constraintObj.Name, constraintObj.Name)
        response = QtGui.QMessageBox.critical(QtGui.qApp.activeWindow(), "Solver Failure!", message, flags)
        if response == QtGui.QMessageBox.Yes:
            removeConstraint( constraintObj )
        #elif response == QtGui.QMessageBox.Ignore:
        #    variableManager.updateFreeCADValues( constraintSystem.variableManager.X )
    return constraintSystem if solved else None
