import httplib2
from json import loads,dumps
#host = 'localhost'
#host_port = 5000
def set_host(host1,host_port1):
    global host_port
    global host
    host_port=host_port1
    host=host1

def beckup_file(file_path):


    h = httplib2.Http(timeout=1)
    print(f"http://{host}:{host_port}/self/put_beckup/{file_path}")
    try:

        (response, content)=h.request(f"http://{host}:{host_port}/self/put_beckup/{file_path}","PUT")

    except (ConnectionRefusedError,TimeoutError):
        return ('the peer refused')

    if content!="writen secsesfully":
        return ('the peer refused')
    else:
        return("writen secsesfully")

def disconect():
    h = httplib2.Http(timeout=1)
    try:

        (response, content)=h.request(f"http://{host}:{host_port}/self/disconect","DELETE")

    except (ConnectionRefusedError,TimeoutError):
        return ('the peer refused')


    return(response, content)

def del_file(path):
    h = httplib2.Http(timeout=1)
    (response, content) = h.request(f"http://{host}:{host_port}/self/del_file/{path}", "DELETE")
    return (content)

def get_files_status(path):
    h = httplib2.Http(timeout=1)
    (response, content) = h.request(f"http://{host}:{host_port}/self/get_files_status/{path}", "GET")
    #print(content)
    return (loads(content))

def serv_exist():
    try:
        h = httplib2.Http()
        (response, content)=h.request(f"http://{host}:{host_port}/exist","GET")
        return (content)
    except:
        return(False)

if __name__ =='__main__':
    # the resever
    host = 'localhost'
    host_port = 5000
    # the sender
    ip = "123.243.345.456"
    port = 5001

    set_host('localhost', 5000)

   # print(beckup_file('C:/Users/yuval/projects/saiber_big_project/source/files_for_tests/test.txt'))





