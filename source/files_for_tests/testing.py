import subprocess
#from peer_client import *
#import threading
import os

from time import sleep


modes='4000'
#modes='0300'

pack_path=r"C:\Users\yuval\projects\saiber_big_project\source\file_packages"
if not os.path.exists(pack_path):
    os.mkdir(pack_path)

pack_path=r"C:\Users\yuval\projects\saiber_big_project\source\file_packages\f1"
if not os.path.exists(pack_path):
    os.mkdir(pack_path)
serv1 = subprocess.Popen( ['python',
    r"C:\Users\yuval\projects\saiber_big_project\source\main_loop.py",modes[0],'5001',
    r"C:\Users\yuval\projects\saiber_big_project\source\file_packages\data_base1.db",
    pack_path,
     'C:\\Users\\yuval\\projects\\saiber_big_project\\source\\file_output'])


pack_path=r"C:\Users\yuval\projects\saiber_big_project\source\file_packages\f2"
if not os.path.exists(pack_path):
    os.mkdir(pack_path)
serv2= subprocess.Popen(['python',r"C:\Users\yuval\projects\saiber_big_project\source\main_loop.py",modes[1],'5002',
                         r"C:\Users\yuval\projects\saiber_big_project\source\file_packages\data_base2.db" ,
                         pack_path,
                         'C:\\Users\\yuval\\projects\\saiber_big_project\\source\\file_output'])


pack_path=r"C:\Users\yuval\projects\saiber_big_project\source\file_packages\f3"
if not os.path.exists(pack_path):
    os.mkdir(pack_path)
serv3= subprocess.Popen(['python',r"C:\Users\yuval\projects\saiber_big_project\source\main_loop.py",modes[2],'5003',
                         r"C:\Users\yuval\projects\saiber_big_project\source\file_packages\data_base3.db" ,
                         pack_path,
                         'C:\\Users\\yuval\\projects\\saiber_big_project\\source\\file_output'])


pack_path=r"C:\Users\yuval\projects\saiber_big_project\source\file_packages\f4"
if not os.path.exists(pack_path):
    os.mkdir(pack_path)
serv4= subprocess.Popen(['python',r"C:\Users\yuval\projects\saiber_big_project\source\main_loop.py",modes[3],'5004',
                         r"C:\Users\yuval\projects\saiber_big_project\source\file_packages\data_base4.db" ,
                         pack_path,
                         'C:\\Users\\yuval\\projects\\saiber_big_project\\source\\file_output'])

try:
    while serv1.poll() is None:
        sleep(1)

except :pass

