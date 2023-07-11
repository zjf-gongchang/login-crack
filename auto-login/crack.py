import os
import json
import numpy as np
import math
import random
import time
from io import BytesIO
from PIL import Image
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# 该URL地址是需要破解登录的地址，根据实际情况更换，这里暂且指定到极验官网
url = 'https://www.geetest.com/Register'
images = './images/'

sliding_block_init_left_offset=16
sliding_block_init_right_offset=70
pixel_equal_threshold = 60


class CrackLogin():
    def __init__(self):
        self.browser = webdriver.Chrome()
        self.wait = WebDriverWait(self.browser, 20)

    def __del__(self):
        try:
            self.browser.close()
        except Exception:
            print('浏览器关闭异常')   

    def start(self, username, password):
        """
        打开登录界面，输入用户名和密码
        :return: None
        """
        print(username)
        self.browser.get(url)
        username_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[formcontrolname="userName"]')))
        password_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[formcontrolname="password"]')))
        time.sleep(1)
        username_input.send_keys(username)
        time.sleep(2)
        password_input.send_keys(password)
        time.sleep(1)            

    def click_verification_code_button(self):
        """
        点击验证码按钮
        """
        button = self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'geetest_radar_btn')))
        button.click()
        
    def get_verification_code_image(self, name='captcha.png', imgtype='验证码图片'):
        """
        获取验证码图片
        :return: 图片对象
        """
        top, bottom, left, right = self.get_verification_code_position()
        print('获取'+imgtype+'，位置：', top, bottom, left, right)
        screenshot = self.get_browser_screenshot()
        captcha = screenshot.crop((left, top, right, bottom))
        captcha.save(images+name)
        return captcha

    def get_verification_code_position(self):
        """
        获取验证码图片位置
        :return: 验证码图片位置的元组
        """
        img = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'geetest_popup_box')))
        time.sleep(2)
        location = img.location
        size = img.size
        #top, bottom, left, right = location['y']+50, location['y'] + size['height']+50, location['x']+95, location['x'] + size['width']+165
        top, bottom, left, right = location['y'], location['y'] + size['height'], location['x'], location['x'] + size['width']
        return (top, bottom, left, right)

    def get_browser_screenshot(self):
        """
        获取浏览器网页截图
        :return: 浏览器网页截图
        """
        browser_screenshot = self.browser.get_screenshot_as_png()
        browser_screenshot = Image.open(BytesIO(browser_screenshot))
        return browser_screenshot
        
    def get_gap_left_offset(self, image_full, image_gap):
        """
        获取缺口的左偏移量
        :param image_full: 完整图片
        :param image_gap: 带缺口图片
        :return:
        """
        left=sliding_block_init_right_offset
        for i in range(left, image_full.size[0]):
            for j in range(image_full.size[1]):
                if not self.is_pixel_equal_in_threshold(image_full, image_gap, i, j):
                    left = i
                    return left
        return left
        
    def is_pixel_equal_in_threshold(self, image_full, image_gap, x, y):
        """
        判断两个像素是否在阈值范围内
        :param image_full: 完整图片
        :param image_gap: 带缺口图片
        :param x: 位置x
        :param y: 位置y
        :return: 像素相同返回True，否则返回False
        """
        pixel1 = image_full.load()[x, y]
        pixel2 = image_gap.load()[x, y]
        if abs(pixel1[0] - pixel2[0]) < pixel_equal_threshold and abs(pixel1[1] - pixel2[1]) < pixel_equal_threshold and abs(pixel1[2] - pixel2[2]) < pixel_equal_threshold:
            return True
        else:
            return False
      
    def ease_out_quad(self, x):
        """
        第一种滑动轨迹
        """
        return 1 - (1 - x) * (1 - x)
 
    def ease_out_quart(self, x):
        """
        第二种滑动轨迹
        """
        return 1 - pow(1 - x, 4)
     
    def ease_out_expo(self, x):
        """
        第三种滑动轨迹
        """
        if x == 1:
            return 1
        else:
            return 1 - pow(2, -10 * x)
     
    def get_slide_tracks(self, distance, seconds, ease_func_name):
        """
        获取滑动轨迹
        :return: 滑块轨迹
        """
        print('使用函数['+ease_func_name+']生成滑动轨迹')
        tracks = [0]
        offsets = [0]
        for t in np.arange(0.0, seconds, 0.1):
            if ease_func_name=='ease_out_quad':
                offset = round(self.ease_out_quad(t/seconds) * distance)
            elif ease_func_name=='ease_out_quart':
                offset = round(self.ease_out_quart(t/seconds) * distance)
            elif ease_func_name=='ease_out_expo':
                # 经过测试该条轨迹函数是最准确的方式，不容易被检测到
                offset = round(self.ease_out_expo(t/seconds) * distance)
            else:
                offset = round(self.ease_out_expo(t/seconds) * distance)
            tracks.append(offset - offsets[-1])
            offsets.append(offset)
        return offsets, tracks    

    def get_slider(self):
        """
        获取滑块对象
        :return: 滑块对象
        """
        slider = self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'geetest_slider_button')))
        return slider

    def move_to_gap_left_offest(self, slider, track):
        """
        滑动滑块到缺口左偏移量处
        :param slider: 滑块
        :param track: 轨迹
        :return:
        """
        ActionChains(self.browser).click_and_hold(slider).perform()
        offset=0
        for x in track:
            offset+=x
            ActionChains(self.browser).move_by_offset(xoffset=x, yoffset=0).perform()
        print('滑块滑动偏移量：', offset)
        ActionChains(self.browser).pause(0.5).release().perform()

    def login(self):
        """
        登录
        :return: None
        """
        submit = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[class="login-form-button ant-btn ant-btn-primary"]')))
        submit.click()
        time.sleep(10)
        
    def change_verification_img_display_attr(self, display):
        """
        改变验证码图片的display属性，以便能够获取到两种验证码图片
        :return:
        """
        js_code = "document.getElementsByClassName('geetest_canvas_fullbg')[0].style.display='{}'".format(display)
        self.browser.execute_script(js_code)        
        
    def cut_out_img(self, img, offset):
        """
        从指定的偏移量截取图片，并保存
        :return: None
        """
        size = img.size
        top, bottom, left, right = 0, size[1], offset, size[0]
        temp_img=img.crop((left, top, right, bottom))
        temp_img.save(images+'temp_img.png')

    def crack(self, username, password):
        try:
            # 浏览器中打开登录页，输入用户名密码
            self.start(username, password)
            
            # 点击验证按钮
            self.click_verification_code_button()
            
            # 获取带缺口的验证码图片
            image_gap = self.get_verification_code_image('captcha_gap.png', '缺口验证码图片')
            # 修改验证码图片部分display属性为block
            self.change_verification_img_display_attr('block')
            # 获取完整的验证码图片
            image_full = self.get_verification_code_image('captcha_full.png', '完整验证码图片')
            # 恢复验证码图片部分display属性为none
            self.change_verification_img_display_attr('none')
            
            # 获取缺口左偏移量
            gap_offset = self.get_gap_left_offset(image_full, image_gap)
            # 从缺口左偏移量开始截取图片并保存（这一步骤只是用来查看偏移量计算的正确性）
            self.cut_out_img(image_gap, gap_offset)
            # 减去缺口左边位移
            slide_offset = gap_offset-sliding_block_init_left_offset
            
            # 获取滑动轨迹
            track_func_name_arr=['ease_out_quad', 'ease_out_quart', 'ease_out_expo']
            track_func_name=track_func_name_arr[random.randint(0,len(track_func_name_arr)-1)]
            offsets, track = self.get_slide_tracks(slide_offset, 2, track_func_name)
            print('获取滑动轨迹：', track)
            
            # 获取滑块
            slider = self.get_slider()
            
            # 拖动滑块
            print('滑块初始偏移量：', sliding_block_init_left_offset)
            self.move_to_gap_left_offest(slider, track)

            success=False
            try:
                success = self.wait.until(EC.text_to_be_present_in_element((By.CLASS_NAME, 'geetest_success_radar_tip_content'), '验证成功'))
            except Exception as e:
                print('获取验证结果超时')
            
            # 失败后重试
            if not success:
                print('滑动验证失败')
                result={"status":1,"cookie":""}
                return result
            else:
                print('滑动验证成功')
                self.login()
                print('登录成功')
                
                # 这里只获取cookie中的部分键值对，可以根据需要提取有用的信息
                time.sleep(3)
                www_json=self.browser.get_cookie('www')
                ws_key_json=self.browser.get_cookie('WS_KEY')
                cookie='www='+www_json['value']+'; WS_KEY='+ws_key_json['value']
                print('获取到cookie信息：' ,cookie)
                
                result={"status":0,"cookie":cookie}
                return result
        except Exception as e:
            print(e)
            print('登录程序异常')  
            result={"status":-1,"cookie":""}
            return result
       

if __name__ == '__main__':
    print('进入登录入口')
    crack = CrackLogin()
    result=crack.crack('test', 'test123')
    print('Cookie信息：', result)