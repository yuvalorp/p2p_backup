from reedsolo import RSCodec

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import threading
import queue
import logging
#from os import listdir
from os.path import exists,basename
#from os import remove
from json import loads
from copy import copy


NUMBER_OF_ERRORS = 9  # number of errors that the reed5 will be able to fix
PACKAGE_SIZE = 1024  # size of every package to send


class RemoveReed5(threading.Thread):
    """
    collect and remove reed
    packeg_n-> number of packeges to add to them rees5 at once
    packeg_q->Queue evrey node is Dictionary that have {"packege":the text of the packege,"path":the path of the file} or a string "file_end"
    """

    def __init__(self, dir_to_read,packet_size,NUMBER_OF_ERRORS, packeg_proportion,size_q_input=10,size_q_output=10):
        # create logger
        self.logger = logging.getLogger('RemoveReed5')
        self.logger.setLevel(logging.INFO)

        self.packet_size = packet_size
        self.NUMBER_OF_ERRORS=NUMBER_OF_ERRORS

        self.dir_to_read=dir_to_read
        self.files_input = queue.Queue(maxsize=size_q_input)
        self.packet_output = queue.Queue(maxsize=size_q_output)

        self.packeg_proportion=packeg_proportion
        self.packeg_proportion["total"]=self.packeg_proportion["normal"]+self.packeg_proportion["reed5"]

        self.waiting_hash=[]


        super(RemoveReed5, self).__init__()

    def run(self):
        while True:

            packets=self.get_packages()


            file_path = packets["path"]
            missing_pack_list=packets["missing_pack_list"]

            key = packets["key"]
            packets=packets["packages"]



            packege_outpot=[b""]*self.packeg_proportion["normal"]

            for symbol_index in range(self.packet_size):
                string_to_remove_reed=b""
                for pack in packets:

                    string_to_remove_reed+=(pack[symbol_index].to_bytes(1, byteorder='big'))


                original=self.remove_reed5(self.NUMBER_OF_ERRORS,string_to_remove_reed,missing_pack_list)



                if original==None:#None meen that there is to mach error
                    self.logger.error("to many errors in the file "+file_path)




                for packege_index in range(self.packeg_proportion["normal"]):




                    packege_outpot[packege_index]+=(original[packege_index].to_bytes(1, byteorder='big'))
                    #packege_outpot[packege_index] += b'a'

            self.packet_output.put({"packets": packege_outpot, "path": file_path,'key':key})



    def get_packages(self):
        '''
        get the packeges of specific file
        only for the poc
        '''

        if len(self.waiting_hash)==0:

            meta_data_path = self.files_input.get()
            meta_data_file = open(meta_data_path, "rb")
            meta_data = meta_data_file.read()
            meta_data_file.close()
            meta_data =loads(meta_data)
            meta_data2=copy(meta_data)
            for hash_list in meta_data['packages']:
                meta_data2['packages']=hash_list

                self.waiting_hash.append(copy(meta_data2))



            self.logger.info("start file " + meta_data_path)


        hash_list = self.waiting_hash[0]['packages']


        file_name=self.waiting_hash[0]['name']
        key=self.waiting_hash[0]['key']

        self.waiting_hash.pop(0)

        pack_list=[]
        missing_pack_list=[]
        for i in range(len(hash_list)):

            file_path = self.dir_to_read + "\\"+hash_list[i]
            if exists(file_path):
                f2 = open(file_path,'rb')

                f3 = f2.read()


                f2.close()
                pack_list.append(f3)

            else:
                missing_pack_list.append(i)
                self.logger.error(file_path + " is missing")
                pack_list.append(b"X"*self.packet_size)


        '''
        for i in hash_list:

            file_path = self.dir_to_read + "\\"+i
            if exists(file_path):
                f2 = open(file_path,'rb')

                f3 = f2.read()


                f2.close()
                pack_list.append(f3)

            else:
                self.logger.error(file_path + " is missing")
        '''
        return ({"packages":pack_list,"path":file_name,"key":key,"missing_pack_list":missing_pack_list})

    def remove_reed5(self, NUMBER_OF_ERRORS, s1,missing_pack_list):

        rsc = RSCodec(NUMBER_OF_ERRORS)
        try:
            s2 = rsc.decode(s1,erase_pos=missing_pack_list)[0]
            return (s2)
        except:

            return (None)

class Crypto(threading.Thread):
    # encrypt the packets

    def __init__(self, file_input, size_results=10):
        # create logger
        self.logger = logging.getLogger('writer')
        self.logger.setLevel(logging.INFO)

        self.packet_input = file_input


        self.packet_output = queue.Queue(maxsize=size_results)
        super(Crypto, self).__init__()

    def run(self):
        self.logger.info("runing")
        while True:
            pack_list = self.packet_input.get()



            if pack_list=="file end":
                self.packet_output.put("file end")
                self.logger.info("end file" )
            else:

                packets = pack_list['packets']
                key=bytes.fromhex(pack_list['key'])
                new_packets=[""]*len(packets)
                for i in range(len(packets)):

                    new_packets[i]=self.decrypt(packets[i],key)


                pack_list['packets']=new_packets


                self.packet_output.put(pack_list)

    def decrypt(self,s,key):

        return (s)

        chiper = Cipher(algorithms.AES(key), modes.ECB())
        decryptor = chiper.decryptor()
        q=decryptor.update(s) + decryptor.finalize()

        return (q)


class Uniter(threading.Thread):
    """
    uniting all the packets togther to one file
    """

    def __init__(self, dir_to_write,q_input):
        # create logger
        self.logger = logging.getLogger('Uniter')
        self.logger.setLevel(logging.INFO)

        self.NUMBER_OF_ERRORS=NUMBER_OF_ERRORS

        self.dir_to_write=dir_to_write
        self.files_input = q_input


        self.start_part=True#help variable


        super(Uniter, self).__init__()

    def run(self):
        while True:

            packets=self.files_input.get()

            file_path = packets["path"]
            new_file_path=self.dir_to_write+"\\"+basename(file_path)


            packets=packets["packets"]

            write_file = open(new_file_path, "ab")
            for pack in packets:
                write_file.write(pack)
            write_file.close()


if __name__ == '__main__':
    remove=RemoveReed5("C:\\Users\\yuval\\projects\\saiber_big_project\\poc\\file_packages",
                PACKAGE_SIZE,NUMBER_OF_ERRORS,{"normal": 16, "reed5": 9})
    crypt=Crypto(remove.packet_output)
    unit = Uniter("C:\\Users\\yuval\\projects\\saiber_big_project\\poc\\file_output",
                  crypt.packet_output)

    # get the file to work on later it will be from the gui
    #remove.files_input.put("C:\\Users\\yuval\\projects\\saiber_big_project\\poc\\file_packages\\meta_test.json")
    remove.files_input.put("C:\\Users\\yuval\\projects\\saiber_big_project\\poc\\file_packages\\meta_test2.json")

    crypt.start()


    remove.start()
    unit.run()


#C:\\Users\\yuval\\projects\\saiber_big_project\\poc\\file_packages\\meta_test.json