from kivy.config import Config
Config.set('graphics', 'width', '700')
Config.set('graphics', 'height', '700')
Config.write()
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from kivy.properties import StringProperty, ListProperty, NumericProperty
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.lang import Builder
import itertools
import random
from random import choice
Window.size = (625,600)
import time 

GREEN = [0, .7, .2, 1]
RED = [.7, 0, .5, 1]
BLUE = [.1, .5, .7, 1]
WHITE = [1,1,1,1]




class Part(Widget):
	color = ListProperty([1,1,1,1])
	step = 16
	def __init__(self, **kwargs):
		super(Part, self).__init__(**kwargs)
		self.g = 0
		self.h = 0
		self.f = 0
		self.block = False
		self.relative = None
	

	def getH(self, goal):
		dx = (goal.x - self.x)//2
		dy = (goal.y - self.y)//2
		return abs(dx) + abs(dy)

	def get_nearbys(self, cells):
		step = self.step
		def filter_cells(cell):
			if (self.x + step, self.y) == (cell.x, cell.y):
				return cell
			if (self.x - step, self.y) == (cell.x, cell.y):
				return cell
			if (self.x, self.y + step) == (cell.x, cell.y):
				return cell
			if (self.x, self.y - step) == (cell.x, cell.y):
				return cell
		return list(filter(filter_cells, cells))


	

class Board(GridLayout):
	snake = None #head
	food = None #food
	cells = list()

	score = NumericProperty(0)
	def __init__(self, **kwargs):
		super(Board, self).__init__(**kwargs)

		Clock.schedule_interval(self.looper, 1/60.)

	def looper(self, dt):
		if self.snake.collide_widget(self.food):
			self.respawn_food()
	
	def callback(self, value):
		if value == "start":
			self.snake.start(True)
			self.btn.text = "stop"
		else:
			self.btn.text = "start"
			self.snake.start(False)

	def respawn_food(self):
		if self.food:
			self.food.block = False
			self.food.color = [0,0,0,0]

		while True:
			food = choice(self.cells)
			if food is not self.snake:
				self.food = food
				self.food.color = RED
				break

	def block_unblock_cell(self, *args):

		def block(cell):
			for temp_cell_pos in args[1]:
				if (cell.x, cell.y) == temp_cell_pos:
					cell.block = True
					break
			return cell

		def unblock(cell):
			cell.block = False
			return cell

		def return_matched_cell():
			match = None
			for cell in self.cells:
				if (cell.x, cell.y) == args[1][0]:
					match = cell
					break
			return match

		self.cells = list(map(unblock, self.cells))

		if args[0]:
			self.cells = list(map(block, self.cells))
		return return_matched_cell()


class __BRAIN__:
	openSet = list()
	closedSet = list()
	path = list()

	goal = None
	exhausted = False

	tracker = "#Processing "
	steps_found = 0

	def __init__(self,  head:None):	
		self.exhausted = False
		self.head = head

	def get_available(self, cells):
		best_cell_value = min([i.f for i in cells])
		for cell in cells:
			if cell.f == best_cell_value:
				return cell

	def reset(self):
		self.tracker = "#Processing "
		del self.openSet[:]
		del self.closedSet[:]
		self.goal = None
		self.exhausted = False
		self.steps_found = 0

	def __call__(self, *args):

		def filter_cells(cell):
			if cell not in self.closedSet and cell.block is False:
				return cell

		brain = self.head(*args)
		print("# initiating process...")
		cells = brain.parent.cells

		self.goal = brain.parent.food
		self.openSet = [brain]

		t1 = time.time()

		while not self.exhausted and len(self.openSet) > 0:
			available = self.get_available(self.openSet)
			del self.openSet[self.openSet.index(available)]
			self.closedSet.append(available)

			if available.relative:
				self.steps_found += 1
				snake_game.board.snake.temp_path.append(available.relative)

			if available is self.goal:
				snake_game.board.snake.temp_path.append(self.goal)
				self.exhausted = True

			else:
				nearbys = list(filter(filter_cells, available.get_nearbys(cells)))

				for cell in nearbys:
					gValue = available.g + 1
					if cell in self.openSet:
						if gValue < cell.g:
							cell.g = gValue
					else:
						cell.g = gValue 
						self.openSet.append(cell)

					cell.h = cell.getH(self.goal)
					cell.f = cell.g + cell.h
					cell.relative = available
			self.tracker += "."
			print(self.tracker)
	
		t2 = time.time()
		print("steps found: ", self.steps_found)
		print("time taken: ", round(t2-t1, 2))
		self.reset()



class Head(Part):
	body = list()
	temp_path = list()
	
	def __init__(self, *args, **kwargs):
		super(Head, self).__init__(*args, **kwargs)

		self.body = [self]

	@__BRAIN__ 
	def find_path(self):
		print("let me think for a second....")
		return self.parent.block_unblock_cell(True, list(map(lambda part: (part.x, part.y), self.body)))
						
	current = None
	before = None

	def looper(self, dt):
		self.current = self.x, self.y
		try:
			step = self.temp_path.pop(0)
			
			self.pos = step.x, step.y

			for body_part in self.body[1:]:
				self.before = body_part.x, body_part.y
				body_part.pos = self.current
				self.current = self.before

			if self.collide_widget(self.parent.food):
				self.parent.score += 1
				if not self.before:
					self.before = self.current
				self.create_new_part(self.before)
			self.current = None
			self.before = None
		except:
			self.path = self.find_path(self)
	
	def create_new_part(self, position):
		part = Cell()
		part.pos = position[0], position[1]
		part.color = GREEN
		self.parent.add_widget(part)
		self.body.append(part)

	def start(self, value = False):
		if value:
			Clock.schedule_interval(self.looper, .2)
		else:
			Clock.unschedule(self.looper)


class Cell(Part):
	color = ListProperty([0,0,0,0])
	def __init__(self, *args, **kwargs):
		super(Cell, self).__init__(*args, **kwargs)


class SnakeGameApp(App):

	def on_start(self):
		random_cell = choice(self.board.cells)
		self.board.snake = Head(pos = random_cell.pos)
		self.board.snake.color = GREEN
		self.board.add_widget(self.board.snake)
		self.board.respawn_food()

	def build(self):
		self.board = Board(size = Window.size)

		x = self.board.x
		y = self.board.y + 100

		width = self.board.width-10
		height = self.board.height - 50

		while y < height:
			while x < width:
				cell = Cell(pos = (x, y))
				self.board.add_widget(cell)
				self.board.cells.append(cell)
				x += 16
			x = self.board.x
			y += 16
		return self.board

Builder.load_string("""
<Part>:
	size_hint:(None, None)
	size: (15, 15)
	canvas:
		Color:
			rgba: root.color
		Rectangle:
			size: self.size
			pos: self.pos
<Board>:
	btn:btn
	canvas.before:
		Color:
			rgb: .4, .6, .7
		Rectangle:
			size: self.size
			pos: self.pos
		Color:
			rgb: 1,1, .8
		Rectangle:
			size: root.width, root.height-136
			pos: root.x, root.y + 100
	Label:
		text: "score " + str(root.score)
		font_size: "20sp"
		pos: root.x, root.height- 65
	Button:
		id: btn
		text: "start"
		size: (100, 30)
		pos: root.width/2.5, 10
		on_release:
			root.callback(self.text)
""")
if __name__ in ('__main__'):
	snake_game = SnakeGameApp()
	snake_game.run()