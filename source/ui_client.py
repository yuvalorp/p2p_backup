import httplib2
#host = 'localhost'
#host_port = 5000
def set_host(host1,host_port1):
    global host_port
    global host
    host_port=host_port1
    host=host1

def beckup_file(file_path):

    h = httplib2.Http()
    print(f"http://{host}:{host_port}/self/put_beckup/{file_path}")
    try:

        (response, content)=h.request(f"http://{host}:{host_port}/self/put_beckup/{file_path}","PUT")

    except (ConnectionRefusedError,TimeoutError):
        return ('the peer refused')

    if content!="writen secsesfully":
        return ('the peer refused')
    else:
        return("writen secsesfully")



if __name__ =='__main__':
    # the resever
    host = 'localhost'
    host_port = 5000
    # the sender
    ip = "123.243.345.456"
    port = 5001

    set_host('localhost', 5000)

    print(beckup_file('C:/Users/yuval/projects/saiber_big_project/source/files_for_tests/test.txt'))





