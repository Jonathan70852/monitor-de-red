import time  
from threading import Timer 

def display():  
    print('Activating Timer' + ' ' + time.strftime('%H:%M:%S'))  
  
##Lets make our timer run in intervals  
class RepeatTimer(Timer):  
    def run(self):
        print('Threading started')    
       # self.function(*self.args) 
        while not self.finished.wait(self.interval):
            display()   
            self.function(*self.args) 
            print(' ')  
