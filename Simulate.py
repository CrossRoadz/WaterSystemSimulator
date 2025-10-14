
print("\n* Crossroads *\n")
try:
	import pygame
except ImportError:
	print("pygame Library needed to tun graphics.",
		"To install pygame run the pip command (package installer for python, https://pypi.org/project/pip/) tool in your command prompt:",
		"pip install pygame",
		sep = "\n")
	input()
pygame.init()
from WaterSystemClasses import *
from os import path
Dir = path.dirname(__file__)




class SelectedObject:
	#seems dedundant, but helps with cursor offsets
	def __init__(self, GraphicObject = None, mouse_pos = (0,0)):
		if GraphicObject is None: 
			self.Exists = False
			return
		self.Exists = True
		self.Object = GraphicObject
		self.X, self.Y = GraphicObject.X, GraphicObject.Y
		self.Offest = mouse_pos[0] - self.X, mouse_pos[1] - self.Y
	def Move(self, pos):
		if self.Object.Kind in (GraphicTypes.Relay, GraphicTypes.Valve, GraphicTypes.Float): return
		x,y = pos
		self.Object.X, self.Object.Y = x - self.Offest[0], y - self.Offest[1]

#draw UI
def draw(wn, WS):
	wn.fill((255,255,255))
	WS.Draw(wn)
	pygame.display.update()

def main(WS):
	#starting res
	wnWidth, wnHeight = WS.Bounds

	if System.PARTICLES: 
		print(WaterParticle.Particles, "Particles Loaded")

	wn = pygame.display.set_mode((wnWidth,wnHeight), pygame.RESIZABLE)
	pygame.display.set_icon(pygame.image.load(path.join(Dir, "Data/Images/Icon.png")))
	pygame.display.set_caption(f"Water System Simulator: {WS.title}")
	Clock = pygame.time.Clock()


	#main sim loop
	Paused = False
	running = True
	selectedObj = SelectedObject()
	while running:
		Clock.tick(System.TICK_RATE) #simulates at TICK_RATE Hz

		#grpahics
		draw(wn, WS)

		#input handling
		keys = pygame.key.get_pressed()
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = False
				global Reset
				Reset = False
			#change sim speed with mouse wheel
			elif event.type == pygame.MOUSEWHEEL: 
				oldTS = System.TimeScale
				System.TimeScale += event.y/100
				if System.TimeScale <= 0: System.TimeScale = oldTS
			#mouse stuff
			elif event.type == pygame.MOUSEBUTTONDOWN:
				#start moving obj
				if event.button == 1: #left
					selectedObj = SelectedObject(WS.GetUnderPos(event.pos), event.pos)
					if selectedObj.Exists and selectedObj.Object.Kind == GraphicTypes.Relay and selectedObj.Object.manualSwitch:
						selectedObj.Object.Clicked = not selectedObj.Object.Clicked

			elif event.type == pygame.MOUSEBUTTONUP:
				#stop moving obj
				if event.button == 1: #left
					selectedObj.Exists = False
				#add 10% fill to hovered tank
				elif event.button == 3: #right
					WS.MouseTankFill(WS.GetUnderPos(event.pos))
				elif event.button == 2: #middle
					WS.MouseTankFill(WS.GetUnderPos(event.pos), False)

			#resize main window
			elif event.type == pygame.VIDEORESIZE:
				wn = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
				WS.Bounds = (event.w, event.h)
			#Key events
			elif event.type == pygame.KEYDOWN:
				#pauses on P
				if event.key == pygame.K_p:
					Paused = not Paused
					print("Paused" if Paused else "Unpaused")
				#hints on h
				elif event.key == pygame.K_h:
					WS.ShowHelp = not WS.ShowHelp
				#ctrl + s to save
				elif event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_CTRL:
					WS.SavePositions()

		mouse_pos = pygame.mouse.get_pos()
		#translate selected object
		if selectedObj.Exists:
			selectedObj.Move(mouse_pos)

		#simlation
		if not Paused:
			WS.Update(selectedObj.Exists)



def Simulate(WS):
	main(WS)
	pygame.quit()