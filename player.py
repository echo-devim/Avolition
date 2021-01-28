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
from direct.showbase.DirectObject import DirectObject
from direct.actor.Actor import Actor
from direct.interval.IntervalGlobal import *
from direct.filter.FilterManager import FilterManager
from direct.gui.DirectGui import *
from panda3d.core import *
from direct.particles import Particles
from panda3d.physics import BaseParticleRenderer
from panda3d.physics import PointParticleRenderer
from panda3d.physics import BaseParticleEmitter
from direct.particles.ParticleEffect import ParticleEffect
from vfx import vfx
from vfx import MovingVfx
import random
import shop
from direct.gui import DirectGuiGlobals as DGG
from DirectTooltip import *
from direct.showbase.PythonUtil import fitSrcAngle2Dest

class Player(DirectObject):
    
    def resetPointer(self, point3D):
        if (point3D != None):
            p3 = base.cam.getRelativePoint(render, point3D)
            p2 = Point2()
            newPos=(0,0,0)
            if base.camLens.project(p3, p2):
                r2d = Point3(p2[0], 0, p2[1])
                newPos = pixel2d.getRelativePoint(render2d, r2d)                            
                base.win.movePointer(0,int(newPos[0]),-int(newPos[2]))
        else:
            print("Warning: point3D is null")

    def onLevelLoad(self, common):
        self.node.setPos(0,0,0)
        self.black=common['map_black']
        self.walls=common['map_walls']
        self.floor=common['map_floor']
        
        #print self.black, self.walls, self.floor
        
        self.monster_list=common['monsterList']
        if not self.common['safemode']:
            wall_shader=loader.loadShader('tiles.sha')
            black_shader=loader.loadShader('black_parts.sha')
            floor_shader=loader.loadShader('floor.sha')
            self.floor.setShader(floor_shader)
            self.walls.setShader(wall_shader)
            self.black.setShader(black_shader)            
            self.floor.hide(BitMask32.bit(1)) 
        #shaders
        if not self.common['safemode']:    
            render.setShaderInput("slight0", self.Ambient)        
            render.setShaderInput("plight0", self.pLightNode)
            
            tex = loader.loadTexture('fog2.png')
            self.proj = render.attachNewNode(LensNode('proj'))
            #lens = OrthographicLens()        
            #lens.setFilmSize(3, 3)  
            lens=PerspectiveLens()        
            lens.setFov(45)
            self.proj.node().setLens(lens)
            #self.proj.node().showFrustum() 
            self.proj.reparentTo(render)
            self.proj.setHpr(180, 45, 0)
            self.proj.setZ(0.0)
            self.proj.reparentTo(self.cameraNode)
            ts = TextureStage('ts')
            tex.setWrapU(Texture.WMBorderColor  )
            tex.setWrapV(Texture.WMBorderColor  )
            tex.setBorderColor(Vec4(1,1,1,1))  
            self.black.projectTexture(ts, tex, self.proj)        
            self.walls.projectTexture(ts, tex, self.proj)       
        
            #shadows    
            self.floor.projectTexture(self.common['shadow_ts'] , self.common['shadowTexture'], self.common['shadowCamera'])  
            #base.bufferViewer.toggleEnable()
            #base.bufferViewer.setPosition("ulcorner")
            #base.bufferViewer.setCardSize(.5, 0.0)
    
    def __init__(self, common):
        self.common=common    
        self.black=common['map_black']
        self.walls=common['map_walls']
        self.floor=common['map_floor']
        self.monster_list=common['monsterList']
        self.audio3d=common['audio3d']
        
        if not self.common['safemode']:
            wall_shader=loader.loadShader('tiles.sha')
            black_shader=loader.loadShader('black_parts.sha')
            floor_shader=loader.loadShader('floor.sha')
            self.floor.setShader(floor_shader)
            self.walls.setShader(wall_shader)
            self.black.setShader(black_shader)
            
            self.floor.hide(BitMask32.bit(1))
        
        #parent node
        if 'player_node' in common:
            self.node=common['player_node']
        else:
            self.node=render.attachNewNode("pc")        

        self.isIdle=True
        self.message=None
        
        #sounds                
        self.sounds={'walk':self.audio3d.loadSfx("sfx/running-loud.wav"),
                     'door_open':self.audio3d.loadSfx("sfx/door_open2.ogg"),
                     'door_locked':self.audio3d.loadSfx("sfx/door_locked.ogg"),
                     'key':self.audio3d.loadSfx("sfx/key_pickup.ogg"),
                     'heal':self.audio3d.loadSfx("sfx/heal.ogg"),
                     'hit1':self.audio3d.loadSfx("sfx/hit1.ogg"),
                     'hit2':self.audio3d.loadSfx("sfx/hit2.ogg"),
                     'swing1':self.audio3d.loadSfx("sfx/swing1.ogg"),
                     'swing2':self.audio3d.loadSfx("sfx/swing2.ogg"),
                     'swing3':self.audio3d.loadSfx("sfx/swing3.ogg"),
                     'pain1':self.audio3d.loadSfx("sfx/pain1.ogg"),
                     'pain2':self.audio3d.loadSfx("sfx/pain2.ogg"),
                     'block1':self.audio3d.loadSfx("sfx/block1.ogg"),
                     'block2':self.audio3d.loadSfx("sfx/block2.ogg"),
                     'heal':self.audio3d.loadSfx("sfx/heal3.ogg")
                    }
        self.sounds['walk'].setVolume(0.2)
        self.sounds['walk'].setLoop(True)       
        for sound in self.sounds:
            self.audio3d.attachSoundToObject(self.sounds[sound], self.node)

        #camera
        self.cameraNode  = render.attachNewNode("cameraNode")         
        self.cameraNode.setPos(0, -2.5, 0)
        self.cameraNode.setHpr(0, -10, 0)
        #base.camera.setHpr ( 0, 10, 0 )
        #base.camera.setPos(0, 0, 7)
        #base.camera.setY(-6)
        #base.camera.setZ(2.7)
        #base.camera.setP(-13)
        base.camera.lookAt(self.node)
        base.camera.wrtReparentTo(self.cameraNode)  
        self.pointer=self.cameraNode.attachNewNode("pointerNode")         
        self.autoCamera=True
        self.pauseCamera=False
        #self.zonk=render.attachNewNode("zonk")         
        #self.zonk.setPos(-12,0,0)
        
        #light
        self.pLight = PointLight('plight')
        self.pLight.setColor(VBase4(.9, .9, 1.0, 1))
        #self.pLight.setColor(VBase4(.7, .7, .8, 1))
        #self.pLight.setAttenuation(Point3(3, 0, 0)) 
        self.pLight.setAttenuation(Point3(8, 0, 0.5))
        self.pLightNode = render.attachNewNode(self.pLight) 
        #self.pLightNode.setZ(3.0)
        render.setLight(self.pLightNode)
        
        self.sLight=Spotlight('sLight')        
        #self.sLight.setColor(VBase4(.4, .35, .35, 1))
        self.sLight.setColor(VBase4(.5, .45, .45, 1))
        if self.common['extra_ambient']:
            self.sLight.setColor(VBase4(.7, .6, .6, 1))
            #print "extra ambient"
        spot_lens = PerspectiveLens()
        spot_lens.setFov(160)
        self.sLight.setLens(spot_lens)
        self.Ambient = self.cameraNode.attachNewNode( self.sLight)
        self.Ambient.setPos(base.camera.getPos(render))
        self.Ambient.lookAt(self.node)
        render.setLight(self.Ambient)          
        
        #shaders
        if not self.common['safemode']:    
            render.setShaderInput("slight0", self.Ambient)        
            render.setShaderInput("plight0", self.pLightNode)
            
            tex = loader.loadTexture('fog2.png')
            self.proj = render.attachNewNode(LensNode('proj'))
            #lens = OrthographicLens()        
            #lens.setFilmSize(3, 3)  
            lens=PerspectiveLens()        
            lens.setFov(45)
            self.proj.node().setLens(lens)
            #self.proj.node().showFrustum() 
            self.proj.reparentTo(render)
            self.proj.setHpr(180, 45, 0)
            self.proj.setZ(0.0)
            self.proj.reparentTo(self.cameraNode)
            ts = TextureStage('ts')
            tex.setWrapU(Texture.WMBorderColor  )
            tex.setWrapV(Texture.WMBorderColor  )
            tex.setBorderColor(Vec4(1,1,1,1))  
            self.black.projectTexture(ts, tex, self.proj)        
            self.walls.projectTexture(ts, tex, self.proj)
        
        
            #shadows    
            self.floor.projectTexture(self.common['shadow_ts'] , self.common['shadowTexture'], self.common['shadowCamera'])  
            #base.bufferViewer.toggleEnable()
            #base.bufferViewer.setPosition("ulcorner")
            #base.bufferViewer.setCardSize(.5, 0.0) 
        
        #the plane will by used to see where the mouse pointer is
        self.plane = Plane(Vec3(0, 0, 1), Point3(0, 0, 1))        
       
        #key mapping
        self.keyMap = {'key_forward': False,
                        'key_back': False,
                        'key_left': False,
                        'key_right': False,
                        'key_cam_left': False,
                        'key_cam_right': False,
                        'key_action1': False,
                        'key_action2': False,
                        'key_menuitems': False}
        #prime key
        self.accept(common['keymap']['key_menuitems'], self.showMenuItems)
        self.accept(common['keymap']['key_useitem'], self.useItem)
        self.accept(common['keymap']['key_nextitem'], self.nextItem)
        self.accept(common['keymap']['key_forward'][0], self.keyMap.__setitem__, ["key_forward", True])
        self.accept(common['keymap']['key_back'][0], self.keyMap.__setitem__, ["key_back", True])
        self.accept(common['keymap']['key_left'][0], self.keyMap.__setitem__, ["key_left", True])
        self.accept(common['keymap']['key_right'][0], self.keyMap.__setitem__, ["key_right", True])
        self.accept(common['keymap']['key_cam_left'][0], self.keyMap.__setitem__, ["key_cam_left", True])
        self.accept(common['keymap']['key_cam_right'][0], self.keyMap.__setitem__, ["key_cam_right", True])
        self.accept(common['keymap']['key_action1'][0], self.keyMap.__setitem__, ["key_action1", True])
        self.accept(common['keymap']['key_action2'][0], self.keyMap.__setitem__, ["key_action2", True])
        #alt key
        self.accept(common['keymap']['key_forward'][1], self.keyMap.__setitem__, ["key_forward", True])
        self.accept(common['keymap']['key_back'][1], self.keyMap.__setitem__, ["key_back", True])
        self.accept(common['keymap']['key_left'][1], self.keyMap.__setitem__, ["key_left", True])
        self.accept(common['keymap']['key_right'][1], self.keyMap.__setitem__, ["key_right", True])
        self.accept(common['keymap']['key_cam_left'][1], self.keyMap.__setitem__, ["key_cam_left", True])
        self.accept(common['keymap']['key_cam_right'][1], self.keyMap.__setitem__, ["key_cam_right", True])
        self.accept(common['keymap']['key_action1'][1], self.keyMap.__setitem__, ["key_action1", True])
        self.accept(common['keymap']['key_action2'][1], self.keyMap.__setitem__, ["key_action2", True])
        self.accept(common['keymap']['key_forward'][0], self.keyMap.__setitem__, ["key_forward", True])
        #prime key up
        self.accept(common['keymap']['key_forward'][0]+"-up", self.keyMap.__setitem__, ["key_forward", False])
        self.accept(common['keymap']['key_back'][0]+"-up", self.keyMap.__setitem__, ["key_back", False])
        self.accept(common['keymap']['key_left'][0]+"-up", self.keyMap.__setitem__, ["key_left", False])
        self.accept(common['keymap']['key_right'][0]+"-up", self.keyMap.__setitem__, ["key_right", False])
        self.accept(common['keymap']['key_cam_left'][0]+"-up", self.keyMap.__setitem__, ["key_cam_left", False])
        self.accept(common['keymap']['key_cam_right'][0]+"-up", self.keyMap.__setitem__, ["key_cam_right", False])
        self.accept(common['keymap']['key_action1'][0]+"-up", self.keyMap.__setitem__, ["key_action1", False])
        self.accept(common['keymap']['key_action2'][0]+"-up", self.keyMap.__setitem__, ["key_action2", False])
        #alt key up
        self.accept(common['keymap']['key_forward'][1]+"-up", self.keyMap.__setitem__, ["key_forward", False])
        self.accept(common['keymap']['key_back'][1]+"-up", self.keyMap.__setitem__, ["key_back", False])
        self.accept(common['keymap']['key_left'][1]+"-up", self.keyMap.__setitem__, ["key_left", False])
        self.accept(common['keymap']['key_right'][1]+"-up", self.keyMap.__setitem__, ["key_right", False])
        self.accept(common['keymap']['key_cam_left'][1]+"-up", self.keyMap.__setitem__, ["key_cam_left", False])
        self.accept(common['keymap']['key_cam_right'][1]+"-up", self.keyMap.__setitem__, ["key_cam_right", False])
        self.accept(common['keymap']['key_action1'][1]+"-up", self.keyMap.__setitem__, ["key_action1", False])
        self.accept(common['keymap']['key_action2'][1]+"-up", self.keyMap.__setitem__, ["key_action2", False])
        self.accept(common['keymap']['key_forward'][0]+"-up", self.keyMap.__setitem__, ["key_forward", False])
        
        #camera zoom
        #self.accept(common['keymap']['key_zoomin'][0], self.zoom_control,[0.1])
        #self.accept(common['keymap']['key_zoomout'][0],self.zoom_control,[-0.1])
        #self.accept(common['keymap']['key_zoomin'][1], self.zoom_control,[0.1])
        #self.accept(common['keymap']['key_zoomout'][1],self.zoom_control,[-0.1])
        
        #self.keyMap = { "w" : False,
        #                "s" : False,
        #                "a" : False,
        #                "d" : False, 
        #                "q" : False,
        #                "e" : False,
        #                "mouse1" : False,
        #                "mouse3" : False,
        #                "space"  : False
        #                }
        #for key in self.keyMap.keys():
        #    self.accept(key, self.keyMap.__setitem__, [key, True])
        #    self.accept(key+"-up", self.keyMap.__setitem__, [key, False])
        
        #self.accept("wheel_up", self.zoom_control,[0.1])
        #self.accept("wheel_down", self.zoom_control,[-0.1])
        
        self.lastPos=self.node.getPos(render)
        self.camera_momentum=1.0
        self.attack_extra_damage=0
        self.powerUp=0
        self.speed=.8
        self.crit_hit=0
        self.actionLock=0
        self.hitMonsters=set()
        self.myWaypoints=[]
        
        #gui
        wp = base.win.getProperties()
        winX = wp.getXSize()
        winY = wp.getYSize()
        self.cursor=DirectFrame(frameSize=(-32, 0, 0, 32),
                                    frameColor=(1, 1, 1, 1),
                                    frameTexture='icon/cursor1.png',
                                    parent=pixel2d)        
        self.cursor.setPos(32,0, -32)
        self.cursor.flattenLight()
        self.cursor.setBin('fixed', 10)
        self.cursor.setTransparency(TransparencyAttrib.MDual)
        
        self.cursorPowerUV=[0.0, 0.75]
        self.cursorPower=DirectFrame(frameSize=(-64, 0, 0, 64),
                                    frameColor=(1, 1, 1, 1),
                                    frameTexture='icon/arc_grow2.png',
                                    parent=self.cursor)
        #self.cursorPower.setR(-45)
        self.cursorPower.setPos(48,0, -48)
        self.cursorPower.stateNodePath[0].setTexScale(TextureStage.getDefault(), 0.25, 0.25)        
        self.cursorPower.stateNodePath[0].setTexOffset(TextureStage.getDefault(),self.cursorPowerUV[0], self.cursorPowerUV[1])
        #self.cursor.setBin('fixed', 11)
        self.cursorPower2=DirectFrame(frameSize=(-64, 0, 0, 64),
                                    frameColor=(1, 1, 1, 1),
                                    frameTexture='icon/arc_shrink.png',
                                    parent=self.cursor)
        self.cursorPowerUV2=[0.0, 0.75]
        #self.cursorPower2.setR(135)
        self.cursorPower2.setPos(48,0,-48)                                            
        self.cursorPower2.stateNodePath[0].setTexScale(TextureStage.getDefault(), 0.25, 0.25)        
        self.cursorPower2.stateNodePath[0].setTexOffset(TextureStage.getDefault(),self.cursorPowerUV2[0], self.cursorPowerUV2[1])
        
        self.healthFrame=DirectFrame(frameSize=(-512, 0, 0, 64),
                                    frameColor=(1, 1, 1, 1),
                                    frameTexture='icon/health_frame2.png',
                                    parent=pixel2d)
        self.healthFrame.setTransparency(TransparencyAttrib.MDual)
        #self.healthFrame.setPos(512+200,0,-600)
        
        self.healthBar=DirectFrame(frameSize=(37, 0, 0, 16),
                                    frameColor=(0, 1, 0, 1),
                                    frameTexture='icon/glass4.png',
                                    parent=pixel2d)
        self.healthBar.setTransparency(TransparencyAttrib.MDual)
        #self.healthBar.setPos(71+200,0,3-600)
        self.healthBar.setScale(10,1, 1)
        self.isOptionsOpen=True
        self.options=DirectFrame(frameSize=(-256, 0, 0, 128),
                                    frameColor=(1,1,1,1),
                                    frameTexture='icon/options.png',
                                    parent=pixel2d)
        self.options.setTransparency(TransparencyAttrib.MDual)
        #self.options.setPos(210+winX,0,-128+84) 
        self.options.setPos(winX,0,-128) 
        self.options.setBin('fixed', 1)
        self.options_close=DirectFrame(frameSize=(-32, 0, 0, 32),
                                    frameColor=(1,1,1,0), 
                                    #frameTexture='icon/x.png',
                                    state=DGG.NORMAL,                                    
                                    parent=self.options)
        self.options_close.setPos(-221, 0, 5)
        self.options_close.bind(DGG.B1PRESS, self.optionsSet,['close']) 
        self.options_exit=DirectFrame(frameSize=(-200, 0, 0, 40),
                                    frameColor=(1,1,1,0), 
                                    state=DGG.NORMAL,                                    
                                    parent=self.options)
        self.options_exit.bind(DGG.B1PRESS, self.optionsSet,['exit'])                                    
        self.options_slider1 = DirectSlider(range=(0,100),
                                    value=self.common['soundVolume'],
                                    pageSize=10,      
                                    thumb_relief=DGG.FLAT,
                                    thumb_frameTexture='glass3.png',
                                    scale=70,
                                    thumb_frameSize=(0.07, -0.07, -0.11, 0.11),
                                    frameTexture='glass2.png',                                    
                                    command=self.optionsSet,
                                    extraArgs=["audio"],
                                    parent=pixel2d) 
        self.options_slider1.setBin('fixed', 2)                                         
        self.options_slider1.setPos(-95+winX,0,-24) 
        self.options_slider1.wrtReparentTo(self.options)
        
        self.options_slider2 = DirectSlider(range=(0,100),
                                    value= self.common['musicVolume'],
                                    pageSize=10,      
                                    thumb_relief=DGG.FLAT,
                                    thumb_frameTexture='glass3.png',
                                    scale=70,
                                    thumb_frameSize=(0.07, -0.07, -0.11, 0.11),
                                    frameTexture='glass2.png',                                    
                                    command=self.optionsSet,
                                    extraArgs=["music"],
                                    parent=pixel2d) 
        self.options_slider2.setBin('fixed', 2)                                         
        self.options_slider2.setPos(-95+winX,0,-50) 
        self.options_slider2.wrtReparentTo(self.options)
        
        self.options_rew=DirectFrame(frameSize=(-16, 0, 0, 16),
                                    frameColor=(1,1,1,0), 
                                    #frameTexture='icon/x.png',
                                    state=DGG.NORMAL,                                    
                                    parent=self.options)
        self.options_rew.setPos(-185, 0, 50)
        self.options_rew.bind(DGG.B1PRESS, self.optionsSet,['rew'])
        
        self.options_loop=DirectFrame(frameSize=(-16, 0, 0, 16),
                                    frameColor=(1,1,1,0), 
                                    #frameTexture='icon/x.png',
                                    state=DGG.NORMAL,                                    
                                    parent=self.options)
        self.options_loop.setPos(-159, 0, 50)
        self.options_loop.bind(DGG.B1PRESS, self.optionsSet,['loop'])
        
        self.options_play=DirectFrame(frameSize=(-16, 0, 0, 16),
                                    frameColor=(1,1,1,0), 
                                    #frameTexture='icon/x.png',
                                    state=DGG.NORMAL,                                    
                                    parent=self.options)
        self.options_play.setPos(-140, 0, 50)
        self.options_play.bind(DGG.B1PRESS, self.optionsSet,['play'])
        
        self.options_shuffle=DirectFrame(frameSize=(-16, 0, 0, 16),
                                    frameColor=(1,1,1,0), 
                                    #frameTexture='icon/x.png',
                                    state=DGG.NORMAL,                                    
                                    parent=self.options)
        self.options_shuffle.setPos(-115, 0, 50)
        self.options_shuffle.bind(DGG.B1PRESS, self.optionsSet,['shufle'])
        
        self.options_ff=DirectFrame(frameSize=(-16, 0, 0, 16),
                                    frameColor=(1,1,1,0), 
                                    #frameTexture='icon/x.png',
                                    state=DGG.NORMAL,                                    
                                    parent=self.options)
        self.options_ff.setPos(-92, 0, 50)
        self.options_ff.bind(DGG.B1PRESS, self.optionsSet,['ff'])
        
        self.options_autocam=DirectFrame(frameSize=(-70, 0, 0, 16),
                                    frameColor=(1,1,1,0), 
                                    #frameTexture='icon/x.png',
                                    state=DGG.NORMAL,                                    
                                    parent=self.options)
        self.options_autocam.setPos(-10, 0, 50)
        self.options_autocam.bind(DGG.B1PRESS, self.optionsSet,['autocam'])
        
        #self.options.setPos(winX,0,-128) 
        self.optionsSet("close")
        
        self.items = []
        self.maxItems = 5
        self.money = 500
        self.armor = 0
        coinIco = DirectLabel(image = "icon/coin.png",
                    frameColor = (0,0,0,0),
                    parent = aspect2d,
                    scale = 0.035,
                    pos = (1, 0, -0.95))
        coinIco.setTransparency(TransparencyAttrib.MDual)
        self.moneyLabel = DirectLabel(text = str(self.money),
                    text_fg = (1,1,1,1),
                    frameColor = (0,0,0,0),
                    parent = aspect2d,
                    text_font=self.common['font'],
                    scale = 0.045,
                    pos = (1.08, 0, -0.95))
        self.menuitems = None

        self.selectedItem = 0

        frm = DirectFrame(frameSize=(0, 0.15, 0, 0.15),
                        #frameColor=(0.1,0.4,0.2,0.5),
                        frameTexture='images/frame_blue.png',
                        pos=(0.75, 0, -0.99),
                        relief = DGG.FLAT,
                        parent=aspect2d)
        self.currItemIcon = DirectLabel(relief=None, image=None,
                pos = (0.075, 0, 0.075),
                parent = frm,
                scale = 0.06)
        frm.setTransparency(TransparencyAttrib.MDual)
        frm.setBin('fixed', 1)

        self.showCurrentItem()
        self.itemtooltip = None

        self.healthFrame.setPos(256+winX/2,0,-winY)
        self.healthBar.setPos(71-256+winX/2,0,7-winY)
        
        self.isBlockin=False
        self.isRunning=False
        #collisions
        #self.traverser=CollisionTraverser("playerTrav")
        #self.traverser.setRespectPrevTransform(True)
        #self.traverser.showCollisions(render)
        #self.queue = CollisionHandlerQueue() 
        
        #collision ray for testing visibility polygons
        self.coll_ray=self.node.attachNewNode(CollisionNode('collRay'))        
        self.coll_ray.node().addSolid(CollisionRay(0, 0, 2, 0,0,-180))
        self.coll_ray.setTag("visibility", "0") 
        self.coll_ray.node().setIntoCollideMask(BitMask32.allOff()) 
        self.coll_ray.node().setFromCollideMask(BitMask32.bit(1))  
        #self.traverser.addCollider(self.coll_ray, self.queue)  
        self.common['traverser'].addCollider(self.coll_ray, self.common['queue'])
        
        #collision sphere
        self.mask_2_3=BitMask32.bit(3)
        self.mask_2_3.setBit(2)
        self.coll_sphere=self.node.attachNewNode(CollisionNode('playerSphere'))
        self.coll_sphere.node().addSolid(CollisionSphere(0, 0, 1, 0.2))   
        self.coll_sphere.setTag("player", "1") 
        self.coll_sphere.node().setIntoCollideMask(BitMask32.bit(2))
        self.coll_sphere.node().setFromCollideMask(self.mask_2_3)
        #self.traverser.addCollider(self.coll_sphere, self.queue)
        self.common['traverser'].addCollider(self.coll_sphere, self.common['queue'])
        #self.coll_sphere.show()

        taskMgr.add(self.__getMousePos, "mousePosTask")
        taskMgr.add(self.update, "updatePC")

    def resetArmor(self, oldArmor, task):
        self.armor = oldArmor
        return task.done

    def getShopItems(self):
        return shop.items

    def useItem(self):
        if self.selectedItem < len(self.items):

            if self.items[self.selectedItem]['name'] == "health flask":
                self.partialHeal(20)
            elif self.items[self.selectedItem]['name'] == "armor flask":
                self.armor += 0.1
            elif self.items[self.selectedItem]['name'] == "attack boost":
                self.attack_extra_damage += 1
            elif self.items[self.selectedItem]['name'] == "great attack boost":
                self.attack_extra_damage += 3
            elif self.items[self.selectedItem]['name'] == "torch":
                self.pLight.setAttenuation(Point3(1, 0, 0.5))
            elif self.items[self.selectedItem]['name'] == "boots":
                self.speed += 0.1
            elif self.items[self.selectedItem]['name'] == "items boost":
                self.common["random-objects-freq"] += 0.1
            elif self.items[self.selectedItem]['name'] == "critical damage":
                self.crit_hit += 0.1
            elif self.items[self.selectedItem]['name'] == "invincible ring":
                oldArmor = self.armor
                self.armor = 1
                taskMgr.doMethodLater(15.0, self.resetArmor,'reset armor', extraArgs=[oldArmor], appendTask=True)
            elif self.items[self.selectedItem]['name'] == "health boost":
                #Ring around player
                self.HPring=Actor("models/ring_morph", {'anim' : 'models/ring_anim'})
                self.HPring.setScale(0.07)
                self.HPring.setColorScale(0,0.9,0.1,0.9)
                self.HPring.setZ(0)
                self.HPring.setLightOff()
                self.HPring.reparentTo(self.node)
                self.HPring.show()
                self.regenCount = 30
                taskMgr.doMethodLater(1.0, self.regenerate,'regenerate_task')

            #Update ui
            self.items[self.selectedItem]['count'] = self.items[self.selectedItem]['count'] - 1
            if (self.items[self.selectedItem]['count'] == 0):
                del self.items[self.selectedItem]
            if (self.selectedItem > 0):
                self.selectedItem-=1

            self.showCurrentItem()
    
    def nextItem(self):
        self.selectedItem += 1
        if (self.selectedItem) >= len(self.items):
            self.selectedItem = 0
        self.showCurrentItem()

    def showCurrentItem(self):
        if self.selectedItem < len(self.items):
            self.currItemIcon.setImage(self.items[self.selectedItem]['icon'])
        else:
            self.currItemIcon.clearImage()

    def sellItem(self,i,label):
        # Player items are the same objects of shop
        if i < len(self.items) and self.items[i]['count'] > 0:
            self.items[i]['count'] = self.items[i]['count'] - 1
            self.items[i]['available'] = self.items[i]['available'] + 1
            self.common['click2'].play()
            self.money += self.items[i]['price']
            if self.items[i]['count'] == 0:
                del self.items[i]
            # Reload items
            self.closeMenuItems()
            self.showMenuItems()
            self.moneyLabel.setText(str(self.money))

    def getItemIndex(self, item_name):
        for i in range(0,len(self.items)):
            if self.items[i]['name'] == item_name:
                return i
        return -1

    def buyItem(self,i):
        if len(self.items) <= self.maxItems:
            #Check if the player has enough money and the item is available
            if self.money >= shop.items[i]['price'] and shop.items[i]['available'] > 0 and len(self.items) < self.maxItems:
                #Check if the player already has this item
                pitem = self.getItemIndex(shop.items[i]['name'])
                if pitem < 0:
                    self.items.append(shop.items[i])
                    self.showCurrentItem()
                shop.items[i]['count'] = shop.items[i]['count'] + 1
                shop.items[i]['available'] = shop.items[i]['available'] - 1
                self.money -= shop.items[i]['price']
                self.common['click2'].play()
                self.closeMenuItems()
                self.showMenuItems()

                self.moneyLabel.setText(str(self.money))

    def addMoney(self, amount):
        self.money += amount
        self.moneyLabel.setText(str(self.money))

    def closeMenuItems(self):
        if self.menuitems:
            if self.itemtooltip:
                self.itemtooltip.delete()
                self.itemtooltip = None
            self.menuitems.cleanup()
            self.menuitems.removeNode()
            self.menuitems = None

    def showMenuItems(self):
        if self.menuitems:
            self.closeMenuItems()
            return
        # Menu Items
        self.menuitems = DirectDialog(frameSize = (-0.7, 0.7, -0.5, 0.5),
                                    frameTexture='images/texture_menuitems.png',
                                   fadeScreen = 0.4,
                                   relief = DGG.FLAT)
        self.menuitems.setTransparency(TransparencyAttrib.MDual)
        self.menuitems.setBin('fixed', 1)
        #self.menuitems.hide()
        DirectLabel(text = "Your Items:",
                    text_fg = (1,1,1,1),
                    frameColor = (0,0,0,0),
                    parent = self.menuitems,
                    text_font=self.common['font'],
                    scale = 0.05,
                    pos = (-0.5, 0, 0.45))
        
        for i in range(0,self.maxItems):
            frm = DirectFrame(frameSize=(0, 0.2, 0, 0.2),
                            frameColor=(1,1,1,0.2),
                            pos=(-0.6 + (0.25*i), 0, 0.2),
                            relief = DGG.RAISED,
                            parent=self.menuitems)
            if i < len(self.items):
                label = DirectLabel(text = "P: " + str(self.items[i]['price']) + ", Q: " + str(self.items[i]['count']),
                            text_fg = (1,1,1,1),
                            frameColor = (0,0,0,0),
                            parent = frm,
                            text_font=self.common['font'],
                            scale = 0.035,
                            pos = (0.1, 0, 0.02))
                btn = DirectButton(relief=None, image=self.items[i]['icon'],
                        command = self.sellItem, extraArgs=[i, label],
                        pos = (0.1, 0, 0.12),
                        parent = frm,
                        scale = 0.07)
                btn.bind(DGG.ENTER, self.showTooltip, [self.items[i]['description']])
                btn.bind(DGG.EXIT, self.deleteTooltip)

        DirectLabel(text = "Shop:",
                    text_fg = (1,1,1,1),
                    frameColor = (0,0,0,0),
                    parent = self.menuitems,
                    text_font=self.common['font'],
                    scale = 0.05,
                    pos = (-0.55, 0, 0.1))

        cols=2  #Columns for available items
        for y in range(0,cols):
            for i in range(0,int(len(shop.items)/cols)):
                j = (i+y*self.maxItems)
                bgcolor = (1,1,1,0.2)
                if shop.items[j]['available'] == 0 or self.money < shop.items[j]['price'] or len(self.items) == self.maxItems:
                    bgcolor = (0.8,0.3,0.3,0.5)
                frm = DirectFrame(frameSize=(0, 0.2, 0, 0.2),
                                frameColor=bgcolor,
                                pos=(-0.6 + (0.25*i), 0, -0.15 - (0.25*y)),
                                relief = DGG.RAISED,
                                parent=self.menuitems)
                btn = DirectButton(relief=None, image=shop.items[j]['icon'],
                        command = self.buyItem, extraArgs=[j],
                        pos = (0.1, 0, 0.12),
                        parent = frm,
                        scale = 0.07)
                DirectLabel(text = "P: " + str(shop.items[j]['price']) + ", Q: " + str(shop.items[j]['available']),
                            text_fg = (1,1,1,1),
                            frameColor = (0,0,0,0),
                            parent = frm,
                            text_font=self.common['font'],
                            scale = 0.035,
                            pos = (0.1, 0, 0.02))
                btn.bind(DGG.ENTER, self.showTooltip, [shop.items[j]['description']])
                btn.bind(DGG.EXIT, self.deleteTooltip)

    def showTooltip(self,text, args=None):
        self.itemtooltip = DirectTooltip()
        self.itemtooltip.show(text)

    def deleteTooltip(self, args=None):
        self.itemtooltip.delete()


    def regenerate(self, task):
        if self.regenCount <= 0:
            self.HPring.cleanup()
            self.HPring.removeNode()
            return task.done
        else:
            self.regenCount -= 1


        if self.MaxHP>self.HP>0:
            self.HP+=1
            self.healthBar.setScale(10*self.HP/self.MaxHP,1, 1)
            green=self.HP/self.MaxHP
            self.healthBar['frameColor']=(1-green, green, 0, 1)
        return task.again

    def optionsSet(self, opt, event=None):
        if opt!="close" and opt!="audio" and opt!="music":
            self.common['click'].play()
        #print opt
        if opt=="close":            
            wp = base.win.getProperties()
            winX = wp.getXSize()
            if self.isOptionsOpen:
                Sequence(LerpPosInterval(self.options, 0.1, VBase3(winX,0,-128+84)),LerpPosInterval(self.options, 0.2, VBase3(210+winX,0,-128+84))).start()
                #self.options.setPos(210+winX,0,-128+84) 
                #self.options_close['frameColor']=(1,1,1,0)
                self.isOptionsOpen=False
                #self.pauseCamera=False
                self.options_exit.hide()
                self.options_slider1.hide()
                self.options_slider2.hide()
                self.options_rew.hide()
                self.options_loop.hide()
                self.options_play.hide()
                self.options_shuffle.hide()
                self.options_ff.hide()
                self.options_autocam.hide()
            else:
                Sequence(LerpPosInterval(self.options, 0.2, VBase3(winX,0,-128+84)),LerpPosInterval(self.options, 0.1, VBase3(winX,0,-128))).start()
                #LerpPosInterval(self.options, 0.3, VBase3(winX,0,-128)).start()
                #self.options.setPos(winX,0,-128)
                #self.options_close['frameColor']=(1,1,1,1)
                self.isOptionsOpen=True
                #self.pauseCamera=True
                self.options_exit.show()
                self.options_slider1.show()
                self.options_slider2.show()
                self.options_rew.show()
                self.options_loop.show()
                self.options_play.show()
                self.options_shuffle.show()
                self.options_ff.show()
                self.options_autocam.show()
        elif opt=="exit":
            self.destroy()
        elif opt=="audio":            
             base.sfxManagerList[0].setVolume(self.options_slider1['value']*0.01)
        elif opt=="music":
            self.common['music'].setVolume(self.options_slider2['value'])
            #base.musicManager.setVolume(self.options_slider2['value']*0.01)
        elif opt=="rew":
            self.common['music'].REW()
        elif opt=="loop":
            self.common['music'].setLoop(True)
        elif opt=="play":
            self.common['music'].setLoop(False)
        elif opt=="shufle":
            self.common['music'].setShuffle()
        elif opt=="ff":
            self.common['music'].FF()
        elif opt=="autocam":
            if self.autoCamera:
                self.autoCamera=False
            else:
                self.autoCamera=True            
        
            
    def heal(self):
        self.sounds["heal"].play()
        vfx(self.node, texture='vfx/vfx3.png', scale=.8, Z=1.0, depthTest=False, depthWrite=False).start(0.03)                         
        self.healthBar.setScale(10,1, 1)        
        self.healthBar['frameColor']=(0, 1, 0, 1)
        self.HP=self.MaxHP

    def partialHeal(self, amount):
        self.sounds["heal"].play()
        vfx(self.node, texture='vfx/vfx3.png', scale=.8, Z=1.0, depthTest=False, depthWrite=False).start(0.03)                         
        self.HP+=amount
        if (self.HP > self.MaxHP):
            self.HP = self.MaxHP
        self.healthBar.setScale(10*self.HP/self.MaxHP,1, 1)
        green=self.HP/self.MaxHP
        self.healthBar['frameColor']=(1-green, green, 0, 1)

    def zoom(self, t):
        Z=base.camera.getY(self.cameraNode)
        #print Z
        if Z>=-5 and t>0:
            t=0 
        elif Z<=-16 and t<0:
            t=0         
        base.camera.setY(base.camera, t)        
        base.camera.setZ(base.camera, -t/2.5)
        base.camera.setP(base.camera, t*2.0)
        
    def hit(self, damage):
        #print "hit"
        damage=damage*(1-self.armor)
        #print damage
        if damage<0:
            damage=0  

        if  self.isBlockin:
            #print damage,
            self.sounds[random.choice(["block1", "block2"])].play()
            if damage > 0:
                damage = damage/(1+self.armor)
        else:
            self.sounds[random.choice(["pain1", "pain2"])].play()
            vfx(self.node, texture='vfx/blood_red.png', scale=.3, Z=1.0, depthTest=True, depthWrite=True).start(0.016)                         
            
        #damage=round(damage,0)    
        self.HP-=damage        
        #print self.HP
        if self.HP<=0:
            if(self.actor.getCurrentAnim()!="die"):
                self.actor.play("die") 
                self.sounds["walk"].stop()
                self.coll_sphere.node().setFromCollideMask(BitMask32.allOff())
                self.coll_sphere.node().setIntoCollideMask(BitMask32.allOff())
            self.HP=0
        elif not self.isBlockin:
            if(self.actor.getCurrentAnim()!="hit"):
                self.actor.play("hit")   
        self.healthBar.setScale(10*self.HP/self.MaxHP,1, 1)
        green=self.HP/self.MaxHP
        self.healthBar['frameColor']=(1-green, green, 0, 1)
        self.sounds["walk"].stop()            
        #self.keyMap["w"]=False
        #self.keyMap["s"]=False
        #self.keyMap["a"]=False
        #self.keyMap["d"]=False

    #TODO: Move into a shared utility class
    def showLabel(self, message):
        text = TextNode('onscreenmessage')
        text.setText(message)
        text.setFont(self.common['font'])
        self.message = aspect2d.attachNewNode(text)
        self.message.setScale(0.05)
        window = base.win.getProperties()
        windowX = window.getXSize()
        windowY = window.getYSize()
        self.message.setPos(-0.6,0,-0.8)

    def die(self, task):
        self.destroy()
        return task.done

    def zoom_control(self, amount):
        LerpFunc(self.zoom,fromData=0,toData=amount, duration=.5, blendType='easeOut').start()
        
    def update(self, task):
        dt = globalClock.getDt()
        self.cameraNode.setPos(self.node.getPos(render))  
        
        if self.HP <= 0:
            self.showLabel("Game over")
            taskMgr.doMethodLater(5.0, self.die,'die_task')
            return task.done

        #auto camera:
        if self.autoCamera and not self.pauseCamera and not self.isOptionsOpen:
            origHpr = self.cameraNode.getHpr()
            targetHpr = self.node.getHpr()
            # Make the rotation go the shortest way around.
            origHpr = VBase3(fitSrcAngle2Dest(origHpr[0], targetHpr[0]),
                                 fitSrcAngle2Dest(origHpr[1], targetHpr[1]),
                                 fitSrcAngle2Dest(origHpr[2], targetHpr[2]))

            # How far do we have to go from here?
            delta = max(abs(targetHpr[0] - origHpr[0]),
                            abs(targetHpr[1] - origHpr[1]),
                            abs(targetHpr[2] - origHpr[2]))
            if delta>10 and delta<150 or self.keyMap["key_forward"]:                                    
                # Figure out how far we should rotate in this frame, based on the
                # distance to go, and the speed we should move each frame.
                t = dt*delta/2            
                if t> .020:
                    t=.020
                    
                # If we reach the target, stop there.
                t = min(t, 1.0)
                newHpr = origHpr + (targetHpr - origHpr) * t
                self.cameraNode.setHpr(newHpr)
                self.camera_momentum+=dt*3
                
        if self.camera_momentum>10.0:
            self.camera_momentum=10.0            
        #rotate camera  
        if self.keyMap["key_cam_right"]:    
            self.cameraNode.setH(self.cameraNode, -70*dt* self.camera_momentum)
            self.camera_momentum+=dt*3
        elif self.keyMap["key_cam_left"]:        
            self.cameraNode.setH(self.cameraNode, 70*dt* self.camera_momentum)
            self.camera_momentum+=dt*3
        else:
            self.camera_momentum=0          
            
        if self.HP<=0:
            return task.again           
        
        #move         
        self.lastPos=self.node.getPos(render) 
        if self.keyMap["key_forward"]: 
            self.isIdle=False
            if self.isRunning:
                self.node.setFluidY(self.node, dt*7)                
                if(self.actor.getCurrentAnim()!="run"):
                    self.actor.loop("run")
                    if self.sounds["walk"].status() == self.sounds["walk"].PLAYING:
                        self.sounds["walk"].stop()
                    if self.sounds["run"].status() != self.sounds["run"].PLAYING:
                        self.sounds["run"].play()
            else:
                self.node.setFluidY(self.node, dt*4*self.speed)
                self.actor.setPlayRate(1, "walk") 
                if(self.actor.getCurrentAnim()!="walk"):
                    self.actor.loop("walk")
                    if self.sounds["walk"].status() != self.sounds["walk"].PLAYING:
                        self.sounds["walk"].play()
            if self.keyMap["key_right"]:
                self.node.setFluidX(self.node, dt*1*self.speed)
            if self.keyMap["key_left"]:            
                self.node.setFluidX(self.node, -dt*1*self.speed)
        elif self.keyMap["key_right"]: 
            self.isIdle=False
            self.node.setFluidX(self.node, dt*4*self.speed)
            self.actor.setPlayRate(-2, "strafe") 
            if(self.actor.getCurrentAnim()!="strafe"):
                self.actor.loop("strafe")
        elif self.keyMap["key_left"]:  
            self.isIdle=False
            self.node.setFluidX(self.node, -dt*4*self.speed)
            self.actor.setPlayRate(2, "strafe") 
            if(self.actor.getCurrentAnim()!="strafe"):
                self.actor.loop("strafe")                
        elif self.keyMap["key_back"]:  
            self.isIdle=False
            self.node.setFluidY(self.node, -dt*3*self.speed)
            self.actor.setPlayRate(-0.8, "walk") 
            if(self.actor.getCurrentAnim()!="walk"):
                self.actor.loop("walk") 
            if self.sounds["walk"].status() != self.sounds["walk"].PLAYING:
                self.sounds["walk"].play()    
        else:
            self.isIdle=True
        
        if not self.isRunning and "run" in self.sounds:
            if self.sounds["run"].status() == self.sounds["run"].PLAYING:
                self.sounds["run"].stop()
        
        if self.isIdle:            
            self.sounds["walk"].stop()
            if(self.actor.getCurrentAnim()!="idle"):
                self.actor.loop("idle")  
                
        return task.cont        
        
    def __getMousePos(self, task):
        if base.mouseWatcherNode.hasMouse():
            mpos = base.mouseWatcherNode.getMouse()
            pos3d = Point3()
            nearPoint = Point3()
            farPoint = Point3()
            base.camLens.extrude(mpos, nearPoint, farPoint)          
            if self.plane.intersectsLine(pos3d, render.getRelativePoint(camera, nearPoint),render.getRelativePoint(camera, farPoint)):            
                #if self.camera_momentum==0:
                if self.HP>0:            
                    self.node.headsUp(pos3d)
                self.pLightNode.setPos(pos3d)
                self.pLightNode.setZ(2.7)
                if hasattr(self, "target_node"):
                    self.target_node.setPos(pos3d)                
                    self.target_node.setZ(0.05)
                if not self.common['safemode']:
                    if self.node.getDistance(self.pLightNode)<13.0: 
                        self.common['shadowNode'].setPos(self.pLightNode.getPos(render))
                        self.common['shadowNode'].setZ(2.7)
            pos2d=Point3(base.mouseWatcherNode.getMouseX() ,0, base.mouseWatcherNode.getMouseY())
            self.cursor.setPos(pixel2d.getRelativePoint(render2d, pos2d))               
        return task.again        
        
    def windowEventHandler( self, window=None ):    
        if window is not None: # window is none if panda3d is not started
            wp = base.win.getProperties()
            winX = wp.getXSize()
            winY = wp.getYSize()    
            self.healthFrame.setPos(256+winX/2,0,-winY)
            self.healthBar.setPos(71-256+winX/2,0,7-winY) 
            if self.isOptionsOpen:
                self.options.setPos(winX,0,-128) 
            else:
                self.options.setPos(210+winX,0,-128+84) 
                
    def destroy(self): 
        self.common['levelLoader'].unload(True)      
        if taskMgr.hasTaskNamed("regenerate_task"):
            taskMgr.remove("regenerate_task")
        if taskMgr.hasTaskNamed("mousePosTask"):
            taskMgr.remove("mousePosTask")
        if taskMgr.hasTaskNamed("updatePC"):
            taskMgr.remove("updatePC")
        if taskMgr.hasTaskNamed("die_task"):
            taskMgr.remove("die_task")
        if self.message:
            self.message.removeNode()
        self.healthFrame.destroy()
        self.healthBar.destroy()
        self.cursor.destroy()
        self.cursorPower.destroy()
        self.cursorPower2.destroy()
        self.options.destroy()
        self.options_close.destroy()
        self.options_exit.destroy()
        self.options_slider1.destroy()
        self.options_slider2.destroy()
        
        self.currItemIcon.removeNode()
        self.closeMenuItems()
        self.actor.cleanup() 
        render.setLightOff()
        self.ignoreAll()

        self.actor.removeNode()
        #self.floor.setShaderOff()
        #self.walls.setShaderOff()
        #self.black.setShaderOff()
        self.pLightNode.removeNode()
        self.Ambient.removeNode()
        #self.walls.clearProjectTexture()
        #self.black.clearProjectTexture()

        self.cameraNode.removeNode()
        base.camera.reparentTo(render)

        #self.plane.removeNode()

        self.keyMap = None

        self.lastPos=None
        self.camera_momentum=None
        self.powerUp=None
        self.shieldUp=None
        self.actionLock=None
        self.hitMonsters=None
        self.myWaypoints=None
        self.HP=None
        self.armor=0 
        self.cursorPowerUV=None
        self.cursorPowerUV2=None
        self.isBlockin=None

        self.common['traverser'].removeCollider(self.coll_ray)
        self.common['traverser'].removeCollider(self.coll_sphere)      

        self.coll_ray.removeNode()
        self.coll_sphere.removeNode()

        self.node.setPos(0,0,0)
        self.common['player_node']=self.node
        self.common['CharGen'].load()

class Knight(Player):      
    
    def __init__(self, common): 
        super().__init__(common)
        #actor
        self.actor=Actor("models/pc/male", {"attack1":"models/pc/male_attack1",
                                            "attack2":"models/pc/male_attack2",
                                            "walk":"models/pc/male_run",
                                            "block":"models/pc/male_block",
                                            "die":"models/pc/male_die",
                                            "strafe":"models/pc/male_strafe2",
                                            "hit":"models/pc/male_hit",
                                            "idle":"models/pc/male_ready2"}) 
        self.actor.setBlend(frameBlend = True)  
        self.actor.setPlayRate(1.5, "attack1")
        self.actor.setPlayRate(0.5, "strafe")
        self.actor.setPlayRate(0.7, "die")
        self.actor.reparentTo(self.node)
        self.actor.setScale(.025)
        self.actor.setH(180.0)       
        self.actor.setBin("opaque", 10)
        
        self.shieldUp=0
        self.HP=60 #50.0+float(self.common['pc_stat1'])
        self.MaxHP=60 #50.0+float(self.common['pc_stat1'])
        self.HPregen=round((101-self.common['pc_stat1'])/100.0, 1)
        self.armor=0.3
        self.speed=(75+(101-self.common['pc_stat2'])/2)/100.0
        self.actor.setPlayRate(self.speed, "walk")
        self.baseDamage=(1.0+self.common['pc_stat3']/50.0)
        self.crit_hit=(5+(101-self.common['pc_stat3'])/2)/100.0
        self.crit_dmg=5+(101-self.common['pc_stat3'])/5
        
        hand=self.actor.exposeJoint(None, 'modelRoot', 'Bip001 R Hand')
        self.attack_ray=self.node.attachNewNode(CollisionNode('attackRay'))
        self.attack_ray.node().addSolid(CollisionSegment(0, 0, 0, 0, 0, 24))
        self.attack_ray.setTag("attack", "1") 
        self.attack_ray.node().setIntoCollideMask(BitMask32.allOff())
        self.attack_ray.node().setFromCollideMask(BitMask32.allOff())
        #self.attack_ray.show()
        self.attack_ray.reparentTo(hand)
        self.attack_ray.setX(self.attack_ray, 3)
        self.attack_ray.setHpr(self.attack_ray, (0,-5,-2))
        #self.traverser.addCollider(self.attack_ray, self.queue)
        self.common['traverser'].addCollider(self.attack_ray, self.common['queue'])
           
        taskMgr.doMethodLater(0.05, self.shield_task,'shield_task')
        taskMgr.doMethodLater(0.05, self.sword_task,'sword_task')
        #taskMgr.doMethodLater(1.0, self.regenerate,'regenerate_task')

    def attack(self, power=1):       
        self.attack_ray.node().setFromCollideMask(BitMask32.allOff())   
        #print self.hitMonsters
        if self.hitMonsters:        
            for monster in self.hitMonsters:
            #monster=self.hitMonsters.pop()            
                if monster:
                    monster=self.monster_list[int(monster)]
                    if monster:
                        monster.onHit((power*self.baseDamage)+self.attack_extra_damage)
                        if self.crit_hit>random.random():
                            Sequence(Wait(0.2), Func(monster.onHit, self.crit_dmg)).start()
        self.hitMonsters=set()
           
    def unBlock(self):
        self.isBlockin=False

    def update(self, task):
        self.common['traverser'].traverse(render) 
        hit_wall=False        
        self.myWaypoints=[]
        for entry in self.common['queue'].getEntries():
            if entry.getFromNodePath().hasTag("player"):
                hit_wall=True                
                if entry.getIntoNodePath().hasTag("id"):
                    monster = self.monster_list[int(entry.getIntoNodePath().getTag("id"))]
                    monster.PCisInRange=True
                    hit_wall=monster.isSolid                
            if entry.getFromNodePath().hasTag("attack"):
                self.hitMonsters.add(entry.getIntoNodePath().getTag("id"))
            if entry.getIntoNodePath().hasTag("index"):
                self.myWaypoints.append(int(entry.getIntoNodePath().getTag("index")))
        
        if hit_wall:
            self.node.setPos(self.lastPos) 
        
        if self.isBlockin:   
            self.sounds["walk"].stop()        
            if(self.actor.getCurrentAnim()!="block"):
                self.actor.loop("block")                
            return task.cont 
        
        
        anim=self.actor.getCurrentAnim()
        if anim=="attack1" or anim =="attack2" or anim=="hit":
            return task.cont
                
        return super().update(task)

    def sword_task(self, task):
        if self.HP<=0:
            return task.done
        if self.isBlockin:
            return task.again  
        if self.keyMap["key_action1"]:
            if self.powerUp>=15:
               return task.again  
            self.powerUp+=1
            self.cursorPowerUV[0]+=0.25
            if self.cursorPowerUV[0]>0.75:
                self.cursorPowerUV[0]=0
                self.cursorPowerUV[1]+=-0.25
            self.cursorPower.stateNodePath[0].setTexOffset(TextureStage.getDefault(),self.cursorPowerUV[0], self.cursorPowerUV[1])    
        else:             
            if self.powerUp>8:
                self.sounds["walk"].stop()
                self.actor.play("attack2") 
                self.sounds["swing2"].play()
                self.attack_ray.node().setFromCollideMask(BitMask32.bit(3))
                Sequence(Wait(.3), Func(self.attack, self.powerUp)).start()
            elif self.powerUp>0:
                self.sounds["walk"].stop()
                self.actor.play("attack1") 
                self.sounds["swing1"].play()
                self.attack_ray.node().setFromCollideMask(BitMask32.bit(3))
                Sequence(Wait(.2), Func(self.attack, self.powerUp)).start()
            self.powerUp=0
            self.cursorPowerUV=[0.0, 0.75]
            self.cursorPower.stateNodePath[0].setTexOffset(TextureStage.getDefault(),self.cursorPowerUV[0], self.cursorPowerUV[1])             
        return task.again 

    def shield_task(self, task):
        if self.HP<=0:
            return task.done
        if self.keyMap["key_action2"]:               
            if self.shieldUp>=15:
                #self.isBlockin=False 
                Sequence(Wait(0.3), Func(self.unBlock)).start()
                return task.again 
            self.isBlockin=True     
            self.shieldUp+=1
            #self.cursor['frameTexture']='icon/shield.png' 
            self.cursorPowerUV2[0]+=0.25
            if self.cursorPowerUV2[0]>0.75:
                self.cursorPowerUV2[0]=0
                self.cursorPowerUV2[1]+=-0.25            
            self.cursorPower2.stateNodePath[0].setTexOffset(TextureStage.getDefault(),self.cursorPowerUV2[0], self.cursorPowerUV2[1]) 
        else:            
            self.isBlockin=False
            if self.shieldUp<0:            
               return task.again
            #self.cursor['frameTexture']='icon/sword.png'    
            self.shieldUp-=1   
            self.cursorPowerUV2[0]-=0.25
            if self.cursorPowerUV2[0]<0:
                self.cursorPowerUV2[0]=0.75
                self.cursorPowerUV2[1]+=0.25           
            self.cursorPower2.stateNodePath[0].setTexOffset(TextureStage.getDefault(),self.cursorPowerUV2[0], self.cursorPowerUV2[1])               
        return task.again
       
    def destroy(self): 
        if taskMgr.hasTaskNamed("shield_task"):
            taskMgr.remove("shield_task")
        if taskMgr.hasTaskNamed("sword_task"):
            taskMgr.remove("sword_task")
        super().destroy()
        self.common['traverser'].removeCollider(self.attack_ray)
        self.attack_ray.removeNode()
        
class Witch(Player):  
    def __init__(self, common):
        super().__init__(common)     
        #actor
        if self.common['nude']:
            self.actor=Actor("models/pc/female_nude", {"attack1":"models/pc/female_attack1",
                                            "attack2":"models/pc/female_attack2",
                                            "walk":"models/pc/female_run",                                            
                                            "die":"models/pc/female_die",
                                            "strafe":"models/pc/female_strafe",
                                            "hit":"models/pc/female_hit",
                                            "idle":"models/pc/female_idle"}) 
        else:                                    
            self.actor=Actor("models/pc/female", {"attack1":"models/pc/female_attack1",
                                            "attack2":"models/pc/female_attack2",
                                            "walk":"models/pc/female_run",                                            
                                            "die":"models/pc/female_die",
                                            "strafe":"models/pc/female_strafe",
                                            "hit":"models/pc/female_hit",
                                            "idle":"models/pc/female_idle"}) 
        self.actor.setBlend(frameBlend = True)  
        self.actor.setPlayRate(1.5, "attack1")
        self.actor.setPlayRate(0.5, "strafe")
        self.actor.setPlayRate(0.7, "die")
        self.actor.reparentTo(self.node)
        self.actor.setScale(.026)
        self.actor.setH(180.0)  
        self.actor.node().setFinal(True)        
        #self.actor.setBin("opaque", 10)
        #self.actor.setTransparency(TransparencyAttrib.MMultisample)
        
        self.lightningOn=0
        self.isLightning=False

        self.sounds['pain1']=self.audio3d.loadSfx("sfx/fem_pain1.ogg")
        self.sounds['pain2']=self.audio3d.loadSfx("sfx/fem_pain2.ogg")
        self.sounds['plasma_charge']=self.audio3d.loadSfx("sfx/plasma_charge.ogg")
        self.sounds['lightning1']=self.audio3d.loadSfx("sfx/thunder2.ogg")                    
        self.sounds['lightning2']=self.audio3d.loadSfx("sfx/thunder3.ogg")
        self.sounds['plasma_fly']=self.audio3d.loadSfx("sfx/plasma_fly_loop.ogg")
        self.sounds['plasma_hit']=self.audio3d.loadSfx("sfx/plasma_hit.ogg")
        
        self.sounds['plasma_fly'].setLoop(True)
        
        self.MaxHP=50.0
        self.HP=50.0
        self.blast_size=(self.common['pc_stat1']+50)/100.0
        self.plasma_amp=(75+(101-self.common['pc_stat1'])/2)/100.0
        self.spark_a=(self.common['pc_stat2']-50)/50.0
        self.spark_b=14.0*(self.common['pc_stat2']-99.9)/100.0
        self.power_progress=1.0-(self.common['pc_stat3']/100.0)
        self.lastPos3d=None
        #print(self.plasma_amp)
        
        
        #lightning ray
        self.hand=self.node.attachNewNode("handNode")   
        self.hand.setZ(0.71)
        self.hand.setY(.3)
        self.lightning_vfx= loader.loadModel('vfx/vfx3')
        self.lightning_vfx.setTransparency(TransparencyAttrib.MDual)
        self.lightning_vfx.setBin("fixed", 1)
        self.lightning_vfx.setDepthTest(True)
        self.lightning_vfx.setDepthWrite(True)        
        self.lightning_vfx.setLightOff()
        self.lightning_vfx.reparentTo(self.hand)
        self.lightning_vfx.setH(-180)
        self.lightning_vfx.setScale(1,3.8,1)
        self.lightning_vfx.hide()
        self.vfxU=0
        self.vfxV=0
        #hand=self.actor.exposeJoint(None, 'modelRoot', 'Bip001 R Hand')
        self.attack_ray=self.node.attachNewNode(CollisionNode('attackRay'))
        self.attack_ray.node().addSolid(CollisionSegment(0, 0, 0, 0, 0, 12.5))
        self.attack_ray.setTag("attack", "1") 
        self.attack_ray.node().setIntoCollideMask(BitMask32.allOff())
        self.attack_ray.node().setFromCollideMask(BitMask32.allOff())
        #self.attack_ray.show()
        self.attack_ray.reparentTo(self.hand)
        #self.attack_ray.setX(self.attack_ray, 3)
        self.attack_ray.setP(-90)
        #self.traverser.addCollider(self.attack_ray, self.queue)
        self.common['traverser'].addCollider(self.attack_ray, self.common['queue'])
        
        #plasma
        self.plasma_node=self.node.attachNewNode("plasmaNode") 
        self.target_node=render.attachNewNode("plasmaTargetNode")
        self.plasma_node.setZ(0.94)
        self.plasma_node.setY(.32)
        self.plasma_vfx=vfx(self.plasma_node, texture='vfx/plasm2.png',scale=0.05, Z=0, depthTest=True, depthWrite=True)
        #self.plasma_vfx.loop(0.015) 
        self.plasma_vfx.hide()
        self.plasmaLock=False
        self.isBoom=False
        self.projectile=vfx(self.plasma_node, texture='vfx/plasm2.png',scale=0.05, Z=0, depthTest=True, depthWrite=True)
        if 'plasma_coll' in self.common:
            self.plasma_coll=self.common['plasma_coll']
        else:    
            self.plasma_coll=render.attachNewNode(CollisionNode('plasmaSphere'))
            self.plasma_coll.node().addSolid(CollisionSphere(0, 0, 0, 0.15))   
            self.plasma_coll.setTag("plasma", "1") 
            #self.plasma_coll.show()
            self.plasma_coll.node().setIntoCollideMask(BitMask32.allOff())
            self.plasma_coll.node().setFromCollideMask(BitMask32.allOff())            
            #audio
            self.audio3d.attachSoundToObject(self.sounds['plasma_fly'], self.plasma_coll)        
            self.audio3d.attachSoundToObject(self.sounds['plasma_hit'], self.plasma_coll)
        
        self.common['traverser'].addCollider(self.plasma_coll, self.common['queue'])
        self.lastPower=0
        self.hitSelf=False
              
        taskMgr.doMethodLater(0.05, self.lightning_task,'lightning_task')
        taskMgr.doMethodLater(0.05, self.plasma_task,'plasma_task')

    
    def spark_dmg(self, power, distance):
        pow=(8.0*self.power_progress+power*(1.0-self.power_progress))/2.0
        #print pow
        return self.attack_extra_damage+(pow*int(distance*self.spark_a-self.spark_b)/6.0)
    def spark_attack(self, power=1):       
        #self.attack_ray.node().setFromCollideMask(BitMask32.allOff())   
        #print self.hitMonsters
        if self.hitMonsters:
            for monster in self.hitMonsters:
                if monster:
                    monster=self.monster_list[int(monster)]
                    if monster:
                        dist=self.node.getDistance(monster.node)                           
                        monster.onHit(self.spark_dmg(power, dist), weapon="spark")
        self.hitMonsters=set()
        
    def plasma_dmg(self, power):
        #print power
        final=(power+5)*self.power_progress+((power+5)*(power+5)/15.0) *(1.0-self.power_progress)
        return (self.plasma_amp*final)+self.attack_extra_damage

    def plasma_attack(self, power=1):       
        #self.attack_ray.node().setFromCollideMask(BitMask32.allOff())   
        if self.hitMonsters:
            for monster in self.hitMonsters:
                if monster:
                    monster=self.monster_list[int(monster)]
                    if monster:
                        monster.onHit(2*self.plasma_dmg(power), weapon="plasma")                        
        self.hitMonsters=set()
    
    def end_boom(self):
        self.isBoom=False 
        self.plasmaLock=False  
        #self.pLight.setColor(VBase4(.8, .8, .9, 1))
        #self.pLight.setColor(VBase4(.7, .7, .8, 1))
        self.pLight.setColor(VBase4(.9, .9, 1.0, 1))
        #self.pLight.setColor(VBase4(.4, .4, .5, 1))
        #self.pLight.setAttenuation(Point3(3, 0, 0))    
        self.pLight.setAttenuation(Point3(2, 0, 0.5))
        self.plasma_coll.setScale(1)        
        self.plasma_attack(self.lastPower)
        if self.hitSelf:
            self.hit(self.lastPower/2)
        self.hitSelf=False    
        self.plasma_coll.node().setFromCollideMask(BitMask32.allOff()) 
        
    def boom(self): 
        vfx_node=self.projectile.vfx
        scale=self.blast_size*(self.lastPower+1)/15.0
        if self.isBoom:
            return
        self.isBoom=True
        self.pLight.setColor(VBase4(.35, .3, 1, 1)) 
        self.sounds['plasma_fly'].stop()
        self.sounds['plasma_hit'].play()
        self.plasma_coll.setScale(10*scale)
        if vfx_node:
            vfx_node.hide()            
            vfx(None, texture='vfx/m_blast.png', scale=scale, Z=0.0, depthTest=True, depthWrite=True, pos=vfx_node.getPos(render)).start(0.016)
            Sequence(Wait(0.6), Func(self.end_boom)).start()  
        
    def arm_plasma(self):
        self.plasma_coll.node().setFromCollideMask(self.mask_2_3)
    
    def plasma_task(self, task):
        if self.HP<=0:
            return task.done
        if self.isLightning:
            return task.again  
        if self.keyMap["key_action1"] and not self.plasmaLock:
            l=(self.powerUp+1)/25.0
            self.pLight.setColor(VBase4(l, l, l*1.5, 1))
            self.pLight.setAttenuation(Point3(0, 0, 1-l*1.2))  
            #self.cursor['frameTexture']='icon/cursor_plasma.png'                 
            if self.powerUp==0:
                if self.autoCamera and not self.pauseCamera and not self.isOptionsOpen:
                    if abs(self.cameraNode.getH()-self.node.getH())>90.0:
                        reset_pos=self.lastPos3d                                   
                        Sequence(LerpHprInterval(self.cameraNode, 0.2, self.node.getHpr()),Func(self.resetPointer,reset_pos)).start()                
                self.plasma_vfx.show()                
                self.plasma_vfx.loop(0.015) 
                self.sounds['plasma_charge'].play()
            if self.powerUp>=15:
               return task.again 
            self.plasma_vfx.vfx.setScale((self.powerUp+1)/3.0)
            #print self.plasma_vfx.vfx.getScale()
            self.powerUp+=1            
            self.cursorPowerUV[0]+=0.25
            if self.cursorPowerUV[0]>0.75:
                self.cursorPowerUV[0]=0
                self.cursorPowerUV[1]+=-0.25
            self.cursorPower.stateNodePath[0].setTexOffset(TextureStage.getDefault(),self.cursorPowerUV[0], self.cursorPowerUV[1])    
        else:   
            #if not self.isLightning:
            #    self.cursor['frameTexture']='icon/cursor1.png' 
            if self.powerUp>0:
                self.sounds["walk"].stop()
                self.actor.play("attack2") 
                self.plasma_vfx.stop()
                self.projectile=MovingVfx(self.plasma_node, self.target_node, texture='vfx/plasm2.png', scale=0.05, Z=0.0, time=.6, gravity=.55, depthTest=True, depthWrite=True)                
                self.projectile.start()
                self.sounds['plasma_fly'].play()
                self.projectile.vfx.setScale((self.powerUp+1)/3.0)
                #self.plasma_coll.node().setFromCollideMask(self.mask_2_3)  
                self.lastPower=self.powerUp               
                Sequence(Wait(0.1),Func(self.arm_plasma), Wait(0.4), Func(self.boom)).start() 
                self.plasmaLock=True
            self.powerUp=0
            self.cursorPowerUV=[0.0, 0.75]
            self.cursorPower.stateNodePath[0].setTexOffset(TextureStage.getDefault(),self.cursorPowerUV[0], self.cursorPowerUV[1])             
        return task.again 
    
    def lightning_task(self, task):
        if self.HP<=0:
            self.lightning_vfx.hide()
            if self.common['extra_ambient']:
                self.sLight.setColor(VBase4(.7, .6, .6, 1)) 
            else:            
                self.sLight.setColor(VBase4(.5, .45, .45, 1))
            #self.cursor['frameTexture']='icon/cursor1.png'     
            return task.done
        if self.keyMap["key_action2"]:               
            if self.lightningOn>=15:
                self.isLightning=False 
                self.lightning_vfx.hide()
                self.attack_ray.node().setFromCollideMask(BitMask32.allOff()) 
                #self.sLight.setColor(VBase4(.3, .25, .25, 1))
                if self.common['extra_ambient']:
                    self.sLight.setColor(VBase4(.7, .6, .6, 1)) 
                else:            
                    self.sLight.setColor(VBase4(.5, .45, .45, 1))   
                return task.again 
            if self.lightningOn==-1:
                self.sounds[random.choice(["lightning1", "lightning2"])].play() 
                self.attack_ray.node().setFromCollideMask(BitMask32.bit(3))                
                self.actor.play("attack1")    
            if self.lightningOn%2==0:
                r=random.uniform(0.2, 0.5)
                self.sLight.setColor(VBase4(r,r, 1, 1))
            else:
                #self.sLight.setColor(VBase4(.3, .25, .25, 1))
                if self.common['extra_ambient']:
                    self.sLight.setColor(VBase4(.7, .6, .6, 1)) 
                else:            
                    self.sLight.setColor(VBase4(.5, .45, .45, 1))   
            self.isLightning=True     
            self.lightningOn+=1
            #self.cursor['frameTexture']='icon/cursor_lightning.png' 
            self.lightning_vfx.show()
            self.cursorPowerUV2[0]+=0.25
            if self.cursorPowerUV2[0]>0.75:
                self.cursorPowerUV2[0]=0
                self.cursorPowerUV2[1]+=-0.25            
            self.cursorPower2.stateNodePath[0].setTexOffset(TextureStage.getDefault(),self.cursorPowerUV2[0], self.cursorPowerUV2[1]) 
            self.vfxU=self.vfxU+0.5   
            if self.vfxU>=1.0:
                self.vfxU=0
                self.vfxV=self.vfxV-0.125
            if self.vfxV <=-1:
                self.vfxU=0
                self.vfxV=0
            #print self.vfxU, self.vfxV  
            self.lightning_vfx.setTexOffset(TextureStage.getDefault(), self.vfxU, self.vfxV)
            self.spark_attack(self.lightningOn)
            #self.spark_attack(8.0)
        else:            
            self.isLightning=False
            self.lightning_vfx.hide()
            self.attack_ray.node().setFromCollideMask(BitMask32.allOff()) 
            #self.sLight.setColor(VBase4(.3, .25, .25, 1))  
            
            if self.common['extra_ambient']:
                self.sLight.setColor(VBase4(.7, .6, .6, 1)) 
            else:            
                self.sLight.setColor(VBase4(.5, .45, .45, 1))   
            #self.hitMonsters=set()
            if self.lightningOn<0:            
               return task.again
            #self.cursor['frameTexture']='icon/cursor1.png'    
            self.lightningOn-=1   
            self.cursorPowerUV2[0]-=0.25
            if self.cursorPowerUV2[0]<0:
                self.cursorPowerUV2[0]=0.75
                self.cursorPowerUV2[1]+=0.25           
            self.cursorPower2.stateNodePath[0].setTexOffset(TextureStage.getDefault(),self.cursorPowerUV2[0], self.cursorPowerUV2[1])               
        return task.again
     
    def update(self, task):
        dt = globalClock.getDt()
        self.common['traverser'].traverse(render)

        if self.projectile.vfx and not self.isBoom:
            self.plasma_coll.setPos(self.projectile.vfx.getPos())

        hit_wall=False  
        self.hitMonsters=set()    
        self.myWaypoints=[]
        for entry in self.common['queue'].getEntries():
            if entry.getFromNodePath().hasTag("player"):
                hit_wall=True                
                if entry.getIntoNodePath().hasTag("id"):
                    monster = self.monster_list[int(entry.getIntoNodePath().getTag("id"))]
                    monster.PCisInRange=True
                    hit_wall=monster.isSolid                    
            if entry.getFromNodePath().hasTag("plasma"):
                if entry.getIntoNodePath().hasTag("radar"):
                    pass
                else:    
                    if self.isBoom:
                        if entry.getIntoNodePath().hasTag("id"):
                            self.hitMonsters.add(entry.getIntoNodePath().getTag("id"))
                        if entry.getIntoNodePath().hasTag("player"):  
                            self.hitSelf=True
                    else:
                        self.boom()
            if entry.getFromNodePath().hasTag("attack"):
                self.hitMonsters.add(entry.getIntoNodePath().getTag("id"))
            if entry.getIntoNodePath().hasTag("index"):
                self.myWaypoints.append(int(entry.getIntoNodePath().getTag("index")))
        
        if hit_wall:
            self.node.setPos(self.lastPos) 
        
        if self.isLightning:   
            self.sounds["walk"].stop()        
            if(self.actor.getCurrentAnim()!="attack1"):
                self.actor.play("attack1")                
            return task.cont 
        
        if self.powerUp>0:
            self.sounds["walk"].stop()
            if(self.actor.getCurrentAnim()!="idle"):
                self.actor.loop("idle")  
            return task.cont             
            
        anim=self.actor.getCurrentAnim()
        if anim =="attack2" or anim=="hit":
            return task.cont 
                
        return super().update(task)
                
    def destroy(self): 
        if taskMgr.hasTaskNamed("lightning_task"):
            taskMgr.remove("lightning_task")
        if taskMgr.hasTaskNamed("plasma_task"):
            taskMgr.remove("plasma_task")
        self.common['traverser'].removeCollider(self.attack_ray)
        self.common['traverser'].removeCollider(self.plasma_coll)
        
        self.attack_ray.removeNode()        
        super().destroy()
            
class Archer(Player):
 
    def __init__(self, common):
        super().__init__(common)
        #actor
        if self.common['nude']:
            self.actor=Actor("models/pc/female2_nude", {"arm":"models/pc/female2_arm",
                                            "fire":"models/pc/female2_fire",
                                            "walk":"models/pc/female2_run",
                                            "run":"models/pc/female2_run2",
                                            "die":"models/pc/female2_die",
                                            "strafe":"models/pc/female2_strafe",
                                            "hit":"models/pc/female2_hit",
                                            "idle":"models/pc/female2_idle"}) 

        else:
            self.actor=Actor("models/pc/female2", {"arm":"models/pc/female2_arm",
                                                "fire":"models/pc/female2_fire",
                                                "walk":"models/pc/female2_run",
                                                "run":"models/pc/female2_run2",
                                                "die":"models/pc/female2_die",
                                                "strafe":"models/pc/female2_strafe",
                                                "hit":"models/pc/female2_hit",
                                                "idle":"models/pc/female2_idle"}) 
        self.actor.setBlend(frameBlend = True) 
        self.actor.setPlayRate(0.5, "strafe")
        self.actor.setPlayRate(1.5, "fire")
        #self.actor.setPlayRate(0.7, "die")
        #self.actor.setPlayRate(1.3, "walk")
        self.actor.reparentTo(self.node)
        self.actor.setScale(.026)
        self.actor.setH(180.0)       
        self.actor.setBin("opaque", 10)        
        #self.actor.setTransparency(TransparencyAttrib.MMultisample)

        self.sounds['pain1']=self.audio3d.loadSfx("sfx/fem_pain1.ogg")
        self.sounds['pain2']=self.audio3d.loadSfx("sfx/fem_pain2.ogg")
        self.sounds['fire']=self.audio3d.loadSfx("sfx/fire_arrow3.ogg")                    
        self.sounds['arm']=self.audio3d.loadSfx("sfx/draw_bow3.ogg")
        self.sounds['run']=self.audio3d.loadSfx("sfx/running-loud.wav")

        self.sounds['walk'].setLoop(True)       
        self.sounds['run'].setLoop(True) 
        for sound in self.sounds:
            self.audio3d.attachSoundToObject(self.sounds[sound], self.node)
        

        self.HP=55.0
        self.MaxHP=55.0
        self.runUp=0
        self.powerUp=0
        self.barbChance=int(self.common['pc_stat1']/2)    #x 100%        
        self.pierceChance=int((100-self.common['pc_stat1'])/2)#x 100%
        #print self.pierceChance
        self.bleedSlowRatio=int(self.common['pc_stat2'])    
        self.critChance=25+int(self.common['pc_stat3']/2)   #x 100%       
        print(self.critChance)
        self.baseDamage=(50+int(100-self.common['pc_stat3']))/100.0       
        self.speed=.8
        self.isRunning=False
        self.lastPos3d=None
                
        self.arrow_bone=self.actor.exposeJoint(None, 'modelRoot', 'arrow_bone')
        self.arrow=loader.loadModel('models/arrow')        
        self.arrow.reparentTo(self.arrow_bone)
        #self.arrow.setP(-45)
        self.arrows=[]
        
        
        
        self.damage_delta=(1.0+self.common['pc_stat3']/50.0)
        self.crit_hit=(5+(101-self.common['pc_stat3'])/2)/100.0
        self.crit_dmg=5+(101-self.common['pc_stat3'])/5
        
        self.isRunning=False
        
        #collisions
        
        self.arrowSpheres=[]
        self.freeArrowSpheres=[]
        for i in range(8):
            self.arrowSpheres.append(render.attachNewNode(CollisionNode('arrow'+str(i))))
            self.arrowSpheres[-1].node().addSolid(CollisionSphere(0, 0, 0, 0.1))   
            self.arrowSpheres[-1].setTag("arrow", str(i))     
            self.arrowSpheres[-1].node().setIntoCollideMask(BitMask32.allOff())
            self.arrowSpheres[-1].node().setFromCollideMask(BitMask32.allOff())
            #self.arrowSpheres[-1].show()
            self.freeArrowSpheres.append(i)
            self.common['traverser'].addCollider(self.arrowSpheres[-1], self.common['queue'])
            
        taskMgr.doMethodLater(0.05, self.run_task,'run_task')
        taskMgr.doMethodLater(0.05, self.bow_task,'bow_task')        

    def attack(self, arrow,  monster): 
        if arrow:
            if arrow in monster.arrows:
                return
            else:
                monster.arrows.add(arrow)
            power= arrow.getPythonTag('power')[2]
            damage=(power*self.baseDamage)+self.attack_extra_damage
            monster.onHit(damage, "arrow_hit")
            barb_roll=random.randrange(0, 101)            
            crit_roll=random.randrange(0, 101)
            barb=False
            if self.barbChance>barb_roll:
                #print "barb!"
                barb=True
                Sequence(Wait(0.2), Func(monster.onHit, damage, None)).start()  
            if crit_roll+power+self.crit_hit>self.critChance:    
                #print "critical:", crit_roll
                effect_roll=random.randrange(0, 101)
                if effect_roll>=self.bleedSlowRatio:
                    #print "slow"
                    if monster.totalSpeed<0.5:
                        monster.DOT+=power/4.0
                    if barb:
                        monster.totalSpeed=monster.totalSpeed*0.8
                    else:
                        monster.totalSpeed=monster.totalSpeed*0.9                        
                else:
                    #print "bleed"
                    if barb:
                        monster.DOT+=power
                    else:
                        monster.DOT+=power/2.0
    def getExpires(self, obj, delta):
        ttl=0.0
        if obj.hasPythonTag('TTL'):  
            ttl=obj.getPythonTag('TTL')              
        ttl+=delta
        if ttl>1.0:    
            return True            
        else:    
            obj.setPythonTag('TTL', ttl)  
            return False    
            
    def getArrowPower(self, arrow):
        return arrow.getPythonTag('power')
    
    def resetCollideMask(self, collider, mask):
        collider.node().setFromCollideMask(mask)
        
    def stickArrow(self, arrow, target=None):
        if arrow:
            collider=arrow.getPythonTag('collider')
            roll=random.randrange(0,101)            
            if target==None:                
                collider.wrtReparentTo(render)
                collider.node().setFromCollideMask(BitMask32.allOff()) 
                collider.setPythonTag('arrow', None)
                id=collider.getTag('arrow')        
                self.freeArrowSpheres.append(int(id))     
                self.arrows.pop(self.arrows.index(arrow))                            
                arrow.wrtReparentTo(render)                            
                Sequence(Wait(10.0),Func(arrow.removeNode)).start()
            elif self.pierceChance<roll:       
                if arrow.hasPythonTag('pierce'):
                    return                
                collider.wrtReparentTo(render)
                collider.node().setFromCollideMask(BitMask32.allOff()) 
                collider.setPythonTag('arrow', None)
                id=collider.getTag('arrow')        
                self.freeArrowSpheres.append(int(id))     
                self.arrows.pop(self.arrows.index(arrow))                            
                arrow.wrtReparentTo(target.rootBone)            
                Sequence(Wait(10.0),Func(arrow.removeNode)).start()
            else:
                arrow.setPythonTag('pierce', 1)
            #    #print "pierce!"
            #    collider.node().setFromCollideMask(BitMask32.allOff())
            #    Sequence(Wait(.2),Func(self.resetCollideMask,collider,self.mask_2_3)).start()
                
    def removeArrow(self, arrow):
        if arrow:
            collider=arrow.getPythonTag('collider')
            collider.wrtReparentTo(render)
            collider.node().setFromCollideMask(BitMask32.allOff()) 
            collider.setPythonTag('arrow', None)
            id=collider.getTag('arrow')            
            self.freeArrowSpheres.append(int(id))        
            #arrow.clearPythonTag('collider')
            arrow.removeNode()
        
    def fireArrow(self, power):
        newArrow=loader.loadModel('models/arrow')        
        newArrow.reparentTo(self.arrow_bone)
        newArrow.setP(-45)
        newArrow.wrtReparentTo(render)
        newArrow.setLightOff()        
        newArrow.setPythonTag('power', [power*80, 10.0+150.0/power, power])
        
        collider=self.arrowSpheres[self.freeArrowSpheres.pop()]
        collider.setPos(render, newArrow.getPos())
        collider.wrtReparentTo(newArrow)
        collider.node().setFromCollideMask(self.mask_2_3) 
        collider.setPythonTag('arrow', newArrow)
        
        newArrow.setPythonTag('collider', collider)
        
        self.arrow.hide()       
        self.arrows.append(newArrow)        
        Sequence(Wait(0.5),Func(self.arrow.show)).start()
    
    def bow_task(self, task):
        if self.HP<=0:
            return task.done
        if self.isRunning:
            return task.again  
        if self.keyMap["key_action1"]:
            if self.powerUp>=15:
               return task.again              
            if self.powerUp==1:  
                if self.autoCamera and not self.pauseCamera and not self.isOptionsOpen:
                    if abs(self.cameraNode.getH()-self.node.getH())>90.0:
                        reset_pos=self.lastPos3d                                   
                        Sequence(LerpHprInterval(self.cameraNode, 0.2, self.node.getHpr()),Func(self.resetPointer,reset_pos)).start()
                self.actor.play("arm")
                self.sounds["arm"].play()
                if self.sounds["walk"].status() == self.sounds["walk"].PLAYING:
                    self.sounds["walk"].stop()
            self.powerUp+=1    
            self.cursorPowerUV[0]+=0.25
            if self.cursorPowerUV[0]>0.75:
                self.cursorPowerUV[0]=0
                self.cursorPowerUV[1]+=-0.25
            self.cursorPower.stateNodePath[0].setTexOffset(TextureStage.getDefault(),self.cursorPowerUV[0], self.cursorPowerUV[1])    
        else:               
            if self.powerUp>2:
                self.actor.play("fire")               
                self.sounds["fire"].play()
                self.fireArrow(self.powerUp)
                self.pauseCamera=False                
            self.powerUp=0
            self.cursorPowerUV=[0.0, 0.75]
            self.cursorPower.stateNodePath[0].setTexOffset(TextureStage.getDefault(),self.cursorPowerUV[0], self.cursorPowerUV[1])             
        return task.again 
           
    def run_task(self, task):
        if self.HP<=0:
            return task.done
        if self.keyMap["key_action2"]:  
            if self.runUp>=15:
                self.isRunning=False 
                #Sequence(Wait(0.3), Func(self.unBlock)).start()
                return task.again 
            self.isRunning=True     
            self.runUp+=1
            #self.cursor['frameTexture']='icon/shield.png' 
            self.cursorPowerUV2[0]+=0.25
            if self.cursorPowerUV2[0]>0.75:
                self.cursorPowerUV2[0]=0
                self.cursorPowerUV2[1]+=-0.25            
            self.cursorPower2.stateNodePath[0].setTexOffset(TextureStage.getDefault(),self.cursorPowerUV2[0], self.cursorPowerUV2[1]) 
        else:            
            self.isRunning=False
            if self.runUp<0:            
               return task.again
            #self.cursor['frameTexture']='icon/sword.png'    
            self.runUp-=1   
            self.cursorPowerUV2[0]-=0.25
            if self.cursorPowerUV2[0]<0:
                self.cursorPowerUV2[0]=0.75
                self.cursorPowerUV2[1]+=0.25           
            self.cursorPower2.stateNodePath[0].setTexOffset(TextureStage.getDefault(),self.cursorPowerUV2[0], self.cursorPowerUV2[1])               
        return task.again

    def update(self, task):
        dt = globalClock.getDt()
        #arrows
        newArrowsArray = []
        for arrow in self.arrows:
            power=self.getArrowPower(arrow)            
            arrow.setFluidX(arrow, power[0]*dt)    
            arrow.setR(arrow, power[1]*dt)            
            if self.getExpires(arrow, dt): 
                self.removeArrow(arrow)
                #arrow.removeNode()
                #print "removed!"
            else:
                newArrowsArray.append(arrow)            
        self.arrows = newArrowsArray    
        
        self.common['traverser'].traverse(render) 
        hit_wall=False        
        self.myWaypoints=[]
        for entry in self.common['queue'].getEntries():
            if entry.getFromNodePath().hasTag('arrow'):                
                arrow=entry.getFromNodePath().getPythonTag('arrow') 
                if entry.getIntoNodePath().hasTag("id"):
                    self.attack(arrow, self.monster_list[int(entry.getIntoNodePath().getTag("id"))])                    
                    self.stickArrow(arrow, self.monster_list[int(entry.getIntoNodePath().getTag("id"))])
                elif entry.getIntoNodePath().hasTag("player"):        
                    pass
                else:
                    #print "wall hit"
                    self.stickArrow(arrow)                    
            if entry.getFromNodePath().hasTag("player"):
                hit_wall=True                
                if entry.getIntoNodePath().hasTag("id"):
                    monster = self.monster_list[int(entry.getIntoNodePath().getTag("id"))]
                    monster.PCisInRange=True
                    hit_wall=monster.isSolid
            if entry.getFromNodePath().hasTag("attack"):
                self.hitMonsters.add(entry.getIntoNodePath().getTag("id"))
            if entry.getIntoNodePath().hasTag("index"):
                self.myWaypoints.append(int(entry.getIntoNodePath().getTag("index")))
        
        if hit_wall:
            self.node.setPos(self.lastPos) 
                
        anim=self.actor.getCurrentAnim()
        if anim=="fire" or anim =="arm" or anim=="hit":
            return task.cont     
            
        if self.powerUp>0:        
            return task.cont
                
        return super().update(task)       
 
    def destroy(self): 
        if taskMgr.hasTaskNamed("run_task"):
            taskMgr.remove("run_task")
        if taskMgr.hasTaskNamed("bow_task"):
            taskMgr.remove("bow_task")
        self.isRunning=None

        for sphere in self.arrowSpheres:
            self.common['traverser'].removeCollider(sphere)
            sphere.removeNode()
            
        self.common['traverser'].removeCollider(self.coll_ray)
        self.common['traverser'].removeCollider(self.coll_sphere)
        

        self.coll_ray.removeNode()
        self.coll_sphere.removeNode()
        super().destroy()
        
class Wizard(Player):
   
    def __init__(self, common):
        super().__init__(common)

        #actor
        self.actor=Actor("models/pc/male2", {"attack":"models/pc/male2_attack",                                            
                                            "walk":"models/pc/male2_walk",
                                            "block":"models/pc/male2_aura",
                                            "die":"models/pc/male2_die",
                                            "strafe":"models/pc/male2_strafe",
                                            "hit":"models/pc/male2_hit",
                                            "idle":"models/pc/male2_idle"}) 
        self.actor.setBlend(frameBlend = True)          
        self.actor.setPlayRate(0.5, "strafe")        
        self.actor.reparentTo(self.node)
        self.actor.setScale(.024)
        self.actor.setH(180.0)       
        self.actor.setBin("opaque", 10)        
        #self.actor.setTransparency(TransparencyAttrib.MMultisample)

        
        self.target_node=render.attachNewNode("magma_node")  
        
        
        self.magmaList=[]
        
        #sounds                
        self.sounds['teleport']=self.audio3d.loadSfx("sfx/teleport.ogg")
        self.sounds['teleport_fail']=self.audio3d.loadSfx("sfx/teleport_fail.ogg")
        self.sounds['block2']=self.audio3d.loadSfx("sfx/block2.ogg")
        self.sounds['flame']=self.audio3d.loadSfx("sfx/flame2.ogg")
        self.sounds['spell']=self.audio3d.loadSfx("sfx/burn2.ogg")

        self.sounds['walk'].setLoop(True)       
        for sound in self.sounds:
            self.audio3d.attachSoundToObject(self.sounds[sound], self.node)
        
        self.magmaSound=base.loader.loadSfx("sfx/magma_flow2.ogg")
        self.magmaSound.setLoop(True)  

        #TODO: aura unused at the moment
        self.aura=vfx(self.actor, texture='vfx/aura2.png',scale=.75, Z=.85, depthTest=False, depthWrite=False)
        self.aura.loop(0.02)
        self.powerUp=0
        self.teleportUp=0
        self.HP=50.0
        self.MaxHP=50.0
        
        self.baseDamage=(50.0+self.common['pc_stat1'])/100.0
        self.maxMagma=1+int((100-self.common['pc_stat1'])/20)
        self.magmaTime=(50.0+self.common['pc_stat2'])/100.0
        self.magmaSize=(50.0+(100.0-self.common['pc_stat2']))/100.0
        self.teleportTime=(100-self.common['pc_stat3'])/1000.0
        self.recverTime=(50.0+(100.0-self.common['pc_stat3']))/100.0
        
        self.actor.setPlayRate(3.0*self.recverTime, "block") 
        
        #print "self.baseDamage",self.baseDamage
        #print "self.maxMagma", self.maxMagma
        #print "self.magmaTime", self.magmaTime
        #print "self.magmaSize", self.magmaSize
        #print "self.teleportTime", self.teleportTime
        #print "self.recverTime", self.recverTime
        
        self.canTeleport=False
        self.playerHit=False

        #collisions
        self.common['traverser'].addCollider(self.coll_ray, self.common['queue'])
        self.coll_ray2=self.target_node.attachNewNode(CollisionNode('collRay'))        
        self.coll_ray2.node().addSolid(CollisionRay(0, 0, 2, 0,0,-180))
        self.coll_ray2.node().setIntoCollideMask(BitMask32.allOff())
        self.coll_ray2.setTag("teleport", "0")
        #self.coll_sphere.show()
        #self.traverser.addCollider(self.coll_ray, self.queue)  
        self.common['traverser'].addCollider(self.coll_ray2, self.common['queue'])
         
        taskMgr.doMethodLater(0.05+self.teleportTime, self.teleport_task,'teleport_task')
        taskMgr.doMethodLater(0.05, self.magma_task,'magma_task')
        taskMgr.doMethodLater(0.5, self.magmaDamage,'magmaDamage')
     
    def attack(self, power=1):       
        self.attack_ray.node().setFromCollideMask(BitMask32.allOff())   
        #print self.hitMonsters
        if self.hitMonsters:        
            for monster in self.hitMonsters:
            #monster=self.hitMonsters.pop()            
                if monster:
                    monster=self.monster_list[int(monster)]
                    if monster:
                        monster.onHit((power*self.damage_delta)+self.attack_extra_damage)
                        if self.crit_hit>random.random():
                            Sequence(Wait(0.2), Func(monster.onHit, self.crit_dmg)).start()
        self.hitMonsters=set()
    
    def magmaDamage(self, task):
        if self.hitMonsters:        
            for monster in self.hitMonsters:
            #monster=self.hitMonsters.pop()            
                if monster and self.monster_list:
                    monster=self.monster_list[int(monster)]
                    if monster:
                        Sequence(Wait(random.uniform(0.0, 0.2)), Func(monster.onHit, damage=0, weapon="magma")).start()
        if self.playerHit:
            if self.HP<=0:
                return task.done
            #print "hit player"   
            self.sounds['flame'].play()            
            vfx(self.node, texture="vfx/small_flame.png",scale=.6, Z=.7, depthTest=False, depthWrite=False).start(0.016, stopAtFrame=24) 
            self.HP-=2.0        
            #print self.HP
            if self.HP<=0:
                if(self.actor.getCurrentAnim()!="die"):
                    self.actor.play("die") 
                self.sounds["walk"].stop()
                self.coll_sphere.node().setFromCollideMask(BitMask32.allOff())
                self.coll_sphere.node().setIntoCollideMask(BitMask32.allOff())
                self.HP=0              
            self.healthBar.setScale(10*self.HP/self.MaxHP,1, 1)
            green=self.HP/self.MaxHP
            self.healthBar['frameColor']=(1-green, green, 0, 1)
                
        self.hitMonsters=set()    
        return task.again    
        
    def magmaMover(self, task):  
        if self.magmaList[-1].getCurrentAnim()=="flow":   
            return task.done
        LerpPosInterval(self.magmaList[-1], 0.6, self.target_node.getPos()).start()
        LerpHprInterval(self.magmaList[-1], 0.2, self.magmaList[-1].getHpr()+Point3(10,0,0)).start()
        return task.again
    
    def magmaSpawn(self):  
        self.sounds['spell'].play()
        self.magmaSound.play()
        magma=Actor("models/lava", {"flow":"models/lava_anim"}) 
        magma.setBlend(frameBlend = True)        
        magma.reparentTo(render)        
        magma.setPos(self.target_node.getPos())
        coll_sphere2=magma.attachNewNode(CollisionNode('magmaSphere'))
        coll_sphere2.node().addSolid(CollisionSphere(0, 0, 0.4, 0.45))   
        coll_sphere2.setTag("magma", "1") 
        #coll_sphere.show()
        coll_sphere2.node().setIntoCollideMask(BitMask32.allOff())
        coll_sphere2.node().setFromCollideMask(self.mask_2_3)        
        self.common['traverser'].addCollider(coll_sphere2, self.common['queue'])
        magma.setPythonTag("collider",coll_sphere2)       
        magma.setScale(0.3*self.magmaSize) 
        self.magmaList.append(magma)                
        taskMgr.doMethodLater(0.2, self.magmaMover, 'magma_task')
        
    def magmaRemove(self, magma):  
        if magma:
            #print magma, "removed"
            actor_node=self.magmaList.pop(self.magmaList.index(magma))
            collider=actor_node.getPythonTag("collider")
            self.common['traverser'].removeCollider(collider)
            actor_node.cleanup()
            actor_node.removeNode()
            if not self.magmaList:
                self.magmaSound.stop()
                self.sLight.setColor(VBase4(.5, .45, .45, 1))
                self.pLight.setColor(VBase4(.9, .9, 1.0, 1))
                if self.common['extra_ambient']:
                    self.sLight.setColor(VBase4(.7, .6, .6, 1))
                    
    def magmaDrop(self):  
        #print len(self.magmaList),
        magma=self.magmaList[-1]
        scale=magma.getScale()[0]                
        magma.setPlayRate(2.0-self.magmaTime, "flow")
        magma.play("flow")
        temp=magma.actorInterval("flow", playRate=2.0-self.magmaTime)
        speed=temp.getDuration()
        magma.wrtReparentTo(render)
        Sequence(Wait(0.6), Func(magma.setZ, render, -0.2)).start()              
        collider=magma.getPythonTag("collider")
        collider.setPythonTag("power", self.powerUp*self.baseDamage)
        collider.setTag("magma", "2") 
        LerpScaleInterval(collider, speed, scale*3.0, blendType='easeOut').start()            
        Sequence(Wait(speed), Func(self.magmaRemove,magma)).start()
        self.powerUp=0
        self.cursorPowerUV=[0.0, 0.75]
        self.cursorPower.stateNodePath[0].setTexOffset(TextureStage.getDefault(),self.cursorPowerUV[0], self.cursorPowerUV[1])             
        self.keyMap["key_action1"]=False
        
    def magma_task(self, task):
        if self.HP<=0:
            return task.done
        if self.keyMap["key_action1"]:
            if len(self.magmaList)>self.maxMagma:
                return task.again
            if(self.actor.getCurrentAnim()=="block"):
                return task.again
            self.pLight.setColor(VBase4(1.0, .7, .7, 1))
            self.sLight.setColor(VBase4(.55, .35, .35, 1))
            if self.common['extra_ambient']:
                self.sLight.setColor(VBase4(.85, .6, .6, 1))
            if self.powerUp==0:
                self.magmaSpawn()
            if self.powerUp>=15:
               return task.again  
            self.powerUp+=1
            self.magmaList[-1].setScale(self.magmaList[-1], 1.1)
            self.cursorPowerUV[0]+=0.25
            if self.cursorPowerUV[0]>0.75:
                self.cursorPowerUV[0]=0
                self.cursorPowerUV[1]+=-0.25
            self.cursorPower.stateNodePath[0].setTexOffset(TextureStage.getDefault(),self.cursorPowerUV[0], self.cursorPowerUV[1])    
        else:             
            if self.powerUp>0:
               self.magmaDrop()               
        return task.again     

    
    def resetLight(self):
        if not self.magmaList:
            self.sLight.setColor(VBase4(.5, .45, .45, 1))
            self.pLight.setColor(VBase4(.9, .9, 1.0, 1))
            if self.common['extra_ambient']:
                self.sLight.setColor(VBase4(.7, .6, .6, 1))
        else:
            self.pLight.setColor(VBase4(1.0, .7, .7, 1))
            self.sLight.setColor(VBase4(.55, .35, .35, 1))
            if self.common['extra_ambient']:
                self.sLight.setColor(VBase4(.85, .6, .6, 1))
                
    def doTeleport(self):
        #print "teleport"        
        self.sLight.setColor(VBase4(.4, .4, .6, 1))
        self.pLight.setColor(VBase4(.4, .4, 1.0, 1))
        if self.common['extra_ambient']:
            self.sLight.setColor(VBase4(.5, .5, .7, 1))
        Sequence(Wait(1.0), Func(self.resetLight)).start()
        if self.canTeleport:           
            self.sounds['teleport'].play()
            vfx(self.actor, texture='vfx/tele2.png',scale=.5, Z=.85, depthTest=False, depthWrite=False).start()
            self.node.setPos(self.target_node.getPos())
            Sequence(Wait(0.1), Func(self.resetPointer,self.node.getPos())).start()        
        else:
            self.sounds['teleport_fail'].play()
            
    def teleport_task(self, task):        
        if self.HP<=0:
            return task.done        
        if self.keyMap["key_action2"]:#key down             
            if self.teleportUp==-1:
                self.doTeleport()
                self.teleportUp=15                
                return task.again
        if not self.keyMap["key_action2"]:   
            if self.teleportUp<0:            
               return task.again
            #self.cursor['frameTexture']='icon/cursor1.png'    
            self.teleportUp-=1   
            self.cursorPowerUV2[0]-=0.25
            if self.cursorPowerUV2[0]<0:
                self.cursorPowerUV2[0]=0.75
                self.cursorPowerUV2[1]+=0.25           
            self.cursorPower2.stateNodePath[0].setTexOffset(TextureStage.getDefault(),self.cursorPowerUV2[0], self.cursorPowerUV2[1])               
        return task.again
        
    def update(self, task):
        self.common['traverser'].traverse(render) 
        hit_wall=False 
        self.canTeleport=False   
        self.playerHit=False
        self.myWaypoints=[]
        for entry in self.common['queue'].getEntries():
            #print entry
            if entry.getFromNodePath().hasTag("player"):
                hit_wall=True                
                if entry.getIntoNodePath().hasTag("id"):
                    monster = self.monster_list[int(entry.getIntoNodePath().getTag("id"))]
                    monster.PCisInRange=True
                    hit_wall=monster.isSolid                 
            if entry.getFromNodePath().hasTag("magma"):               
                status=entry.getFromNodePath().getTag("magma")
                into=entry.getIntoNodePath()
                if status=="1":
                    self.magmaDrop()
                if into.hasTag('id'):
                    self.hitMonsters.add(into.getTag("id"))
                    self.monster_list[int(into.getTag("id"))].lastMagmaDmg=entry.getFromNodePath().getPythonTag("power")
                elif into.hasTag('player'):                         
                    self.playerHit=True
            if entry.getFromNodePath().hasTag("visibility"):            
                if entry.getIntoNodePath().hasTag("index"):
                    self.myWaypoints.append(int(entry.getIntoNodePath().getTag("index")))
            if entry.getFromNodePath().hasTag("teleport"):            
                if entry.getIntoNodePath().hasTag("index"):
                    self.canTeleport=True
                    

        if hit_wall:
            self.node.setPos(self.lastPos) 
        
        #if self.teleportUp>0:   
        #    self.sounds["walk"].stop()             
        #    if(self.actor.getCurrentAnim()!="block"):
        #        self.actor.loop("block")                
        #    return task.cont         
        
        if self.keyMap["key_action2"]:
            if self.teleportUp==-1:
                self.doTeleport()
                self.actor.play("block")
                self.teleportUp=15
        
        if self.powerUp>0:            
            self.sounds["walk"].stop()             
            if(self.actor.getCurrentAnim()!="attack"):
                self.actor.loop("attack")                
            return task.cont         
        else:
            if(self.actor.getCurrentAnim()=="attack"):
                self.actor.loop("idle") 
                
        anim=self.actor.getCurrentAnim()
        if anim=="attack" or anim=="hit" or anim=="block":
            self.sounds["walk"].stop()
            return task.cont             

        return super().update(task)      
     
    def destroy(self): 
        if taskMgr.hasTaskNamed("teleport_task"):
            taskMgr.remove("teleport_task")
        if taskMgr.hasTaskNamed("magma_task"):
            taskMgr.remove("magma_task")  
        if taskMgr.hasTaskNamed("magmaDamage"):
            taskMgr.remove("magmaDamage")     
        
        for magma in self.magmaList:
            self.magmaRemove(magma)
        
        #self.common['traverser'].removeCollider(self.attack_ray)        

        self.coll_ray.removeNode()
        self.coll_sphere.removeNode()
        #self.attack_ray.removeNode()        
        super().destroy()
                
