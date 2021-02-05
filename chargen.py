'''
    Avolotion
    Copyright (C) 2014  Grzegorz 'Wezu' Kalinski grzechotnik1984@gmail.com

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''    
from panda3d.core import *
from direct.actor.Actor import Actor
from direct.interval.IntervalGlobal import *
from direct.showbase.DirectObject import DirectObject
from direct.gui.DirectGui import *
from pathlib import Path
from vfx import vfx
#from vfx import RayVfx
import random, sys
#from levelloader import LevelLoader
from engine import *
from player import *
from boss import *
#from player import PC2
from direct.interval.ActorInterval import ActorInterval
import webbrowser

class CharGen(DirectObject):
    def __init__(self, common):
        self.common=common
        self.common['chargen']=self
        self.load()        
    def load(self):
        self.newGame = True
        self.font = loader.loadFont('Bitter-Bold.otf')
        self.common['font']=self.font
        
        self.common['pc_stat1']=50
        self.common['pc_stat2']=50
        self.common['pc_stat3']=50
        #render.setShaderAuto()
        #base.disableMouse()  
        #render.setAntialias(AntialiasAttrib.MMultisample)
        #base.setBackgroundColor(0, 0, 0)
        wp = base.win.getProperties()
        winX = wp.getXSize()
        winY = wp.getYSize()
        
        
        self.campmap=loader.loadModel("models/camp3")
        self.campmap.reparentTo(render)
        
        #music       
        self.common['music']=MusicPlayer(self.common)
        self.common['music'].loop(0)
        #self.common['music']=base.loadMusic("music/LuridDeliusion.ogg")
        #self.common['music'].setLoop(True)
        #self.common['music'].play()        
        
        self.common["random-objects-freq"] = 0.65

        self.node=render.attachNewNode("node")
        
        self.cameraNode  = self.node.attachNewNode("cameraNode")         
        self.cameraNode.setZ(-1)
        base.camera.setY(-8)
        base.camera.setZ(5)
        base.camera.lookAt((0,3,0))
        base.camera.wrtReparentTo(self.cameraNode)  
        self.pointer=self.cameraNode.attachNewNode("pointerNode") 
        
        #light
        self.pLight = PointLight('plight')
        self.pLight.setColor(VBase4(1, .95, .9, 1))
        self.pLight.setAttenuation(Point3(.5, 0, 0.1))          
        self.pLightNode = self.node.attachNewNode(self.pLight) 
        self.pLightNode.setZ(1.0)
        render.setLight(self.pLightNode)
        
        self.sLight=Spotlight('sLight')
        self.sLight.setColor(VBase4(.4, .25, .25, 1))
        if self.common['extra_ambient']:            
            self.sLight.setColor(VBase4(.7, .5, .5, 1))        
        spot_lens = PerspectiveLens()
        spot_lens.setFov(40)        
        self.sLight.setLens(spot_lens)
        self.Ambient = self.cameraNode.attachNewNode( self.sLight)
        self.Ambient.setPos(base.camera.getPos(render))
        self.Ambient.lookAt((0,3,0))
        render.setLight(self.Ambient)
        
        self.fire_node=self.node.attachNewNode("fireNode")    
        self.fire=vfx(self.fire_node, texture='vfx/big_fire3.png',scale=.29, Z=.5, depthTest=True, depthWrite=True)
        self.fire.show()
        self.fire.loop(0.02) 
        
        self.character1=Actor("models/pc/male", {"attack":"models/pc/male_attack2","idle":"models/pc/male_ready2", "block":"models/pc/male_block"}) 
        self.character1.reparentTo(self.node)
        self.character1.setBlend(frameBlend = True)  
        self.character1.setPos(1,2, 0)
        self.character1.setScale(.025)
        self.character1.setH(-25.0)       
        self.character1.setBin("opaque", 10)
        self.character1.loop("idle")        
        self.swingSound = base.loader.loadSfx("sfx/swing2.ogg")
        
        
        coll_sphere=self.node.attachNewNode(CollisionNode('monsterSphere'))
        coll_sphere.node().addSolid(CollisionSphere(1, 2, 1, 1))   
        coll_sphere.setTag("class", "1") 
        coll_sphere.node().setIntoCollideMask(BitMask32.bit(1))
        
        
        self.character2=Actor("models/pc/female", {"attack":"models/pc/female_attack1","idle":"models/pc/female_idle"}) 
        #self.character2.setPlayRate(.4, "attack")
        self.character2.reparentTo(self.node)
        self.character2.setBlend(frameBlend = True)  
        self.character2.setPos(-1,2, 0)
        self.character2.setScale(.026)
        self.character2.setH(25.0)       
        #self.character2.setBin("opaque", 10)
        self.character2.loop("idle")
        
        self.char2_magic= loader.loadModel('vfx/vfx3')
        self.char2_magic.setPos(self.character2.getPos())
        self.char2_magic.setH(self.character2.getH())
        self.char2_magic.setP(-10.0)
        self.char2_magic.setZ(0.71)
        self.char2_magic.setScale(1,2,1)
        self.char2_magic.wrtReparentTo(self.character2)
        self.char2_magic.setY(-10)        
        self.char2_magic.setDepthWrite(False)
        self.char2_magic.setDepthTest(False)
        self.char2_magic.setLightOff()
        self.char2_magic.hide()        
        self.vfxU=-0.125
        self.vfxV=0
        self.magicSound = base.loader.loadSfx("sfx/thunder3.ogg")
        
        coll_sphere=self.node.attachNewNode(CollisionNode('monsterSphere'))
        coll_sphere.node().addSolid(CollisionSphere(-1, 2, 1, 1))   
        coll_sphere.setTag("class", "2") 
        coll_sphere.node().setIntoCollideMask(BitMask32.bit(1))
        
        self.character3=Actor("models/pc/female2", {"attack":"models/pc/female2_arm","reset":"models/pc/female2_fire","idle":"models/pc/female2_idle"}) 
        #self.character2.setPlayRate(.4, "attack")
        self.character3.reparentTo(self.node)
        self.character3.setBlend(frameBlend = True)  
        self.character3.setPos(-1.8,0.9, 0)
        self.character3.setScale(.026)
        self.character3.setH(40.0)       
        #self.character2.setBin("opaque", 10)
        self.character3.loop("idle")
        
        coll_sphere=self.node.attachNewNode(CollisionNode('monsterSphere'))
        coll_sphere.node().addSolid(CollisionSphere(-1.8,0.9, 0, 1))   
        coll_sphere.setTag("class", "3") 
        coll_sphere.node().setIntoCollideMask(BitMask32.bit(1))
        
        self.arrow_bone=self.character3.exposeJoint(None, 'modelRoot', 'arrow_bone')
        self.arrow=loader.loadModel('models/arrow')        
        self.arrow.reparentTo(self.arrow_bone)
        self.arrow.setP(-45)
        self.movingArrow=None
        self.arrowTime=0.0
        self.drawSound = base.loader.loadSfx("sfx/draw_bow2.ogg")
        self.fireSound = base.loader.loadSfx("sfx/fire_arrow3.ogg")
        
        
        self.character4=Actor("models/pc/male2", {"attack":"models/pc/male2_aura","idle":"models/pc/male2_idle"}) 
        #self.character2.setPlayRate(.4, "attack")
        self.character4.reparentTo(self.node)
        self.character4.setBlend(frameBlend = True)  
        self.character4.setPos(1.8,0.9, 0)
        self.character4.setScale(.024)
        self.character4.setH(-60.0)       
        #self.character2.setBin("opaque", 10)
        self.character4.loop("idle")
        self.FFSound = base.loader.loadSfx("sfx/teleport.ogg")
        #self.FFSound = base.loader.loadSfx("sfx/walk_new3.ogg")
        
        coll_sphere=self.node.attachNewNode(CollisionNode('monsterSphere'))
        coll_sphere.node().addSolid(CollisionSphere(1.8,0.9, 0, 1))   
        coll_sphere.setTag("class", "4") 
        coll_sphere.node().setIntoCollideMask(BitMask32.bit(1))
        
        
        
        #gui
        self.mp_logo=DirectFrame(frameSize=(-512, 0, 0, 128),
                                    frameColor=(1,1,1, 1),
                                    frameTexture='images/mp_logo.png',
                                    state=DGG.NORMAL,
                                    parent=pixel2d)       
        self.mp_logo.setPos(256+winX/2, 0, -winY)
        self.mp_logo.setBin('fixed', 1)
        self.mp_logo.hide()
        self.mp_logo.setTransparency(TransparencyAttrib.MDual)
        self.mp_logo.bind(DGG.B1PRESS, self.open_www, ['http://www.matthewpablo.com/'])
        #self.mp_logo.bind(DGG.WITHIN, self.GUIOnEnter, ["MP"]) 
        #self.mp_logo.bind(DGG.WITHOUT, self.GUIOnExit)
        
        self.title = DirectFrame(frameSize=(-512, 0, 0, 128),
                                    frameColor=(1,1,1, 1),
                                    frameTexture='images/select.png',
                                    parent=pixel2d)       
        self.title.setPos(256+winX/2, 0, -128)
        self.title.setBin('fixed', 1)
        self.title.setTransparency(TransparencyAttrib.MDual)
        #self.title.hide()
        self.close=DirectFrame(frameSize=(-32, 0, 0, 32),
                                    frameColor=(1, 1, 1, 1),
                                    frameTexture='icon/close.png',
                                    state=DGG.NORMAL,
                                    parent=pixel2d)        
        self.close.setPos(winX, 0, -32)
        self.close.setBin('fixed', 1)
        self.close.bind(DGG.B1PRESS, self.exit) 

        self.new_game_button=DirectButton(frameSize=(-0.2, 0.2, 0, 0.08),
                                    frameColor=(1,1,1,1),    
                                    frameTexture='images/level_select.png',
                                    text_font=self.font,
                                    text='START NEW GAME',
                                    text_pos = (-0.16,0.026,0),
                                    text_scale = 0.035,
                                    text_fg=(0,0,0,1),
                                    text_align=TextNode.ALeft, 
                                    textMayChange=1,  
                                    state=DGG.FLAT,
                                    relief=DGG.FLAT,
                                    pos=(0,0,0.5),
                                    command=self.onStart,
                                    parent=aspect2d)
        self.new_game_button.setBin('fixed', 1)
        self.new_game_button.hide()
        self.continue_button=DirectButton(frameSize=(-0.2, 0.2, 0, 0.08),
                                    frameColor=(1,1,1,1),    
                                    frameTexture='images/level_select.png',
                                    text_font=self.font,
                                    text='CONTINUE GAME',
                                    text_pos = (-0.16,0.026,0),
                                    text_scale = 0.035,
                                    text_fg=(0,0,0,1),
                                    text_align=TextNode.ALeft, 
                                    textMayChange=1,  
                                    state=DGG.FLAT,
                                    relief=DGG.FLAT,
                                    pos=(0,0,0.4),
                                    command=self.loadAndStart,
                                    parent=aspect2d)
        self.continue_button.setBin('fixed', 1)
        self.continue_button.hide()
              
        self.cursor=DirectFrame(frameSize=(-32, 0, 0, 32),
                                    frameColor=(1, 1, 1, 1),
                                    frameTexture='icon/cursor1.png',
                                    parent=pixel2d)        
        self.cursor.setPos(32,0, -32)
        self.cursor.flattenLight()
        self.cursor.setBin('fixed', 10)
        self.cursor.setTransparency(TransparencyAttrib.MDual)
        
        self.frameDesc=DirectFrame(frameSize=(0, 1, 0, 0.3),
                                    frameColor=(1,1,1, 1),
                                    frameTexture='images/frame1.png',
                                    state=DGG.NORMAL,
                                    pos=(-0.5,0,0.6),
                                    parent=aspect2d)
        self.labelDesc = DirectLabel(text="",
                    text_fg=(1,1,1,1),
                    frameColor=(0,0,0,0),
                    #text_font=self.font,
                    text_scale=0.06,
                    text_align = TextNode.ALeft,
                    pos=(0.1,0,0.2),
                    parent=self.frameDesc)
        self.frameDesc.setBin('fixed', 1)
        self.frameDesc.hide()
        self.frameDesc.bind(DGG.WITHIN, self.GUIOnEnter, ["3B"]) 
        self.frameDesc.bind(DGG.WITHOUT, self.GUIOnExit)

        #tooltip
        
        #self.font.setPixelsPerUnit(16)
        #self.font.setMinfilter(Texture.FTNearest )
        #self.font.setMagfilter(Texture.FTNearest )
        #self.font.setAnisotropicDegree(4)        
        #self.font.setNativeAntialias(False) 
        #self.font.setPageSize(1024,1024)
        
        self.Tooltip=DirectLabel(frameColor=(0, 0, 0, 0),
                                text_font=self.font,
                                text='Lorem ipsum dolor sit amet,\n consectetur adipisicing elit,\n sed do eiusmod tempor incididunt \nut labore et dolore magna aliqua.',
                                #pos = (0, 0,-35),
                                text_scale = 16,
                                text_fg=(1,1,1,1),                                
                                text_align=TextNode.ALeft , 
                                textMayChange=1,
                                parent=pixel2d
                                )
        self.Tooltip.flattenLight()                        
        self.Tooltip.setBin('fixed', 300)
        self.Tooltip.hide()
        #collisions
        #self.traverser=CollisionTraverser("playerTrav")
        #self.traverser.setRespectPrevTransform(True)        
        #self.queue = CollisionHandlerQueue() 
        self.MousePickerNode = CollisionNode('mouseRay')        
        self.pickerNP = base.camera.attachNewNode(self.MousePickerNode)        
        self.MousePickerNode.setFromCollideMask(BitMask32.bit(1))
        self.MousePickerNode.setIntoCollideMask(BitMask32.allOff())
        self.pickerRay = CollisionSegment()               #Make our ray
        self.MousePickerNode.addSolid(self.pickerRay)      #Add it to the collision node        
        self.common['traverser'].addCollider(self.pickerNP, self.common['queue'])
        
        self.accept("mouse1", self.onClick)
        
        taskMgr.doMethodLater(0.2, self.flicker,'flicker')
        #taskMgr.add(self.camera_spin, "camera_spin")  
        taskMgr.add(self.__getMousePos, "chargenMousePos")  
        
        self.current_class=None
        self.currentLevel=0
        self.camLoop=Sequence(LerpHprInterval(self.cameraNode, 10.0, VBase3(-20,0, 0), bakeInStart=0),LerpHprInterval(self.cameraNode, 10.0, VBase3(20,0, 0),bakeInStart=0))
        self.camLoop.loop()
        self.accept( 'window-event', self.windowEventHandler)
    
    def selectLevel(self, next, event=None):
        self.currentLevel+=next
        if self.currentLevel<0:
            self.currentLevel=0
        if self.currentLevel>self.common['max_level']:
            self.currentLevel=self.common['max_level']
        self.start_main['text']="Start in Level "+str(self.currentLevel+1)    
    
    def moveArrow(self, task):
        if self.movingArrow:
            self.arrowTime+=task.time
            if self.arrowTime>3.0:
                self.movingArrow.removeNode()
                self.arrowTime=0.0
                return task.done
            dt = globalClock.getDt()    
            self.movingArrow.setX(self.movingArrow, 400*dt)    
            return task.again
        else:
            return task.done
            
    def fireArrow(self):
        self.movingArrow=loader.loadModel('models/arrow')        
        self.movingArrow.reparentTo(self.arrow_bone)
        self.movingArrow.setP(-45)
        self.movingArrow.wrtReparentTo(render)
        self.arrow.hide()
        self.fireSound.play()
        taskMgr.add(self.moveArrow, "moveArrowTask") 
        Sequence(Wait(0.5),Func(self.arrow.show)).start()
    
    def loadAndStart(self):
        self.newGame = False
        self.common['levelLoader'].loadGame(PCLoad=False)
        self.onStart()

    def onStart(self, event=None):
        #unload stuff        
        self.camLoop.pause()
        self.camLoop=None
        base.camera.reparentTo(render)
        self.campmap.removeNode()
        self.node.removeNode()
        self.fire.remove_loop()
        if taskMgr.hasTaskNamed('flicker'):
            taskMgr.remove('flicker') 
        if taskMgr.hasTaskNamed('chargenMousePos'):
            taskMgr.remove('chargenMousePos')  
        self.common['traverser'].removeCollider(self.pickerNP)
        self.pickerNP.removeNode() 
        self.Ambient.removeNode()

        self.frameDesc.destroy()
        self.labelDesc.destroy()
        self.Tooltip.destroy()
        self.cursor.destroy()
        self.new_game_button.destroy()
        self.continue_button.destroy()
        self.close.destroy()
        self.title.destroy()
        self.mp_logo.destroy()
        
        render.setLightOff()
        self.ignoreAll()
        
        #self.common['music'].stop()
        
        #self.common['spawner']=Spawner(self.common)
        #self.common['levelLoader']=LevelLoader(self.common)
        if not self.newGame and 'max_level' in self.common:
            self.currentLevel = self.common['max_level']
        else:
            self.currentLevel = 0
        self.common['levelLoader'].load(self.currentLevel, PCLoad=False)
        #render.ls()
        if self.newGame or not 'current_class' in self.common:
            self.common['current_class'] = self.current_class
        else:
            self.current_class = self.common['current_class']

        if self.current_class=="1":
            self.common['PC']=Knight(self.common)
            #self.common['PC'].node.setPos(-12, 0, 0)
        elif self.current_class=="2": 
            self.common['PC']=Witch(self.common)
            #self.common['PC'].node.setPos(-12, 0, 0)
        elif self.current_class=="3": 
            self.common['PC']=Archer(self.common)
            #self.common['PC'].node.setPos(-12, 0, 0)    
        elif self.current_class=="4": 
            self.common['PC']=Wizard(self.common)
            #self.common['PC'].node.setPos(-12, 0, 0)
        pos=(data.levels[self.currentLevel]["enter"][0], data.levels[self.currentLevel]["enter"][1], data.levels[self.currentLevel]["enter"][2])     
        self.common['PC'].node.setPos(pos)
        self.common['music'].loop(1, fadeIn=True)
        if not self.newGame:
            self.common['levelLoader'].loadGame(PCLoad=True)

    def open_www(self, url, event=None):
        webbrowser.open_new(url)
    
    def windowEventHandler( self, window=None ): 
        #print "resize"
        if window is not None: # window is none if panda3d is not started
            wp = base.win.getProperties()
            X= wp.getXSize()/2
            Y= wp.getYSize()

#            self.frameDesc.setPos(-96+X, 0, -32)
            self.title.setPos(256+X, 0, -128)
            self.close.setPos(X*2, 0, -32)
            self.mp_logo.setPos(256+X, 0, -Y) 
        
    def GUIOnEnter(self, object, event=None):       
        if object[0]=="4":            
            if object[1]=="A":
                self.Tooltip['text']="Click to start!"    
            elif object[1]=="B":
                self.Tooltip['text']="Next level"        
            elif object[1]=="C":
                self.Tooltip['text']="Previous level"        
            self.Tooltip['text_pos'] = (10, -40,0)
            self.Tooltip['text_align'] =TextNode.ACenter 
            self.Tooltip.show()    
            return
        if not self.current_class:
            return            
        #print int(self.current_class)
        
    def GUIOnExit(self, event=None):
        self.Tooltip.hide()
        #print "out"
        
    def start_lightning(self, time=0.03):
        taskMgr.doMethodLater(time, self.lightning,'vfx')
        self.magicSound.play()
        
    def lightning(self, task):
        self.char2_magic.show()
        self.vfxU=self.vfxU+0.5   
        if self.vfxU>=1.0:
            self.vfxU=0
            self.vfxV=self.vfxV-0.125
        if self.vfxV <=-1:
            self.char2_magic.hide()
            self.vfxU=0
            self.vfxV=0
            return task.done
        self.char2_magic.setTexOffset(TextureStage.getDefault(), self.vfxU, self.vfxV)
        return task.again   
        
    def loopAnim(self, actor, anim):
        actor.loop(anim)
    
    def set_slider(self, id):
        #self.current_class=id
        #print id, 
        if id=="1":
            self.common['pc_stat1']=int(self.slider1['value'])
            #print self.common['pc_stat1']
        elif id=="2":
            self.common['pc_stat2']=int(self.slider2['value'])
            #print self.common['pc_stat2']
        elif id=="3":
            self.common['pc_stat3']=int(self.slider3['value'])        
            #print self.common['pc_stat3']
            
    def onClick(self):
        self.common['traverser'].traverse(render) 
        my_class=None
        for entry in self.common['queue'].getEntries():
            if entry.getIntoNodePath().hasTag("class"):
                my_class=entry.getIntoNodePath().getTag("class")
        
        if Path("save.dat").exists():
            self.continue_button.show()

        if my_class=="1":

            self.current_class=my_class
            self.title.hide()
            self.labelDesc.setText("Knight:\nHe has greater resistance.\nHe can attack with the sword\nand defend with a shield.")
            self.frameDesc.show()
            self.new_game_button.show()
            Sequence(self.character1.actorInterval("attack"),self.character1.actorInterval("block"), Func(self.loopAnim, self.character1, "idle")).start()
            self.swingSound.play()
            #self.character1.play("attack")
            self.character2.loop("idle")
        elif my_class=="2":
            self.current_class=my_class
            self.title.hide()
            self.labelDesc.setText("Witch:\nShe can throw energy balls and\na long distance beam.")
            self.frameDesc.show()
            self.new_game_button.show()
            Sequence(self.character2.actorInterval("attack", playRate=0.8),Func(self.loopAnim, self.character2, "idle")).start()
            Sequence(Wait(0.3), Func(self.start_lightning, 0.05)).start()
            #self.character2.play("attack")
            self.character1.loop("idle")
            #RayVfx(self.character2, texture='vfx/lightning.png').start()
        elif my_class=="3":
            self.current_class=my_class
            self.title.hide()
            self.labelDesc.setText("Archer:\nShe can throw arrows\nand run faster.")
            self.frameDesc.show()
            self.new_game_button.show()
            self.drawSound.play()
            self.character3.play("attack")
            Sequence(Wait(1.5),Func(self.fireArrow), Func(self.character3.play, "reset"),Wait(1.0),Func(self.loopAnim, self.character3, "idle")).start()
        elif my_class=="4":
            self.current_class=my_class
            self.title.hide()
            self.labelDesc.setText("Wizard:\nHe can throw magma balls\nand teleport himself.")
            self.frameDesc.show()
            self.new_game_button.show()
            self.character4.loop("attack")
            aura=vfx(self.character4, texture='vfx/tele2.png',scale=.5, Z=.85, depthTest=False, depthWrite=False)
            aura.show()
            aura.start()
            self.FFSound.play()
            Sequence(Wait(2.2), Func(self.loopAnim, self.character4, "idle")).start()
               
    def exit(self, event=None):
        self.common['root'].save_and_exit()
        #sys.exit()
    
    def __getMousePos(self, task):
        if base.mouseWatcherNode.hasMouse():  
            mpos = base.mouseWatcherNode.getMouse()
            self.pickerRay.setFromLens(base.camNode, mpos.getX(), mpos.getY())        
            pos2d=Point3(mpos.getX() ,0, mpos.getY())
            self.cursor.setPos(pixel2d.getRelativePoint(render2d, pos2d)) 
            self.Tooltip.setPos(self.cursor.getPos())    
        return task.again  
        
    def flicker(self, task):
        self.pLight.setAttenuation(Point3(1, 0, random.uniform(.1, 0.15)))  
        self.pLightNode.setZ(random.uniform(.9, 1.1))
        #self.pLight.setColor(VBase4(random.uniform(.9, 1.0), random.uniform(.9, 1.0), .9, 1))        
        return task.again  
        
    def camera_spin(self, task):
        H=self.cameraNode.getH()
        #Z=self.cameraNode.getZ()
        #print H
        if H<=-20.0 or H>=20.0:
            if self.reverse_spin:
                self.reverse_spin=False
            else:
                self.reverse_spin=True
        if self.reverse_spin:        
            self.cameraNode.setH(self.cameraNode, 4*globalClock.getDt())
            #self.cameraNode.setZ(Z+0.1*globalClock.getDt())
        else:
            self.cameraNode.setH(self.cameraNode, -4*globalClock.getDt())
            #self.cameraNode.setZ(Z-0.1*globalClock.getDt())
        return task.again  
#c=Camp()
#run()        
