from reedsolo import RSCodec

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import threading
import queue
import logging
from os.path import basename
from copy import copy
from database_maneger import DatabaseMeneger
import peer_client

NUMBER_OF_ERRORS = 9  # number of errors that the reed5 will be able to fix
PACKAGE_SIZE = 1024  # size of every package to send

class RemoveReed5(threading.Thread):
    '''
    collect and remove reed
    packeg_n-> number of packeges to add to them rees5 at once
    packeg_q->Queue evrey node is Dictionary that have {"packege":the text of the packege,"path":the path of the file} or a string "file_end"
    '''

    def __init__(self, dir_to_read,data_base,ip,port,packet_size,NUMBER_OF_ERRORS, packeg_proportion,size_q_input=10,size_q_output=10):
        # create logger
        self.logger = logging.getLogger('RemoveReed5')
        self.logger.setLevel(logging.INFO)

        self.packet_size = packet_size
        self.NUMBER_OF_ERRORS=NUMBER_OF_ERRORS

        self.dir_to_read=dir_to_read
        self.data_base=data_base
        self.files_input = queue.Queue(maxsize=size_q_input)
        self.packet_output = queue.Queue(maxsize=size_q_output)

        self.packeg_proportion=packeg_proportion
        self.packeg_proportion["total"]=self.packeg_proportion["normal"]+self.packeg_proportion["reed5"]

        self.waiting_hash=[]
        self.ip = ip
        self.port = port


        super(RemoveReed5, self).__init__()

    def run(self):
        while True:

            packets=self.get_packages()


            file_path = packets["path"]
            missing_pack_list=packets["missing_pack_list"]

            packets=packets["packages"]



            packege_outpot=[b""]*self.packeg_proportion["normal"]

            for symbol_index in range(self.packet_size):
                string_to_remove_reed=b""

                for pack in packets:
                    string_to_remove_reed+=(pack[symbol_index].to_bytes(1, byteorder='big'))


                original=self.remove_reed5(string_to_remove_reed,missing_pack_list)



                if original==None:#None meen that there is to mach error
                    self.logger.error("to many errors in the file "+file_path)
                    break


                for packege_index in range(self.packeg_proportion["normal"]):


                    packege_outpot[packege_index]+=(original[packege_index].to_bytes(1, byteorder='big'))

            self.packet_output.put({"packets": packege_outpot, "path": file_path})

    def get_packages(self):
        '''
        get the packeges of specific file
        '''

        if len(self.waiting_hash)==0:
            self.logger.info('waiting for work')

            file_path = self.files_input.get()
            self.logger.info('start working')
            parts=self.data_base.get_parts_of_file(file_path)

            a=[]
            n=0

            for i in parts:
                a.append(i)
                n = n + 1
                if n % self.packeg_proportion["total"] == 0:
                    self.waiting_hash.append(copy(a))
                    a = []
                    n = 0

            self.logger.info("start file " +file_path)


        hash_list = self.waiting_hash.pop(0)

        file_path=hash_list[0]['file_path']


        pack_list=[]
        missing_pack_list=[]
        for i in range(len(hash_list)):
            exist,data=peer_client.return_pack(hash_list[i]['hash'],hash_list[i]['ip'],hash_list[i]['port'],self.ip, self.port)

            if exist:
                self.logger.info("returned secsesfully "+hash_list[i]['hash'])
                pack_list.append(data)

            else:
                missing_pack_list.append(i)
                self.logger.error(file_path + " is missing")
                pack_list.append(b"X"*self.packet_size)

        return ({"packages":pack_list,"path":file_path,"missing_pack_list":missing_pack_list})

    def remove_reed5(self, s1,missing_pack_list):

        rsc = RSCodec(self.NUMBER_OF_ERRORS)
        try:
            s2 = rsc.decode(s1,erase_pos=missing_pack_list)

            return (s2[0])
        except:
            return (None)


class Crypto(threading.Thread):
    # encrypt the packets

    def __init__(self, file_input,key, size_results=10):
        # create logger
        self.logger = logging.getLogger('writer')
        self.logger.setLevel(logging.INFO)
        self.packet_input = file_input
        self.key = key

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

                new_packets=[""]*len(packets)
                for i in range(len(packets)):

                    new_packets[i]=self.decrypt(packets[i],self.key)


                pack_list['packets']=new_packets


                self.packet_output.put(pack_list)

    def decrypt(self,s,key):



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

    key_file_path = r'C:\Users\yuval\projects\saiber_big_project\source\passward.txt'
    data_base = DatabaseMeneger("C:\\Users\\yuval\\projects\\saiber_big_project\\source\\file_packages\\data_base.db")

    remove=RemoveReed5("C:\\Users\\yuval\\projects\\saiber_big_project\\source\\file_packages",
                PACKAGE_SIZE,NUMBER_OF_ERRORS,{"normal": 16, "reed5": 9})
    crypt=Crypto(remove.packet_output,key_file_path)
    unit = Uniter("C:\\Users\\yuval\\projects\\saiber_big_project\\source\\file_output",
                  crypt.packet_output)


