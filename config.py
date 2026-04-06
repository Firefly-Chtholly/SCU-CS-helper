
"""
*Copyright (C) 2025 Firefly_Chtholly
*This program is free software: you can redistribute it and/or modify
*it under the terms of the GNU General Public License as published by
*the Free Software Foundation, either version 3 of the License, or
*(at your option) any later version.
*This program is distributed in the hope that it will be useful,
*but WITHOUT ANY WARRANTY; without even the implied warranty of
*MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
*GNU General Public License for more details.
*You should have received a copy of the GNU General Public License
*along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
# -*- coding: UTF-8 -*-
import datetime as date
import hashlib
import os
import time
import colorama
import re



def md5_hash(string, ver):
    if ver != "1.8":
        string += "{Urp602019}"
    utf8_string = string.encode('utf-8')
    md5_obj = hashlib.md5()
    md5_obj.update(utf8_string)
    return md5_obj.hexdigest()

def encrypo(string):
    pass1 = md5_hash(md5_hash(o_password, "1.7"), "1.8")
    pass2 = md5_hash(md5_hash(o_password, "1.8"), "1.8")
    return pass1 + "*" + pass2

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

colorama.init(autoreset=True)

waiting_url = "http://202.115.47.141/student/courseSelect/selectCourses/waitingfor"
select_captcha_url = "http://202.115.47.141/student/courseSelect/selectCourse/getYzmPic"
select_result_url = "http://202.115.47.141/student/courseSelect/selectResult/query"
redis_key_url = 'http://202.115.47.141/student/courseSelect/selectCourses/waitingfor'
login_token_url = 'http://202.115.47.141/login'
captcha_url = "http://202.115.47.141/img/captcha.jpg"
index_url = "http://202.115.47.141/"
login_url = "http://202.115.47.141/j_spring_security_check"
course_select_url = "http://202.115.47.141/student/courseSelect/courseSelect/index"
select_url = "http://202.115.47.141/student/courseSelect/selectCourse/checkInputCodeAndSubmit"
courseList_url = "http://202.115.47.141/student/courseSelect/freeCourse/courseList"
already_select_course_url = "http://202.115.47.141/student/courseSelect/thisSemesterCurriculum/callback"
queryTeacherJL_url = "http://202.115.47.141/student/courseSelect/queryTeacherJL"
selectcourse_xueqi = "2025-2026-1-1"
header = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3782.0 Safari/537.36 Edg/76.0.152.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Connection': 'keep-alive',
    'DNT': '1',
    'Host': '202.115.47.141',
    'Upgrade-Insecure-Requests': '1'
}

print(f"{bcolors.HEADER}SCU 抢课脚本: 使用该软件造成的后果与作者无关{bcolors.ENDC}")
time.sleep(1)
print(f"{bcolors.HEADER}当前适配 2026.3.24 版本川大抢课系统{bcolors.ENDC}")
time.sleep(1)
print(f"{bcolors.HEADER}原作者：Junbo2002 当前版本作者：萤朵莉{bcolors.ENDC}")
time.sleep(1)
print(f"{bcolors.HEADER}有不会用的地方可以找作者！！！\n{bcolors.ENDC}")
time.sleep(1)

def get_login_token(session):
    try:
        response = session.get(login_token_url, headers=header)
        token_match = re.search(r'name="tokenValue"\s+value="([a-fA-F0-9]{32})"', response.text)
        if token_match:
            return token_match.group(1)
        else:
            print(f"{bcolors.FAIL}无法从登录页面提取tokenValue{bcolors.ENDC}")
            return None
    except Exception as e:
        print(f"{bcolors.FAIL}获取tokenValue时出错: {str(e)}{bcolors.ENDC}")
        return None


if os.path.exists("config.txt"):
    with open("config.txt", "r", encoding='utf-8') as f:
        info = [line.strip() for line in f.readlines()]
    if len(info) != 7:
        raise RuntimeError("配置文件格式错误，应包含7行：学号、密码、培养计划代码、API Key、课程名称(分号分隔)、课程号(分号分隔)、课序号(分号分隔)")
    j_username = info[0]
    o_password = info[1]
    j_password = encrypo(o_password)
    fajhh = info[2]
    zhipuai_api_key = info[3]
    courseNames = info[4].split(';') if info[4] else []
    courseNums = info[5].split(';') if info[5] else []
    coursekxhNums = info[6].split(';') if info[6] else []
    print(f"{bcolors.OKCYAN}检测到本地配置文件，将使用{bcolors.ENDC}" + j_username + f"{bcolors.OKCYAN}进行选课\n{bcolors.ENDC}")
    time.sleep(1)
    print("开始登录 ^_^\n")
else:
    manchoice = input(f'{bcolors.OKCYAN}\n未检测到本地配置文件，如果你只是想临时使用，请输入 1；如果你想生成一个配置文件以便后续重复使用，请输入 2：{bcolors.ENDC}')
    j_username = input(f'{bcolors.OKGREEN}\n请输入学号：{bcolors.ENDC}')
    o_password = input(f'{bcolors.OKGREEN}\n请输入教务系统密码：{bcolors.ENDC}')
    j_password = encrypo(o_password)
    fajhh = input(f'{bcolors.OKGREEN}\n请输入培养计划代码：（2024级代码改变，可以在手动选课时用 burpsuite 抓包得到 fajhh 的值作为代码）{bcolors.ENDC}')
    zhipuai_api_key = input(f'{bcolors.OKGREEN}\n请输入AI API Key：{bcolors.ENDC}')
    courseNames_input = input(f'{bcolors.OKGREEN}\n请输入课程名称（如果有多个课程，请用分号分隔名称）：{bcolors.ENDC}')
    courseNums_input = input(f'{bcolors.OKGREEN}\n请输入课程号（如果有多个课程，请用分号分隔课程号）：{bcolors.ENDC}')
    coursekxhNums_input = input(f'{bcolors.OKGREEN}\n请输入课序号（如果有多个课程，请用分号分隔课序号）：{bcolors.ENDC}')
    
    courseNames = courseNames_input.split(';') if courseNames_input else []
    courseNums = courseNums_input.split(';') if courseNums_input else []
    coursekxhNums = coursekxhNums_input.split(';') if coursekxhNums_input else []
    
    if manchoice == '2':
        configcontent = [j_username, o_password, fajhh, zhipuai_api_key, courseNames_input, courseNums_input, coursekxhNums_input]
        with open("config.txt", "w", encoding='utf-8') as file:
            for line in configcontent:
                file.write(line + "\n")
        print(f"{bcolors.OKCYAN}\n配置文件已保存至程序同文件夹下的 config.txt 文件中！\n{bcolors.ENDC}")
    # 临时使用，不保存文件
    time.sleep(1)
    print("开始登录 ^_^\n")

def secondAppend(time_str, s):
    cnt = time_str.count(':')
    if cnt == 1:
        time_str += ":"+str(s)
    if cnt > 2:
        raise "时间格式为: %H:%M 或者 %H:%M:%S"
    return time_str

def check():
    if not (len(j_username) == 13 and j_username.isdigit()):
        raise RuntimeError("学号格式错误（学号为13位数字），你是不是输错啦")
    if not fajhh.isdigit():
        raise RuntimeError("方案计划号错误：为纯数字")

try:
    rawnum = "9:30 21:59"
    selectTime = rawnum.strip('\n').split(' ')
    selectTime[0] = secondAppend(selectTime[0], 0)
    selectTime[1] = secondAppend(selectTime[1], 59)
except Exception:
    print("请检查config.txt中是否在第六行以“9:30 21:59”添加了起止时间，中间以空格分隔")

try:
    check()
except RuntimeError as e:
    print("出错啦！错误内容：" + str(e))