from Simulate import Simulate
from WaterSystemClasses import *


def main():
	"""Define a water system.
	volume in gals, flowrate in gals/minute"""
	#create base system (window size, title)
	System.PARTICLES = True
	WS = System((1500, 720), "Example")

	#start by adding tanks, wells, sinks (x, y, label, capacity, generate/consume rate)
	#positions can be moved in gui
	WS.Add(Tank(300, 500,"Raw Water", 1500))
	WS.Add(Tank(825, 500,"Clean Water", 4500))
	WS.Add(Tank(700, 50,"Water Tower", 2000))
	WS.Add(Sink(1250, 250, "Hill Sink", 250, 1))
	WS.Add(Sink(1350, 600, "Valley Sink", 200, 0.75))
	WS.Add(Well(50,300, "Wells", 300, 2))

	#next add pumps, then valves (source, end, flowrate, label)
	WS.MakePump("Wells", "Raw Water", 15, "RW Pump")
	WS.MakePump("Raw Water", "Clean Water", 5, "Treatment Pump")
	WS.MakePump("Clean Water", "Water Tower", 20, "Tower Pump")
	WS.MakePump("Clean Water", "Valley Sink", 20, "Valley Sink Pump")
	WS.MakePump("Water Tower", "Hill Sink", 20, "Hill Sink Pump")

	#add valves to pump (pump label, label, endSide = True, distance % = 0.5)
	WS.MakeValve("Treatment Pump", "Treatment Valve", False)

	#add relays to pumps and valves (controlled object label, label, num=0, isManual=False)
	WellPR = WS.MakeRelay("RW Pump", "Well Pump Relay")
	TreatPR = WS.MakeRelay("Treatment Pump", "Treating Pump Relay")
	TowerPR = WS.MakeRelay("Tower Pump", "Tower Pump Relay")
	HillSPR = WS.MakeRelay("Hill Sink Pump", "Hill Sink Relay")
	ValleySPR = WS.MakeRelay("Valley Sink Pump", "Valley Sink Relay")
	WS.MakeRelay("Tower Pump", "Tower Pump Relay manual", 1, True) #manual Switch
	WS.MakeRelay("Treatment Valve", "TV Relay manual", 0, True) #manual Switch

	#add indicators (x, y, label, (colourOff, colourOn) = (darkred, red))
	SinksEmpty = WS.Add(Indicator(40,40,"Sinks Empty"))
	PumpsDamaged = WS.Add(Indicator(140,40,"Pumps Damaged"))

	#add floats to tanks (tank label,label, trigger threshold %, amplitude %, normally open)
	WS.MakeFloat("Wells", "WELL HIGH", 0.5, 0.25)
	WS.MakeFloat("Raw Water", "RW HIGH", 0.92, 0.04)
	WS.MakeFloat("Raw Water", "RW LOW", 0.12, 0.04, False)
	WS.MakeFloat("Clean Water", "CW HIGH", 0.92, 0.04)
	WS.MakeFloat("Clean Water", "CW LOW", 0.12, 0.04, False)
	WS.MakeFloat("Clean Water", "CW MID", 0.5, 0.04)
	WS.MakeFloat("Water Tower", "TW HIGH", 0.92, 0.04)
	WS.MakeFloat("Water Tower", "TW LOW", 0.12, 0.04, False)
	WS.MakeFloat("Hill Sink", "HS LOW", 0.5, 0.3, False)
	WS.MakeFloat("Valley Sink", "VS LOW", 0.5, 0.3, False)

	#last for gui, add any boxes (x, y, w, h, label)
	WS.Add(Box(205,375,90,120, "RW Sediment Filters"))
	WS.Add(Box(550,450,200,200, "DW Treatment (1µm, Cl, UV)"))
	WS.Add(Box(885,285,120,150, "High Pressure"))

	#add float logic
	#most logic consists of 'if source not empty and end not full'
	WellPR.wlf = WS.FindWithLabel("WELL HIGH", FloatSwitch)
	WellPR.rwhf = WS.FindWithLabel("RW HIGH", FloatSwitch)
	def WellPR_Trigger(self, System):
		if self.wlf.Active and not self.rwhf.Active:
			self.Triggered = True
		else:
			self.Triggered = False
	WellPR.Triggers = WellPR_Trigger.__get__(WellPR, Relay)

	TreatPR.rwlf = WS.FindWithLabel("RW LOW", FloatSwitch)
	TreatPR.cwhf = WS.FindWithLabel("CW HIGH", FloatSwitch)
	def TreatPR_Trigger(self, System):
		if not self.rwlf.Active and not self.cwhf.Active:
			self.Triggered = True
		else:
			self.Triggered = False
	TreatPR.Triggers = TreatPR_Trigger.__get__(TreatPR, Relay)
		 
	TowerPR.cwmf = WS.FindWithLabel("CW MID", FloatSwitch)
	TowerPR.twhf = WS.FindWithLabel("TW HIGH", FloatSwitch)
	def TowerPR_Trigger(self, System):
		if self.cwmf.Active and not self.twhf.Active:
			self.Triggered = True
		else:
			self.Triggered = False
	TowerPR.Triggers = TowerPR_Trigger.__get__(TowerPR, Relay)

	HillSPR.twlf = WS.FindWithLabel("TW LOW", FloatSwitch)
	HillSPR.hslf = WS.FindWithLabel("HS LOW", FloatSwitch)
	def HillSPR_Trigger(self, System):
		if not self.twlf.Active and self.hslf.Active:
			self.Triggered = True
		else:
			self.Triggered = False
	HillSPR.Triggers = HillSPR_Trigger.__get__(HillSPR, Relay)


	ValleySPR.cwlf = WS.FindWithLabel("CW LOW", FloatSwitch)
	ValleySPR.vslf = WS.FindWithLabel("VS LOW", FloatSwitch)
	def ValleySPR_Trigger(self, System):
		if not self.cwlf.Active and self.vslf.Active:
			self.Triggered = True
		else:
			self.Triggered = False
	ValleySPR.Triggers = ValleySPR_Trigger.__get__(ValleySPR, Relay)

	#add indicator conditions
	SinksEmpty.Sinks = WS.Sinks
	def CheckCondition(self, system)-> bool:
		for sink in self.Sinks:
			if sink.Fill <= 0:
				return True
		return False
	SinksEmpty.CheckCondition = CheckCondition.__get__(SinksEmpty, Indicator)

	PumpsDamaged.Pumps = WS.Pumps
	def CheckCondition(self, system)-> bool:
		for pump in self.Pumps:
			if pump.Damage > 0:
				return True
		return False
	PumpsDamaged.CheckCondition = CheckCondition.__get__(PumpsDamaged, Indicator)



	#set inital conditions
	WS.SetTankFill("Clean Water", 3000)

	#load saved positions
	WS.LoadPositions()
	#start simulation
	#WS.MakeHistoricDataTemplate(False)
	Simulate(WS)
	


if __name__ == "__main__":
	main()
	