'''
    Avolition
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
from panda3d.ai import *
from vfx import vfx
from vfx import short_vfx
import random
import data
import json
import pickle
from pathlib import Path
from direct.particles import Particles
from panda3d.physics import BaseParticleRenderer
from panda3d.physics import PointParticleRenderer
from panda3d.physics import BaseParticleEmitter
from direct.particles.ParticleEffect import ParticleEffect

class Interactive():
    '''Object that are "clickable". Made from both a 3d object and a 2d UI
       proto should be a  dict containing these keys:
       'model' - path to a bam or eg model
       'scale' - uniform or XYZ scale
       'gui' - path to a gui picture
       'command' - command executed on click
      Each of these can be overriden by an argument of the same name.'''
    def __init__(self, common, proto, pos, model=None, scale=None, gui=None, command=None):
        common['interactiveList'].append(self)
        self.id=len(common['interactiveList'])-1
        self.interactiveList=common['interactiveList']

        self.common=common
        if model:
            self.model=loader.loadModel(model)
        else:
            self.model=loader.loadModel(proto['model'])
        self.model.reparentTo(render)
        self.model.setPos(pos)
        if scale:
            self.model.setScale(scale)
        else:
            self.model.setScale(proto['scale'])
        #self.model.setTransparency(TransparencyAttrib.MDual)
        self.model.setBin("opaque", 10)
        if gui:
            self.gui=DirectFrame(frameSize=(-64, 0, 0, 64),
                                    frameColor=(1, 1, 1, 1),
                                    frameTexture=gui,
                                    state=DGG.NORMAL,
                                    parent=pixel2d)
        else:
            self.gui=DirectFrame(frameSize=(-64, 0, 0, 64),
                                    frameColor=(1, 1, 1, 1),
                                    frameTexture=proto['gui'],
                                    state=DGG.NORMAL,
                                    parent=pixel2d)
        self.gui.setPos(32, 0, 90)
        self.gui.flattenLight()
        self.gui.setTransparency(TransparencyAttrib.MDual)
        if command:
            self.gui.bind(DGG.B1PRESS, self._execute, [command])
        else:
            self.gui.bind(DGG.B1PRESS, self._execute, [proto['command']])
        self.gui.setBin('fixed', -10)
        self.gui.hide()

        self.active=True

        ProjectileInterval(self.model, startPos=(pos[0], pos[1], pos[2]+1), endPos=pos, duration=1.0, gravityMult=1.0).start()
        #print "hop!"
        taskMgr.doMethodLater(.1, self._update,'ia_update'+str(self.id))

    def destroy(self):
        self.active=False

    def _execute(self, command, mouse=None):
        if self.model.getDistance(self.common['PC'].node)>2.5:
            #print "can't reach!"
            return
        if command=="heal":
            self.common['PC'].heal()
            self.active=False
        elif command=="key_pickup":
            #print "Got Key!"
            self.common['PC'].sounds['key'].play()
            self.common["key_icon"].show()
            self.active=False
        elif command=="exit":
            if self.common["key_icon"].isHidden():
               #print "no key"
               self.common['PC'].sounds['door_locked'].play()
            else:
                #print "next level..."
                self.common['PC'].sounds['door_open'].play()
                self.common['levelLoader'].load_next()
                self.common['music'].FF()
                self.active=False

    def _update(self, task):
        if not self.active:
            self.gui.destroy()
            self.model.removeNode()
            self.interactiveList[self.id]=None
            return task.done
        if self.model.getDistance(self.common['PC'].node)<5:
            self.gui.show()
            p3 = base.cam.getRelativePoint(render, self.model.getPos(render))
            p2 = Point2()
            newPos=(0,0,0)
            if base.camLens.project(p3, p2):
                r2d = Point3(p2[0], 0, p2[1])
                newPos = pixel2d.getRelativePoint(render2d, r2d)
                #newPos[2]+=50
            LerpPosInterval(self.gui, 0.1, newPos).start()
        else:
            self.gui.hide()
        return task.again

class RandomObject():
    def __init__(self, id, common, node, render, moneyamount=1):
        self.id = id
        self.common = common
        self.node = node
        self.message = None
        self.moneyamount = moneyamount
        self.object=Actor("models/object", {'rotate' : 'models/object-rotate'})
        self.object.setScale(0.20)
        self.object.setZ(1.5)
        self.object.reparentTo(render)
        self.object.loop("rotate")
        #Get last position of monster
        (x,y,z) = self.node.getPos()
        self.object.setPos((x,y,z+0.5))
        base.enableParticles()
        #Load particles
        self.pe = ParticleEffect()
        self.pe.loadConfig(Filename("vfx/object.ptf"))
        self.pe.start(parent=self.object, renderParent=self.object)
        self.ambientLight=AmbientLight('ambientLight')
        self.ambientLight.setColor(VBase4(.3, .3, .3, 1))
        self.ambientLightNode = render.attachNewNode(self.ambientLight)
        self.object.setLight(self.ambientLightNode)
        taskMgr.doMethodLater(.1, self.update,'random-object'+str(self.id))

    def showLabel(self, message):
        text = TextNode('onscreenmessage')
        text.setText(message)
        text.setFont(loader.loadFont('Bitter-Bold.otf'))
        self.message = aspect2d.attachNewNode(text)
        self.message.setScale(0.05)
        window = base.win.getProperties()
        windowX = window.getXSize()
        windowY = window.getYSize()
        self.message.setPos(-0.6,0,-0.8)

    def update(self, task):
        if self.object.getDistance(self.common['PC'].node)<1:
            notifysound = base.loader.loadSfx("sfx/effect-notify.wav")
            notifysound.play()
            self.object.hide()
            self.pe.disable()
            #The object can fully heal the player, give him money or give him an item
            n = random.randrange(100)
            if (n == 0):
                self.common['PC'].heal()
            elif (n < 5):
                shopitems = self.common['PC'].getShopItems()
                i = random.randrange(len(shopitems))
                self.showLabel("You received '" + shopitems[i]['name'] + "'")
                shopitems[i]['count'] += shopitems[i]['count'] + 1
                self.common['PC'].items.append(shopitems[i])
                self.common['PC'].showCurrentItem()
                taskMgr.doMethodLater(2, self.destroyTask,'show-message')
            else:
                self.common['PC'].addMoney(self.moneyamount)
            return task.done
        return task.again

    def destroyTask(self, task):
        self.destroy()
        return task.done

    def destroy(self):
        taskMgr.remove('random-object' + str(self.id))
        self.object.cleanup()
        self.object.removeNode()
        self.pe.removeNode()
        if self.message:
            self.message.removeNode()
        self.ambientLightNode.removeNode()

class Monster():
    def __init__(self, setup_data, common, start_pos=(0,0,0)):
        level=common['max_level']+1 # max_level is the current level starting from 0
        common['monsterList'].append(self)
        id=len(common['monsterList'])-1
        self.monsterList=common['monsterList']
        self.waypoints_data=common['waypoints_data']
        self.waypoints=common['waypoints']
        self.audio3d=common['audio3d']
        self.common=common

        #root node
        self.node=render.attachNewNode("monster")
        self.sound_node=None
        self.soundset=None

        self.actor=Actor(setup_data["model"],setup_data["anim"] )
        self.actor.setBlend(frameBlend = True)
        self.actor.reparentTo(self.node)
        self.actor.setScale(setup_data["scale"]*random.uniform(0.9, 1.1))
        self.actor.setH(setup_data["heading"])
        self.actor.setBin("opaque", 10)

        self.rootBone=self.actor.exposeJoint(None, 'modelRoot', setup_data["root_bone"])

        #sounds
        self.soundID=self.common['soundPool'].get_id()
        self.common['soundPool'].set_target(self.soundID, self.node)
        self.sound_names={"hit":setup_data["hit_sfx"],
                          "arrow_hit":setup_data["arrowhit_sfx"],
                          "attack":setup_data["attack_sfx"],
                          "die":setup_data["die_sfx"]}

        self.vfx=setup_data["hit_vfx"]

        self.stats={"speed":setup_data["speed"],
                    "hp":setup_data["hp"]*(level**0.15),
                    "armor":setup_data["armor"]*(level**0.2),
                    "dmg":setup_data["dmg"]*(level**0.8)
                    }
        if self.stats['hp']>500:
            self.stats['hp']=500
        self.maxHP=self.stats['hp']
        self.healthBar=DirectFrame(frameSize=(-0.05, 0.05, 0, 0.05),
                                    frameColor=(1, 0, 0, 1),
                                    frameTexture='icon/glass4.png',
                                    parent=self.node)
        self.healthBar.setTransparency(TransparencyAttrib.MDual)
        self.healthBar.setScale(10,1, 1)
        self.healthBar.setZ(2)
        self.healthBar.setBillboardPointEye() #Make it flat in front of the camera
        self.ambientLight=AmbientLight('ambientLight')
        self.ambientLight.setColor(VBase4(.3, .3, .3, 1))
        self.ambientLightNode = render.attachNewNode(self.ambientLight)
        self.healthBar.setLight(self.ambientLightNode)
        self.healthBar.hide()
        wp = base.win.getProperties()
        winX = wp.getXSize()
        winY = wp.getYSize()

        #self.HPring.setColorScale(0.0, 1.0, 0.0, 1.0)

        #gamestate variables
        self.attack_pattern=setup_data["attack_pattern"]
        self.damage=setup_data["dmg"]
        #self.HP=setup_data["hp"]
        self.state="STOP"
        self.id=id
        self.nextWaypoint=None
        self.canSeePC=False
        self.PCisInRange=False
        self.PC=common['PC']
        self.speed_mode=random.randrange(0+int(level),42+int(level), 7)/100.0
        self.totalSpeed=self.stats['speed']+self.speed_mode
        self.sparkSum=0
        self.lastMagmaDmg=0
        self.DOT=0
        self.arrows=set()
        self.isSolid=True
        self.traverser=CollisionTraverser("Trav"+str(self.id))
        #self.traverser.showCollisions(render)
        self.queue = CollisionHandlerQueue()

        #bit masks:
        # 1  visibility polygons & coll-rays
        # 2  walls & radar-ray
        # 3  spheres

        #collision ray for testing visibility polygons
        coll=self.node.attachNewNode(CollisionNode('collRay'))
        coll.node().addSolid(CollisionRay(0, 0, 2, 0,0,-180))
        coll.setTag("id", str(id))
        coll.node().setIntoCollideMask(BitMask32.allOff())
        coll.node().setFromCollideMask(BitMask32.bit(1))
        self.traverser.addCollider(coll, self.queue)

        #radar collision ray
        self.radar=self.node.attachNewNode(CollisionNode('radarRay'))
        self.radar.node().addSolid(CollisionRay(0, 0, 1, 0,90,0))
        self.radar.node().setIntoCollideMask(BitMask32.allOff())
        self.radar.node().setFromCollideMask(BitMask32.bit(2))
        self.radar.setTag("radar", str(id))
        #self.radar.show()
        self.traverser.addCollider(self.radar, self.queue)

        #collision sphere
        self.coll_sphere=self.node.attachNewNode(CollisionNode('monsterSphere'))
        self.coll_sphere.node().addSolid(CollisionSphere(0, 0, 0.8, 0.6))
        self.coll_sphere.setTag("id", str(id))
        self.coll_sphere.node().setIntoCollideMask(BitMask32.bit(3))
        #self.coll_sphere.show()

        #other monster blocking
        self.coll_quad=loader.loadModel("models/plane")
        self.coll_quad.reparentTo(self.node)

        #self.coll_quad=render.attachNewNode(CollisionNode('monsterSphere'))
        #self.coll_quad.node().addSolid(CollisionPolygon(Point3(-.5, -.5, 2), Point3(-.5, .5, 0), Point3(.5, .5, 0), Point3(.5, .5, 2)))
        #self.coll_quad.setTag("id", str(id))
        #self.coll_quad.node().setIntoCollideMask(BitMask32.bit(2))
        #self.coll_quad.reparentTo(self.node)
        #self.coll_quad.show()

        Sequence(Wait(random.uniform(.6, .8)), Func(self.restart)).start()
        self.node.setPos(render,start_pos)
        taskMgr.add(self.runAI, "AIfor"+str(self.id))
        taskMgr.doMethodLater(.6, self.runCollisions,'collFor'+str(self.id))
        taskMgr.doMethodLater(1.0, self.damageOverTime,'DOTfor'+str(self.id))

    def die(self, soundname):
        n = random.random()
        if n < self.common["random-objects-freq"]:
            id = len(self.common["random-objects"])
            object = RandomObject(id, self.common, self.node, render)
            self.common["random-objects"].append(object)
        self.actor.play("die")
        #self.common['soundPool'].play(self.soundID, self.sound_names["hit"])
        self.common['soundPool'].play(self.soundID, soundname)
        self.state="DIE"


    def damageOverTime(self, task):
        if self.state=="DIE":
            return task.done
        if self.DOT>0:
            self.doDamage(self.DOT)
            self.DOT=int((self.DOT*0.9)-1.0)
            if self.stats['hp']<1:
                self.die(self.sound_names["die"])
            vfx(self.node, texture=self.vfx,scale=.5, Z=1.0, depthTest=True, depthWrite=True).start(0.016, 24)
        return task.again

    def restart(self):
        self.state="SEEK"

    def check_stacking(self):
        for monster in self.monsterList:
            if monster and monster.id!=self.id :
                if self.node.getDistance(monster.node)< .8:
                    if monster.state!="STOP" and self.state=="SEEK":
                        if self.totalSpeed <= monster.totalSpeed:
                            self.state="STOP"
                            self.actor.stop()
                            Sequence(Wait(1.5), Func(self.restart)).start()
                            return True

    def hideHealthbarTask(self, task):
        self.healthBar.hide()

    def doDamage(self, damage, ignoreArmor=False):
        if self.state=="DIE":
            return
        if not ignoreArmor:
            damage-=self.stats['armor']
        if damage<1:
            damage=1
        #print damage
        self.stats['hp']-=damage
        self.healthBar.show()
        self.healthBar.setScale(10*self.stats['hp']/self.maxHP,1, 1)
        taskMgr.doMethodLater(7.0, self.hideHealthbarTask,'hideHealthbar')
        if self.stats['hp']<1:
            self.healthBar.hide()

    def attack(self, pattern):
        if self.state=="DIE":
            return
        if not self.PC.node:
            return
        if pattern:
            next=pattern.pop()
        else:
            self.state="SEEK"
            self.PCisInRange=False
            return
        if self.PC.node and self.node:
            range= self.node.getDistance(self.PC.node)
        else:
            return
        #print range
        if range<1.8:
            self.PC.hit(self.damage)
        Sequence(Wait(next), Func(self.attack, pattern)).start()

    def onHit(self, damage, sound="hit", weapon=None):
        if self.state=="DIE":
            return

        if weapon == "magma":
            damage=self.lastMagmaDmg
            self.common['soundPool'].play(self.soundID, "onFire")
            vfx(self.node, texture="vfx/small_flame.png",scale=.6, Z=.7, depthTest=False, depthWrite=False).start(0.016, stopAtFrame=24)
        elif weapon == "spark":
            self.common['soundPool'].play(self.soundID, "spark")
            short_vfx(self.node, texture="vfx/short_spark.png",scale=.5, Z=1.0, depthTest=True, depthWrite=True).start(0.03)
        else:
            vfx(self.node, texture=self.vfx,scale=.5, Z=1.0, depthTest=True, depthWrite=True).start(0.016)

        self.doDamage(damage)

        if self.stats['hp']<1:
            if sound:
                self.common['soundPool'].play(self.soundID, self.sound_names[sound])
            self.die(self.sound_names["die"])
        else:
            if sound:
                self.common['soundPool'].play(self.soundID, self.sound_names[sound])

    def findFirstWaypoint(self):
        min=100000
        nearest=None
        for waypoint in self.waypoints:
            dist=self.node.getDistance(waypoint)
            if dist<min:
                min=dist
                nearest=waypoint
        return nearest

    def runCollisions(self, task):
        if self.state=="DIE":
            return task.done
        if self.node.getDistance(self.PC.node) >50.0:
            self.nextWaypoint=None
            return task.again
        if self.check_stacking():
            return task.again
        self.radar.lookAt(self.PC.node)
        valid_waypoints=[]
        isFirstTest=True
        self.canSeePC=False
        self.traverser.traverse(render)
        self.queue.sortEntries()
        for entry in self.queue.getEntries():
            if entry.getFromNodePath().hasTag("id"): #it's the monsters collRay
                valid_waypoints.append(int(entry.getIntoNodePath().getTag("index"))) #visibility polygons
            elif entry.getFromNodePath().hasTag("radar"): #it's the radar-ray
                #print "radar hit", entry.getIntoNodePath()
                if isFirstTest:
                    isFirstTest=False
                    #print "first hit!"
                    #print "radar hit", entry.getIntoNodePath()
                    if entry.getIntoNodePath().hasTag("player"):
                        self.canSeePC=True
        '''distance={}
        for target in self.PC.myWaypoints:
            for waypoint in valid_waypoints:
                distance[target]=self.waypoints_data[target][waypoint]
                print(target, distance[target])
        if distance:
            self.nextWaypoint=self.waypoints[min(distance, key=distance.get)]
        #print self.canSeePC'''
        if not valid_waypoints:
            #self.nextWaypoint=self.findFirstWaypoint()
            print(self.id, ": I'm lost!")
            valid_waypoints=[self.findFirstWaypoint()]
            #return task.again
        if self.state=="STOP":
            self.nextWaypoint=self.waypoints[random.choice(valid_waypoints)]
            return task.again
        best_distance=9000000
        target_node=None
        for target in self.PC.myWaypoints:
            for valid in valid_waypoints:
                distance=self.waypoints_data[target][valid]
                #print "target->valid=",target, valid, distance
                if distance<best_distance:
                    best_distance=distance
                    target_node=valid
        if target_node:
            self.nextWaypoint=self.waypoints[target_node]
        else:
            #print "no target", valid_waypoints
            self.nextWaypoint=self.findFirstWaypoint()
            #self.waypoints[random.choice(valid_waypoints)]
            #print self.nextWaypoint
        return task.again

    def runAI(self, task):
        #print self.state
        if self.state=="DIE":
            self.coll_sphere.node().setIntoCollideMask(BitMask32.allOff())
            self.coll_quad.removeNode()
            #self.actor.play("die")
            self.common["kills"]-=1
            if self.common["kills"]==0:
                Interactive(self.common, data.items['key'], self.node.getPos(render))
            Sequence(Wait(2.0),LerpPosInterval(self.node, 2.0, VBase3(self.node.getX(),self.node.getY(),self.node.getZ()-5)),Func(self.destroy)).start()
            return task.done
        elif self.state=="STOP":
            target=self.nextWaypoint
            if not target:
                return task.again
            self.node.headsUp(target)
            if self.node.getDistance(target)>0.3:
               self.node.setY(self.node, self.totalSpeed*globalClock.getDt())
               if(self.actor.getCurrentAnim()!="walk"):
                   self.actor.loop("walk")
            return task.again
        elif self.state=="ATTACK":
            self.node.headsUp(self.PC.node)
            if(self.actor.getCurrentAnim()!="attack"):
                self.actor.play("attack")
                #Sequence(Wait(self.attack_pattern[-1]+self.speed_mode), Func(self.attack, list(self.attack_pattern))).start()
                Sequence(Wait(self.attack_pattern[-1]), Func(self.attack, list(self.attack_pattern))).start()
            return task.again
        elif self.state=="SEEK":
            if self.PCisInRange:
                self.state="ATTACK"
                return task.again
            target=self.nextWaypoint
            if self.canSeePC and self.PC.HP>0:
                target=self.PC.node
                #print "target pc!"
            if not target:
                return task.again
            self.node.headsUp(target)
            if self.node.getDistance(target)>0.3:
               self.node.setY(self.node, self.totalSpeed*globalClock.getDt())
               if(self.actor.getCurrentAnim()!="walk"):
                   self.actor.loop("walk")
               return task.again
            else:
                #print "I'm stuck?"
                #print target
                #print self.canSeePC
                self.nextWaypoint=self.PC.node
                return task.again

    def destroy(self):
        #for sound in self.soundset:
        #    self.soundset[sound].stop()
        #print  "destroy:",
        #self.sound_node.reparentTo(render)
        #self.common['soundPool'].append([self.sound_node,self.soundset])
        self.common['soundPool'].set_free(self.soundID)
        #self.sounds=None
        #print  " sounds",
        self.arrows=None
        if self.actor:
            self.actor.cleanup()
            self.actor.removeNode()
            #print  " actor",
        if taskMgr.hasTaskNamed("hideHealthbar"):
            taskMgr.remove("hideHealthbar")
        if taskMgr.hasTaskNamed("AIfor"+str(self.id)):
            taskMgr.remove("AIfor"+str(self.id))
            #print  " AI",
        if taskMgr.hasTaskNamed('collFor'+str(self.id)):
            taskMgr.remove('collFor'+str(self.id))
            #print  " collision",
        if taskMgr.hasTaskNamed('DOTfor'+str(self.id)):
            taskMgr.remove('DOTfor'+str(self.id))
        if self.node:
            self.node.removeNode()
            #print  " node",
        self.monsterList[self.id]=None
        self.traverser=None
        self.queue=None
        self.healthBar.removeNode()
        self.ambientLightNode.removeNode()
        #base.sfxManagerList[0].update()
        #print  " list, ALL DONE!"
        #print self.common['monsterList']


class Spawner():
    '''Spawns Monsters'''
    def  __init__(self, common,tick=7.13):
        self.status="STOP"
        self.common=common
        taskMgr.doMethodLater(tick, self.update,'spawnerTask')

    def start(self, monster_type, level=0.5, monster_limit=3):
        if 'PC' in self.common:
            self.PC=self.common['PC']
            self.status="GO"
        else:
            self.PC=None
            self.status="WAIT_FOR_PC"
        self.spawnpoints=self.common['spawnpoints']
        self.monsterList=self.common['monsterList']
        self.monster_limit=monster_limit
        self.monster_type=monster_type
        self.level=level
        self.last_spawnpoint=None

    def stop(self):
        self.status="STOP"

    def update(self, task):
        if self.status=="WAIT_FOR_PC":
            if 'PC' in self.common:
                self.PC=self.common['PC']
                self.status="GO"
            else:
                return task.again
        elif self.status=="STOP":
            return task.again
        num_monsters=0
        #print self.level, self.status
        for monster in self.monsterList:
            if monster:
                num_monsters+=1
        if num_monsters>=self.monster_limit:
            return task.again

        points_in_range=[]
        for spawnpoint in self.spawnpoints:
            distance=spawnpoint.getDistance(self.PC.node)
            if 40>distance>10:
                points_in_range.append(spawnpoint)

        if points_in_range:
            final_point=points_in_range.pop(random.randrange(len(points_in_range)-1))
            if final_point==self.last_spawnpoint:
                if len(points_in_range)>1:
                    final_point=points_in_range.pop(random.randrange(len(points_in_range)-1))
            self.last_spawnpoint=final_point
            #Monster(data.monsters[random.randrange(1,10)].copy(), self.common, self.level, final_point.getPos(render))
            #Monster(data.monsters[15].copy(), self.common, self.level, final_point.getPos(render))
            Monster(data.monsters[random.choice(self.monster_type)].copy(), self.common, final_point.getPos(render))
            #self.level+=0.1
            #print "spawn!"
        return task.again


class MusicPlayer():
    def __init__(self, common):
        self.common=common
        self.musicList=[base.loader.loadMusic("music/LuridDeliusion.ogg"),
                        base.loader.loadMusic("music/Defying.ogg"),
                        base.loader.loadMusic("music/Descent.ogg"),
                        base.loader.loadMusic("music/HeroicDemise.ogg"),
                        base.loader.loadMusic("music/HeroicDemiseNoChoir.ogg"),
                        base.loader.loadMusic("music/Wasteland.ogg"),
                        base.loader.loadMusic("music/WastelandNoChoir.ogg")]
        self.volume=base.musicManager.getVolume()
        self.track=0
        self.nextTrack=1
        self.shuffle=False
        self.seq=None
        self.isLoop=True

    def setLoop(self, loop=True):
        if loop:
            self.isLoop=True
            self.loop(self.track)
        else:
            self.isLoop=False
            if self.seq:
                self.seq.pause()
                self.seq=None
            self.playAll()

    def setShuffle(self):
        if self.shuffle:
            self.shuffle=False
        else:
            self.shuffle=True
            self.playAll()
    def FF(self):
        if self.isLoop:
            if self.shuffle:
                self.loop(random.randrange(len(self.musicList)-1)+1)
            else:
                self.loop(self.track+1)
        else:
            if self.seq:
                self.seq.pause()
                self.seq=None
            self.playAll()

    def REW(self):
        if self.isLoop:
            if self.shuffle:
                self.loop(random.randrange(len(self.musicList)-1)+1)
            else:
                if self.track!=1:
                    self.loop(self.track-1)
                else:
                    self.loop(len(self.musicList)-1 )
        else:
            if self.seq:
                self.seq.pause()
                self.seq=None
            self.playAll(-1)

    def setVolume(self, volume):
        base.musicManager.setVolume(volume*0.01)
        self.volume=volume*0.01

    def playAll(self, skip=1):
        if self.shuffle:
            #self.nextTrack=random.choice(self.musicList[1:])
            self.nextTrack=random.randrange(len(self.musicList)-1)+1
        else:
            self.nextTrack=skip+self.track
            if self.nextTrack>=len(self.musicList):
                self.nextTrack=1
            if self.nextTrack==0:
                self.nextTrack=len(self.musicList)-1
        #print "playing:", self.track, self.nextTrack
        self.musicList[self.nextTrack].setLoop(False)
        time=self.musicList[self.nextTrack].length()
        #print time
        self.seq=Sequence(LerpFunc(base.musicManager.setVolume,fromData=self.volume,toData=0.0,duration=1.0),
                        Wait(1.0),
                        Func(self.musicList[self.track].stop),
                        Func(self.musicList[self.nextTrack].play),
                        LerpFunc(base.musicManager.setVolume,fromData=0.0,toData=self.volume,duration=1.0),
                        Wait(time-2.0),
                        Func(self.playAll))
        self.seq.start()
        self.track=self.nextTrack

    def loop(self, track=0, fadeIn=False):
        if fadeIn:
            base.musicManager.setVolume(0)
            LerpFunc(base.musicManager.setVolume,fromData=0.0,toData=self.volume,duration=5.0).start()

        if self.musicList[self.track].status() == self.musicList[self.track].PLAYING:
            self.musicList[self.track].stop()
        if track>=len(self.musicList):
                track=1
        self.musicList[track].setLoop(True)
        self.musicList[track].play()
        self.track=track

from boss import *
class LevelLoader():
    '''Loads new levels and unloads old ones'''
    def __init__(self, common):
        self.common=common

    def unload(self, stop_spawner=False):
        #unload previous map
        if 'map' in self.common:
            if self.common['map']:
                self.common['map'].removeNode()
        if 'map_black' in self.common:
            if self.common['map_black']:
                self.common['map_black'].removeNode()
        if 'map_walls' in self.common:
            if self.common['map_walls']:
                self.common['map_walls'].removeNode()
        if 'map_floor' in self.common:
            if self.common['map_floor']:
                self.common['map_floor'].removeNode()
        if 'white' in self.common:
            if self.common['white']:
                self.common['white'].removeNode()

        #remove monsters
        if 'monsterList' in self.common:
            for monster in self.common['monsterList']:
                if monster:
                    monster.destroy()
        self.common['monsterList']=[]
        #remove interactive
        if 'interactiveList' in self.common:
            for object in self.common['interactiveList']:
                if object:
                    object.destroy()
        self.common['interactiveList']=[]
        #remove objects
        if 'random-objects' in self.common:
            for object in self.common["random-objects"]:
                if object:
                    object.destroy()
        self.common["random-objects"] = []
        #remove music
        #self.music=[]
        #if self.common['music'].status() == self.common['music'].PLAYING:
        #    self.common['music'].stop()
        #self.common['music'].pause()
        #self.common['music']=Sequence()

        #stop spawner
        if stop_spawner:
            self.common['spawner'].stop()

        self.common["key_icon"].hide()

    def load_next(self):
        level=1+self.common["current_level"]
        self.load(level)

    def saveGame(self):
        #Save dict to file
        player=self.common['PC']
        data={"level" : self.common['max_level'], "money" : player.money, "character" : self.common['current_class'], "items" : player.items,
        "armor" : player.armor, "speed" : player.speed, "HP" : player.HP, "extra_attack" : player.attack_extra_damage}
        with open('save.dat', 'wb') as f:
            pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)

    def loadGame(self, PCLoad=False):
        if not Path("save.dat").exists():
            return False
        #load dict from file
        with open('save.dat', 'rb') as f:
            data = pickle.load(f)
        self.common['max_level'] = data["level"]
        self.common['current_class'] = data['character']
        if PCLoad:
            player=self.common['PC']
            player.money = data['money']
            player.moneyLabel.setText(str(player.money))
            player.items = data['items']
            player.showCurrentItem()
            player.armor = data['armor']
            player.speed = data['speed']
            player.HP = data['HP']
            player.updateHealthbar()

            player.attack_extra_damage = data['extra_attack']
        return True

    def load(self, level=0, PCLoad=True):
        map_name=data.levels[level]["map_name"]
        map_monsters=data.levels[level]["map_monsters"]
        self.common["current_level"]=level
        self.unload()
        #Save the game only if the player has reached a new level
        if level>self.common['max_level']:
            self.common['max_level']=level
            self.saveGame()

        #map
        self.common['map']=loader.loadModel(map_name)
        self.common['map'].reparentTo(render)

        self.common['map_black']=self.common['map'].find("**/black")
        self.common['map_walls']=self.common['map'].find("**/tile")
        self.common['map_floor']=self.common['map'].find("**/floor")

        self.common['white']=self.common['map'].find("**/white")
        if self.common['white']:
            self.common['white'].setLightOff()

        self.common['map_black'].reparentTo(render)
        self.common['map_walls'].reparentTo(render)
        self.common['map_floor'].reparentTo(render)

        self.common['map_black'].setTransparency(TransparencyAttrib.MBinary)
        self.common['map_walls'].setTransparency(TransparencyAttrib.MBinary)
        self.common['map_floor'].hide(BitMask32.bit(1))

        self.common['waypoints']=[]
        self.common['waypoints_data']=[]
        self.common["random-objects"] = []

        if 'PC' in self.common and PCLoad:
            self.common['PC'].onLevelLoad(self.common)
            pos=(data.levels[level]["enter"][0], data.levels[level]["enter"][1], data.levels[level]["enter"][2])
            self.common['PC'].node.setPos(pos)

        pos=(data.levels[level]["exit"][0], data.levels[level]["exit"][1], data.levels[level]["exit"][2])
        Interactive(self.common, data.items['exit'],pos)

        self.common["kills"]= data.levels[level]["kills_for_key"]

        #waypoints
        i=0
        while True:
            node=self.common['map'].find("**/WP"+str(i))
            if not node.isEmpty():
                self.common['waypoints'].append(node)
                self.common['waypoints_data'].append(json.loads(node.getTag("path"))[::-1])#data is in reverse order... but why?
                i+=1
            else:
                break

        #spawnpoints
        self.common['spawnpoints']=[]
        for spawnpoint in self.common['map'].findAllMatches("**/spawnpoint"):
            self.common['spawnpoints'].append(spawnpoint)

        #interactive
        #for active in self.common['map'].findAllMatches("**/interactive"):
        #    active_data=json.loads(active.getTag("proto"))
        #    Interactive(self.common, active.getTag("proto"), active.getPos(render))

        #music
        if not 'PC' in self.common:
            self.common['music'].loop(1, fadeIn=True)
        #self.common['music'].setShuffle()
        #self.common['music']=base.loadMusic("music/"+data.levels[level]["music"])
        #self.common['music'].setLoop(True)
        #default_volume=base.musicManager.getVolume()
        #base.musicManager.setVolume(0)
        #LerpFunc(self.pump_volume,fromData=0.0,toData=default_volume,duration=5.0).start()
        #self.common['music'].play()

        #spawner
        self.common['spawner'].start( data.levels[level]["map_monsters"], 1.0, data.levels[level]["num_monsters"])

        #soft particles
        base.enableParticles()
        pe = ParticleEffect()
        pe.loadConfig(Filename("vfx/softparticles.ptf"))
        pe.start(parent=base.render2d, renderParent=base.render2d)

        if map_name == "models/level_a1.bam":
            self.boss = Boss2(self.common, pos=(-7.39251, -19.2672, 1))
        elif map_name == "models/level_a5.bam":
            self.boss = Boss1(self.common, pos=(28.8778, 46.8372, 0))
