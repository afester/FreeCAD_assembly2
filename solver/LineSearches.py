import numpy
from numpy.linalg import norm

class LineSearchEvaluation:
    def __init__(self, f, x, searchDirection, lam, fv=None):
        self.lam = lam
        self.xv = x + lam*searchDirection
        self.fv = f(x + lam*searchDirection) if not fv else fv
    def __lt__(self, b):
        return self.fv < b.fv
    def __eq__(self, b):
        return self.lam == b.lam
    def str(self, prefix='LSEval', lamFmt='%1.6f', fvFmt='%1.2e'):
        return '%s %s,%s' % (prefix, lamFmt % self.lam, fvFmt % self.fv )



def quadraticLineSearch( f, x1, f1, intialStep, it, debugPrintLevel, printF, tol_stag=3, tol_x=10**-6):
    if norm(intialStep) == 0:
        printF('    quadraticLineSearch: norm search direction is 0, aborting!')
        return x1
    def LSEval(lam, fv=None):
        return LineSearchEvaluation( f,  x1, intialStep, lam, fv )
    Y = [ LSEval(     0.0,  f1), LSEval(       1 ), LSEval(       2 )]
    y_min_prev = min(Y)
    count_stagnation = 0
    tol_lambda = tol_x / norm(intialStep)
    for k in range(it):
        Y.sort()
        if debugPrintLevel > 0:
            printF('    quadratic line search   it %i, fmin %1.2e, lam  %1.6f  %1.6f  %1.6f, f(lam) %1.2e  %1.2e  %1.2e'%( k+1, Y[0].fv, Y[0].lam,Y[1].lam,Y[2].lam,Y[0].fv,Y[1].fv,Y[2].fv ))
        #``p[0]*x**(N-1) + p[1]*x**(N-2) + ... + p[N-2]*x + p[N-1]``
        quadraticCoefs, residuals, rank, singular_values, rcond = numpy.polyfit( [y.lam for y in Y], [y.fv for y in Y], 2, full=True)
        if quadraticCoefs[0] > 0 and rank == 3:
            lam_c = -quadraticCoefs[1] / (2*quadraticCoefs[0]) #diff poly a*x**2 + b*x + c -> grad_poly = 2*a*x + b
            lam_c = min( max( [y.lam for y in Y])*4, lam_c)
            if lam_c < 0:
                if debugPrintLevel > 1:  printF('    quadratic line search lam_c < 0')
                lam_c = 1.0 / (k + 1) ** 2
        else:
            if debugPrintLevel > 1: printF('    quadratic fit invalid, using interval halving instead')
            lam_c = ( Y[0].lam + Y[1].lam )/2
        del Y[2] # Y sorted at start of each iteration
        Y.append(  LSEval( lam_c ))
        y_min = min(Y)
        if y_min == y_min_prev:
            count_stagnation = count_stagnation + 1
            if count_stagnation > tol_stag:
                if debugPrintLevel > 0:  printF('    terminating quadratic line search as count_stagnation > tol_stag')
                break
        else:
            y_min_prev = y_min
            count_stagnation = 0
        Lam = [y.lam for y in Y]
        if max(Lam) - min(Lam) < tol_lambda:
            if debugPrintLevel > 0:  printF('    terminating quadratic max(Lam)-min(Lam) < tol_lambda (%e < %e)' % (max(Lam) - min(Lam), tol_lambda))
            break

    return min(Y).xv
