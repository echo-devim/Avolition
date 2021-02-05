from panda3d.core import *
from direct.actor.Actor import Actor
from direct.interval.IntervalGlobal import *
from direct.showbase.DirectObject import DirectObject
from direct.gui.DirectGui import *
from panda3d.ai import *
from vfx import vfx
from vfx import short_vfx
import random
from engine import *


class Boss1():
    def __init__(self, common, pos=(0,0,0)):
        self.common = common
        common['monsterList'].append(self)
        id=len(common['monsterList'])-1
        self.id=id
        self.stats={"speed":9,
            "hp":500,
            "armor":3
            }
        self.totalSpeed=10
        self.sparkSum=0
        self.lastMagmaDmg=0
        self.DOT=0
        self.arrows=set()
        self.isSolid=True
        self.node=render.attachNewNode("monster")
        self.boss=Actor("models/boss1-monster/monster", {"die":"models/boss1-monster/monster-die",
                                            "attack1":"models/boss1-monster/monster-doublepunch",
                                            "hit":"models/boss1-monster/monster-hit",
                                            "idle":"models/boss1-monster/monster-idle",
                                            "attack2":"models/boss1-monster/monster-kick",
                                            "run":"models/boss1-monster/monster-run",
                                            "scream":"models/boss1-monster/monster-scream",
                                            "walk":"models/boss1-monster/monster-walk",
                                            "rwalk":"models/boss1-monster/monster-walk-right",
                                            "lwalk":"models/boss1-monster/monster-walk-left"})
        self.boss.setBlend(frameBlend = True)
        self.boss.setPlayRate(0.8, "walk")
        self.boss.reparentTo(self.node)
        self.boss.setScale(1)
        #self.boss.setH(180.0)
        #self.boss.setBin("opaque", 10)
        #tex = loader.loadTexture('models/boss1-monster/creature1Normal.png')
        #boss1.setTexture(tex, 1)
        #self.boss.setColor(0.2, 0.0, 0.9, 0.5)
        self.node.setPos(render,pos)
        self.rootBone=self.boss.exposeJoint(None, 'modelRoot', 'hips')

        self.maxHP=self.stats['hp']
        self.healthBar=DirectFrame(frameSize=(37, 0, 0, 6),
                                    frameColor=(0, 0, 1, 1),
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
        self.left_thumb=self.boss.exposeJoint(None, 'modelRoot', 'L_thumb1')
        #self.right_foot = self.boss.exposeJoint(None, "modelRoot", "R_foot")
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
        taskMgr.doMethodLater(1.0, self.setAI, 'setAITask')
        taskMgr.doMethodLater(1.0, self.damageOverTime,'DOTfor'+str(self.id))
        #taskMgr.add(self.runAI, "BossAIfor"+str(id))

    def setAI(self, task):
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
        return task.done

    def runAI(self, task):
        #print(self.stats['hp'])
        #(x,y,z) = self.right_foot.getPos()
        ## Our model is rotated of 180°, thus we need to move the collision sphere to the opposite directions
        #self.coll_attack2.setPos(-1*x, -1*y, z)
        target = self.common['PC'].node
        if self.state=="DIE":
            if(self.boss.getCurrentAnim()!="die"):
                self.common['soundPool'].attachAndPlay(self.boss, "creature_roar_01.ogg")
                self.boss.play("die")
            #Check if we have finished the animation
            if (self.boss.getCurrentFrame() < self.boss.getNumFrames()-1):
                return task.again
            else:
                id = len(self.common["random-objects"])
                object = RandomObject(id, self.common, self.node, render, moneyamount=5)
                self.common["random-objects"].append(object)
                Interactive(self.common, data.items['key'], self.node.getPos(render))
                self.coll_body.node().setIntoCollideMask(BitMask32.allOff())
                self.coll_quad.removeNode()
                Sequence(Wait(2.0),LerpPosInterval(self.node, 2.0, VBase3(self.node.getX(),self.node.getY(),self.node.getZ()-5)),Func(self.destroy)).start()
                return task.done

        if self.stats['hp'] < 50:
            self.AIchar.setMass(180)

        if (self.state == "HIT"):
            rn = 0.005
            if (type(self.common['PC']).__name__ == "Knight"):
                rn = 0.4
            if (random.random() < rn):
                if(self.boss.getCurrentAnim()!="hit"):
                    self.boss.play("hit")
                    self.common['soundPool'].attachAndPlay(self.boss, "creature_roar_01.ogg")
                    self.state = "PLAYINGHIT"

        if (self.state == "PLAYINGHIT"):
            if (self.boss.getCurrentFrame() == None) or (self.boss.getCurrentFrame() == self.boss.getNumFrames()-1):
                self.state = self.previous_state
            return task.again

        if self.state == "IDLE":
            if(self.boss.getCurrentAnim()!="idle"):
                self.boss.play("idle")

        if self.common['PC'].HP <= 0 or self.node.getDistance(target)>14:
            self.state="IDLE"
            self.common['spawner'].monster_limit = 4
        else:
            self.common['spawner'].monster_limit = 2
            if self.boss.getAnimControl('scream').isPlaying():
                #we must wait until the animation is finished
                return task.again
            if (random.random() < 0.001):
                self.state="SCREAMING"
                if(self.boss.getCurrentAnim()!="scream"):
                    self.boss.play("scream")
                    self.common['soundPool'].attachAndPlay(self.boss, "awake-the-beast.wav")
            else:
                if self.node.getDistance(target)>2:
                    #If the boss is idle or has finished to play an animation (e.g. an attack) he must pursue the player
                    if self.state == "IDLE" or self.boss.getCurrentAnim() == None:
                        self.state="PURSUING"
                    if self.state == "PURSUING":
                        self.AIworld.update()
                        #self.node.setY(self.node, 1*globalClock.getDt())
                        if(self.boss.getCurrentAnim()!="walk"):
                            self.common['soundPool'].attachAndPlay(self.boss, "creature_slime_01-2.ogg", 0.7)
                            self.boss.play("walk")
                else:
                    self.state="ATTACKING"
                    if(self.boss.getCurrentAnim()!="attack2") and (self.boss.getCurrentAnim()!="attack1"):
                        if (type(self.common['PC']).__name__ == "Knight") and (random.random() > 0.1):
                            self.state="IDLE"
                            self.previous_state = self.state
                            return task.again
                        if (random.random() < 0.5):
                            self.boss.play("attack2")
                            self.common['soundPool'].attachAndPlay(self.boss, "Whoosh4.ogg")
                            self.boss.attackdamage = 20
                        else:
                            self.boss.play("attack1")
                            self.boss.attackdamage = 30
                    # Inflict damage only when we played half of the animation (it should be the moment when the attack hits the player)
                    # This function could be called multiple times even if we are at the same frame (probably depends on the frame rate of the animation)
                    # Thus, we should also check if we are seeing the same previous hit (based on the last frame, it must not be the same)
                    elif (self.boss.getCurrentFrame() == int(self.boss.getNumFrames()/2)) and (self.boss.getCurrentFrame() != self.boss.lastFrame):
                        if (self.boss.getCurrentAnim() == "attack1"):
                            #The sound must be played only when the boss hit the floor (it's in the mid of the animation)
                            self.common['soundPool'].attachAndPlay(self.boss, "explodemini.wav")
                            # Get position of the joint respect to render (i.e. absolute position)
                            (x,y,_) = self.left_thumb.getPos(render)
                            vfx(None, texture='vfx/dust.png',scale=1, Z=0, depthTest=True, depthWrite=True,pos=(x,y,0)).start(0.016)
                        self.common['PC'].hit(self.boss.attackdamage)
                    self.boss.lastFrame = self.boss.getCurrentFrame()
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

    def onHit(self, damage, sound="hit", weapon=None):
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
        if self.boss:
            self.boss.cleanup()
            self.boss.removeNode()
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




class Boss2():
    def __init__(self, common, pos=(0,0,0)):
        self.common = common
        common['monsterList'].append(self)
        id=len(common['monsterList'])-1
        self.id=id
        self.stats={"speed":9,
            "hp":400,
            "armor":0
            }
        self.totalSpeed=1
        self.sparkSum=0
        self.lastMagmaDmg=0
        self.DOT=0
        self.arrows=set()
        self.isSolid=True
        #self.bullet.hide()
        self.node=render.attachNewNode("monster")
        self.boss=Actor("models/boss2/boss2.bam", {"die":"models/boss2/boss2_die.bam",
                                            "attack1":"models/boss2/boss2_attack1.bam",
                                            "hit":"models/boss2/boss2_hit.bam",
                                            "idle":"models/boss2/boss2_idle.bam",
                                            "attack2":"models/boss2/boss2_attack2.bam",
                                            "fly":"models/boss2/boss2_flyforward.bam"})
        self.boss.setBlend(frameBlend = True)
        self.boss.setPlayRate(2, "attack1")
        self.boss.reparentTo(self.node)
        self.boss.setScale(0.01,0.01,0.01)
        self.boss.setP(10)
        self.boss.setH(180)
        self.boss.setBin("opaque", 10)
        #tex = loader.loadTexture('models/boss1-monster/creature1Normal.png')
        #boss1.setTexture(tex, 1)
        #self.boss.setColor(0.2, 0.0, 0.9, 0.5)
        self.node.setPos(render,pos)
        self.rootBone=self.boss.exposeJoint(None, 'modelRoot', 'Hips')

        self.ambientLight=AmbientLight('ambientLight')
        self.ambientLight.setColor(VBase4(.7, .7, .7, 1))
        self.ambientLightNode = render.attachNewNode(self.ambientLight)
        self.boss.setLight(self.ambientLightNode)


        self.maxHP=self.stats['hp']
        self.healthBar=DirectFrame(frameSize=(37, 0, 0, 6),
                                    frameColor=(0, 0, 1, 1),
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
        self.waitfor = 0 # time to wait before to pursue the player
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
        self.coll_body.node().addSolid(CollisionCapsule(0, 0, 0.3, 0, 0.2, 1.5, 0.3))
        self.coll_body.setTag("id", str(id))
        self.coll_body.node().setIntoCollideMask(BitMask32.bit(3))
        #self.coll_body.show()
        #self.right_foot = self.boss.exposeJoint(None, "modelRoot", "R_foot")
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
        #taskMgr.doMethodLater(1.0, self.damageOverTime,'DOTfor'+str(self.id))
        self.boss.setTransparency(True)
        self.visible = True
        self.bullet=loader.loadModel("models/ball.egg")
        self.bullet.setScale(0.5)
        self.bullet.reparentTo(render)
        self.bullet.setPos(0,0,-5)
        mat = Material()
        mat.setShininess(0)
        mat.setAmbient((0.7, 0.1, 0, 0.8))
        self.ambientLightBullet=AmbientLight('ambientLight')
        self.ambientLightBullet.setColor(VBase4(.5, .5, .5, 1))
        self.ambientLightBulletNode = render.attachNewNode(self.ambientLightBullet)
        self.bullet.setLight(self.ambientLightBulletNode)
        self.bullet.setMaterial(mat)
        self.bullet.setBin("opaque", 10)
        self.bullet.hide()
        self.bullet_radius = 0
        # Our model is rotated of 180°, thus we need to move the collision sphere to the opposite directions
        #self.bullet.setPos(-1*x, -1*y, z)
        self.fog = Fog("Fog")
        self.fog.setColor(0.5, 0.5, 0.5)
        self.fog.setExpDensity(0.1)

#        self.node.setColorScale(1,1,1,1)
#        self.node.clearFog()

        #Sequence(Wait(2),LerpColorScaleInterval(self.node, 2.0, VBase4(1,1,1,0.1))).start()
        #Sequence(Wait(6),LerpColorScaleInterval(self.node, 2.0, VBase4(1,1,1,1))).start()
        #Sequence(Wait(10),LerpColorScaleInterval(self.node, 2.0, VBase4(1,1,1,0.1))).start()
        taskMgr.add(self.runAI, "BossAIfor"+str(id))

    def toggleVisibility(self):
        if (self.visible):
            #Sequence(Wait(0),LerpColorScaleInterval(self.node, 2.0, VBase4(1,1,1,0.1))).start()
            self.node.setFog(self.fog)
            self.node.setColorScale(1,1,1,0.1)
        else:
            #Sequence(Wait(0),LerpColorScaleInterval(self.node, 2.0, VBase4(1,1,1,1))).start()
            self.node.setColorScale(1,1,1,1)
            self.node.clearFog()
        self.visible = not self.visible


    def runAI(self, task):
        #print(self.stats['hp'])
        #(x,y,z) = self.right_foot.getPos()
        ## Our model is rotated of 180°, thus we need to move the collision sphere to the opposite directions
        #self.coll_attack2.setPos(-1*x, -1*y, z)
        target = self.common['PC'].node
        if self.state=="DIE":
            if(self.boss.getCurrentAnim()!="die"):
                self.common['soundPool'].attachAndPlay(self.boss, "argh-woman.ogg")
                self.boss.play("die")
                Sequence(Wait(0),LerpPosInterval(self.node, 0.4, VBase3(self.node.getX(),self.node.getY(),self.node.getZ()-1))).start()
            #Check if we have finished the animation
            if (self.boss.getCurrentFrame() < self.boss.getNumFrames()-1):
                return task.again
            else:
                id = len(self.common["random-objects"])
                object = RandomObject(id, self.common, self.node, render, moneyamount=5)
                self.common["random-objects"].append(object)

                self.coll_body.node().setIntoCollideMask(BitMask32.allOff())
                self.coll_quad.removeNode()
                Interactive(self.common, data.items['key'], self.node.getPos(render))
                Sequence(Wait(1.0),LerpPosInterval(self.node, 2.0, VBase3(self.node.getX(),self.node.getY(),self.node.getZ()-5)),Func(self.destroy)).start()
                return task.done

        if (self.state == "HIT") and (self.previous_state == "IDLE"):
            if(self.boss.getCurrentAnim()!="hit"):
                self.boss.play("hit")
                self.common['soundPool'].attachAndPlay(self.boss, "argh-woman.ogg")
            if (self.boss.getCurrentFrame() == self.boss.getNumFrames()-1):
                self.state = self.previous_state
            return task.again

        #Check if the player is colliding with the bullet
        if (self.bullet_radius > 0) and (self.bullet.getDistance(target)<1):
            self.boss.attackdamage = 10 * self.bullet_radius
            self.common['PC'].hit(self.boss.attackdamage)
            self.bullet_radius = 0

        if self.state == "IDLE":
            if(self.boss.getCurrentAnim()!="idle"):
                self.boss.play("idle")
            if (self.waitfor > 0):
                self.waitfor -= 1
                return task.again

        if self.common['PC'].HP <= 0 or self.node.getDistance(target)>25:
            self.state="IDLE"
            self.common['spawner'].monster_limit = 4
        else:
            self.common['spawner'].monster_limit = 2
            if (random.random() < 0.003) and (self.state == "PURSUING"):
                self.state="IDLE"
                self.waitfor = random.randrange(200)
                return task.again
            if (random.random() < 0.008) or (self.state == "ATTACKING"):
                self.state="ATTACKING"
                if(self.boss.getCurrentAnim()!="attack2") and (self.boss.getCurrentAnim()!="attack1"):
                    if (random.random() < 0.5):
                        self.boss.play("attack2")
                        self.common['soundPool'].attachAndPlay(self.boss, "beam-sound.wav", volume=3)
                        self.boss.attackdamage = 0
                    else:
                        self.boss.play("attack1")
                        self.boss.attackdamage = 0
                        (x,y,z)=self.node.getPos()
                        self.bullet.setPos(x,y,z+0.75)
                        self.bullet.show()
                        self.bullet_radius = random.randrange(2, 4)
                        Sequence(Wait(0),LerpScaleInterval(self.bullet, 1.0, VBase3(self.bullet_radius,self.bullet_radius,self.bullet_radius), VBase3(0.5,0.5,0.5))).start()
                        Sequence(Wait(0),LerpPosInterval(self.bullet, 4.0, VBase3(self.common['PC'].node.getPos()))).start()
                        #The sound must be played only when the boss hit the floor (it's in the mid of the animation)
                        self.common['soundPool'].attachAndPlay(self.boss, "energy1.wav", volume=3)
                        # Get position of the joint respect to render (i.e. absolute position)
                        #(x,y,_) = self.left_thumb.getPos(render)
                        #vfx(None, texture='vfx/dust.png',scale=1, Z=0, depthTest=True, depthWrite=True,pos=(x,y,0)).start(0.016)

                # Inflict damage only when we played half of the animation (it should be the moment when the attack hits the player)
                # This function could be called multiple times even if we are at the same frame (probably depends on the frame rate of the animation)
                # Thus, we should also check if we are seeing the same previous hit (based on the last frame, it must not be the same)
                elif (self.boss.getCurrentFrame() == int(self.boss.getNumFrames()/2)) and (self.boss.getCurrentFrame() != self.boss.lastFrame):
                    if (self.boss.getCurrentAnim() == "attack2"):
                        self.toggleVisibility()
                        if (self.visible == False):
                            self.stats['hp'] += 10
                            self.healthBar.setScale(10*self.stats['hp']/self.maxHP,1, 1)

                elif (self.boss.getCurrentFrame() == self.boss.getNumFrames()-1):
                    #When the animation is finished return to pursuing the player
                    self.state = "PURSUING"

                self.boss.lastFrame = self.boss.getCurrentFrame()
                return task.again

            self.state = "PURSUING"
            self.node.headsUp(target) #Look at the player
            if(self.boss.getCurrentAnim()!="fly"):
                self.boss.loop("fly")
            if self.node.getDistance(target)>5:
                self.node.setY(self.node, self.totalSpeed*globalClock.getDt())
            else:
                self.node.setX(self.node, self.totalSpeed*globalClock.getDt())

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

    def onHit(self, damage, sound="hit", weapon=None):
        if self.state=="DIE" or self.visible == False:
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
        if self.boss:
            self.boss.cleanup()
            self.boss.removeNode()
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
        self.ambientLightNode.removeNode()
        self.ambientLightBulletNode.removeNode()
        self.ambientLightBulletNode.removeNode()
        #base.sfxManagerList[0].update()
        #print  " list, ALL DONE!"
        #print self.common['monsterList']
