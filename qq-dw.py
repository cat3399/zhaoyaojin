import os
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import ddddocr
import re
from multiprocessing import Process, Queue
import websockets
import asyncio
import json
import requests
from pathlib import Path


def process_watch(q_shot: Queue):
    uri = "ws://127.0.0.1:3001/event"

    def get_text(data_json):
        text = ""
        for i in data_json:
            if i['type'] == "text":
                text += i['data']['text']
        commod = ''
        f = '/t'
        if f in text:
            commod = text.replace(f, '')
        commod = commod.strip()
        arg_list = [arg.strip() for arg in commod.split()]
        exp_name = arg_list[0]
        week = arg_list[1]
        pattern1 = r'^实验'
        pattern2 = r'^\d+$'
        if re.match(pattern1, exp_name):
            if re.match(pattern2, week):
                return arg_list
            else:
                print("周次为数字")
        else:
            print("请以实验二字开头")

    async def receive_message(uri, ping_interval=20, ping_timeout=30):
        async with websockets.connect(uri) as ws:
            print('websocket链接成功')

            while True:
                message = await ws.recv()
                data = json.loads(message)
                # data_str = json.dumps(data, indent=4, ensure_ascii=False)
                # print(data_str)

                try:
                    if data['message_type'] == 'group':
                        group_id = data["group_id"]
                        sender_id = data['sender']['user_id']
                        sender_name = data['sender']['card']
                        # print(data)
                        arg_list = get_text(data['message'])
                        # print(data['message'][0]['data'])
                        # print(mesgae_text)
                        # print(data)

                        if arg_list:
                            # print(arg_list)
                            q_shot.put({
                                "exp_name": arg_list[0],
                                "week": arg_list[1],
                                "group_id": group_id,
                                "sender_id": sender_id
                            })
                            print(f'收到群组{group_id} {sender_name} 信息:{arg_list[0], arg_list[1]}')

                except:
                    # print('收到一条无关的信息')
                    # print(data)
                    pass

    asyncio.run(receive_message(uri))


def process_shot(q_shot: Queue, q_send: Queue):
    ocr = ddddocr.DdddOcr(show_ad=False)

    options = webdriver.FirefoxOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument('--lang=zh-CN.UTF-8')    # 初始化WebDriver
    driver = webdriver.Firefox(options=options)
    js_script = """
    (function() {
        'use strict';

        function unhideAndReplace(temp, names) {
            if (temp) {
                let htmltext = temp.innerHTML;
                htmltext = htmltext.replace(/<!--\\s?(.*?)\\s?-->/g, '$1');
                names.forEach(function(name) {
                    const regex = new RegExp(name, 'g');
                    htmltext = htmltext.replace(regex, `${name}（慎选）`);
                });
                // 更新HTML
                temp.innerHTML = htmltext;
            }
        }
        // 四大天王(慢慢更新)
        const namesToReplace = ["李志刚", "刘松江"];

        // 标题栏
        const temp1 = document.querySelector("body > main > div > div.container-fluid > div:nth-child(3) > div > div.panel.panel-primary.filterable > div.panel-body > table > tbody:nth-child(1) > tr");
        unhideAndReplace(temp1, namesToReplace);

        // 内容
        const tbody = document.querySelector("body > main > div > div.container-fluid > div:nth-child(3) > div > div.panel.panel-primary.filterable > div.panel-body > table > tbody:nth-child(2)");
        if (tbody) {
            for (let i = 1; i <= tbody.children.length; i++) {
                const temp = tbody.querySelector(`tr:nth-child(${i})`);
                unhideAndReplace(temp, namesToReplace);
            }
        }
    })();
    """

    def next_get_screenshot(exp_name, week):
        try:
            time1 = time.time()
            wait = WebDriverWait(driver, 15)
            print("jietuzong")
            driver.get(
                f'https://10-235-0-15.webvpn.nepu.edu.cn/experiments?exp_name={exp_name}&half_semi=1&page=1&semi_name=2024-2025&week={week}')
            container = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'container-fluid')))
            driver.execute_script("arguments[0].parentNode.removeChild(arguments[0]);", container)

            table_img = driver.find_element(By.CLASS_NAME, 'panel-body')
            driver.execute_script(js_script)
            driver.execute_script("document.charset='UTF-8';")
            file_name = f'{exp_name}-{week}-20242025-1'
            table_img.screenshot(file_name + '.png')
            time111 = time.time() - time1
            print(f'截图成功,花费{time111}秒')
        except:
            print("截图失败！！！！！！！！")

    def pass_rucaptcha(driver, wait):
        print("dengludawu")
        driver.get('https://10-235-0-15.webvpn.nepu.edu.cn/users/sign_in')
#        print(driver.page_source)
        username_input = wait.until(EC.presence_of_element_located((By.NAME, 'user[account_numb]')))
        passname_input = wait.until(EC.presence_of_element_located((By.NAME, 'user[password]')))
        login_butt = wait.until(EC.presence_of_element_located((By.NAME, 'commit')))
        rucaptcha = wait.until(EC.presence_of_element_located((By.NAME, '_rucaptcha')))
        rucaptcha_image = driver.find_element(By.CLASS_NAME, 'rucaptcha-image')
        username_input.send_keys('学号')
        passname_input.send_keys('大物实验平台密码')
        time.sleep(0.3)
        # 截图
        rucaptcha_image.screenshot('rucaptcha.png')
        print("截图验证码成功")

        start = time.time()
        with open('rucaptcha.png', 'rb') as fp:
            img_byte = fp.read()
        ru_text = ocr.classification(img_byte)
        end = time.time()
        print('识别验证码结果：', ru_text)
        print('识别验证码花费：', end - start)

        # 输入验证码
        rucaptcha.send_keys(ru_text)
        time.sleep(0.3)
        login_butt.click()
        return driver.page_source

    def get_screenshot(exp_name, week):
        # 打开目标网页
        wait = WebDriverWait(driver, 15)
        print("webvpndenglu")
        driver.get('https://webvpn.nepu.edu.cn/users/sign_in')
        if "WebVPN登录问题" in driver.page_source:
            username_input = wait.until(EC.presence_of_element_located((By.NAME, 'user[login]')))
            passname_input = wait.until(EC.presence_of_element_located((By.NAME, 'user[password]')))
            butt = wait.until(EC.presence_of_element_located((By.NAME, 'commit')))
            username_input.send_keys('学号')
            passname_input.send_keys('webvpn密码')
            butt.click()

        retry_num = 0
        while retry_num <= 10:
            if "请输入学号或工号" not in pass_rucaptcha(driver, wait):
                break
            else:
                retry_num += 1
                print(f"第{retry_num}次识别错误")
                print()
        driver.get(
            f'https://10-235-0-15.webvpn.nepu.edu.cn/experiments?exp_name={exp_name}&half_semi=1&page=1&semi_name=2024-2025&week={week}')
        container = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'container-fluid')))
        driver.execute_script("arguments[0].parentNode.removeChild(arguments[0]);", container)

        table_img = driver.find_element(By.CLASS_NAME, 'panel-body')
        driver.execute_script(js_script)
        driver.execute_script("document.charset='UTF-8';")
        file_name = f'{exp_name}-{week}-20242025-1'
        table_img.screenshot(file_name + '.png')
        # time.sleep(5)
        print("截图成功！")

    def work_bu_queue():
        while True:
            arg_json = q_shot.get()
            # print(arg_json)
            driver.get("https://10-235-0-15.webvpn.nepu.edu.cn/")
            if "您的课堂实验临时成绩为" in driver.page_source:
                print('已登陆')
                next_get_screenshot(arg_json["exp_name"], arg_json["week"])
            else:
                print('实验平台未登录，正在登录')
                get_screenshot(arg_json["exp_name"], arg_json["week"])
            q_send.put(arg_json)

    work_bu_queue()


def process_end(q_send: Queue):
    def send_img(g_id, png_name, s_id: int):
        url = "http://127.0.0.1:3000/send_group_msg"
        file_path = Path(f"/app/qq/{png_name}")
#        print(file_path)
        file_uri = file_path.as_uri()
        message_qc = f"[CQ:image,file={file_uri}]"
        r = requests.post(url=url, params={
            "group_id": group_id,
            "message": message_qc,
            "auto_escape": True
        })
        print(r.text)
    while True:
        arg_json = q_send.get()
        group_id = arg_json["group_id"]
        exp_name = arg_json["exp_name"]
        week = arg_json["week"]
        sender_id = arg_json["sender_id"]
        file_name = f"{exp_name}-{week}-20242025-1.png"
        if file_name in os.listdir(os.getcwd()):
            send_img(group_id, file_name, sender_id)
            print("发送成功")


if __name__ == "__main__":
    queue_shot = Queue()
    queue_send = Queue()
    p1 = Process(target=process_watch, args=(queue_shot,))
    p2 = Process(target=process_shot, args=(queue_shot, queue_send))
    p3 = Process(target=process_end, args=(queue_send,))
    p1.start()
    p2.start()
    p3.start()
    p1.join()
    p2.join()
    p3.join()
