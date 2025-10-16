from Simulate import Simulate
from WaterSystemClasses import *


def main():
	"""Define a water system.
	volume in gals, flowrate in gals/minute"""
	System.PARTICLES = True
	System.ZIG = True
	WS = System((1150, 850), "Maple")
		
	WS.Add(Tank(500,100, "Raw Water", 1000))
	WS.Add(Well(50,150,"Well Cluster", 200, 0.25))
	WS.Add(Tank(50,600, "Distrubtion Water", 3000))
	WS.Add(Sink(700,600, "Sink", 150, -0.23))


	WS.SetTankFill("Distrubtion Water", 2300)
	#add pumps
	WS.MakePump("Well Cluster", "Raw Water", 10, "Well Pump")
	WS.MakePump("Raw Water", "Distrubtion Water", 10, "Treating Pump")
	WS.MakePump("Distrubtion Water", "Sink", 5, "DW Pump")

	WS.MakeValve("Treating Pump", "Treatment Valve", True, 0.75)
	#add relays
	WPR = WS.MakeRelay("Well Pump", "Well Pump Relay")
	TPR = WS.MakeRelay("Treating Pump", "Treating Pump Relay")
	DPR = WS.MakeRelay("DW Pump", "DW Pump Relay")
	TVR = WS.MakeRelay("Treatment Valve", "TV Relay")
	WS.MakeRelay("Well Pump", "Manual Relay", 1, True)
	WS.MakeRelay("Treatment Valve", "Valve Manual Relay", 1, True)
	#add indicators
	SinkEmpty = WS.Add(Indicator(40, 40, "Sink Empty"))
	Full3000 = WS.Add(Indicator(40,40,"3000 Full", ((0,75,0), (0,255,0)), False))
	Full1000 = WS.Add(Indicator(40,40,"1000 Full", ((0,0,75), (100,150,255)), False))
	#add floats
	WS.MakeFloat("Well Cluster", "WC HIGH", 0.4, 0.1)
	WS.MakeFloat("Raw Water", "RW HIGH", 0.92, 0.04)
	WS.MakeFloat("Raw Water", "RW LOW", 0.12, 0.04)
	WS.MakeFloat("Distrubtion Water", "DW HIGH", 0.92, 0.04)
	WS.MakeFloat("Distrubtion Water", "DW LOW", 0.12, 0.04, False)
	WS.MakeFloat("Sink", "SINK LOW", 0.5, 0.3, False)

	#add boxes
	WS.Add(Box(150,300,225,175,"Treatment"))
	WS.Add(Box(225,40,150,125,"Pump House"))

	#Relay Logic Function Overrides
	def WPR_Trigger(self, System):
		rwlf = System.FindWithLabel("RW LOW", FloatSwitch).Active
		rwhf = System.FindWithLabel("RW HIGH", FloatSwitch).Active
		dwhf = System.FindWithLabel("DW HIGH", FloatSwitch).Active
		wclf = System.FindWithLabel("WC HIGH", FloatSwitch).Active

		treatingServo = (rwlf) and (not dwhf)

		if not rwhf and wclf and not treatingServo:
			self.Triggered = True
		else:
			self.Triggered = False

	TPR.rwlf = WS.FindWithLabel("RW LOW", FloatSwitch)
	TPR.tvr = WS.FindWithLabel("TV Relay", Relay)
	def TPR_Trigger(self, System):
		#dwhf = System.FindWithLabel("DW HIGH", FloatSwitch).Active
		#wpr = System.FindWithLabel("Well Pump Relay").Triggered

		if self.tvr.Triggered or self.rwlf.Active:
			self.Triggered = True
		else:
			self.Triggered = False

	def DPR_Trigger(self, System):
		dwlf = System.FindWithLabel("DW LOW", FloatSwitch).Active
		sklf = System.FindWithLabel("SINK LOW", FloatSwitch).Active

		if sklf and not dwlf:
			self.Triggered = True
		else:
			self.Triggered = False

	TVR.dwhf = WS.FindWithLabel("DW HIGH", FloatSwitch)
	TVR.rwlf = WS.FindWithLabel("RW LOW", FloatSwitch)
	def TVR_Trigger(self, System):
		if not self.dwhf.Active and self.rwlf.Active:
			self.Triggered = True
		else:
			self.Triggered = False

	WPR.Triggers = WPR_Trigger.__get__(WPR, Relay)
	TPR.Triggers = TPR_Trigger.__get__(TPR, Relay)
	TVR.Triggers = TVR_Trigger.__get__(TVR, Relay)
	DPR.Triggers = DPR_Trigger.__get__(DPR, Relay)

	SinkEmpty.Sink = WS.FindWithLabel("Sink")
	def SinkEmptyCondition(self, system) -> bool:
		if self.Sink.Fill <= 0:
			return True
		return False
	SinkEmpty.CheckCondition = SinkEmptyCondition.__get__(SinkEmpty, Indicator)

	Full3000.dwhf = WS.FindWithLabel("DW HIGH")
	def CheckCondition(self, system) -> bool:
		return self.dwhf.Active
	Full3000.CheckCondition = CheckCondition.__get__(Full3000, Indicator)

	Full1000.rwhf = WS.FindWithLabel("RW HIGH")
	def CheckCondition(self, system) -> bool:
		return self.rwhf.Active
	Full1000.CheckCondition = CheckCondition.__get__(Full1000, Indicator)

	WS.LoadPositions()
	Simulate(WS)
	


if __name__ == "__main__":
	main()
	