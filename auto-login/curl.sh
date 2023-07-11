#/bin/bash
#说明：该脚本可以在服务启动之后，在linux系统中执行，测试在线服务是否可以接收请求并登录。启动在线服务直接执行start.bat即可

username=$1
password=$2
pub_key="B7EF5B74-8FB0-85C6-8F7272DCDCDEB545"
server_addr="127.0.0.1:8001"

curtime=`date +%s`
sig=`echo -n "$curtime|$pub_key" | md5sum | cut -d " " -f1`
base_url="http://$server_addr/Api_v1?params=$username|$password&sig="
echo "$base_url$curtime"\$"$sig"
curl "$base_url$curtime"\$"$sig"