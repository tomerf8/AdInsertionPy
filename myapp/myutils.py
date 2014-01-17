#!/usr/bin/python
from constants import consts
import os
from datetime import datetime


class utils_class:

    def __init__(self): 
        self.debug_mode = 2
        # 1 = err,warn,log,flow  | all
        # 2 = err,warn,flow      | Errors and Warnings and flow
        # 3 = err,warn           | Errors and Warnings
        # 4 = err                | only Errors
        
        #- Init performance file
        if consts.ENABLE_PERFORMANCE_PRINT:
            self.header = "StartTime\,ServiceTime\,RequestID\,RequestFile\,CPU\,Memory"
            self.performace_file = consts.BASE_DIR + consts.PWD_LOGS_FILES + "performance_log.csv"
            os.system("echo %s > %s"%(self.header, self.performace_file))


    def debug_print(self,msg,sts='log'):
        try:
            if sts == 'log':
                code = 1
            elif sts == 'flow':
                code = 2
            elif sts == 'warn':
                code = 3   
            elif sts == 'err':
                code = 4   

            if self.debug_mode <= code:
                print '@'+sts.upper()+':\t'+msg
        except:
            pass
    
    def print_performance(self,msg):
        if consts.ENABLE_PERFORMANCE_PRINT:
            os.system("echo %s >> %s"%(msg, self.performace_file))
            
            
            
            