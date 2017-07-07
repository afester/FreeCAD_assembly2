import pickle
import numpy
from numpy import dot, cross, sin, cos, arctan2, arcsin, arccos, pi
from numpy.linalg import norm


def arccos2( v, allowableNumericalError=10**-1 ):
    if -1 <= v and v <= 1:
        return arccos(v)
    elif abs(v) -1 < allowableNumericalError:
        return 0 if v > 0 else pi
    else:
        raise ValueError("arccos2 called with invalid input of %s" % v)


def arcsin2( v, allowableNumericalError=10**-1 ):
    if -1 <= v and v <= 1:
        return arcsin(v)
    elif abs(v) -1 < allowableNumericalError:
        return pi/2 if v > 0 else -pi/2
    else:
        raise ValueError("arcsin2 called with invalid input of %s" % v)


def normalize( v ):
    return v / norm(v)


def gram_schmidt_proj(u,v):
    return dot(v,u)/dot(u,u)*u


def gram_schmidt_orthonormalization( v1, v2, v3 ):
    'https://en.wikipedia.org/wiki/Gram%E2%80%93Schmidt_process'
    u1 = v1
    u2 = v2 - gram_schmidt_proj(u1,v2)
    u3 = v3 - gram_schmidt_proj(u1,v3) - gram_schmidt_proj(u2,v3)
    return normalize(u1), normalize(u2), normalize(u3)


def axis_to_azimuth_and_elevation_angles( u_x, u_y, u_z ):
    return arctan2( u_y, u_x), arcsin2(u_z)


def azimuth_and_elevation_angles_to_axis( a, e):
    u_z = sin(e)
    u_x = cos(e)*cos(a)
    u_y = cos(e)*sin(a)
    return numpy.array([ u_x, u_y, u_z ])

def quaternion(theta, u_x, u_y, u_z ):
    '''http://en.wikipedia.org/wiki/Quaternions_and_spatial_rotation
    returns q_1, q_2, q_3, q_0 as to match FreeCads, if wikipedias naming is used'''
    return ( u_x*sin(theta/2), u_y*sin(theta/2), u_z*sin(theta/2), cos(theta/2) )


def quaternion_to_axis_and_angle(  q_1, q_2, q_3, q_0):
    'http://en.wikipedia.org/wiki/Rotation_formalisms_in_three_dimensions'
    q =  numpy.array( [q_1, q_2, q_3])
    if norm(q) > 0:
        return q/norm(q), 2*arccos2(q_0)
    else:
        return numpy.array([1.0,0,0]), 2*arccos2(q_0)


def axis_rotation_matrix( theta, u_x, u_y, u_z ):
    ''' http://en.wikipedia.org/wiki/Rotation_matrix '''
    return numpy.array( [
            [ cos(theta) + u_x**2 * ( 1 - cos(theta)) , u_x*u_y*(1-cos(theta)) - u_z*sin(theta) ,  u_x*u_z*(1-cos(theta)) + u_y*sin(theta) ] ,
            [ u_y*u_x*(1-cos(theta)) + u_z*sin(theta) , cos(theta) + u_y**2 * (1-cos(theta))    ,  u_y*u_z*(1-cos(theta)) - u_x*sin(theta )] ,
            [ u_z*u_x*(1-cos(theta)) - u_y*sin(theta) , u_z*u_y*(1-cos(theta)) + u_x*sin(theta) ,              cos(theta) + u_z**2*(1-cos(theta))   ]
            ])


def azimuth_elevation_rotation_matrix(azi, ela, theta ):
    #print('azimuth_and_elevation_angles_to_axis(azi, ela) %s' % azimuth_and_elevation_angles_to_axis(azi, ela))
    return axis_rotation_matrix( theta, *azimuth_and_elevation_angles_to_axis(azi, ela))


def azimuth_elevation_rotation( p, azi, ela, theta ):
    return dot(azimuth_elevation_rotation_matrix( azi, ela, theta ), p)


def distance_between_axis_and_point( p1,u1,p2 ):
    assert numpy.linalg.norm( u1 ) != 0
    d = p2 - p1
    offset = d - dot(u1,d)*u1
    #print(norm(offset))
    return norm(offset)




def rotation_matrix_axis_and_angle(R, debug=False, checkAnswer=True, errorThreshold=10**-7, angle_pi_tol = 10**-5):
    'http://en.wikipedia.org/wiki/Rotation_formalisms_in_three_dimensions#Rotation_matrix_.E2.86.94_Euler_axis.2Fangle'
    a = arccos2( 0.5 * ( R[0,0]+R[1,1]+R[2,2] - 1) )
    if abs(a % pi) > angle_pi_tol and abs(pi - (a % pi)) > angle_pi_tol:
        msg='checking angles sign, angle %f' % a
        for angle in [a, -a]:
            u_x = 0.5* (R[2,1]-R[1,2]) / sin(angle)
            u_y = 0.5* (R[0,2]-R[2,0]) / sin(angle)
            u_z = 0.5* (R[1,0]-R[0,1]) / sin(angle)
            if abs( (1-cos(angle))*u_x*u_y - u_z*sin(angle) - R[0,1] ) < errorThreshold:
                msg = 'abs( (1-cos(angle))*u_x*u_y - u_z*sin(angle) - R[0,1] ) < 10**-6 check passed'
                break
        axis = numpy.array([u_x, u_y, u_z])
        error  = norm(axis_rotation_matrix(angle, *axis) - R)
        if debug: print('  norm(axis_rotation_matrix(angle, *axis) - R) %1.2e' % error)
        if error > errorThreshold:
            axis, angle = rotation_matrix_axis_and_angle_2(R, errorThreshold=errorThreshold, debug=debug, msg=msg)
    else:
        msg = 'abs(a % pi) > angle_pi_tol and abs(pi - (a % pi)) > angle_pi_tol'
        axis, angle = rotation_matrix_axis_and_angle_2( R, errorThreshold=errorThreshold, debug=debug, msg=msg)
    if numpy.isnan( angle ):
        raise RuntimeError('locals %s' % locals() )
    return axis, angle


def rotation_matrix_axis_and_angle_2(R, debug=False, errorThreshold=10**-7, msg=None):
    w, v = numpy.linalg.eig(R) #this method is not used at the primary method as numpy.linalg.eig does not return answers in high enough precision
    angle, axis = None, None
    eigErrors = abs(w -1) #errors from 1+0j
    i = (eigErrors == min(eigErrors)).tolist().index(True)
    axis = numpy.real(v[:,i])
    if i != 1:
        angle = arccos2(  numpy.real( w[1] ) )
    else:
        angle = arccos2(  numpy.real( w[0] ) )
    error  = norm(axis_rotation_matrix(angle, *axis) - R)
    if debug: print('rotation_matrix_axis_and_angle error %1.1e' % error)
    if error > errorThreshold:
        angle = -angle
        error = norm(axis_rotation_matrix(angle, *axis) - R)
        if error > errorThreshold:
            R_pickle_str = pickle.dumps(R)
            #R_abs_minus_identity = abs(R) - numpy.eye(3)
            print(R*R.transpose())
            raise ValueError( 'rotation_matrix_axis_and_angle_2: no solution found! locals %s' % str(locals()))
    return axis, angle




def rotation_required_to_rotate_a_vector_to_be_aligned_to_another_vector( v, v_ref ):
    c = cross( v, v_ref)
    if norm(c) > 0:
        axis = normalize(c)
    else: #dont think this ever happens.
        axis, notUsed = plane_degrees_of_freedom( v )
    #if dof_axis == None:
    angle = arccos2( dot( v, v_ref ))
    #else:
    #    axis3 = normalize ( crossProduct(v_ref, dof_axis) )
    #    a = dotProduct( v, v_ref ) #adjacent
    #    o = dotProduct( v, axis3 ) #oppersite
    #    angle = numpy.arctan2( o, a )
    return axis, angle


def plane_degrees_of_freedom( normalVector, debug=False, checkAnswer=False ):
    a,e = axis_to_azimuth_and_elevation_angles(*normalVector)
    dof1 = azimuth_and_elevation_angles_to_axis( a, e - pi/2)
    dof2 = azimuth_and_elevation_angles_to_axis( a+pi/2, 0)
    if checkAnswer: plane_degrees_of_freedom_check_answer( normalVector, dof1, dof2, debug )
    return dof1, dof2


def plane_degrees_of_freedom_check_answer( normalVector, d1, d2, disp=False, tol=10**-12):
    if disp:
        print('checking plane_degrees_of_freedom result')
        print('  plane normal vector   %s' % normalVector)
        print('  plane dof1            %s' % d1)
        print('  plane dof2            %s' % d2)
    Q = numpy.array([normalVector,d1,d2])
    P = dot(Q,Q.transpose())
    error = norm(P - numpy.eye(3))
    if disp:
        print('  dotProduct( array([normalVector,d1,d2]), array([normalVector,d1,d2]).transpose():')
        print(P)
        print(' error norm from eye(3) : %e' % error)
    if error > tol:
        raise RuntimeError('plane_degrees_of_freedom check failed!. locals %s' % locals())



def planeIntersection( normalVector1, normalVector2, debug=False, checkAnswer=False ):
    return normalize ( cross(normalVector1, normalVector2) )


def planeIntersection_check_answer( normalVector1, normalVector2, d,  disp=False, tol=10**-12):
    if disp:
        print('checking planeIntersection result')
        print('  plane normal vector 1 : %s' % normalVector1 )
        print('  plane normal vector 2 : %s' % normalVector2 )
        print('  d  : %s' % d )
    for t in [-3, 7, 12]:
        error1 = abs(dot( normalVector1, d*t ))
        error2 = abs(dot( normalVector2, d*t ))
        if disp:print('    d*(%1.1f) -> error1 %e, error2 %e' % (t, error1, error2) )
        if error1 > tol or error2 > tol:
            raise RuntimeError(' planeIntersection check failed!. locals %s' % locals())
