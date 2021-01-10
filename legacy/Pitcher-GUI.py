import tkinter as tk
from socket import socket
import sys

def main():
	
	if DEBUG:
		class GUI(Thread):
			def __init__(self, condition):
				Thread.__init__(self)
				self.intVar = None
				self.condition = condition
				self.root = None
			
			def getIntVar(self):
				return self.intVar
			
			def onClose(self):
				self.intVar = None
				self.root.destroy()
			
			def run(self):
				with self.condition:
					root = tk.Tk()
					self.intVar = tk.IntVar()
					condition.notify()
				scale = tk.Scale(root, to = 0, from_ = 255, resolution = 1, 
								variable = self.intVar)
				scale.set(128)
				scale.pack()
				root.title('Pitcher GUI')
				root.protocol('WM_DELETE_WINDOW', self.onClose)
				self.root = root
				root.mainloop()
				del self.root
		
		global getIntVar
		condition = Condition()
		gui = GUI(condition)
		with condition:
			gui.start()
			while gui.getIntVar() is None:
				condition.wait()
			getIntVar = gui.getIntVar

main()
sys.exit(0)
