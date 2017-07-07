import numpy
from numpy import pi, inf
from numpy.linalg import norm

from Lib3d import quaternion_to_axis_and_angle, axis_to_azimuth_and_elevation_angles
from Lib3d import azimuth_and_elevation_angles_to_axis, quaternion, azimuth_elevation_rotation, azimuth_elevation_rotation_matrix

class VariableManager:
    def __init__(self, doc, objectNames=None):
        self.doc = doc
        self.index = {}
        X = []
        if objectNames == None:
            objectNames = [obj.Name for obj in doc.Objects if hasattr(obj,'Placement')]
        for objectName in objectNames:
            self.index[objectName] = len(X)
            obj = doc.getObject(objectName)
            x, y, z = obj.Placement.Base.x, obj.Placement.Base.y, obj.Placement.Base.z
            axis, theta = quaternion_to_axis_and_angle( *obj.Placement.Rotation.Q )
            if theta != 0:
                azi, ela = axis_to_azimuth_and_elevation_angles(*axis)
            else:
                azi, ela = 0, 0
            X = X + [ x, y, z, azi, ela, theta]
        self.X0 = numpy.array(X)
        self.X = self.X0.copy()

    def updateFreeCADValues(self, X, tol_base = 10.0**-8, tol_rotation = 10**-6):
        for objectName in self.index.keys():
            i = self.index[objectName]
            obj = self.doc.getObject(objectName)
            #obj.Placement.Base.x = X[i]
            #obj.Placement.Base.y = X[i+1]
            #obj.Placement.Base.z = X[i+2]
            if norm( numpy.array(obj.Placement.Base) - X[i:i+3] ) > tol_base: #for speed considerations only update placement variables if change in values occurs
                obj.Placement.Base = tuple( X[i:i+3] )
            azi, ela, theta =  X[i+3:i+6]
            axis = azimuth_and_elevation_angles_to_axis( azi, ela )
            new_Q = quaternion( theta, *axis ) #tuple type
            if norm( numpy.array(obj.Placement.Rotation.Q) - numpy.array(new_Q)) > tol_rotation:
                obj.Placement.Rotation.Q = new_Q

    def bounds(self):
        return [ [ -inf, inf], [ -inf, inf], [ -inf, inf], [-pi,pi], [-pi,pi], [-pi,pi] ] * len(self.index)

    def rotate(self, objectName, p, X):
        'rotate a vector p by objectNames placement variables defined in X'
        i = self.index[objectName]
        return azimuth_elevation_rotation( p, *X[i+3:i+6])

    def rotateUndo( self, objectName, p, X):
        i = self.index[objectName]
        R = azimuth_elevation_rotation_matrix(*X[i+3:i+6])
        return numpy.linalg.solve(R,p)

    def rotateAndMove( self, objectName, p, X):
        'rotate the vector p by objectNames placement rotation and then move using objectNames placement'
        i = self.index[objectName]
        return azimuth_elevation_rotation( p, *X[i+3:i+6]) + X[i:i+3]

    def rotateAndMoveUndo( self, objectName, p, X): # or un(rotate_and_then_move) #synomyn to get co-ordinates relative to objects placement variables.
        i = self.index[objectName]
        v = numpy.array(p) - X[i:i+3]
        R = azimuth_elevation_rotation_matrix(*X[i+3:i+6])
        return numpy.linalg.solve(R,v)
