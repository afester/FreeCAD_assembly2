import Logging

class PartMover:

    def __init__(self, view, obj):
        Logging.debug('PartMover.__init__()')

        self.obj = obj
        self.initialPostion = self.obj.Placement.Base
        self.view = view
        self.callbackMove = self.view.addEventCallback("SoLocation2Event",self.moveMouse)
        self.callbackClick = self.view.addEventCallback("SoMouseButtonEvent",self.clickMouse)
        self.callbackKey = self.view.addEventCallback("SoKeyboardEvent",self.KeyboardEvent)

    def moveMouse(self, info):
        Logging.debug('PartMover.moveMouse({})'.format(info))

        newPos = self.view.getPoint( *info['Position'] )
        self.obj.Placement.Base = newPos

    def removeCallbacks(self):
        Logging.debug('PartMover.removeCallbacks()')

        self.view.removeEventCallback("SoLocation2Event",self.callbackMove)
        self.view.removeEventCallback("SoMouseButtonEvent",self.callbackClick)
        self.view.removeEventCallback("SoKeyboardEvent",self.callbackKey)

    def clickMouse(self, info):
        Logging.debug('PartMover.clickMouse({})'.format(info))

        # Note: Do not mess around with CTRL/SHIFT state here.
        # Depending on the active navigation mechanism, SHIFT already needs to be
        # pressed for MOVE operations. 
        # Just remove the callbacks - we are done with moving.
        if info['Button'] == 'BUTTON1' and info['State'] == 'DOWN':
            self.removeCallbacks()



    def KeyboardEvent(self, info):
        Logging.debug('PartMover.KeyboardEvent({})'.format(info))

        # Discard move by pressing the ESC key
        if info['State'] == 'UP' and info['Key'] == 'ESCAPE':
            self.obj.Placement.Base = self.initialPostion
