from flask import Flask, request
from flask_script import Manager
import time
import hashlib
import os
from crack import CrackLogin
from concurrent.futures import ThreadPoolExecutor


pri_key='B7EF5B74-8FB0-85C6-8F7272DCDCDEB545'
login_num=3
single_login_interval=60
cookie_cache_time=1*60
caches = './caches/'

cur_request_time=0
cur_request=None
executor=ThreadPoolExecutor(1)
app = Flask(__name__)
manager = Manager(app)


@app.route('/Api_v1', methods=['GET', 'POST'])
def action():
    
    print('接收客户端请求')
    
    sig=request.args.get('sig')
    sig_arr=sig.split('$')
    cur_second=int(time.time())
    print('当前时间：', cur_second)
    print('请求时间：', sig_arr[0])
    diff_secong=cur_second-int(sig_arr[0])
    print('时间差(S)：', diff_secong)     
    if diff_secong>30:
        return '密钥过期'
    computer_sig=hashlib.md5((sig_arr[0]+"|"+pri_key).encode()).hexdigest()
    if computer_sig!=sig_arr[1]:
        print('非法请求', computer_sig)
        return '非法请求'
    print('签名：', sig_arr[1])
    
    params=request.args.get('params')
    params_arr=params.split('|')
    username=params_arr[0]
    print('用户：', username)
    password=params_arr[1]
    print('密码：', password)
    
    cache_file_name=username+'-'+password+'.txt'
    cookie=get_cookie_cache(cache_file_name)
    if cookie is not None:
        print('读取缓存中的Cookie：', cookie)
        result={"status":0,"msg":"ok","data":cookie}
        return result
    
    global cur_request_time
    global cur_request
    if cur_request is None:
        print('线程池空闲')
        submit_request(cache_file_name, username, password)
        result={"status":1006,"msg":"系统正在处理，请稍后获取结果！","data":""}
        return result
    elif (int(time.time())-cur_request_time)>(login_num*single_login_interval):
        print('线程池任务超时丢弃')
        submit_request(cache_file_name, username, password)
        result={"status":1006,"msg":"系统正在处理，请稍后获取结果！","data":""}
        return result
    else:
        print('系统繁忙')
    
    result={"status":1006,"msg":"系统繁忙，请稍后重试！","data":""}
    return result


def try_login(data):
    print('系统尝试执行'+str(login_num)+'次登录')
    for num in range(1,login_num+1):
        print("第"+str(num)+"次尝试登录开始")
        crackLogin = CrackLogin()        
        result=crackLogin.crack(data['username'], data['password'])
        if result['status']==0:
            save_cookie_cache(data['cache_file_name'], result['cookie'])
            break;        
    global cur_request        
    cur_request=None

def submit_request(cache_file_name, username, password):
    print('提交客户端请求')
    global cur_request_time
    global cur_request
    cur_request_time=int(time.time())
    cur_request={"cache_file_name":cache_file_name, "username":username, "password":password}
    executor.submit(try_login, cur_request)
  
def get_cookie_cache(filename):
    if os.path.exists(caches+filename):
        with open(caches+filename, "r") as f:
                cache_time=f.readline()
                if cache_time and int(time.time())-int(cache_time)<cookie_cache_time:
                    cookie=f.readline()
                    if len(cookie)>0:
                        return cookie
                    else:
                        return None                    
    else:
        return None        

def save_cookie_cache(filename, cookie):
    with open(caches+filename, "w") as f:
        f.write(str(int(time.time())))       
        f.write("\n")
        f.write(cookie)  


if __name__ == "__main__":
    print("在线服务启动")
    manager.run()
    