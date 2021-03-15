import encoder
import decoder
import logging
import server
import database_maneger
from sys import argv
import os
import signal
import  time

#encode/decode parneters
NUMBER_OF_ERRORS = 9  # number of errors that the reed5 will be able to fix
PACKAGE_SIZE = 1024  # size of every package to send

#files
database_path="C:\\Users\\yuval\\projects\\saiber_big_project\\source\\file_packages\\data_base.db"
key_file_path = r'C:\Users\yuval\projects\saiber_big_project\source\passward.txt'
saves_dir="C:\\Users\\yuval\\projects\\saiber_big_project\\source\\file_packages"
peers_list_file='C:\\Users\\yuval\\projects\\saiber_big_project\\source\\peers.json'

#server parameters
MAX_SAVE_SIZE = 10000
host_port = 5000

mode='1'

try:
    #print(argv)
    (useless,mode,host_port,database_path,saves_dir)=argv
except:pass
r'''C:\Users\yuval\projects\saiber_big_project\source\main_loop.py 1 5001 "C:\Users\yuval\projects\saiber_big_project\source\file_packages\data_base.db" "C:\Users\yuval\projects\saiber_big_project\source\file_packages"
'''
global threads
global main_loop_running
threads = []
main_loop_running = True
def signal_handler(signum, frame):
    logging.info("Stopping all threads")
    for t in threads:
        t.stop()
    main_loop_running = False
    for t in threads:
        t.join()
    logging.info("All threads stopped")

if __name__=='__main__':
    #global threads
    #global main_loop_running

    logging.basicConfig(level=logging.INFO)

    signal.signal(signal.SIGINT, signal_handler)

    #start the thredes
    database = database_maneger.DatabaseMeneger(database_path,peers_list_file,['127.0.0.1',host_port])

    split = encoder.Splitter(PACKAGE_SIZE)
    split.start()
    threads.append(split)

    serv = server.Server(saves_dir, database, MAX_SAVE_SIZE, host_port,split.files_input)
    serv.start()


    cryp = encoder.Crypto(split.packeg_q, key_file_path)
    cryp.start()

    reed = encoder.AddReed5(PACKAGE_SIZE, NUMBER_OF_ERRORS, cryp.packet_output)
    reed.start()


    sender=encoder.Sender(reed.reed5_q,saves_dir,reed.packeg_proportion,database,'127.0.0.1',host_port)
    sender.start()

    if mode=='1':
        split.files_input.put("C:\\Users\\yuval\\projects\\saiber_big_project\\source\\files_for_tests\\test.txt")

    while main_loop_running:
        time.sleep(1)




def give_files_status(dir_path,database):
    '''return list of all the files in a dir and their status'''
    files={}
    beckuped=database.files_in_dir(dir_path)
    beckuped2=[p[0] for p in beckuped]
    in_dir=os.listdir(dir_path)

    for f in beckuped+in_dir:
        if_beckuped=f in beckuped2
        if_in_dir=f in in_dir
        if if_in_dir and if_beckuped:
            files[f]="becuped"
        if if_in_dir and not if_beckuped:
            files[f]="doesnt beckuped"
        else:
            files[f]="needs reconstruction"
    return(files)


