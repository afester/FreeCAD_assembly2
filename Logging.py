import FreeCAD

def debug(msg):
    FreeCAD.Console.PrintMessage('[debug  ] {}\n'.format(msg))

def info(msg):
    FreeCAD.Console.PrintMessage('[info   ] {}\n'.format(msg))
     
def warning(msg):
    FreeCAD.Console.PrintMessage('[warning] {}\n'.format(msg))
     
def error(msg):
    FreeCAD.Console.PrintMessage('[error  ] {}\n'.format(msg))
