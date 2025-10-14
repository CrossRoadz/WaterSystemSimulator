from enum import Enum
from random import randrange
import pygame
from os import path, makedirs
pygame.font.init()


#types of classes
class GraphicTypes(Enum):
	Tank = "Tank"
	Pump = "Pump"
	Well = "Well"
	Sink = "Sink"
	Relay = "Relay"
	Float = "Float"
	Wire = "Wire"
	Box = "Box"
	Valve = "Valve"
	Particle = "Particle"

#main class
class System():
	ZIG = False
	PARTICLES = False
	VISUAL_SCALE = 1
	TEXT_GAP = 10 * VISUAL_SCALE
	TICK_RATE = 60
	#time sclae of 1 = 3600x speed
	TimeScale = 1/TICK_RATE*2
	FontSizeLarge = int(20 * VISUAL_SCALE)
	FontSizeSmall = int(15 * VISUAL_SCALE)
	TextFontLarge = pygame.font.SysFont("arialblack", FontSizeLarge)
	TextFontSmall = pygame.font.SysFont("arial", FontSizeSmall)
	HELP_HINT = TextFontLarge.render("Press H for help", True, (100,100,100))
	HELP_IMAGES = [TextFontLarge.render("Hold Left-Click to drag Component", True, (100,100,100)),
		TextFontLarge.render("Right-Click to add 10% fill to tank", True, (100,100,100)),
		TextFontLarge.render("Middile-Click to remove 10% fill", True, (100,100,100)),
		TextFontLarge.render("Scroll to change sim speed", True, (100,100,100)),
		TextFontLarge.render("P pauses", True, (100,100,100)),
		TextFontLarge.render("Ctrl + S Saves Current Positions", True, (100,100,100))
		]
	HELP_IMAGE_XGAP = 0
	for image in HELP_IMAGES:
		HELP_IMAGE_XGAP = max(HELP_IMAGE_XGAP, image.get_width())

	def __init__(self, bounds, title: str = "No Title"):
		self.Bounds = bounds
		self.title = title
		self.Dir = path.join(path.dirname(__file__), f"data/{title}")
		self.Tanks = []
		self.Pumps = []
		self.Wells = []
		self.Sinks = []
		self.Relays = []
		self.Floats = []
		self.Wires = []
		self.Boxes = []
		self.Valves = []
		self.AllObjects = []
		self.TimeRunning = 0
		self.MinutesPassed = 0
		self.ShowHelp = False
		self.FirstRun = True
		self.updateTimeImage()		

	def updateTimeImage(self):
		#bottom text
		self.imagePos = (10, self.Bounds[1] - System.FontSizeLarge - 10)
		timeFactor = System.TimeScale * System.TICK_RATE
		if self.MinutesPassed <= 300:
			RealTimePassed = f"{self.MinutesPassed:.1f}mins"
		elif self.MinutesPassed <= 3600:
			RealTimePassed = f"{self.MinutesPassed / 60:.1f}hours"
		else:
			RealTimePassed = f"{self.MinutesPassed / 3600:.1f}days"


		self.TimeImage = System.TextFontLarge.render(f"{self.TimeRunning}t, {RealTimePassed}, {1/(timeFactor):.2f}s passes for each min (x{timeFactor * System.TICK_RATE:.1f} Speed)", True, (0,0,0))

	def SavePositions(self):
		#saves positions (ctrl+s),stored in Positions.txt under here/data/title
		if not path.exists(self.Dir):
			makedirs(self.Dir)
			print("Made folder", self.Dir)

		with open(path.join(self.Dir, "Positions.txt"), 'w') as f:
			for obj in self.AllObjects:
				f.write(f"{obj}\n")
			print("Saved")

	def LoadPositions(self):
		#loads object positions from Positions.txt under here/data/title
		posDir = path.join(self.Dir, "Positions.txt")
		if not path.exists(posDir):
			print("No Position File found")
			return

		objs = list(self.AllObjects)
		with open(posDir, 'r') as f:
			for line in f:
				x, y, label, d = line.split(';')
				for obj in objs:
					if obj.Label == label:
						obj.X = int(x)
						obj.Y = int(y)
						objs.pop(objs.index(obj))
						continue

	def Add(self, obj):
		#add object to system
		if isinstance(obj, Well):
			self.Wells.append(obj)
		elif isinstance(obj, Pump):
			self.Pumps.append(obj)
		elif isinstance(obj, Sink):
			self.Sinks.append(obj)
		elif isinstance(obj, Relay):
			self.Relays.append(obj)
		elif isinstance(obj, FloatSwitch):
			self.Floats.append(obj)
		elif isinstance(obj, Wire):
			self.Wires.append(obj)
		elif isinstance(obj, Box):
			pass
		elif isinstance(obj, Valve):
			self.Valves.append(obj)
		elif isinstance(obj, Tank):
			self.Tanks.append(obj)
		else:
			print("Invalid Add type")
			return

		self.AllObjects.append(obj)

	def MakePump(self, sourceLabel, endLabel, flowRate, myLabel = ""):
		#make pump in refernce to its input/output tanks
		source = self.FindWithLabel(sourceLabel)
		end = self.FindWithLabel(endLabel)
		if System.ZIG:
			x = (source.X + end.X)//2
			y = (source.Y + end.Y)//2
		else:
			x = (source.OutputPoint[0] + end.InputPoint[0])//2
			y = (source.OutputPoint[1] + end.InputPoint[1])//2
		if myLabel == "":
			myLabel = sourceLabel + " to " + endLabel
		self.Add(Pump(x, y, myLabel, flowRate, source, end))

	def MakeValve(self, pumpLabel: str, label: str, endSide: bool = True, distance = 0.5):
		#Make a valve for a pump, placed along its pipes
		pump = self.FindWithLabel(pumpLabel)
		x,y = pump.X, pump.Y
		self.Add(Valve(pump, label, endSide, distance))

	def MakeRelay(self, contolledObejectLabel, mylabel, num: int = 0, manualSwitch: bool = False):
		"""make relay in reference to controlable object
		increment num for each new relay on the same object"""
		obj = self.FindWithLabel(contolledObejectLabel)
		obj.Enabled = False
		relay = Relay(obj.X, obj.Y, mylabel, obj, num, manualSwitch)
		self.Add(relay)
		return relay

	def MakeFloat(self, monitoredTankLabel, mylabel, Threshold, Amplitude, NO = True):
		#make float switch in refernce to a tank
		obj = self.FindWithLabel(monitoredTankLabel)
		floatswitch = FloatSwitch(obj.X, obj.Y, mylabel, obj, ToggleFunc(Threshold, Amplitude, NO))
		self.Add(floatswitch)
		return floatswitch


	def GetUnderPos(self, pos):
		#return first found object under mouse postion
		for obj in self.AllObjects:
			if obj.Rect.collidepoint(pos):
				return obj
		return None 


	def FindWithLabel(self, label: str, instance = None):
		"""find object with a certain label
		NO LABEL SHOULD BE EQUAL
		optional type argument for faster search"""
		if instance is FloatSwitch:
			searchlist = self.Floats
		elif instance is Tank:
			searchlist = self.Tanks
		elif instance is Relay:
			searchlist = self.Relays
		elif instance is Wire:
			searchlist = self.Wires
		else:
			searchlist = self.AllObjects

		for obj in searchlist:
			if obj.Label == label:
				return obj
		print("No matching Object to find with label:", label)
		return None

	def SetTankFill(self, tankLabel: str, fill: float):
		#set inital tank fill in unit volume (not %)
		tank = self.FindWithLabel(tankLabel)
		tank.Fill = min(tank.Size, fill)

	def MouseTankFill(self, obj, add = True):
		#adjust fill by 10% with mouse interaction
		if not isinstance(obj, Tank): return
		if add:
			print(f"Adding {obj.Size/10:.1f}gal Water to",obj.Label)
			obj.Fill += obj.Size/10
			obj.Fill = min(obj.Size, obj.Fill)
			return
		
		print(f"Removing {obj.Size/10:.1f}gal Water from",obj.Label)
		obj.Fill -= obj.Size/10
		obj.Fill = max(0, obj.Fill)


	def Draw(self, wn):
		#draw all graphics
		for obj in self.AllObjects:
			obj.Draw(wn)
		wn.blit(System.HELP_HINT, (self.imagePos[0] + self.TimeImage.get_width() + System.TEXT_GAP, self.imagePos[1]))
		wn.blit(self.TimeImage, self.imagePos)

		if self.ShowHelp:
			tg = System.TEXT_GAP
			x = self.Bounds[0] - System.HELP_IMAGE_XGAP - tg
			y = tg//2
			h = len(System.HELP_IMAGES) * (System.FontSizeLarge + tg//2) + 2*tg
			pygame.draw.rect(wn, (100,100,100), (x - tg, y - tg//2, System.HELP_IMAGE_XGAP + 2*tg, h), width = 5)
			for image in System.HELP_IMAGES:
				wn.blit(image, (x, y))
				y += System.FontSizeLarge



	def Update(self, UpdatePos: bool):
		#adVance sim
		self.TimeRunning += 1
		self.MinutesPassed += System.TimeScale
		self.updateTimeImage()
		#print(self.TimeRunning)

		#change grpahical position
		if UpdatePos or self.FirstRun:
			self.FirstRun = False
			for obj in self.AllObjects:
				obj.Update()

		#simulation system
		for well in self.Wells:
			well.Generate()

		for sink in self.Sinks:
			sink.Consume()
			sink.Randomize()

		for floatswitch in self.Floats:
			floatswitch.Evaluate()

		for relay in self.Relays:
			relay.Triggers(self)
			relay.CheckTriggers()

		for valve in self.Valves:
			valve.LimitPumpFlow()

		for pump in self.Pumps:
			pump.PumpWater()

		for tanks in (self.Tanks, self.Sinks, self.Wells):
			for tank in tanks:
				tank.GetChange()
				for particle in tank.Particles:
					particle.Update()




class GraphicObject():
	#object that will be drawn
	grey = (125,125,125)

	def __init__(self, x: int, y: int, label: str, kind):
		self.X, self.Y = x,y
		self.Label = label.replace(';', '') #removes any ;
		self.Kind = kind
		self.Width = 50
		self.Height = 50

		if kind in (GraphicTypes.Tank, GraphicTypes.Sink, GraphicTypes.Well):
			self.ImageLabel = System.TextFontLarge.render(self.Label, True, (0,0,0))
		elif kind in (GraphicTypes.Pump, GraphicTypes.Valve):
			self.ImageLabel = System.TextFontSmall.render(self.Label, True, (100,100,100))

	def __str__(self):
		return f"{self.X};{self.Y};{self.Label};{self.Kind}"

	def Draw(self, wn):
		#drawn graphic based on .Kind
		

		if self.Kind in (GraphicTypes.Tank, GraphicTypes.Well, GraphicTypes.Sink):
			
			wn.blit(self.ImageLabel, (self.X, self.Y - System.FontSizeLarge - System.TEXT_GAP))

			WaterLevel = int(self.Height * (self.Fill / self.Size))
			pygame.draw.rect(wn, (150,150,255), (self.X, self.Y+(self.Height - WaterLevel), self.Width, WaterLevel))
			pygame.draw.rect(wn, (0,0,0), (self.X, self.Y, self.Width, self.Height), width = 3)

			for particle in self.Particles:
				particle.Draw(wn)
			

		if self.Kind in (GraphicTypes.Sink, GraphicTypes.Well):
			wn.blit(self.RateImage, (self.X, self.Y + System.TEXT_GAP//2 + self.Height))
		elif self.Kind == GraphicTypes.Tank:
			wn.blit(self.FillImage, (self.X, self.Y + System.TEXT_GAP//2 + self.Height))

	def Update(self):
		#update positions
		self.Rect = pygame.Rect(self.X, self.Y, self.Width, self.Height)





class Tank(GraphicObject):
	#object with water volume
	def __init__(self, x, y, label, size = 1000, host = None):
		#pass .Kind to parent
		if host is None:
			super(Tank, self).__init__(x, y, label, GraphicTypes.Tank)
		else:
			super(Tank, self).__init__(x, y, label, host)
		#scale 2d volume from 3d volume
		self.Width = int(max((1000 * (size/1000) ** 0.33)//5, 60) * System.VISUAL_SCALE)
		self.Height = int(self.Width // 2 * System.VISUAL_SCALE)
		self.Rect = pygame.Rect(x,y,self.Width,self.Height)

		self._Size = size #readonly
		self.Fill = size/2 #amount of unit volume filled
		self.dV = 0 #change in volume
		self.LastFill = self.Fill #for dV
		#for pipes
		self.InputPoint = (self.X, self.Y)
		self.OutputPoint = (self.X + self.Width, self.Y + self.Height)
		#for small text
		self.FillImage = System.TextFontSmall.render(f"{int(self.Fill)}gal, 0gal/min", True, (0,0,0))
		pnum = self.Width // 10
		if not System.PARTICLES: pnum = 0
		self.Particles = [WaterParticle(self) for i in range(pnum)]

	@property
	def Size(self):
		return self._Size

	def GetChange(self):
		#change in volume (dV)
		self.dV = (self.Fill - self.LastFill) / System.TimeScale
		self.FillImage = System.TextFontSmall.render(f"{int(self.Fill)}gal, {self.dV:.1f}gal/min", True, (0,0,0))
		self.LastFill = self.Fill

	def Update(self):
		#position
		self.Rect = pygame.Rect(self.X, self.Y, self.Width, self.Height)
		self.InputPoint = (self.X, self.Y)
		self.OutputPoint = (self.X + self.Width, self.Y + self.Height)
		

class Pump(GraphicObject):
	#pushes water between tanks if enabled
	def __init__(self, x, y, label, flowRate, source, end):
		super(Pump, self).__init__(x, y, label, GraphicTypes.Pump)
		self.Source = source
		self.End = end
		self._MaxFlowRate = flowRate		
		self.FlowRate = flowRate
		self.Enabled = True
		self.Radius = 25 * System.VISUAL_SCALE
		self.Rect = pygame.Rect(x - self.Radius,y - self.Radius,self.Radius*2 ,self.Radius*2)
		self.Damage = 0
		self.Health = 100

	@property
	def MaxFlowRate(self):
		return self._MaxFlowRate

	def PumpWater(self):
		if (not self.Enabled): return


		flow = self.FlowRate * System.TimeScale * (self.Health / (self.Health + self.Damage))
		self.Source.Fill -= flow

		#prevent negative fill
		if (self.Source.Fill < 0):
			flow += self.Source.Fill
			self.Source.Fill = 0
			self.Damage += 1
		self.End.Fill += flow

		#prevent overfill
		overfill = self.End.Size - self.End.Fill
		if overfill < 0:
			self.End.Fill += overfill
			self.Source.Fill -= overfill
			self.Damage += 1

	def Update(self):
		self.Rect = pygame.Rect(self.X - self.Radius,self.Y - self.Radius,self.Radius*2 ,self.Radius*2)
	def Draw(self, wn):
		wn.blit(self.ImageLabel, (self.X - self.ImageLabel.get_width()//2, self.Y - System.TEXT_GAP - System.FontSizeSmall - self.Width//2))
		pygame.draw.circle(wn, GraphicObject.grey, self.Source.OutputPoint, 5)
		pygame.draw.circle(wn, GraphicObject.grey, self.End.InputPoint, 5)
		pygame.draw.circle(wn, GraphicObject.grey, (self.X, self.Y), 5)
		pygame.draw.line(wn, GraphicObject.grey, (self.X, self.Y), self.Source.OutputPoint, width = 4)
		pygame.draw.line(wn, GraphicObject.grey, (self.X, self.Y), self.End.InputPoint, width = 4)
		if self.Damage:
			colour = (200,0,0)
		else:
			colour = (0,0,0)
		pygame.draw.circle(wn, colour, (self.X, self.Y), self.Radius, width = 3)


class Sink(Tank):
	#constant water drain
	def __init__(self, x, y, label, size, consumeRate):
		super(Sink, self).__init__(x, y, label, size, GraphicTypes.Sink)
		self.ConsumeRate = consumeRate
		self.ConsumeRates = [consumeRate*0.9,consumeRate*1.1]
		self.RateChangeChance = 100
		self.RateImage = System.TextFontSmall.render(f"-{self.ConsumeRate:.2f}gal/min", True, (0,0,0))
		self.NoWaterTime = 0

	def Consume(self):
		self.Fill -= self.ConsumeRate * System.TimeScale
		if self.Fill <= 0: 
			self.NoWaterTime += 1
		self.Fill = max(self.Fill,0)

	def Randomize(self):
		#sim random water usage
		if randrange(0, self.RateChangeChance) == 0:
			self.ConsumeRate = self.ConsumeRates[randrange(0, len(self.ConsumeRates)-1)]
			self.RateImage = System.TextFontSmall.render(f"-{self.ConsumeRate:.2f}gal/min", True, (0,0,0))

class Well(Tank):
	#water generator
	def __init__(self, x, y, label, size, generateRate):
		super(Well, self).__init__(x, y, label, size, GraphicTypes.Well)
		self.GenerateRate = generateRate
		self.Fill = self.Size *0.85

		self.RateImage = System.TextFontSmall.render(f"{generateRate:.2f}gal/min", True, (0,0,0))

	def Generate(self):
		self.Fill += self.GenerateRate * System.TimeScale
		self.Fill = min(self.Fill, self.Size)

class Relay(GraphicObject):
	"""logic controller / manual switch
	manual switches with num 0 will override any other relays
	increment num for each new relay on the same object"""
	def __init__(self, x, y, label, EnabledObject, num: int, manualSwitch: bool):
		self.Size = 21 * System.VISUAL_SCALE
		self.num = num + 1
		self.manualSwitch = manualSwitch
		super(Relay, self).__init__(x+self.Size*self.num +self.num, y+self.Size, label, GraphicTypes.Relay)		
		self.ContolledObject = EnabledObject
		self.Height = self.Size
		self.Width = self.Size
		self.Rect = pygame.Rect(x,y,self.Width,self.Height)

		self.ImageLabel = System.TextFontSmall.render(f"{"M" if manualSwitch else "A"}", True, GraphicObject.grey)

		self.Triggered = False
		self.HIGHtrigger = None
		self.LOWtrigger = None
		self.Clicked = False
		self.JustClicked = False

	def CheckTriggers(self):
		if self.manualSwitch: return
		self.ContolledObject.Enabled = self.Triggered

	def Triggers(self, System):
		#meant to be overrided, to control self.Triggered

		#manual switch doesn't need to be overridden
		if self.manualSwitch:
			self.Triggered = self.Clicked
			if self.Clicked:
				self.ContolledObject.Enabled = True
			elif self.num == 1:
				self.ContolledObject.Enabled = False


	def Update(self):
		self.Rect = pygame.Rect(self.X, self.Y, self.Size, self.Size)
		self.X = self.ContolledObject.X + self.Size*self.num +self.num
		self.Y = self.ContolledObject.Y + self.Size

	def Draw(self, wn):
		wn.blit(self.ImageLabel, (self.X + self.Width//2 - self.ImageLabel.get_width()//2, self.Y + self.Width//2 + System.TEXT_GAP))
		pygame.draw.rect(wn, (0,0,0), (self.X, self.Y, self.Width, self.Height), width = 2)
		if self.Triggered:
			colour = (0,255,0)
		else:
			colour = (255,0,0)
		pygame.draw.circle(wn, colour, (self.X+self.Width//2, self.Y+self.Width//2), self.Width//3)
		if self.manualSwitch:
			pygame.draw.line(wn, (0,0,0), (self.X+self.Width//2,self.Y+2), (self.X+self.Width//2, self.Y+self.Width-2))


class FloatSwitch(GraphicObject):
	#based logic to give states to relays
	def __init__(self, x, y, label, monitoredTank, toggle):
		x = int(monitoredTank.X + monitoredTank.Width)
		y = int(monitoredTank.Y + monitoredTank.Height * (1-toggle.Threshold))
		super(FloatSwitch, self).__init__(x, y, label, GraphicTypes.Float)
		self.Radius = 7 * System.VISUAL_SCALE
		self.Rect = pygame.Rect(x - self.Radius,y - self.Radius,self.Radius*2 ,self.Radius*2)

		self.MonitoredTank = monitoredTank
		self.Toggle = toggle
		self.Active = False
	def Evaluate(self):
		self.Active = self.Toggle.Evaluate(self.MonitoredTank.Fill/self.MonitoredTank.Size)
	def Update(self):
		self.Rect = pygame.Rect(self.X - self.Radius,self.Y - self.Radius,self.Radius*2 ,self.Radius*2)
		self.X = int(self.MonitoredTank.X + self.MonitoredTank.Width)
		self.Y = int(self.MonitoredTank.Y + self.MonitoredTank.Height * (1-self.Toggle.Threshold))
	def Draw(self, wn):
		if self.Active: colour = (0,200,0)
		else: colour = (200,0,0)
		pygame.draw.circle(wn, colour, (self.X, self.Y), self.Radius)

class Wire(GraphicObject):
	def __init__(self, x, y, label, source, end):
		super(Wire, self).__init__(x, y, label, GraphicTypes.Wire)

class Box(GraphicObject):
	#grpahic box for visual organization or extra information
	def __init__(self, x, y, w, h, label):
		super(Box, self).__init__(x, y, label, GraphicTypes.Box)
		self.ImageLabel = System.TextFontLarge.render(label, True, (0,0,0))
		self.Rect = pygame.Rect(x,y,w,h)
		self.Width = w
		self.Height = h
	def Draw(self, wn):
		wn.blit(self.ImageLabel, (self.X,self.Y-System.FontSizeLarge-System.TEXT_GAP))
		pygame.draw.rect(wn, (0,0,0), (self.Rect), width = 1)

class Valve(GraphicObject):
	#valve that can stop a pump from pumping water
	def __init__(self, impeededPump, label, endSide: bool, distance):
		self.endSide = endSide
		self.Pump = impeededPump
		self.distance = min(max(0.05,distance), 0.95)
		self.Radius = 13

		self.Update()
		super(Valve, self).__init__(self.X, self.Y, label, GraphicTypes.Valve)
		self.Enabled = True
		self.Rect = pygame.Rect(self.X - self.Radius,self.Y - self.Radius,self.Radius*2 ,self.Radius*2)

		
	def Update(self):
		#update postion, places valve somewhere on the pump's pipes based on % distance and end/source pipe
		point = self.Pump.End.InputPoint if self.endSide else self.Pump.Source.OutputPoint
		if self.Pump.X < point[0]:
			startpoint =  self.Pump.X, self.Pump.Y
			endpoint = point
		else:
			startpoint = point
			endpoint = self.Pump.X, self.Pump.Y	

		#get slope
		x2, y2 = endpoint
		x1, y1 = startpoint
		length = abs(x1 - x2) * self.distance
		slope = -(y2 - y1) / (x2 - x1)

		self.X = int(length) + x1
		self.Y = int(y1 - length * slope) 
		self.Rect = pygame.Rect(self.X - self.Radius,self.Y - self.Radius,self.Radius*2 ,self.Radius*2)


	def LimitPumpFlow(self):
		if self.Enabled:
			self.Pump.FlowRate = self.Pump.MaxFlowRate
		else:
			self.Pump.FlowRate = 0

	def Draw(self, wn):
		colour = (0,255,0) if self.Enabled else (255,0,0)
		wn.blit(self.ImageLabel, (self.X - self.ImageLabel.get_width()//2, self.Rect.y - System.TEXT_GAP - System.FontSizeSmall))
		pygame.draw.circle(wn, colour, (self.X, self.Y), self.Radius)
		pygame.draw.circle(wn, (0,0,0), (self.X, self.Y), self.Radius, 2)

class WaterParticle(GraphicObject):
	Particles = 0
	def __init__ (self, tank):
		WaterParticle.Particles += 1
		self.Tank = tank
		self.Active = True
		x, y = tank.X, tank.Y
		super(WaterParticle, self).__init__(x, y, "", GraphicTypes.Particle)

		self.Radius = 9 #partilce size
		self.decayChance = 15 #1/chance to deactivated per tick once flow stop
		self.maxSpd = 2 #max downward spd of partilce
		self.startingV = -2.5 #starting upward spd
		self.lifeSpanRange = (20,35) #randrange lifespan
		self.g = 0.3 #force of gravity
		self.colour = WaterParticle.getColour() #random very light blue colour

		self.LifeSpan = CappedNumber(randrange(0,10), randrange(*self.lifeSpanRange))
		self.vy = self.startingV

	@staticmethod
	def getColour():
		brigthness = randrange(215,235)
		return (brigthness, brigthness, 255)
	def Update(self):
		greatFlow = int(abs(self.Tank.dV)) > 0 # enough flow to trigger particles, >=1gal/min
		if greatFlow:
			self.Active = True
		elif self.Active and not randrange(0,self.decayChance):
			self.Active = False
			self.LifeSpan = CappedNumber(0, randrange(*self.lifeSpanRange))


		if self.LifeSpan.isLess():
			self.vy = min(self.vy + self.g, self.maxSpd)
			self.Y = min(self.Y + int(self.vy), self.Tank.Y + self.Tank.Height - self.Radius)
			self.LifeSpan.value += 1
		elif not self.LifeSpan.isLess() and self.Active:
			self.vy = self.startingV
			self.colour = WaterParticle.getColour()
			self.LifeSpan = CappedNumber(0, randrange(*self.lifeSpanRange))
			wl = int(self.Tank.Height * (self.Tank.Fill / self.Tank.Size) )
			self.X = self.Tank.X + randrange(self.Radius, self.Tank.Width - self.Radius)
			self.Y = self.Tank.Y - wl + self.Tank.Height - 5 + randrange(0, self.Radius)

	def Draw(self, wn):
		if not self.Active: return
		pygame.draw.circle(wn, self.colour, (self.X, self.Y), 9)
		pygame.draw.circle(wn, (150,150,150), (self.X, self.Y), 9, width = 1)



class ToggleFunc:
	#switch with hysteresis (deadband) from +/- Amplitude of threshold
	#all in %
	def __init__(self, Threshold, Amplitude, GreaterThan = True):
		self.Threshold = Threshold
		self.ThresholdTest = Threshold + Amplitude
		self.Amplitude = Amplitude
		self.Active = False
		self.GreaterThan = GreaterThan
	def Evaluate(self, Test):
		# greatan than: threshold < test
		if self.GreaterThan:
			if self.ThresholdTest < Test and not self.Active:
				self.ThresholdTest = self.Threshold - self.Amplitude
				self.Active = True
			elif self.ThresholdTest > Test and self.Active:
				self.ThresholdTest = self.Threshold + self.Amplitude
				self.Active = False
		else:
			if self.ThresholdTest > Test and not self.Active:
				self.ThresholdTest = self.Threshold + self.Amplitude
				self.Active = True
			elif self.ThresholdTest < Test and self.Active:
				self.ThresholdTest = self.Threshold - self.Amplitude
				self.Active = False
		return self.Active

class CappedNumber():
	def __init__ (self, currentValue, maxValue):
		self.value = currentValue
		self._max = maxValue

	@property
	def max(self):
		return self._max

	def isLess(self):
		return self.value < self._max



if __name__ == "__main__":
	num = .4
	tf = ToggleFunc(0.5,0.04, False)

	for i in range(100):
		num+=0.01
		tf.Evaluate(num)
		print(tf.Active, num)

		if i >= 50:
			num-=0.02



	pygame.font.quit()