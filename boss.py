from panda3d.core import *
from direct.actor.Actor import Actor
from direct.interval.IntervalGlobal import *
from direct.showbase.DirectObject import DirectObject
from direct.gui.DirectGui import *
from panda3d.ai import *
from vfx import vfx
from vfx import short_vfx
import random


class Boss():
    def __init__(self, common):
        self.common = common
        common['monsterList'].append(self)
        id=len(common['monsterList'])-1
        self.id=id
        self.stats={"speed":9,
            "hp":300,
            "armor":3
            }
        self.totalSpeed=10
        self.sparkSum=0
        self.lastMagmaDmg=0
        self.DOT=0
        self.arrows=set()
        self.isSolid=True
        self.node=render.attachNewNode("monster")
        self.boss1=Actor("models/boss1-monster/monster", {"die":"models/boss1-monster/monster-die",
                                            "attack1":"models/boss1-monster/monster-doublepunch",
                                            "hit":"models/boss1-monster/monster-hit",
                                            "idle":"models/boss1-monster/monster-idle",
                                            "attack2":"models/boss1-monster/monster-kick",
                                            "run":"models/boss1-monster/monster-run",
                                            "scream":"models/boss1-monster/monster-scream",
                                            "walk":"models/boss1-monster/monster-walk",
                                            "rwalk":"models/boss1-monster/monster-walk-right",
                                            "lwalk":"models/boss1-monster/monster-walk-left"}) 
        self.boss1.setBlend(frameBlend = True)
        self.boss1.setPlayRate(0.8, "walk")
        self.boss1.reparentTo(self.node)
        self.boss1.setScale(1)
        #self.boss1.setH(180.0)       
        #self.boss1.setBin("opaque", 10)
        #tex = loader.loadTexture('models/boss1-monster/creature1Normal.png')
        #boss1.setTexture(tex, 1)
        #self.boss1.setColor(0.2, 0.0, 0.9, 0.5)
        self.node.setPos(render,(0,2,0))
        self.rootBone=self.boss1.exposeJoint(None, 'modelRoot', 'hips')

        self.maxHP=self.stats['hp']
        self.healthBar=DirectFrame(frameSize=(37, 0, 0, 6),
                                    frameColor=(1, 0, 0, 1),
                                    frameTexture='icon/glass4.png',
                                    parent=pixel2d)
        self.healthBar.setTransparency(TransparencyAttrib.MDual)
        self.healthBar.setScale(10,1, 1)
        #self.healthBar.reparentTo(self.node)
        wp = base.win.getProperties()
        winX = wp.getXSize()
        winY = wp.getYSize()
        self.healthBar.setPos(71-256+winX/2,0,34-winY)
        self.healthBar.hide()

        self.soundID=self.common['soundPool'].get_id()
        self.common['soundPool'].set_target(self.soundID, self.node)

        self.traverser=CollisionTraverser("BossTrav"+str(id))
        #self.traverser.showCollisions(render)
        self.queue = CollisionHandlerQueue()

        #radar collision ray
#        self.radar=self.node.attachNewNode(CollisionNode('radarRay'))
#        self.radar.node().addSolid(CollisionRay(0, 0, 1, 0, 90, 0))
#        self.radar.node().setIntoCollideMask(BitMask32.allOff())
#        self.radar.node().setFromCollideMask(BitMask32.bit(2))
#        self.radar.setTag("radar", str(id))
#        self.radar.show()
#        self.traverser.addCollider(self.radar, self.queue)

        self.coll_body=self.node.attachNewNode(CollisionNode('bossmonsterCollisionNode'))
        self.coll_body.node().addSolid(CollisionCapsule(0, 0, 0.3, 0, 0, 2, 0.6))
        self.coll_body.setTag("id", str(id))
        self.coll_body.node().setIntoCollideMask(BitMask32.bit(3))
        #self.coll_body.show()
        self.left_thumb=self.boss1.exposeJoint(None, 'modelRoot', 'L_thumb1')
        #self.right_foot = self.boss1.exposeJoint(None, "modelRoot", "R_foot")
        #self.coll_attack2=self.node.attachNewNode(CollisionNode('bossattack2CollisionNode'))
        #self.coll_attack2.node().addSolid(CollisionSphere(0, 0, 0, 0.2))
        ##self.coll_attack2.setTag("id", str(id))
        #self.coll_attack2.node().setIntoCollideMask(BitMask32.bit(3))
        #self.coll_attack2.show()

        #other monster blocking
        self.coll_quad=loader.loadModel("models/plane")
        self.coll_quad.reparentTo(self.node)
        self.state="IDLE"
        self.previous_state=self.state
        #self.PC = self.common['PC']
        #taskMgr.doMethodLater(.6, self.runCollisions,'collFor'+str(self.id))
        self.setAI()
        taskMgr.doMethodLater(1.0, self.damageOverTime,'DOTfor'+str(self.id))   
        #taskMgr.add(self.runAI, "BossAIfor"+str(id))

    def setAI(self):
        #Creating AI World
        self.AIworld = AIWorld(render)

        self.AIchar = AICharacter("pursuer",self.node, 200, 0.05, 5)
        self.AIworld.addAiChar(self.AIchar)
        self.AIbehaviors = self.AIchar.getAiBehaviors()
        
        self.AIbehaviors.pursue(self.common['PC'].node)
        # Obstacle avoidance (FIXME)
        #self.AIbehaviors.obstacleAvoidance(0.0001)
        #self.AIworld.addObstacle(self.common['map_walls'])
        #self.AIworld.addObstacle(self.common['map_black'])

        #AI World update
        taskMgr.add(self.runAI,"AIUpdate")

    def runAI(self, task):
        #print(self.stats['hp'])
        #(x,y,z) = self.right_foot.getPos()
        ## Our model is rotated of 180°, thus we need to move the collision sphere to the opposite directions
        #self.coll_attack2.setPos(-1*x, -1*y, z)
        target = self.common['PC'].node
        if self.state=="DIE":
            if(self.boss1.getCurrentAnim()!="die"):
                self.common['soundPool'].attachAndPlay(self.boss1, "creature_roar_01.ogg")
                self.boss1.play("die")
            #Check if we have finished the animation
            if (self.boss1.getCurrentFrame() < self.boss1.getNumFrames()-1):
                return task.again
            else:
                id = len(self.common["random-objects"])
                object = RandomObject(id, self.common, self.node, render)
                self.common["random-objects"].append(object)
                
                self.coll_body.node().setIntoCollideMask(BitMask32.allOff())
                self.coll_quad.removeNode()
                self.common["kills"]-=1
                if self.common["kills"]==0:
                    Interactive(self.common, data.items['key'], self.node.getPos(render))               
                Sequence(Wait(2.0),LerpPosInterval(self.node, 2.0, VBase3(self.node.getX(),self.node.getY(),self.node.getZ()-5)),Func(self.destroy)).start()
                return task.done

        if (self.state == "HIT") and (self.previous_state == "FOLLOWING"):
            if(self.boss1.getCurrentAnim()!="hit"):
                self.boss1.play("hit")
                self.common['soundPool'].attachAndPlay(self.boss1, "creature_roar_01.ogg")
            if (self.boss1.getCurrentFrame() == self.boss1.getNumFrames()-1):
                self.state = self.previous_state
            return task.again

        if self.state == "IDLE":
            if(self.boss1.getCurrentAnim()!="idle"):
                self.boss1.play("idle")

        if self.common['PC'].HP <= 0 or self.node.getDistance(target)>14:
            self.state="IDLE"
        else:
            if self.boss1.getAnimControl('scream').isPlaying():
                #we must wait until the animation is finished
                return task.again
            if (random.random() < 0.001):
                self.state="SCREAMING"
                if(self.boss1.getCurrentAnim()!="scream"):
                    self.boss1.play("scream")
                    self.common['soundPool'].attachAndPlay(self.boss1, "awake-the-beast.wav")
            else:
                if self.node.getDistance(target)>2:
                    #If the boss is idle or has finished to play an animation (e.g. an attack) he must pursue the player
                    if self.state == "IDLE" or self.boss1.getCurrentAnim() == None:
                        self.state="PURSUING"
                    if self.state == "PURSUING":
                        self.AIworld.update()
                        #self.node.setY(self.node, 1*globalClock.getDt())
                        if(self.boss1.getCurrentAnim()!="walk"):
                            self.common['soundPool'].attachAndPlay(self.boss1, "creature_slime_01-2.ogg", 0.7)
                            self.boss1.play("walk")
                else:
                    self.state="ATTACKING"
                    if(self.boss1.getCurrentAnim()!="attack2") and (self.boss1.getCurrentAnim()!="attack1"):
                        if (random.random() < 0.5):
                            self.boss1.play("attack2")
                            self.common['soundPool'].attachAndPlay(self.boss1, "Whoosh4.ogg")
                            self.boss1.attackdamage = 20
                        else:
                            self.boss1.play("attack1")
                            self.boss1.attackdamage = 30
                    # Inflict damage only when we played half of the animation (it should be the moment when the attack hits the player)
                    # This function could be called multiple times even if we are at the same frame (probably depends on the frame rate of the animation)
                    # Thus, we should also check if we are seeing the same previous hit (based on the last frame, it must not be the same)
                    elif (self.boss1.getCurrentFrame() == int(self.boss1.getNumFrames()/2)) and (self.boss1.getCurrentFrame() != self.boss1.lastFrame):
                        if (self.boss1.getCurrentAnim() == "attack1"):
                            #The sound must be played only when the boss hit the floor (it's in the mid of the animation)
                            self.common['soundPool'].attachAndPlay(self.boss1, "explodemini.wav")
                            # Get position of the joint respect to render (i.e. absolute position)
                            (x,y,_) = self.left_thumb.getPos(render)
                            vfx(None, texture='vfx/dust.png',scale=1, Z=0, depthTest=True, depthWrite=True,pos=(x,y,0)).start(0.016)
                        self.common['PC'].hit(self.boss1.attackdamage)
                    self.boss1.lastFrame = self.boss1.getCurrentFrame()
        self.previous_state = self.state
        return task.again

    def doDamage(self, damage, igoreArmor=False):
        if self.state=="DIE":
            return
        if not igoreArmor:
            damage-=self.stats['armor']
        if damage<1:
            damage=1
        #print damage
        self.stats['hp']-=damage
        self.healthBar.show()
        self.healthBar.setScale(10*self.stats['hp']/self.maxHP,1, 1)
        if self.stats['hp']<1:
            self.healthBar.hide()

    def die(self, soundname):
        #self.common['soundPool'].play(self.soundID, self.sound_names["hit"])
        #self.common['soundPool'].play(self.soundID, soundname)
        self.state="DIE"

    def onHit(self, damage, sound="hit"):
        if self.state=="DIE":
            return
        self.state="HIT"
        self.doDamage(damage)

        if self.stats['hp']<1:
            self.die("die")

    def damageOverTime(self, task):
        if self.state=="DIE":
            return task.done
        if self.DOT>0:
            self.doDamage(self.DOT)
            self.DOT=int((self.DOT*0.9)-1.0)
            vfx(self.node, texture='vfx/blood_dark.png',scale=.5, Z=1.0, depthTest=True, depthWrite=True).start(0.016)
        return task.again

    def destroy(self):
        self.arrows=None
        if self.boss1:
            self.boss1.cleanup()
            self.boss1.removeNode()
        if taskMgr.hasTaskNamed("BossAIfor"+str(self.id)):
            taskMgr.remove("BossAIfor"+str(self.id))
#        if taskMgr.hasTaskNamed('collFor'+str(self.id)):
#            taskMgr.remove('collFor'+str(self.id))
        if taskMgr.hasTaskNamed('DOTfor'+str(self.id)):
            taskMgr.remove('DOTfor'+str(self.id))
        if taskMgr.hasTaskNamed('AIUpdate'):
            taskMgr.remove('AIUpdate')
        if self.node:
            self.node.removeNode()
        self.common['monsterList'][self.id]=None
        self.traverser=None
        self.queue=None
        #self.common['traverser'].removeCollider(self.coll_sphere) 
        self.coll_body.removeNode()
        self.coll_quad.removeNode()
        self.healthBar.removeNode()
        #base.sfxManagerList[0].update()
        #print  " list, ALL DONE!"
        #print self.common['monsterList']
