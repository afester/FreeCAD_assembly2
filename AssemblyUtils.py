import os
import FreeCAD
import Part
import Logging
import numpy
from numpy import linspace, cross, dot
from PySide.QtCore import QObject

def formatDictionary( d, indent):
    return '%s{' % indent + '\n'.join(['%s%s:%s' % (indent,k,d[k]) for k in sorted(d.keys())]) + '}'

def getModulePath():
    return os.path.dirname(__file__)

def getResourceFilePath():
    return os.path.join(getModulePath(), 'Gui', 'Resources', 'resources.rcc')

def findUnusedObjectName(base, counterStart=1, fmt='%02i', document=None):
    i = counterStart
    objName = '%s%s' % (base, fmt%i)
    if document == None:
        document = FreeCAD.ActiveDocument
    usedNames = [ obj.Name for obj in document.Objects ]
    while objName in usedNames:
        i = i + 1
        objName = '%s%s' % (base, fmt%i)
    return objName

def findUnusedLabel(base, counterStart=1, fmt='%02i', document=None):
    i = counterStart
    label = '%s%s' % (base, fmt%i)
    if document == None:
        document = FreeCAD.ActiveDocument
    usedLabels = [ obj.Label for obj in document.Objects ]
    while label in usedLabels:
        i = i + 1
        label = '%s%s' % (base, fmt%i)
    return label


def removeConstraint( constraint ):
    'required as constraint.Proxy.onDelete only called when deleted through GUI'
    doc = constraint.Document
    Logging.debug("removing constraint %s" % constraint.Name )
    if constraint.ViewObject != None: #do not this check is actually nessary ...
        constraint.ViewObject.Proxy.onDelete( constraint.ViewObject, None )
    doc.removeObject( constraint.Name )


def isLine(param):
    if hasattr(Part,"LineSegment"):
        return isinstance(param,(Part.Line,Part.LineSegment))
    else:
        return isinstance(param,Part.Line)


def getObjectEdgeFromName( obj, name ):
    assert name.startswith('Edge')
    ind = int( name[4:]) -1
    return obj.Shape.Edges[ind]

def getObjectVertexFromName( obj, name ):
    assert name.startswith('Vertex')
    ind = int( name[6:]) -1
    return obj.Shape.Vertexes[ind]

def getSubElementPos(obj, subElementName):
    pos = None
    if subElementName.startswith('Face'):
        face = getObjectFaceFromName(obj, subElementName)
        surface = face.Surface
        if str(surface) == '<Plane object>':
            pos = getObjectFaceFromName(obj, subElementName).Faces[0].BoundBox.Center
            # axial constraint for Planes
            # pos = surface.Position
        elif all( hasattr(surface,a) for a in ['Axis','Center','Radius'] ):
            pos = surface.Center
        elif str(surface).startswith('<SurfaceOfRevolution'):
            pos = getObjectFaceFromName(obj, subElementName).Edges[0].Curve.Center
        else: #numerically approximating surface
            plane_norm, plane_pos, error = fit_plane_to_surface1(face.Surface)
            error_normalized = error / face.BoundBox.DiagonalLength
            if error_normalized < 10**-6: #then good plane fit
                pos = plane_pos
            axis, center, error = fit_rotation_axis_to_surface1(face.Surface)
            error_normalized = error / face.BoundBox.DiagonalLength
            if error_normalized < 10**-6: #then good rotation_axis fix
                pos = center
    elif subElementName.startswith('Edge'):
        edge = getObjectEdgeFromName(obj, subElementName)
        if isLine(edge.Curve):
            pos = edge.Vertexes[-1].Point
        elif hasattr( edge.Curve, 'Center'): #circular curve
            pos = edge.Curve.Center
        else:
            BSpline = edge.Curve.toBSpline()
            arcs = BSpline.toBiArcs(10**-6)
            if all( hasattr(a,'Center') for a in arcs ):
                centers = numpy.array([a.Center for a in arcs])
                sigma = numpy.std( centers, axis=0 )
                if max(sigma) < 10**-6: #then circular curce
                    pos = centers[0]
            if all(isLine(a) for a in arcs):
                lines = arcs
                D = numpy.array([L.tangent(0)[0] for L in lines]) #D(irections)
                if numpy.std( D, axis=0 ).max() < 10**-9: #then linear curve
                    return lines[0].value(0)
    elif subElementName.startswith('Vertex'):
        return  getObjectVertexFromName(obj, subElementName).Point
    if pos != None:
        return numpy.array(pos)
    else:
        raise NotImplementedError("getSubElementPos Failed! Locals:\n%s" % formatDictionary(locals(),' '*4))


def getSubElementAxis(obj, subElementName):
    axis = None
    if subElementName.startswith('Face'):
        face = getObjectFaceFromName(obj, subElementName)
        surface = face.Surface
        if hasattr(surface,'Axis'):
            axis = surface.Axis
        elif str(surface).startswith('<SurfaceOfRevolution'):
            axis = face.Edges[0].Curve.Axis
        else: #numerically approximating surface
            plane_norm, plane_pos, error = fit_plane_to_surface1(face.Surface)
            error_normalized = error / face.BoundBox.DiagonalLength
            if error_normalized < 10**-6: #then good plane fit
                axis = plane_norm
            axis_fitted, center, error = fit_rotation_axis_to_surface1(face.Surface)
            error_normalized = error / face.BoundBox.DiagonalLength
            if error_normalized < 10**-6: #then good rotation_axis fix
                axis = axis_fitted
    elif subElementName.startswith('Edge'):
        edge = getObjectEdgeFromName(obj, subElementName)
        if isLine(edge.Curve):
            axis = edge.Curve.tangent(0)[0]
        elif hasattr( edge.Curve, 'Axis'): #circular curve
            axis =  edge.Curve.Axis
        else:
            BSpline = edge.Curve.toBSpline()
            arcs = BSpline.toBiArcs(10**-6)
            if all( hasattr(a,'Center') for a in arcs ):
                centers = numpy.array([a.Center for a in arcs])
                sigma = numpy.std( centers, axis=0 )
                if max(sigma) < 10**-6: #then circular curce
                    axis = a.Axis
            if all(isLine(a) for a in arcs):
                lines = arcs
                D = numpy.array([L.tangent(0)[0] for L in lines]) #D(irections)
                if numpy.std( D, axis=0 ).max() < 10**-9: #then linear curve
                    return D[0]
    if axis != None:
        return numpy.array(axis)
    else:
        raise NotImplementedError("getSubElementAxis Failed! Locals:\n%s" % formatDictionary(locals(),' '*4))


def getObjectFaceFromName( obj, faceName ):
    assert faceName.startswith('Face')
    ind = int( faceName[4:]) -1
    return obj.Shape.Faces[ind]


class SelectionExObject:
    'allows for selection gate functions to interface with classification functions below'
    def __init__(self, doc, Object, subElementName):
        self.doc = doc
        self.Object = Object
        self.ObjectName = Object.Name
        self.SubElementNames = [subElementName]

def planeSelected( selection ):
    if len( selection.SubElementNames ) == 1:
        subElement = selection.SubElementNames[0]
        if subElement.startswith('Face'):
            face = getObjectFaceFromName( selection.Object, subElement)
            if str(face.Surface) == '<Plane object>':
                return True
            elif hasattr(face.Surface,'Radius'):
                return False
            elif str(face.Surface).startswith('<SurfaceOfRevolution'):
                return False
            else:
                plane_norm, plane_pos, error = fit_plane_to_surface1(face.Surface)
                error_normalized = error / face.BoundBox.DiagonalLength
                #debugPrint(2,'plane_norm %s, plane_pos %s, error_normalized %e' % (plane_norm, plane_pos, error_normalized))
                return error_normalized < 10**-6
    return False

def linearEdgeSelected( selection ):
    if len( selection.SubElementNames ) == 1:
        subElement = selection.SubElementNames[0]
        if subElement.startswith('Edge'):
            edge = getObjectEdgeFromName( selection.Object, subElement)
            if not hasattr(edge, 'Curve'): #issue 39
                return False
            if isLine(edge.Curve):
                return True
            elif hasattr( edge.Curve, 'Radius' ):
                return False
            else:
                BSpline = edge.Curve.toBSpline()
                try:
                    arcs = BSpline.toBiArcs(10**-6)
                except:  #FreeCAD exception thrown ()
                    return False
                if all(isLine(a) for a in arcs):
                    lines = arcs
                    D = numpy.array([L.tangent(0)[0] for L in lines]) #D(irections)
                    return numpy.std( D, axis=0 ).max() < 10**-9
    return False

def vertexSelected( selection ):
    if len( selection.SubElementNames ) == 1:
        return selection.SubElementNames[0].startswith('Vertex')
    return False


def circularEdgeSelected( selection ):
    if len( selection.SubElementNames ) == 1:
        subElement = selection.SubElementNames[0]
        if subElement.startswith('Edge'):
            edge = getObjectEdgeFromName( selection.Object, subElement)
            if not hasattr(edge, 'Curve'): #issue 39
                return False
            if hasattr( edge.Curve, 'Radius' ):
                return True
            elif isLine(edge.Curve):
                return False
            else:
                BSpline = edge.Curve.toBSpline()
                try:
                    arcs = BSpline.toBiArcs(10**-6)
                except:  #FreeCAD exception thrown ()
                    return False
                if all( hasattr(a,'Center') for a in arcs ):
                    centers = numpy.array([a.Center for a in arcs])
                    sigma = numpy.std( centers, axis=0 )
                    return max(sigma) < 10**-6
    return False


def cylindricalPlaneSelected( selection ):
    '''Checks if the specified object is a cylindrical plane.

       Args:
           selection     The object to check.

       Returns: 
           True if the given object is a cylindrical plane, False otherwise
    '''

    if len( selection.SubElementNames ) == 1:
        subElement = selection.SubElementNames[0]
        if subElement.startswith('Face'):
            face = getObjectFaceFromName( selection.Object, subElement)
            if hasattr(face.Surface,'Radius'):
                return True
            elif str(face.Surface).startswith('<SurfaceOfRevolution'):
                return True
            elif str(face.Surface) == '<Plane object>':
                return False
            else:
                axis, center, error = fit_rotation_axis_to_surface1(face.Surface)
                error_normalized = error / face.BoundBox.DiagonalLength
                #debugPrint(2,'fitted axis %s, center %s, error_normalized %e' % (axis, center,error_normalized))
                return error_normalized < 10**-6
    return False


def sphericalSurfaceSelected( selection ):
    if len( selection.SubElementNames ) == 1:
        subElement = selection.SubElementNames[0]
        if subElement.startswith('Face'):
            face = getObjectFaceFromName( selection.Object, subElement)
            return str( face.Surface ).startswith('Sphere ')
    return False


def axisOfPlaneSelected( selection ): #adding Planes/Faces selection for Axial constraints
    if len( selection.SubElementNames ) == 1:
        subElement = selection.SubElementNames[0]
        if subElement.startswith('Face'):
            face = getObjectFaceFromName( selection.Object, subElement)
            if str(face.Surface) == '<Plane object>':
                return True
            else:
                axis, center, error = fit_rotation_axis_to_surface1(face.Surface)
                error_normalized = error / face.BoundBox.DiagonalLength
                #debugPrint(2,'fitted axis %s, center %s, error_normalized %e' % (axis, center,error_normalized))
                return error_normalized < 10**-6
    return False


def printSelection(selection):
    entries = []
    for s in selection:
        for e in s.SubElementNames:
            entries.append(' - %s:%s' % (s.ObjectName, e))
            if e.startswith('Face'):
                ind = int( e[4:]) -1
                face = s.Object.Shape.Faces[ind]
                entries[-1] = entries[-1] + ' %s' % str(face.Surface)
    return '\n'.join( entries[:5] )



def get_treeview_nodes( treeWidget ):

    tree_nodes = {}
    def walk( node ):
        key =  node.text(0)
        #print(key)
        if not key in tree_nodes:
            tree_nodes[ key ] = []
        tree_nodes[key].append( node )
        for i in range( node.childCount() ):
            walk( node.child( i ) )
    walk( treeWidget.itemAt(0,0) )
    return tree_nodes


def fit_plane_to_surface1( surface, n_u=3, n_v=3 ):
    uv = sum( [ [ (u,v) for u in linspace(0,1,n_u)] for v in linspace(0,1,n_v) ], [] )
    P = [ surface.value(u,v) for u,v in uv ] #positions at u,v points
    N = [ cross( *surface.tangent(u,v) ) for u,v in uv ]
    plane_norm = sum(N) / len(N) #plane's normal, averaging done to reduce error
    plane_pos = P[0]
    error = sum([ abs( dot(p - plane_pos, plane_norm) ) for p in P ])
    return plane_norm, plane_pos, error

def fit_rotation_axis_to_surface1( surface, n_u=3, n_v=3 ):
    'should work for cylinders and pssibly cones (depending on the u,v mapping)'
    uv = sum( [ [ (u,v) for u in linspace(0,1,n_u)] for v in linspace(0,1,n_v) ], [] )
    P = [ numpy.array(surface.value(u,v)) for u,v in uv ] #positions at u,v points
    N = [ cross( *surface.tangent(u,v) ) for u,v in uv ]
    intersections = []
    for i in range(len(N)-1):
        for j in range(i+1,len(N)):
            # based on the distance_between_axes( p1, u1, p2, u2) function,
            if 1 - abs(dot( N[i], N[j])) < 10**-6:
                continue #ignore parrallel case
            p1_x, p1_y, p1_z = P[i]
            u1_x, u1_y, u1_z = N[i]
            p2_x, p2_y, p2_z = P[j]
            u2_x, u2_y, u2_z = N[j]
            t1_t1_coef = u1_x**2 + u1_y**2 + u1_z**2 #should equal 1
            t1_t2_coef = -2*u1_x*u2_x - 2*u1_y*u2_y - 2*u1_z*u2_z # collect( expand(d_sqrd), [t1*t2] )
            t2_t2_coef = u2_x**2 + u2_y**2 + u2_z**2 #should equal 1 too
            t1_coef    = 2*p1_x*u1_x + 2*p1_y*u1_y + 2*p1_z*u1_z - 2*p2_x*u1_x - 2*p2_y*u1_y - 2*p2_z*u1_z
            t2_coef    =-2*p1_x*u2_x - 2*p1_y*u2_y - 2*p1_z*u2_z + 2*p2_x*u2_x + 2*p2_y*u2_y + 2*p2_z*u2_z
            A = numpy.array([ [ 2*t1_t1_coef , t1_t2_coef ] , [ t1_t2_coef, 2*t2_t2_coef ] ])
            b = numpy.array([ t1_coef, t2_coef])
            try:
                t1, t2 = numpy.linalg.solve(A,-b)
            except numpy.linalg.LinAlgError:
                continue #print('distance_between_axes, failed to solve problem due to LinAlgError, using numerical solver instead')
            pos_t1 = P[i] + numpy.array(N[i])*t1
            pos_t2 = P[j] + N[j]*t2
            intersections.append( pos_t1 )
            intersections.append( pos_t2 )
    if len(intersections) < 2:
        error = numpy.inf
        return 0, 0, error
    else: #fit vector to intersection points; http://mathforum.org/library/drmath/view/69103.html
        X = numpy.array(intersections)
        centroid = numpy.mean(X,axis=0)
        M = numpy.array([i - centroid for i in intersections ])
        A = numpy.dot(M.transpose(), M)
        U,s,V = numpy.linalg.svd(A)    #numpy docs: s : (..., K) The singular values for every matrix, sorted in descending order.
        axis_pos = centroid
        axis_dir = V[0]
        error = s[1] #dont know if this will work
        return axis_dir, axis_pos, error
    

def tr(text):
    return QObject.tr(text)
