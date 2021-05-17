import encoder
import decoder
import logging
import logging_config
import logging.config
import server
import database_maneger
from sys import argv
import os
import  time
import ui_client
from json import loads

#settings
settings_path="settings.json"
settings_file=open(settings_path)
settings=loads(settings_file.read())
settings_file.close()

NUMBER_OF_ERRORS=settings["NUMBER_OF_ERRORS"]
PACKAGE_SIZE=settings["PACKAGE_SIZE"]
TIME_BETWEEN_BECKUPS=settings["TIME_BETWEEN_BECKUPS"]# time between becups in days
TIME_BETWEEN_BECKUPS=TIME_BETWEEN_BECKUPS*86400#number of secends in one day

database_path=settings["database_path"]
saves_dir=settings["saves_dir"]
peers_list_file=settings["peers_list_file"]
output_dir=settings["output_dir"]
host=settings["host"]
host_port=settings["host_port"]
MAX_SAVE_SIZE=settings["MAX_SAVE_SIZE"]

key=settings["key"]

key=str.encode(key)
key = key + b'0' * (32 - len(key))


global threads
global main_loop_running
threads = []


if __name__=='__main__':
    #global threads
    #global main_loop_running
    print(host,host_port)
    if not os.path.exists(saves_dir):
        os.mkdir(saves_dir)

    logging.config.dictConfig(logging_config.get_config(host+'  '+str(host_port)))

    if not os.path.exists(saves_dir):
        os.mkdir(saves_dir)
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    #start the thredes
    database = database_maneger.DatabaseMeneger(database_path,peers_list_file,[host,host_port])

    # ===============================encoder

    split = encoder.Splitter(PACKAGE_SIZE)
    split.start()
    threads.append(split)

    serv = server.Server(saves_dir, database,output_dir, MAX_SAVE_SIZE, host_port,split.files_input,host)
    serv.start()

    cryp = encoder.Crypto(split.packeg_q, key)
    cryp.start()

    reed = encoder.AddReed5(PACKAGE_SIZE, NUMBER_OF_ERRORS, cryp.packet_output)
    reed.start()

    sender=encoder.Sender(reed.reed5_q,saves_dir,reed.packeg_proportion,database,host,host_port)
    sender.start()

    #===============================decoder

    remove = decoder.RemoveReed5(saves_dir,database,host,host_port,PACKAGE_SIZE, NUMBER_OF_ERRORS, reed.packeg_proportion)
    remove.start()

    dcryp = decoder.Crypto(remove.packet_output, key)
    dcryp.start()

    unit = decoder.Uniter(output_dir,dcryp.packet_output)
    unit.start()

    ui_client.set_host('127.0.0.1', int(host_port))

    # ============================runing modes
    
    '''
    print('mode: '+mode)

    if mode=='1':
        split.files_input.put("C:\\Users\\yuval\\projects\\saiber_big_project\\source\\files_for_tests\\test.txt")
        #split.files_input.put("C:\\Users\\yuval\\projects\\saiber_big_project\\source\\files_for_tests\\test2.jpg")

    if mode=='2':
        remove.files_input.put("C:\\Users\\yuval\\projects\\saiber_big_project\\source\\files_for_tests\\test.txt")

    if mode=='3':
        ui_client.disconect()


    if mode=='4':
        ui_client.del_file("C:\\Users\\yuval\\projects\\saiber_big_project\\source\\files_for_tests\\test.txt")
    '''
    '''
    while main_loop_running:
        file_list = database.get_all_files()
        t=time.time()
        print(file_list)
        for f in file_list:
            if f[1]+TIME_BETWEEN_BECKUPS<t:
                ui_client.del_file(f[0])
                time.sleep(30)
                split.files_input.put(f[0])
            if not (os.path.exists(f[0]) or os.path.exists(os.path.join(output_dir,os.path.basename(f[0])))):
                print("             need to restore "+f[0])
                #remove.files_input.put(f[0])

        time.sleep(100)'''


