

from util import nios2_as, get_debug, require_symbols, hotpatch, get_clobbered, get_regs
from csim import Nios2
#from sim import Nios2


class Exercises:
    __instance = None
    @staticmethod
    def getInstance():
        if Exercises.__instance == None:
            Exercises()
        return Exercises.__instance

    @staticmethod
    def addExercise(name, val):
        Exercises.getInstance().__addExercise(name, val)

    @staticmethod
    def getExercise(name):
        return Exercises.getInstance().__getExercise(name)

    @staticmethod
    def getAllExercises():
        return Exercises.getInstance().__instance.exercises

    def __addExercise(self, name, val):
        print('Adding exercise %s' % name)
        self.exercises[name] = val


    def __getExercise(self, name):
        if name not in self.exercises:
            return None
        return self.exercises[name]

    def __init__(self):
        if Exercises.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            Exercises.__instance = self
            self.exercises = {}

#from exercises.led_on import *

import os
for module in os.listdir(os.path.dirname(__file__)):
    if module == '__init__.py' or module[-3:] != '.py':
        continue
    __import__('exercises.'+module[:-3], locals(), globals())
del module
