from Simulate import Simulate
from WaterSystemClasses import *


def main():
	"""Define a water system.
	volume in gals, flowrate in gals/minute"""
	#create base system (window size, title)
	#System.PARTICLES = True
	#System.ZIG = True
	#WS = System((1500, 720), "title")

	#start by adding tanks, wells, sinks (x, y, label, capacity, generate/consume rate)
	#positions can be moved in gui

	#next add pumps (source tank, end tank, flowrate, label)

	#add valves to pumps (pump label, label, endSide = True, distance % = 0.5)

	#add relays to pumps or valves (controlled object label, label, num=0, isManual)

	#add floats to tanks (tank label,label, trigger threshold %, amplitude %, normally open)

	#last for gui, add any boxes (x, y, w, h, label)

	#make float logic


	#set float logic

	#set inital conditions

	#load saved positions
	#WS.LoadPositions()
	#start simulation
	#Simulate(WS)
	


if __name__ == "__main__":
	main()
	