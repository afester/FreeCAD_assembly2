import numpy
from numpy import pi, dot
from numpy.linalg import norm
from Lib3d import rotation_required_to_rotate_a_vector_to_be_aligned_to_another_vector, axis_rotation_matrix, azimuth_elevation_rotation_matrix
from Lib3d import axis_to_azimuth_and_elevation_angles, rotation_matrix_axis_and_angle, plane_degrees_of_freedom, gram_schmidt_orthonormalization


maxStep_linearDisplacement = 10.0

class PlacementDegreeOfFreedom:
    def __init__(self, parentSystem, objName, object_dof):
        self.system = parentSystem
        self.objName = objName
        self.object_dof = object_dof
        self.vM = parentSystem.variableManager
        self.ind = parentSystem.variableManager.index[objName] + object_dof
        if self.ind % 6 < 3:
            self.directionVector = numpy.zeros(3)
            self.directionVector[ self.ind % 6 ] = 1

    def getValue( self):
        return self.vM.X[self.ind]

    def setValue( self, value):
        self.vM.X[self.ind] = value
    
    def maxStep(self):
        if self.ind % 6 < 3:
            return maxStep_linearDisplacement
        else:
            return pi/5
    
    def rotational(self):
        return self.ind % 6 > 2
    
    def migrate_to_new_variableManager( self, new_vM):
        self.vM = new_vM
        self.ind =  new_vM.index[self.objName] + self.object_dof
    
    def str(self, indent=''):
        return '%s<Placement DegreeOfFreedom %s-%s value:%f>' % (indent, self.objName, ['x','y','z','azimuth','elavation','rotation'][self.ind % 6], self.getValue())
    
    def __repr__(self):
        return self.str()


class LinearMotionDegreeOfFreedom:
    def __init__(self, parentSystem, objName):
        self.system = parentSystem
        self.objName = objName
        self.vM = parentSystem.variableManager
        self.objInd = parentSystem.variableManager.index[objName]
        
    def setDirection(self, directionVector):
        self.directionVector = directionVector
        
    def getValue( self ):
        i = self.objInd
        return dot( self.directionVector, self.vM.X[i:i+3])
    
    def setValue( self, value):
        currentValue = self.getValue()
        correction = (value -currentValue)*self.directionVector
        i = self.objInd
        self.vM.X[i:i+3] = self.vM.X[i:i+3] + correction
        
    def maxStep(self):
        return maxStep_linearDisplacement #inf
    
    def rotational(self):
        return False
    
    def migrate_to_new_variableManager( self, new_vM):
        self.vM = new_vM
        self.objInd =  new_vM.index[self.objName]
        
    def str(self, indent=''):
        return '%s<LinearMotion DegreeOfFreedom %s direction:%s value:%f>' % (indent, self.objName, self.directionVector, self.getValue())
    
    def __repr__(self):
        return self.str()


class AxisRotationDegreeOfFreedom:
    '''
    calculate the rotation variables ( azi, ela, angle )so that
    R_effective = R_about_axis * R_to_align_axis
    where
      R = azimuth_elevation_rotation_matrix(azi, ela, theta )

    '''
    def __init__(self, parentSystem, objName):
        self.system = parentSystem
        self.vM = parentSystem.variableManager
        self.objName = objName
        self.objInd = self.vM.index[objName]

    def setAxis(self, axis, axis_r, check_R_to_align_axis=False):
        if not ( hasattr(self, 'axis') and numpy.array_equal( self.axis, axis )): #if to avoid unnessary updates.
            self.axis = axis
            axis2, angle2 = rotation_required_to_rotate_a_vector_to_be_aligned_to_another_vector( axis_r, axis )
            self.R_to_align_axis = axis_rotation_matrix(  angle2, *axis2 )
            if check_R_to_align_axis:
                print('NOTE: checking AxisRotationDegreeOfFreedom self.R_to_align_axis')
                if norm(  dot(self.R_to_align_axis, axis_r) - axis ) > 10**-12:
                    raise ValueError(" dotProduct(self.R_to_align_axis, axis_r) - axis ) [%e] > 10**-12" % norm(  dot(self.R_to_align_axis, axis_r) - axis ))

            if not hasattr(self, 'x_ref_r'):
                self.x_ref_r, self.y_ref_r  =  plane_degrees_of_freedom( axis_r )
            else: #use gram_schmidt_orthonormalization ; import for case where axis close to z-axis, where numerical noise effects the azimuth angle used to generate plane DOF...
                notUsed, self.x_ref_r, self.y_ref_r = gram_schmidt_orthonormalization( axis_r,  self.x_ref_r, self.y_ref_r) #still getting wonky rotations :(
            self.x_ref = dot(self.R_to_align_axis, self.x_ref_r)
            self.y_ref = dot(self.R_to_align_axis, self.y_ref_r)

    def determine_R_about_axis(self, R_effective, checkAnswer=True, tol=10**-12): #not used anymore
        'determine R_about_axis so that R_effective = R_about_axis * R_to_align_axis'
        A = self.R_to_align_axis.transpose()
        X = numpy.array([
                numpy.linalg.solve(A, R_effective[row,:]) for row in range(3)
                ])
        #prettyPrintArray(X)
        if checkAnswer:
            print('  determine_R_about_axis: diff between R_effective and R_about_axis * R_to_align_axis (should be all close to zero):')
            error = R_effective - dot(X, self.R_to_align_axis)
            assert norm(error) <= tol
        return X

    def vectorsAngleInDofsCoordinateSystem(self,v):
        return numpy.arctan2(
                dot(self.y_ref, v),
                dot(self.x_ref, v),
                )
        
    def getValue( self, refApproach=True, tol=10**-7 ):
        i = self.objInd
        R_effective = azimuth_elevation_rotation_matrix( *self.vM.X[i+3:i+6] )
        if refApproach:
            v = dot( R_effective, self.x_ref_r)
            if tol != None and abs( dot(v, self.axis) ) > tol:
                raise ValueError("abs( dotProduct(v, self.axis) ) > %e [error %e]" % (tol, abs( dot(v, self.axis) )))
            angle = self.vectorsAngleInDofsCoordinateSystem(v)
        else:
            raise NotImplementedError("does not work yet")
            R_effective = azimuth_elevation_rotation_matrix( *self.vM.X[i+3:i+6] )
            R_about_axis = self.determine_R_about_axis(R_effective)
            axis, angle =  rotation_matrix_axis_and_angle( R_about_axis )
            print( axis )
            print( self.axis )
            # does not work because   axis(R_about_axis) != self.axis #which is damm weird if you ask me
        return angle

    def setValue( self, angle):
        R_about_axis = axis_rotation_matrix( angle, *self.axis )
        R = dot(R_about_axis, self.R_to_align_axis)
        axis, angle = rotation_matrix_axis_and_angle( R )
        #todo, change to quaternions
        #Q2 = quaternion2( self.value, *self.axis )
        #q0,q1,q2,q3 = quaternion_multiply( Q2, self.Q1 )
        #axis, angle = quaternion_to_axis_and_angle( q1, q2, q3, q0 )
        azi, ela = axis_to_azimuth_and_elevation_angles(*axis)
        i = self.objInd
        self.vM.X[i+3:i+6] = azi, ela, angle

    def maxStep(self):
        return pi/5

    def rotational(self):
        return True
    
    def migrate_to_new_variableManager( self, new_vM):
        self.vM = new_vM
        self.objInd =  new_vM.index[self.objName]
    
    def str(self, indent=''):
        return '%s<AxisRotation DegreeOfFreedom %s axis:%s value:%f>' % (indent, self.objName, self.axis, self.getValue())
    
    def __repr__(self):
        return self.str()

