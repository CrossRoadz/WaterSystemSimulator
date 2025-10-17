from enum import Enum
from random import randrange
import pygame
import json
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
	Indicator = "Indicator"

def MakeDir(Dir):
	if not path.exists(Dir):
		makedirs(Dir)
		print("Made folder", Dir)
		return True
	return False

def Average(numList):
	#returns mean
	return sum(numList) / len(numList)

def Variance(numList, average = 0):
	#return variance
	if not average:
		average = Average(numList)
	var = 0
	for num in numList:
		var += (num - average) ** 2
	return var

def MinsToDHM(minutes)->str:
	#return time string
	days = int(minutes) // 1440
	hours = int(minutes % 1440) // 60
	mins = (minutes % 60)
	return f"@ {days}D {hours}h {mins:.1f}m"


#main class
class System():
	ZIG = False
	PARTICLES = False
	VISUAL_SCALE = 1
	TEXT_GAP = 10 * VISUAL_SCALE
	TICK_RATE = 60
	V_UNIT = 'gal'
	T_UNIT = 'min'
	F_UNIT = f"{V_UNIT}/{T_UNIT}"
	#time sclae of 1 = 3600x speed
	TimeScale = 1/TICK_RATE*2 #1s == 2m pass
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
	OverSpeedWarningSent = False
	done = False # will stop all sims if True

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
		self.Indicators = []
		self.AllObjects = []
		self.TimeRunning = 0
		self.MinutesPassed = 0
		self.ShowHelp = False
		self.FirstRun = True
		self.updateTimeImage()
		MakeDir(self.Dir)

	def updateTimeImage(self):
		#bottom text
		self.imagePos = (10, self.Bounds[1] - System.FontSizeLarge - 10)
		timeFactor = System.TimeScale * System.TICK_RATE
		if self.MinutesPassed <= 300:
			RealTimePassed = f"{self.MinutesPassed:.1f}mins"
		elif self.MinutesPassed <= 3600:
			RealTimePassed = f"{self.MinutesPassed / 60:.1f}hours"
		else:
			RealTimePassed = f"{self.MinutesPassed / 1440:.1f}days"


		self.TimeImage = System.TextFontLarge.render(f"{self.TimeRunning}t, {RealTimePassed}, {1/(timeFactor):.2f}s passes for each min (x{timeFactor * System.TICK_RATE:.1f} Speed)", True, (0,0,0))

	def QuickSim(self):
		print("\nRuning longterm quick sim\n")
		totalWellProduction = 0
		totalSinkProduction = 0
		smallestAvgProduction = 0
		largestAvgConsumation = 0


		for well in self.Wells:
			totalWellProduction += Average(well.ProduceRates)
			smallestAvgProduction += min(well.ProduceRates) * well.interval

		for sink in self.Sinks:
			totalSinkProduction += Average(sink.ProduceRates)
			largestAvgConsumation += min(sink.ProduceRates) * sink.interval

		wellVariance = []
		for well in self.Wells:
			wellVariance.append(round(Variance(well.ProduceRates), 3))
		sinkVariance = []
		for sink in self.Sinks:
			sinkVariance.append(round(Variance(sink.ProduceRates), 3))
		wellDeviation = [round(var**0.5, 2) for var in wellVariance]
		sinkDeviation = [round(var**0.5, 2) for var in sinkVariance]

		stable = totalWellProduction + totalSinkProduction >= 0

		totalSystemStorage = 0
		for tank in self.Tanks + self.Sinks + self.Wells:
			totalSystemStorage += tank.Size

		if not stable:
			timeTilEmpty = totalSystemStorage/2 / (totalWellProduction + totalSinkProduction)
		else:
			timeTilEmpty = totalSystemStorage/2 / (smallestAvgProduction + largestAvgConsumation)
		

		print(f"is Water System Stable? (well >= sink): {stable}",
			  f"avg Well Production: {totalWellProduction:.3f}{System.F_UNIT}",
			  f"avg Sink Conumation: {totalSinkProduction:.3f}{System.F_UNIT}",
			  f"Well Variance: {wellVariance}",
			  f"Sink Variance: {sinkVariance}",
			  f"Well Deviation: {wellDeviation}",
			  f"Sink Deviation: {sinkDeviation}",
			  f"System Water Storage: {totalSystemStorage}{System.V_UNIT}",
			  sep = '\n')
		print("Greater Deviations can require more storage\n\nin Summary:\n")


		if not stable:
			print("System is NOT stable, sinkswill go empty")
			print(f"Estimated Time until sinks are empty: {MinsToDHM(-timeTilEmpty)}")
		else:
			print("System is Stable!")
			if timeTilEmpty < 0:
				print(f"During a worst case senario, sinks can become empty in: {MinsToDHM(-timeTilEmpty)}",
					"-More Storage recommended", sep='\n')
			else:
				print("Storage should buffer most worst case senarios!")



	def SavePositions(self):
		#saves positions (ctrl+s),stored in Positions.txt under here/data/title

		with open(path.join(self.Dir, "Positions.txt"), 'w') as f:
			for obj in self.AllObjects:
				f.write(f"{obj}\n")
			print("Saved positions")

	def writeHistoicData(self, mode):
		with open(path.join(self.Dir, "Historic Data.json"), mode) as f:
			data = []
			for sink in self.Sinks:
				data.append(sink.ToJson())
			for well in self.Wells:
				data.append(well.ToJson())
			f.write(json.dumps(data, indent=2, sort_keys=True))

	def MakeHistoricDataTemplate(self, YouAreDoneDesign: bool=False):
		if not YouAreDoneDesign: 
			print("Ensure you are done your design, this will override any manually imported data")
			return
		self.writeHistoicData('w')
		print("!Reset Historic Data!")

	def TryLoadHistoricData(self):
		try:
			self.writeHistoicData('x')
			print("Made Baseline Historic Data Template",
				" Call 'WS.MakeHistoricDataTemplate(True)' if you'd wish to reset template", sep="\n")
		except FileExistsError:
			print("Well and Sink historic data found")

		with open(path.join(self.Dir, "Historic Data.json"), 'r') as f:
			data = json.loads(f.read())
			for item in data:
				obj = self.FindWithLabel(item["Label"])
				if not obj:
					print("Label in historic json not found")
					continue
				obj.ProduceRates = item["ProduceRates"]
				obj.SetInterval(item["interval"])
				obj.isRandom = item["isRandom"]
				if obj.isRandom:
					obj.Randomize()
				else:
					obj.ProduceRate = obj.ProduceRates[0]
				obj.RateChange()
				obj.WillRepeat  = item["WillRepeat"]




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
		elif isinstance(obj, Indicator):
			self.Indicators.append(obj)
		elif isinstance(obj, Tank):
			self.Tanks.append(obj)
		else:
			print("Invalid Add type")
			return

		self.AllObjects.append(obj)
		return obj

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
			print(f"Adding {obj.Size/10:.1f}{System.V_UNIT} Water to",obj.Label)
			obj.Fill += obj.Size/10
			obj.Fill = min(obj.Size, obj.Fill)
			return
		
		print(f"Removing {obj.Size/10:.1f}{System.V_UNIT} Water from",obj.Label)
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
		for source in self.Wells + self.Sinks:
			source.Produce()
			source.Randomize()
			source.CheckNextRate(self.MinutesPassed)

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

		for indicator in self.Indicators:
			if indicator.CheckCondition(self):
				indicator.TimeStamp = self.MinutesPassed
				indicator.Enabled = True
			elif not indicator.StayOn:
				indicator.Enabled = False




class GraphicObject():
	#object that will be drawn
	grey = (125,125,125)
	dark_grey = (80,80,80)

	def __init__(self, x: int, y: int, label: str, kind):
		self.X, self.Y = x,y
		self.Label = label.replace(';', '') #removes any ;
		self.Kind = kind
		self.Width = 50
		self.Height = 50

		self.Damage = 0
		self.Health = 250
		self.DamageUnit = 1 / System.TimeScale
		self.DamageCap = 0

		if kind in (GraphicTypes.Tank, GraphicTypes.Sink, GraphicTypes.Well):
			self.ImageLabel = System.TextFontLarge.render(self.Label, True, (0,0,0))
		elif kind in (GraphicTypes.Pump, GraphicTypes.Valve, GraphicTypes.Indicator):
			self.ImageLabel = System.TextFontSmall.render(self.Label, True, GraphicObject.dark_grey)

	def __str__(self):
		return f"{self.X};{self.Y};{self.Label};{self.Kind}"

	@property
	def DamageScale(self):
		return self.Health / (self.Health + self.Damage)

	def DoDamage(self, amount = 0):
		#applies damage
		#if damage if over a cap, ignore
		if self.DamageCap and self.DamageCap < self.Damage:
			return
		#custom damage
		if amount:
			self.Damage += amount * System.TimeScale
			return

		self.Damage += self.DamageUnit * System.TimeScale

	def GetScaledChance(self, chance)->int:
		return int(chance / System.TICK_RATE * 2 / System.TimeScale) + 1


	def Draw(self, wn):
		#drawn graphic based on .Kind
		if self.Kind in (GraphicTypes.Tank, GraphicTypes.Well, GraphicTypes.Sink):
			
			wn.blit(self.ImageLabel, (self.X, self.Y - System.FontSizeLarge - System.TEXT_GAP))

			WaterLevel = int(self.Height * (self.Fill / self.Size))
			pygame.draw.rect(wn, (150,150,255), (self.X, self.Y+(self.Height - WaterLevel), self.Width, WaterLevel))
			colour = (0,0,0) if not self.Damage else (200,0,0)
			pygame.draw.rect(wn, colour, (self.X, self.Y, self.Width, self.Height), width = 3)

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
		self.FillImage = System.TextFontSmall.render(f"{int(self.Fill)}{System.V_UNIT}, 0{System.F_UNIT}", True, (0,0,0))
		
		pnum = self.Width // WaterParticle.Radius #adds particles bades on width
		if not System.PARTICLES: pnum = 0
		self.Particles = [WaterParticle(self) for i in range(pnum)]

	@property
	def Size(self):
		return self._Size

	def ClampFill(self):
		#ensure water doesnt over/under flow
		self.Fill = Clamp(self.Fill, self.Size)

	def GetChange(self):
		#change in volume (dV)
		self.dV = (self.Fill - self.LastFill) / System.TimeScale
		self.FillImage = System.TextFontSmall.render(f"{int(self.Fill)}{System.V_UNIT}, {self.dV:.1f}{System.F_UNIT}", True, (0,0,0))
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

	@property
	def MaxFlowRate(self):
		return self._MaxFlowRate

	def PumpWater(self):
		#pumps water from source tank to end tank
		if (not self.Enabled): return


		flow = self.FlowRate * System.TimeScale * self.DamageScale
		#if flow is too large, it will bypass floast and damage itself
		#this is a bug which I plan to fix
		if not System.OverSpeedWarningSent and flow / self.Source.Size > 0.1:
			print("Sim running over speed, pumps may damage themselves as a bug")
			System.OverSpeedWarningSent = True
		self.Source.Fill -= flow

		#prevent negative fill
		if (self.Source.Fill < 0):
			flow += self.Source.Fill
			self.Source.Fill = 0
			self.DoDamage()
		self.End.Fill += flow

		#prevent overfill
		overfill = self.End.Size - self.End.Fill
		if overfill < 0:
			self.End.Fill += overfill
			self.Source.Fill -= overfill
			self.DoDamage()

	def Update(self):
		self.Rect = pygame.Rect(self.X - self.Radius,self.Y - self.Radius,self.Radius*2 ,self.Radius*2)
	def Draw(self, wn):
		wn.blit(self.ImageLabel, (self.X - self.ImageLabel.get_width()//2, self.Y - System.TEXT_GAP - System.FontSizeSmall - self.Width//2))
		pygame.draw.circle(wn, GraphicObject.grey, self.Source.OutputPoint, 5)
		pygame.draw.circle(wn, GraphicObject.grey, self.End.InputPoint, 5)
		pygame.draw.circle(wn, GraphicObject.grey, (self.X, self.Y), 5)
		pygame.draw.line(wn, GraphicObject.grey, (self.X, self.Y), self.Source.OutputPoint, width = 4)
		pygame.draw.line(wn, GraphicObject.grey, (self.X, self.Y), self.End.InputPoint, width = 4)
		
		colour = (200,0,0) if self.Damage else (0,0,0)
		pygame.draw.circle(wn, colour, (self.X, self.Y), self.Radius, width = 3)

class Source(Tank):
	#generates or consumes water

	def __init__(self, x, y, label, size, kind, rate, interval=120, isRandom = True):
		super(Source, self).__init__(x, y, label, size, kind)
		self.ProduceRate = rate
		self.EffectiveRate = rate
		self.ProduceRates = [rate]
		self.SetInterval(interval)
		self.isRandom = isRandom
		self.index = 0
		self.WillRepeat = True
		self.HealChance = 30
		self.RateChange()

	def SetInterval(self, value):
		#flow rate change intervals
		self.interval = value
		self.intervalInc = value
	
	def RateChange(self):
		#update the flow rate text
		self.RateImage = System.TextFontSmall.render(f"{self.EffectiveRate:.2f}{System.F_UNIT}", True, (0,0,0))

	def TryHeal(self):
		#try to recover damage
		if self.Damage and not randrange(0, self.GetScaledChance(self.HealChance)):
			self.Damage -= self.DamageUnit * System.TimeScale
			self.Damage = max(self.Damage, 0)
			self.RateChange()

	def Produce(self):
		#should be overridden by child
		self.EffectiveRate = self.ProduceRate*self.DamageScale
		self.Fill += self.EffectiveRate * System.TimeScale
		if not 0 < self.Fill < self.Size:
			self.ClampFill()

	def Randomize(self):
		#pick new random rate
		if not self.isRandom: return
		#scales with sim speed, more likely at faster speeds
		if not randrange(0, self.GetScaledChance(self.interval)):
			self.ProduceRate = self.ProduceRates[randrange(0, len(self.ProduceRates))]
			self.RateChange()

	def CheckNextRate(self, minutesPassed):
		#if not random mode, increment through list of flow rates
		if self.isRandom: return

		if self.interval < minutesPassed:
			self.interval += self.intervalInc
			self.index += 1
			if self.index >= len(self.ProduceRates):
				self.index = 0
				#if not repeat the list, will stop simulation
				if not self.WillRepeat:
					System.done = True
			self.ProduceRate = self.ProduceRates[self.index]
			self.RateChange()


	def ToJson(self):
		#for use in file saving, returns dict for json
		return {"Label": self.Label,
				"Kind": self.Kind.value,
				"interval": self.interval,
				"isRandom": self.isRandom,
				"ProduceRates": self.ProduceRates,
				"WillRepeat": self.WillRepeat}


class Sink(Source):
	#constant water drain
	def __init__(self, x, y, label, size, consumeRate):
		rate = -abs(consumeRate)
		super(Sink, self).__init__(x, y, label, size, GraphicTypes.Sink, rate)
		self.ProduceRates = [0.9*rate, 1.1*rate]
		self.HealChance = 10
		self.DamageCap = self.Health * 3
	def Produce(self):
		#consume water from its own tank
		self.EffectiveRate = self.ProduceRate/self.DamageScale

		self.Fill += self.EffectiveRate * System.TimeScale
		self.ClampFill()

		#damage self if left empty
		#acts as if people will consume more water after losing water
		if self.Fill <= 0.01:
			self.DoDamage()
			self.RateChange()
		else:
			self.TryHeal()
		

class Well(Source):
	#water generator
	def __init__(self, x, y, label, size, generateRate):
		super(Well, self).__init__(x, y, label, size, GraphicTypes.Well, abs(generateRate))
		self.Fill = self.Size *0.85
		self.DamageUnit /= 2
		self.HealChance = 30
		self.DamageCap = self.Health * 6

	def Produce(self):
		#generate water to its own tank
		self.EffectiveRate = self.ProduceRate*self.DamageScale

		self.Fill += self.EffectiveRate * System.TimeScale
		self.ClampFill()

		percentFilled = self.Fill / self.Size
		if percentFilled < 0.1:
			self.DoDamage()
			self.RateChange()
		elif percentFilled < 0.2:
			self.DoDamage(self.DamageUnit/4)
			self.RateChange()
		else:
			self.TryHeal()

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

		self.ImageLabel = System.TextFontSmall.render("M" if manualSwitch else "A", True, GraphicObject.grey)

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

class Indicator(GraphicObject):
	def __init__ (self, x, y, label, colours = ((100,0,0), (255,0,00)), stayOn = True):
		super(Indicator, self).__init__(x, y, label, GraphicTypes.Indicator)
		self.ColourOff, self.ColourOn = colours
		self.Radius = 15
		self.StayOn = stayOn
		self.TimeStamp = 0
		self.TimeImage = None
		self.Enabled = False
		self.Update()

	def Update(self):
		self.Rect = pygame.Rect(self.X - self.Radius,self.Y - self.Radius,self.Radius*2 ,self.Radius*2)

	def CheckCondition(self, system):
		return False

	def Draw(self, wn):
		#show time when indicator condition was met
		if self.TimeImage:
			x_offset = self.X - self.TimeImage.get_width()//2 
			y_offset = self.Y - self.TimeImage.get_height() - self.Radius - System.TEXT_GAP
			wn.blit(self.TimeImage, (x_offset, y_offset))
		#render time image if not already made and if indicator will stay on
		elif not self.TimeImage and self.TimeStamp and self.StayOn:
			timeText = MinsToDHM(self.TimeStamp)
			self.TimeImage = System.TextFontSmall.render(timeText, True, GraphicObject.dark_grey)

		wn.blit(self.ImageLabel, (self.X - self.ImageLabel.get_width()//2, self.Y + self.Radius + System.TEXT_GAP))
		pygame.draw.rect(wn, (200,200,200), (self.X-3-self.Radius, self.Y-3-self.Radius, self.Radius*2+6, self.Radius*2+6))
		pygame.draw.rect(wn, (50,50,50), (self.X-3-self.Radius, self.Y-3-self.Radius, self.Radius*2+6, self.Radius*2+6), width = 2)
		colour = self.ColourOn if self.Enabled else self.ColourOff
		pygame.draw.circle(wn, colour, (self.X, self.Y), self.Radius)
		pygame.draw.circle(wn, (0,0,0), (self.X, self.Y), self.Radius, 2)
		pygame.draw.circle(wn, (50,50,50), (self.X, self.Y), self.Radius*2//3, 1)




class WaterParticle(GraphicObject):
	Particles = 0
	Radius = 9
	def __init__ (self, tank):
		WaterParticle.Particles += 1
		self.Tank = tank
		self.Active = True
		x, y = tank.X, tank.Y
		super(WaterParticle, self).__init__(x, y, "", GraphicTypes.Particle)

		self.Radius = WaterParticle.Radius #partilce size
		self.decayChance = 15 #1/chance to deactivated per tick once flow stop
		self.maxSpd = 2 #max downward spd of partilce
		self.startingV = -2.5 #starting upward spd
		self.lifeSpanRange = (20,35) #randrange lifespan
		self.g = 0.25 #force of gravity
		self.colour = WaterParticle.getColour() #random very light blue colour

		self.LifeSpan = CappedNumber(randrange(0,10), randrange(*self.lifeSpanRange))
		self.vy = self.startingV

	@staticmethod
	def getColour():
		brigthness = randrange(215,236)
		return (brigthness, brigthness, 255)
	def Update(self):
		greatFlow = int(abs(self.Tank.dV)) > 0 # enough flow to trigger particles, >=1gal/min
		#hide particle if low flowrate in tank
		if greatFlow:
			self.Active = True
		elif self.Active and not randrange(0,self.decayChance):
			self.Active = False
			self.LifeSpan = CappedNumber(0, randrange(*self.lifeSpanRange))

		#simulate gravity
		if self.LifeSpan.isLess():
			self.vy = min(self.vy + self.g, self.maxSpd)
			self.Y = min(self.Y + int(self.vy), self.Tank.Y + self.Tank.Height - self.Radius)
			self.LifeSpan.value += 1
		#reset
		elif not self.LifeSpan.isLess() and self.Active:
			self.vy = self.startingV
			self.colour = WaterParticle.getColour()
			self.LifeSpan = CappedNumber(0, randrange(*self.lifeSpanRange))
			wl = int(self.Tank.Height * (self.Tank.Fill / self.Tank.Size) )
			self.X = self.Tank.X + randrange(self.Radius, self.Tank.Width - self.Radius+1)
			self.Y = self.Tank.Y - wl + self.Tank.Height - 5 + randrange(0, self.Radius)

	def Draw(self, wn):
		if self.Active:	
			pygame.draw.circle(wn, self.colour, (self.X, self.Y), self.Radius)
			pygame.draw.circle(wn, (150,150,150), (self.X, self.Y), self.Radius, width = 1)



class ToggleFunc:
	#switch with hysteresis (deadband) from +/- Amplitude of threshold
	#all in %, GreaterThan also means normally open
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

def Clamp(value, max_value, min_value=0):
	return min(max(min_value, value),max_value)

if __name__ == "__main__":
	


	pygame.font.quit()