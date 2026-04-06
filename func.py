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

import ast
import json
import random
import re
import time
import requests
import base64
import webbrowser
from PIL import Image
from config import *
from zai import ZhipuAiClient
 # 导入GLM-4 SDK

redis_key_re = re.compile('redisKey.*?\"(?P<redisKey>.*?)\"', re.S)

def download_captcha(session, url):
    """下载验证码图片到本地"""
    response = session.get(url, headers=header)
    with open("captcha.jpg", "wb") as f:
        f.write(response.content)
    return "captcha.jpg"

def recognize_captcha_by_glm(image_path):
    """使用GLM-4 API识别验证码"""
    client = ZhipuAiClient(api_key=zhipuai_api_key)  # 从config导入API密钥
    
    try:
        # 读取图片并转换为base64
        with open(image_path, "rb") as image_file:
            base64_data = base64.b64encode(image_file.read()).decode('utf-8')
        
        # 构建消息格式
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "请识别图片中的验证码文字，只返回纯文本验证码内容，不要包含任何其他文字或解释。"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_data}"
                        }
                    }
                ]
            }
        ]
        
        # 调用GLM-4 API
        response = client.chat.completions.create(
            model="GLM-4v-flash",  
            messages=messages,
            max_tokens=10,
        )
        
        # 提取并清理识别结果
        captcha_text = response.choices[0].message.content.strip()
        # print(captcha_text)
        # 去除可能的非验证码字符
        captcha_text = re.sub(r'[^a-zA-Z0-9]', '', captcha_text)
        
        print(f"{bcolors.OKCYAN}GLM-4识别结果: {captcha_text}{bcolors.ENDC}")
        return captcha_text
    except Exception as e:
        print(f"{bcolors.FAIL}验证码识别失败: {str(e)}{bcolors.ENDC}")
        return None

# 选课界面
def login(session):
    print(f"{bcolors.OKCYAN}正在获取登录token...{bcolors.ENDC}")
    login_token = get_login_token(session)
    if not login_token:
        print(f"{bcolors.FAIL}无法获取登录token，登录失败{bcolors.ENDC}")
        return "failed"
    
    # 下载验证码图片
    print(f"{bcolors.OKCYAN}正在获取验证码...{bcolors.ENDC}")
    captcha_path = download_captcha(session, captcha_url)
    # open(captcha_path)
    # 使用GLM-4识别验证码
    captcha_code = recognize_captcha_by_glm(captcha_path)
    if not captcha_code:
        print(f"{bcolors.FAIL}验证码识别失败，请手动检查{bcolors.ENDC}")
        return "failed"
    
    login_data = {
        "tokenValue": login_token,
        'j_username': j_username,
        'j_password': j_password,
        'j_captcha': captcha_code
    }
    
    print(f"{bcolors.OKCYAN}登录信息: 学号={j_username}, 验证码={captcha_code}{bcolors.ENDC}")
    
    try:
        response = session.post(url=login_url, headers=header, data=login_data)
        response_text = response.text
        
        print(f"{bcolors.OKCYAN}登录响应状态码: {response.status_code}{bcolors.ENDC}")
        
        # 保存登录响应用于调试
        with open("login_response.html", "w", encoding="utf-8") as f:
            f.write(response_text)
        
        # 检查是否需要关闭公告
        if "选课公告" in response_text or "选课安排" in response_text:
            print(f"{bcolors.OKCYAN}检测到选课公告页面，尝试关闭公告...{bcolors.ENDC}")
            
            # 尝试访问首页关闭公告
            home_response = session.get(index_url, headers=header)
            
            # 检查关闭后是否成功进入系统
            if "欢迎您" in home_response.text:
                print(f"{bcolors.OKGREEN}登录成功！{bcolors.ENDC}")
                return "success"
            else:
                print(f"{bcolors.WARNING}关闭公告后仍未进入系统{bcolors.ENDC}")
        
        # 直接登录成功的情况
        if "欢迎您" in response_text:
            print(f"{bcolors.OKGREEN}登录成功！{bcolors.ENDC}")
            return "success"
        
        # 其他错误情况
        if "用户密码错误" in response_text:
            print(f"{bcolors.FAIL}登录失败: 用户名或密码错误{bcolors.ENDC}")
        elif "验证码错误" in response_text:
            print(f"{bcolors.FAIL}登录失败: 验证码错误{bcolors.ENDC}")
            # 验证码错误时自动重试
            return login(session)
        elif "token校验失败" in response_text:
            print(f"{bcolors.FAIL}登录失败: token校验失败{bcolors.ENDC}")
        else:
            print(f"{bcolors.FAIL}登录失败: 未知原因{bcolors.ENDC}")
            
        return "failed"
    except Exception as e:
        print(f"{bcolors.FAIL}登录请求异常: {str(e)}{bcolors.ENDC}")
        return "failed"


# 获取已选课程
def get_already_course(session):
    already_select_course_list = []
    try:
        response = session.get(url=already_select_course_url, headers=header).text
        for each in json.loads(response)['xkxx'][0]:
            already_select_course_list.append(json.loads(response)['xkxx'][0][each]['courseName'])
        return already_select_course_list
    except Exception as e:
        print(f"{bcolors.FAIL}获取已选课程出错: {str(e)}{bcolors.ENDC}")

# 选课
def course_select(session, each_course, alreadySelectCourse, courseName, courseNum, coursekxhNum):
    """
    执行单门课程选课操作
    :param session: requests会话
    :param each_course: 课程信息字典（包含kcm, kch, kxh, bkskyl, skjs等）
    :param alreadySelectCourse: 已选课程名列表
    :param courseName: 待选课程名称
    :param courseNum: 待选课程号
    :param coursekxhNum: 待选课序号（可能多个，空格分隔）
    :return: True/False 表示是否选课成功
    """
    # 检查课程是否已选，以及课程号/课序号是否匹配
    if courseName not in alreadySelectCourse and courseNum == each_course['kch'] and each_course['kxh'] in coursekxhNum.split():
        
        # 显示课程信息
        print(each_course['bkskyl'])
        if each_course['bkskyl'] <= 0:
            print(f"{bcolors.WARNING}课程名:{each_course['kcm']} 课序号:{each_course['kxh']} 教师:{each_course['skjs']} 课余量:{each_course['bkskyl']}{bcolors.ENDC},本课程暂时没有课余量")
            return False
        else:
            print(f"{bcolors.OKGREEN}课程名:{each_course['kcm']} 课序号:{each_course['kxh']} 教师:{each_course['skjs']} 课余量:{each_course['bkskyl']}{bcolors.ENDC}")
        
        # 调用教师查询接口（可能用于反爬，保留）
        kch = each_course['kch']
        kxh = each_course['kxh']
        status = queryTeacherJL(session, kch, kxh)
        if status is None:
            return False
        
        # 获取课程名编码（Unicode逗号分隔）
        kcms = getKcms(each_course['kcm'])
        
        # 构造课程标识：课程号_课序号_学期
        course_id = f"{kch}_{kxh}_{selectcourse_xueqi}"
        
        # 获取选课页面token和验证码需求
        tokenValue, need_captcha = get_token_and_captcha(session)
        if tokenValue is None:
            return False
        
        # 构造选课提交数据
        select_data = {
            'dealType': 3,
            'kcIds': course_id,
            'kcms': kcms,
            'fajhh': fajhh,
            'sj': '0_0',
            'searchtj': courseName,
            'kclbdm': '',
            'kclbdm2': '',
            'tokenValue': tokenValue
        }
        
        # 如果需要验证码，获取并识别
        if need_captcha:
            captcha_path = download_captcha(session, select_captcha_url)
            code = recognize_captcha_by_glm(captcha_path)
            if not code:
                print(f"{bcolors.FAIL}选课验证码识别失败，跳过本次尝试{bcolors.ENDC}")
                return False
            print(f'{bcolors.OKCYAN}识别的选课验证码:{code}{bcolors.ENDC}')
            select_data["inputCode"] = code
        else:
            select_data["inputCode"] = "undefined"
        
        # 提交选课请求
        submit_url = "http://202.115.47.141/student/courseSelect/selectCourse/checkInputCodeAndSubmit"
        try:
            response = session.post(url=submit_url, data=select_data)
            print(f"{bcolors.OKCYAN}选课响应状态码: {response.status_code}{bcolors.ENDC}")
            response_json = response.json()
            print(f"{bcolors.OKCYAN}选课响应内容: {response_json}{bcolors.ENDC}")
            
            # 检查提交结果
            result = response_json.get("result")
            if result != "ok":
                print(f"{bcolors.WARNING}选课提交失败: {result}{bcolors.ENDC}")
                return False
            
            # 获取服务器返回的redisKey
            redis_key = response_json.get("redisKey")
            if not redis_key:
                print(f"{bcolors.FAIL}选课响应中未包含redisKey{bcolors.ENDC}")
                return False
            
            # 轮询查询选课结果
            query_url = "http://202.115.47.141/student/courseSelect/selectResult/query"
            query_data = {
                "kcNum": 1,          # 每次只选一门课，固定为1
                "redisKey": redis_key
            }
            
            max_attempts = 10
            for attempt in range(max_attempts):
                time.sleep(1)  # 间隔1秒查询一次
                try:
                    query_resp = session.post(query_url, data=query_data)
                    query_json = query_resp.json()
                    print(f"{bcolors.OKCYAN}查询结果第{attempt+1}次: {query_json}{bcolors.ENDC}")
                    
                    # 检查是否完成
                    if query_json.get("isFinish"):
                        result_list = query_json.get("result", [])
                        # result 结构：["", "课程标识: 选课成功！"]
                        if len(result_list) > 1 and result_list[1]:
                            msg = result_list[1]
                            if "选课成功" in msg:
                                print(f"{bcolors.OKGREEN}选课成功！{bcolors.ENDC}")
                                return True
                            else:
                                print(f"{bcolors.WARNING}选课失败: {msg}{bcolors.ENDC}")
                                return False
                        else:
                            # 可能结果为空，继续等待
                            continue
                except Exception as e:
                    print(f"{bcolors.FAIL}查询选课结果异常: {e}{bcolors.ENDC}")
                    continue
            
            print(f"{bcolors.WARNING}选课结果查询超时{bcolors.ENDC}")
            return False
            
        except Exception as e:
            print(f"{bcolors.FAIL}选课请求异常: {str(e)}{bcolors.ENDC}")
            import traceback
            traceback.print_exc()
            return False
    
    return False
# 获取选课token和选课是否需要验证码
def get_token_and_captcha(session):
    try:
        response = session.get(url=course_select_url, headers=header).text
        
        # 新的验证码需求判断逻辑
        flag = False
        # 检查是否存在验证码区域且未被隐藏
        if 'id="yzm_area"' in response:
            # 检查是否未设置display:none
            if 'style="display: none;"' not in response:
                flag = True
            # 或者直接检查是否有验证码图片
            if '/student/courseSelect/selectCourse/getYzmPic' in response:
                flag = True
        
        # 提取tokenValue（使用之前修改的正则）
        token_match = re.search(r'id="tokenValue"\s+value="([a-fA-F0-9]{32})"', response)
        if token_match:
            token_value = token_match.group(1)
            return token_value, flag
        else:
            # 添加详细调试信息
            print(f"{bcolors.FAIL}无法从选课页面提取tokenValue{bcolors.ENDC}")
            print(f"{bcolors.WARNING}页面标题: {re.search('<title>(.*?)</title>', response).group(1) if re.search('<title>', response) else '无标题'}{bcolors.ENDC}")
            return None, flag
    except Exception as e:
        print(f"{bcolors.FAIL}获取选课token出错: {str(e)}{bcolors.ENDC}")
        return None, False
# 课程名编码
def getKcms(kms):
    kcms = ""
    for each in kms:
        kcms += str(ord(each)) + ","
    return kcms

# 查询课程课余量
def get_free_course_list(session, courseName):
#这是一个失效的函数，会无视 courseName 返回所有课程的列表，但后面直接基于这个特性（bug）（其实是不想修）完成了代码，所以在弄清原理前不要动(
    list_data = {
        'searchtj': courseName,
        'xq': 0,
        'jc': 0,
        'kclbdm': ""
    }
    try:
        response = session.post(url=courseList_url, headers=header, data=list_data).content.decode()
        # print(response)
        return json.loads(response)['rwRxkZlList']
    except Exception as e:
        print(f"{bcolors.FAIL}查询课程列表出错: {str(e)}{bcolors.ENDC}")

# （可能）教务处反爬机制
def queryTeacherJL(session, kch, kxh):
    data = {
        "id": selectcourse_xueqi + "@" + kch + "@" + kxh
    }
    try:
        response = session.post(url=queryTeacherJL_url, data=data, headers=header).content.decode()
        if response:
            return response
    except Exception as e:
        print(f"{bcolors.FAIL}查询教师信息出错: {str(e)}{bcolors.ENDC}")
        return None

# 定时选课
def isSelectTime() -> bool:
    Now = time.strftime("%H:%M:%S", time.localtime())
    Now_time = date.datetime.strptime(Now,'%H:%M:%S')
    toSelect_0 = date.datetime.strptime(selectTime[0], '%H:%M:%S')
    toSelect_1 = date.datetime.strptime(selectTime[1], '%H:%M:%S')
    return (Now_time>toSelect_0) and (Now_time < toSelect_1)

# 更新课程情况，去除已经选择的课程
def updateCourse(select_course_idx):
    if len(select_course_idx) == 0:
        return
    global courseNames
    global courseNums
    global coursekxhNums
    new_courseNames = []
    new_courseNums = []
    new_coursekxhNums = []

    for i in range(len(courseNames)):
        if i in select_course_idx:
            continue
        new_courseNames.append(courseNames[i])
        new_courseNums.append(courseNums[i])
        new_coursekxhNums.append(coursekxhNums[i])

    courseNames = new_courseNames
    courseNums = new_courseNums
    coursekxhNums = new_coursekxhNums

def main(session):
    cnt = 1
    while cnt <= 3:  # 限制登录尝试次数
        loginResponse = login(session)
        if loginResponse == "success":
            while not isSelectTime():
                current_time = str(date.datetime.now().time()).split('.')[0]
                print(f"{bcolors.WARNING}当前时间: {current_time} 在非设置选课时间{bcolors.ENDC}")
                
                # 计算距离选课开始时间
                now_time = date.datetime.strptime(time.strftime("%H:%M:%S", time.localtime()),'%H:%M:%S')
                start_time = date.datetime.strptime(selectTime[0],'%H:%M:%S')
                expireSeconds = (start_time - now_time).seconds
                
                if expireSeconds > 0:
                    print(f"{bcolors.OKCYAN}将在 {expireSeconds} 秒后开始抢课...{bcolors.ENDC}")
                    time.sleep(min(expireSeconds, 60))  # 最多等待60秒
                else:
                    break
            print(f"{bcolors.OKGREEN}抢课开始！ *_*{bcolors.ENDC}")
            break
        else:
            print(f"{bcolors.FAIL}第{cnt}次登录失败{bcolors.ENDC}")
            cnt += 1
            time.sleep(2)  # 登录失败后等待2秒再重试

    if cnt > 3:
        print(f"{bcolors.FAIL}登录失败，请检查学号密码正确性{bcolors.ENDC}")
        return

    clock = 1
    while True:
        print(f"{bcolors.OKCYAN}\n正在第{clock}轮选课！{bcolors.ENDC}")
        alreadySelectCourse = get_already_course(session)
        if alreadySelectCourse is None:
            time.sleep(0.5)
            continue

        select_course_idx = []
        for i in range(len(courseNames)):
            if courseNames[i] in alreadySelectCourse:
                select_course_idx.append(i)
                print(f"{bcolors.OKGREEN}你已经选上了 {courseNames[i]} ！{bcolors.ENDC}")
        updateCourse(select_course_idx)
        if len(courseNames) == 0:
            print(f"{bcolors.OKGREEN}选课完成 ^.^{bcolors.ENDC}")
            exit()
        # print(len(courseNames))
        # print(courseNames)
        # 在 main 函数中，登录成功后，选课循环开始前，一次性获取所有课程列表
        # 注意：假设 get_free_course_list 内部使用 searchtj 但实际返回所有课程，我们这里用空字符串或固定值尝试
        # 为了保险，可以传入一个通用的课程名（比如空字符串）来获取所有课程
        all_courses = get_free_course_list(session, "")  # 尝试传空字符串获取所有课程
        if all_courses is None:
            print(f"{bcolors.FAIL}获取课程列表失败{bcolors.ENDC}")
            return

        # 将课程列表转换为按课程名索引的字典，方便快速过滤
        print(time.time())
        unique_courses = {}
        for each_course in all_courses:
            key = (each_course['kch'], each_course['kxh'])
            if key not in unique_courses:
                unique_courses[key] = each_course
        all_courses = list(unique_courses.values())
        courses_by_name = {}
        for course in all_courses:
            name = course['kcm']
            if name not in courses_by_name:
                courses_by_name[name] = []
            courses_by_name[name].append(course)
        print(time.time())
        # time.sleep(10)
        # ... 获取已选课程 ...
        for i in range(len(courseNames)):
            course_name = courseNames[i]
            # 从预先获取的字典中取出该课程的列表
            if course_name not in courses_by_name:
                print(f"{bcolors.WARNING}未找到课程 {course_name}{bcolors.ENDC}")
                continue
            courseList = courses_by_name[course_name]
            # 筛选有余量的
            available_courses = [c for c in courseList if c.get('bkskyl', 0) > 0]
            if not available_courses:
                print(f"{bcolors.WARNING}课程 {course_name} 课程号{courseNums[i]} 课序号{coursekxhNums[i]} 当前无课余量，跳过{bcolors.ENDC}")
                continue
            # 对每个有余量的课序号尝试选课
            for each_course in available_courses:
                if course_select(session, each_course, alreadySelectCourse,
                                course_name, courseNums[i], coursekxhNums[i]):
                    break
            time.sleep(random.uniform(0.5, 1))
    # ... 循环控制 ...

        clock += 1