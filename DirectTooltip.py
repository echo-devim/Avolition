"""This snippet shows how to create a tooltip text that will be attached
to the cursor and check it's position to not move out of the screen."""

import sys

from panda3d.core import TextNode
from direct.gui.DirectGui import DirectLabel

class DirectTooltip():
    def __init__(self):

        self.tooltipText = DirectLabel(
            text = "Tooltip",
            text_fg = (1,1,1,1),
            text_scale = 0.05,
            text_align = TextNode.ALeft,
            frameColor = (0, 0, 0, 0.75),
            borderWidth = (0.1, 0.1))
        self.tooltipText.setTransparency(True)

        self.textXShift = 0.05
        self.textYShift = -0.08

        self.mousePos = None

        # this will determine when the tooltip should be moved in the
        # respective direction, whereby
        # 1  : display edge
        # <1 : margin inside the window
        # >1 : margin outside the window
        self.xEdgeStartShift = 0.99
        self.yEdgeStartShift = 0.99

        self.tooltipText.hide()

    def show(self, text=None, args=None):
        if text is not None:
            self.tooltipText.setText(text)
            self.tooltipText.resetFrameSize()
        self.tooltipText.show()

        # add the tooltips update task so it will be updated every frame
        base.taskMgr.add(self.updateTooltipPos, "task_updateTooltipPos")

    def delete(self, args=None):
        self.tooltipText.removeNode()

        # remove the tooltips update task
        base.taskMgr.remove("task_updateTooltipPos")

    def updateTooltipPos(self, task):
        # calculate new aspec tratio
        wp = base.win.getProperties()
        aspX = 1.0
        aspY = 1.0
        wpXSize = wp.getXSize()
        wpYSize = wp.getYSize()
        if wpXSize > wpYSize:
            aspX = wpXSize / float(wpYSize)
        else:
            aspY = wpYSize / float(wpXSize)

        # variables to store the mouses current x and y position
        x = 0.0
        y = 0.0
        if base.mouseWatcherNode.hasMouse():
            self.tooltipText.show()
            # get the mouse position
            x = base.mouseWatcherNode.getMouseX()
            y = base.mouseWatcherNode.getMouseY()

            # Move the tooltip to the mouse

            # set the text to the current mouse position
            self.tooltipText.setPos(
                (x*aspX) + self.textXShift,
                0,
                (y*aspY)+self.textYShift)

            bounds = self.tooltipText.getBounds()
            # bounds = left, right, bottom, top

            # calculate the texts bounds respecting its current position
            xLeft = self.tooltipText.getX() + bounds[0]*self.tooltipText.getScale()[0]
            xRight = self.tooltipText.getX() + bounds[1]*self.tooltipText.getScale()[0]
            yUp = self.tooltipText.getZ() + bounds[3]*self.tooltipText.getScale()[1]
            yDown = self.tooltipText.getZ() + bounds[2]*self.tooltipText.getScale()[1]

            # these will be used to shift the text in the desired direction
            xShift = 0.0
            yShift = 0.0
            if xRight/aspX > self.xEdgeStartShift:
                # shift to the left
                xShift = self.xEdgeStartShift - xRight/aspX
            elif xLeft/aspX < -self.xEdgeStartShift:
                # shift to the right
                xShift = -(self.xEdgeStartShift + xLeft/aspX)
            if yUp/aspY > self.yEdgeStartShift:
                # shift down
                yShift = self.yEdgeStartShift - yUp/aspY
            elif yDown/aspY < -self.yEdgeStartShift:
                # shift up
                yShift = -(self.yEdgeStartShift + yDown/aspY)

            # some aspect ratio calculation
            xShift *= aspX
            yShift *= aspY

            # move the tooltip to the new position
            self.tooltipText.setX(self.tooltipText.getX() + xShift)
            self.tooltipText.setZ(self.tooltipText.getZ() + yShift)
        else:
            self.tooltipText.delete()


        # continue the task until it got manually stopped
        return task.cont
