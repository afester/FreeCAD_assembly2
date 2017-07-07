import Logging
import FreeCAD
from PySide import QtGui
import numpy
from numpy.linalg import norm 
from numpy.random import rand
from LineSearches import quadraticLineSearch

from ConstraintViewProviderProxy import ConstraintViewProviderProxy
from ImportedPartViewProviderProxy import ImportedPartViewProviderProxy
from AssemblyUtils import get_treeview_nodes

def updateOldStyleConstraintProperties( doc ):
    'used to update old constraint attributes, [object, faceInd] -> [object, subElement]...'
    for obj in doc.Objects:
        if 'ConstraintInfo' in obj.Content:
            updateObjectProperties( obj )


def updateObjectProperties( c ):
    if hasattr(c,'FaceInd1'):
        Logging.debug('updating properties of %s' % c.Name )
        for i in [1,2]:
            c.addProperty('App::PropertyString','SubElement%i'%i,'ConstraintInfo')
            setattr(c,'SubElement%i'%i,'Face%i'%(getattr(c,'FaceInd%i'%i)+1))
            c.setEditorMode('SubElement%i'%i, 1)
            c.removeProperty('FaceInd%i'%i)
        if hasattr(c,'planeOffset'):
            v = c.planeOffset
            c.removeProperty('planeOffset')
            c.addProperty('App::PropertyDistance','offset',"ConstraintInfo")
            c.offset = '%f mm' % v
        if hasattr(c,'degrees'):
            v = c.degrees
            c.removeProperty('degrees')
            c.addProperty("App::PropertyAngle","angle","ConstraintInfo")
            c.angle = v
    elif hasattr(c,'EdgeInd1'):
        Logging.debug('updating properties of %s' % c.Name )
        for i in [1,2]:
            c.addProperty('App::PropertyString','SubElement%i'%i,'ConstraintInfo')
            setattr(c,'SubElement%i'%i,'Edge%i'%(getattr(c,'EdgeInd%i'%i)+1))
            c.setEditorMode('SubElement%i'%i, 1)
            c.removeProperty('EdgeInd%i'%i)
        v = c.offset
        c.removeProperty('offset')
        c.addProperty('App::PropertyDistance','offset',"ConstraintInfo")
        c.offset = '%f mm' % v
    if c.Type == 'axial' or c.Type == 'circularEdge':
        if not hasattr(c, 'lockRotation'):
            Logging.debug('updating properties of %s, to add lockRotation (default=false)' % c.Name )
            c.addProperty("App::PropertyBool","lockRotation","ConstraintInfo")
    if FreeCAD.GuiUp:
        if not isinstance( c.ViewObject.Proxy , ConstraintViewProviderProxy):
            iconPaths = {
                'angle_between_planes':':/assembly2/icons/angleConstraint.svg',
                'axial':':/assembly2/icons/axialConstraint.svg',
                'circularEdge':':/assembly2/icons/circularEdgeConstraint.svg',
                'plane':':/assembly2/icons/planeConstraint.svg',
                'sphericalSurface': ':/assembly2/icons/sphericalSurfaceConstraint.svg'
            }
            c.ViewObject.Proxy = ConstraintViewProviderProxy( c, iconPaths[c.Type] )

def repair_tree_view():

    doc = FreeCAD.ActiveDocument
    matches = []

    def search_children_recursively( node ):
        for c in node.children():
            if isinstance(c,QtGui.QTreeView) and isinstance(c, QtGui.QTreeWidget):
                matches.append(c)
            search_children_recursively( c)

    search_children_recursively(QtGui.qApp.activeWindow())
    for m in matches:
        tree_nodes =  get_treeview_nodes(m)

        def get_node_by_label( label ):
            if label in tree_nodes and len( tree_nodes[label] ) == 1:
                return tree_nodes[label][0]
            elif not obj.Label in tree_nodes:
                Logging.warning("  repair_tree_view: skipping %s since no node with text(0) == %s\n" % ( label, label) )
            else:
                Logging.warning( "  repair_tree_view: skipping %s since multiple nodes matching label\n" % ( label, label) )

        if doc.Label in tree_nodes: #all the code up until now has geen to find the QtGui.QTreeView widget (except for the get_node_by_label function)
            #FreeCAD.Console.PrintMessage( tree_nodes )
            for imported_obj in doc.Objects:
                try: #allow use of assembly2 contraints also on non imported objects
                    if isinstance( imported_obj.ViewObject.Proxy, ImportedPartViewProviderProxy ):
                        #FreeCAD.Console.PrintMessage( 'checking claim children for %s\n' % imported_obj.Label )
                        if get_node_by_label( imported_obj.Label ):
                            node_imported_obj =  get_node_by_label( imported_obj.Label )
                            if not hasattr( imported_obj.ViewObject.Proxy, 'Object'):
                                imported_obj.ViewObject.Proxy.Object = imported_obj # proxy.attach not called properly
                                FreeCAD.Console.PrintMessage('repair_tree_view: %s.ViewObject.Proxy.Object = %s' % (imported_obj.Name, imported_obj.Name) )
                            for constraint_obj in imported_obj.ViewObject.Proxy.claimChildren():
                                #FreeCAD.Console.PrintMessage('  - %s\n' % constraint_obj.Label )
                                if get_node_by_label( constraint_obj.Label ):
                                    #FreeCAD.Console.PrintMessage('     (found treeview node)\n')
                                    node_constraint_obj = get_node_by_label( constraint_obj.Label )
                                    if id( node_constraint_obj.parent()) != id(node_imported_obj):
                                        FreeCAD.Console.PrintMessage("repair_tree_view: %s under %s and not %s, repairing\n" % (constraint_obj.Label, node_constraint_obj.parent().text(0),  imported_obj.Label ))
                                        wrong_parent = node_constraint_obj.parent()
                                        wrong_parent.removeChild( node_constraint_obj )
                                        node_imported_obj.addChild( node_constraint_obj )
                except:
                    # FreeCAD.Console.PrintWarning( "not repaired %s \n" % ( imported_obj.Label ) )
                    pass
            #break
            
analytics = {}
class SearchAnalyticsWrapper:
    def __init__(self, f):
        self.f = f
        self.x = []
        self.f_x = []
        self.notes = {}
        analytics['lastSearch'] = self
    def __call__(self, x):
        self.x.append(x)
        self.f_x.append( self.f(x) )
        return self.f_x[-1]
    def addNote(self, note):
        key = len(self.x)
        assert key not in self.notes
        self.notes[key] = note
    def __repr__(self):
        return '<SearchAnalyticsWrapper %i calls made>' % len(self.x)
    def plot(self):
        from matplotlib import pyplot
        pyplot.figure()
        it_ls = [] #ls = lineseach
        y_ls = []
        it_ga = [] #gradient approximation
        y_ga = []
        gradApprox = False
        for i in range(len(self.x)):
            y = norm( self.f_x[i] ) + 10**-9
            if i in self.notes:
                if self.notes[i] == 'starting gradient approximation':
                    gradApprox = True
                if self.notes[i] == 'finished gradient approximation':
                    gradApprox = False
            if gradApprox:
                it_ga.append( i )
                y_ga.append( y )
            else:
                it_ls.append( i )
                y_ls.append( y )
        pyplot.semilogy( it_ls, y_ls, 'go')
        pyplot.semilogy( it_ga, y_ga, 'bx')
        pyplot.xlabel('function evaluation')
        pyplot.ylabel('norm(f(x)) + 10**-9')
        pyplot.legend(['line searches', 'gradient approx' ])

        pyplot.show()            




def toStdOut(txt):
    print(txt)

def prettyPrintArray( A, printF, indent='  ', fmt='%1.1e' ):
    def pad(t):
        return t if t[0] == '-' else ' ' + t
    for r in A:
        txt = '  '.join( pad(fmt % v) for v in r)
        printF(indent + '[ %s ]' % txt)


class GradientApproximatorRandomPoints:
    def __init__(self, f):
        '''samples random points around a given X. as to approximate the gradient.
        Random sample should help to aviod saddle points.
        Testing showed that noise on gradient causes to scipy.optimize.fmin_slsqp to bomb-out so does not really help...
        '''
        self.f = f
    def __call__(self, X, eps=10**-7):
        n = len(X)
        samplePoints = eps*( rand(n+1,n) - 0.5 )
        #print(samplePoints)
        #samplePoints[:,n] = 1
        values = [ numpy.array(self.f( X + sp )) for  sp in samplePoints ]
        #print(values[0].shape)
        A = numpy.ones([n+1,n+1])
        A[:,:n] = samplePoints
        x_c, residuals, rank, s = numpy.linalg.lstsq( A, values )
        return x_c[:-1].transpose()

def addEps( x, dim, eps):
    y = x.copy()
    y[dim] = y[dim] + eps
    return y

class GradientApproximatorForwardDifference:
    def __init__(self, f):
        self.f = f
    def __call__(self, x, eps=10**-7, f0=None):
        if hasattr(self.f,'addNote'): self.f.addNote('starting gradient approximation')
        n = len(x)
        if f0 == None:
            f0 = self.f(x)
        f0 = numpy.array(f0)
        if f0.shape == () or f0.shape == (1,):
            grad_f = numpy.zeros(n)
        else:
            grad_f = numpy.zeros([n,len(f0)])
        for i in range(n):
            f_c = self.f( addEps(x,i,eps) )
            grad_f[i] = (f_c - f0)/eps
        if hasattr(self.f,'addNote'): self.f.addNote('finished gradient approximation')
        return grad_f.transpose()

class GradientApproximatorCentralDifference:
    def __init__(self, f):
        self.f = f
    def __call__(self, x, eps=10**-6):
        n = len(x)
        if hasattr(self.f,'addNote'): self.f.addNote('starting gradient approximation')
        grad_f = None
        for i in range(n):
            f_a = self.f( addEps(x,i, eps) )
            f_b = self.f( addEps(x,i,-eps) )
            if grad_f == None:
                if f_a.shape == () or f_a.shape == (1,):
                    grad_f = numpy.zeros(n)
                else:
                    grad_f = numpy.zeros([n,len(f_a)])
            grad_f[i] = (f_a - f_b)/(2*eps)
        if hasattr(self.f,'addNote'): self.f.addNote('finished gradient approximation')
        return grad_f.transpose()

            
def solve_via_Newtons_method( f_org, x0, maxStep, grad_f=None, x_tol=10**-6, f_tol=None, maxIt=100, randomPertubationCount=2,
                              debugPrintLevel=0, printF=toStdOut, lineSearchIt=5, record=False):
    '''
    determine the routes of a non-linear equation using netwons method.
    '''
    f = SearchAnalyticsWrapper(f_org) if record else f_org
    n = len(x0)
    x = numpy.array(x0)
    x_c = numpy.zeros(n) * numpy.nan
    x_prev =  numpy.zeros( [ maxIt+1, n ] ) #used to check against cyclic behaviour, for randomPertubationCount
    x_prev[0,:] = x
    if grad_f == None:
        #grad_f = GradientApproximatorForwardDifference(f)
        grad_f = GradientApproximatorCentralDifference(f)
    if lineSearchIt > 0:
        f_ls = lambda x: norm(f(x))
    for i in range(maxIt):
        b = numpy.array(-f(x))
        singleEq = b.shape == () or b.shape == (1,)
        if debugPrintLevel > 0:
            printF('it %02i: norm(prev. step) %1.1e norm(f(x))  %1.1e' % (i, norm(x_c), norm(-b)))
        if debugPrintLevel > 1:
            printF('  x    %s' % x)
            printF('  f(x) %s' % (-b))
        if norm(x_c) <= x_tol:
            break
        if f_tol != None:
            if singleEq and abs(b) < f_tol:
                break
            elif singleEq==False and all( abs(b) < f_tol ):
                break
        if not isinstance( grad_f, GradientApproximatorForwardDifference):
            A = grad_f(x)
        else:
            A = grad_f(x, f0=-b)
        if len(A.shape) == 1: #singleEq
            A = numpy.array([A])
            b = numpy.array([b])
        try:
            x_c, residuals, rank, s = numpy.linalg.lstsq( A, b)
        except ValueError as e:
            printF('  solve_via_Newtons_method numpy.linalg.lstsq failed: %s.  Setting x_c = x' % str(e))
            x_c = x
        if debugPrintLevel > 1:
            if singleEq:
                printF('  grad_f : %s' % A)
            else:
                printF('  grad_f :')
                prettyPrintArray(A, printF, '    ')
            printF('  x_c    %s' % x_c)
        r = abs(x_c / maxStep)
        if r.max() > 1:
            x_c = x_c / r.max()
        if lineSearchIt > 0:
            #x_next = goldenSectionSearch( f_ls, x, norm(b), x_c, lineSearchIt, lineSearchIt_x0, debugPrintLevel, printF )
            x_next =  quadraticLineSearch( f_ls, x, norm(b), x_c, lineSearchIt, debugPrintLevel-2, printF, tol_x=x_tol )
            x_c = x_next - x
        x = x + x_c
        if randomPertubationCount > 0 : #then peturb as to avoid lock-up [i.e jam which occurs when trying to solve axis direction constraint]
            distances = ((x_prev[:i+1,:] -x)**2).sum(axis=1)
            #print(distances)
            if any(distances <= x_tol) :
                if debugPrintLevel > 0:
                    printF(' any(distances < x_tol) therefore randomPertubation...')
                x_p = (0.5 - rand(n)) * numpy.array(maxStep)* (1 - i*1.0/maxIt)
                x = x + x_p
                x_c = x_c + x_p
                randomPertubationCount = randomPertubationCount - 1
            x_prev[i,:] = x
    return x
