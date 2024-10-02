# from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.common.exceptions import *
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from seleniumbase import Driver
import time, random, requests, csv, string, json, re,sys
from faker import Faker
from datetime import datetime
from fake_useragent import UserAgent
def readfile(name_file):
    with open(f"data/{name_file}",'r') as file:
        isi_file = file.read()
        print(f"Api: {isi_file}")
        return isi_file

# providers = int(input("0 = Siotp\n1 = tokoclaude\nPilih = "))
providers = int(1)
api = str(readfile("api.txt"))
fake = Faker()
def change_status(status_id, order_id):
    if providers == 0:
        while True:
            response = requests.get(f'https://siotp.com/api/changestatus?apikey={api}&id={order_id}&status={status_id}', timeout=20)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    return True
                else:
                    print("Response status is not 'success'.")
            else:
                print(f"Failed to get data. Status code: {response.status_code}")
    elif providers == 1:
        while True:
            response = requests.get(f'https://tokoclaude.com/api/resend-order/ddbbf23ae4791048e8d82f42af3ad3a5/{order_id}', timeout=20)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    print(data)
                    return True
                else:
                    print("Response status is not 'success'.")
            else:
                print(f"Failed to get data. Status code: {response.status_code}")
            
def get_phone():
    if providers == 1:
        while True:
            response = requests.get(f'https://tokoclaude.com/api/set-orders/{api}/965',timeout=20)
            if response.status_code == 201:
                data = response.json()
                if data.get('success') == True:
                    order_ids = data['data']['data'].get('order_id')
                    numbers = data['data']['data'].get('number')
                    if numbers.startswith("0"):
                        number = f"62{numbers[1:]}"
                    return order_ids, number
                else:
                    print(data)
            time.sleep(2)
    elif providers == 0:
        while True:
            response = requests.get(f'https://api.siotp.com/api/order?apikey={api}&service=2&operator=axis&country=1', timeout=20)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    order_ids = data.get('id')
                    numbers = data.get('number')
                    return order_ids, numbers
                else:
                    print("Response status is not 'success'.")
            else:
                print(f"Failed to get data. Status code: {response.status_code}")
            time.sleep(2)

def get_inbox(id_order):
    if providers == 1:
        url = f'https://tokoclaude.com/api/get-orders/{api}/{id_order}'
        start_time = time.time()
        timeout_duration = 2 * 60
        while True:
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout_duration:
                print("Timeout reached. No SMS received within 2 minutes.")
                return False, 0
            response = requests.get(url)
            if response.status_code == 201:
                data = response.json()
                if data.get('success') == True:
                    order_data = data["data"]["data"][0]
                    if order_data.get("status_sms") == "1":
                        sms_data = json.loads(order_data.get("sms", "[]"))
                        if sms_data:
                            sms_data.sort(key=lambda x: datetime.strptime(x["date"], '%Y-%m-%d %H:%M:%S'), reverse=True)
                            latest_sms = sms_data[0]["sms"]
                            print(f"Latest SMS: {latest_sms}")
                            otp = re.search(r'\b\d{6}\b', latest_sms)
                            if otp:
                                return True, otp.group()
                        else:
                            print("No SMS data found. Retrying...")
                    else:
                        print("Both conditions (status_sms == 1 and status == 3) not met yet. Retrying...")
            else: 
                print(f"Failed to get data. Status code: {response.status_code}. Retrying...")
            time.sleep(5)
    elif providers == 0:
        url = f'https://siotp.com/api/getotp?apikey={api}&id={id_order}'
        start_time = time.time()
        timeout_duration = 2 * 60
        while True:
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout_duration:
                print("Timeout reached. No SMS received within 2 minutes.")
                return False, 0
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    data_content = data.get('data', {})
                    if data_content.get('status') == '3':
                        otp_message = data_content.get('inbox')
                        change_status(2, id_order)
                        sys.stdout.write(f"\rotp: {otp_message}\n")
                        sys.stdout.flush()
                        return True, otp_message
                    else:
                        sys.stdout.write("\rRetive OTP")
                        sys.stdout.flush()
                        time.sleep(1)
                else:
                    print("Response status is not 'success'. Retrying...")
                    time.sleep(5)
            else:
                print(f"Failed to get data. Status code: {response.status_code}. Retrying...")
                time.sleep(5)

def cancel_order(id_order):
    url = f'https://tokoclaude.com/api/cancle-orders/{api}/{id_order}'
    response = requests.get(url)
    data = response.json()
    return data

def get_balance():
    if providers == 1:
        while True:
            print(api)
            response = requests.get(f'https://tokoclaude.com/api/get-profile/{api}',timeout=20)
            if response.status_code == 201:
                data = response.json()
                if data.get('success') == True:
                    username = data['data']['data'].get('username')
                    saldo = data['data']['data'].get('saldo')
                    return username, saldo                
                else:
                    print(data)
            time.sleep(2)
    elif providers == 0:
        while True:
            response = requests.get(f'https://api.siotp.com/api/getbalance?apikey={api}', timeout=20)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    saldo = data.get('balance')
                    username ="unknow"
                    return username, saldo
                else:
                    print("Response status is not 'success'.")
            else:
                print(f"Failed to get data. Status code: {response.status_code}")
            time.sleep(2)

def wait_and_click(driver, css_selector):
    try:
        element = WebDriverWait(driver, 10).until(  # Menunggu elemen sampai muncul (default 10 detik)
            EC.element_to_be_clickable((By.CSS_SELECTOR, css_selector))
        )
        element.click()  # Klik elemen setelah valid
    except TimeoutException:
        print("Element tidak ditemukan atau tidak bisa diklik.")

def wait_and_send(driver, css_selector, action):
    try:
        element = WebDriverWait(driver, 10).until(  # Menunggu elemen sampai muncul (default 10 detik)
            EC.element_to_be_clickable((By.CSS_SELECTOR, css_selector))
        )
        element.send_keys(action)  # Klik elemen setelah valid
    except TimeoutException:
        print("Element tidak ditemukan atau tidak bisa di send.")

def main():
    print(api)
    while True:
        ortua = str(input("Email Ortu: "))
        pilih = int(input("new number (0 = nomer lama / 1 = nomer baru) : "))
        # try:
        print("==========================================================")
        username, saldo = get_balance()
        print(f"Username : {username}")
        print(f"Balance  : {saldo}")
        print("==========================================================")
        print(UserAgent().random)
        driver = Driver(uc=True,agent="Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36")
        driver.delete_all_cookies()
        max_retries = 5
        attempt = 0
        while attempt <= max_retries:
            if pilih == 0 : 
                order_id = str(input("order_id : "))
                phone_number = str(input("phone_number : "))
                otp_code = None
                otp_code_2 = None
            elif pilih == 1 :
                order_id = None
                phone_number = None
                otp_code = None
                otp_code_2 = None
            driver.get('https://myaccount.google.com/security')
            print("Login Email...")
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#yDmH0d > c-wiz > div > div:nth-child(2) > div > c-wiz > c-wiz > div > div.s7iwrf.gMPiLc.Kdcijb > div > div > c-wiz > section > div > div > div > div > div > div > header > div.m6CL9 > div'))).click()
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.NAME, 'identifier'))).send_keys(ortua)
            print("Email : "+"email")
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#identifierNext > div > button'))).click()
            time.sleep(5)
            try:
                WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#password > div.aCsJod.oJeWuf > div > div.Xb9hP > input'))).send_keys("123456tujuh")
                print("Password : "+"password")
                WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#passwordNext > div > button'))).click()
                
                # try:
                #     print("Checking Recovery Email")
                #     WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#yDmH0d > c-wiz > div > div.UXFQgc > div > div > div > form > span > section:nth-child(2) > div > div > section > div > div > div > ul > li:nth-child(3) > div'))).click()
                #     WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#knowledge-preregistered-email-response'))).send_keys(recovery_login)
                #     WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#yDmH0d > c-wiz > div > div.JYXaTc.lUWEgd > div > div.TNTaPb > div > div > button'))).click()
                # except:
                #     print("No Recovery")
                break
            except:
                print("Captcha Require, Next Email...\n======================================")
                attempt += 1
                if attempt > max_retries:
                    print("Max login attempts reached. Moving to the next email.")
                    break
        time.sleep(3)
        driver.get("https://myaccount.google.com/signinoptions/recoveryoptions?opendialog=collectphone")
        if phone_number == None:
            order_id, phone_number = get_phone()
        wait_and_send(driver, "#c6", phone_number)
        wait_and_click(driver, "#yDmH0d > div.uW2Fw-Sx9Kwc.uW2Fw-Sx9Kwc-OWXEXe-n2to0e.iteLLc.uW2Fw-Sx9Kwc-OWXEXe-FNFY6c > div.uW2Fw-wzTsW > div > div.uW2Fw-T0kwCb > div.qsqhnc > div > button")
        max_loop = 10
        h_done = False
        inc = 0
        while not h_done : 
            print(f"\n=====================Create Email ( {inc+1} )=====================")
            driver.get("https://accounts.google.com/embedded/v2/kidsignup/createaccount")
            wait_and_send(driver, '#firstName',fake.first_name())
            wait_and_send(driver, '#lastName',fake.last_name())
            wait_and_click(driver, '#collectNameNext > div > button')
            wait_and_send(driver, '#day',random.randint(1, 9))
            dropdown_element = driver.find_element(By.ID, 'month')
            random_value = str(random.randint(1, 12))
            select = Select(dropdown_element)
            select.select_by_value(random_value)

            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#year'))).send_keys("2019")
            dropdown_element = driver.find_element(By.ID, 'gender')
            random_value = str(random.randint(1, 2))
            select = Select(dropdown_element)
            select.select_by_value(random_value)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#birthdaygenderNext > div > button'))).click()
            time.sleep(3)
            try:
                WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#view_container > div > div > div.pwWryf.bxPAYd > div > div.WEQkZc > div > form > span > section > div > div > div.IhH7Wd.hdGwMb.V9RXW > div.ci67pc > div > span > div:nth-child(1) > div > div.enBDyd > div'))).click()
                wait_and_click(driver, "#next > div > button")
            except:
                xops = "ffggg"
            try:
                email = f"{fake.first_name()}{fake.last_name()}{str(random.randint(1, 10000000))}"
                print(f"{email}@gmail.com")
                WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#view_container > div > div > div.pwWryf.bxPAYd > div > div.WEQkZc > div > form > span > section > div > div > div > div.d2CFce.cDSmF > div > div.aCsJod.oJeWuf > div > div.Xb9hP > input'))).send_keys(email)
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#next > div > button'))).click()
            except:
                sj = "yeah"

            wait_and_send(driver, '#password > div.aCsJod.oJeWuf > div > div.Xb9hP > input', '123456tujuh')
            # wait_and_send(driver, '#confirm-passwd > div.aCsJod.oJeWuf > div > div.Xb9hP > input', '123456tujuh')
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#createpasswordNext > div > button'))).click()
            time.sleep(5)
            while True:
                try:
                    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#phoneNumberId'))).clear()
                    print("Get Phone Number")
                    if phone_number == None:
                        order_id, phone_number = get_phone()

                    # phone_number ="6285751807847"
                    # order_id ="11049801"
                    print(f"phone: {phone_number}")
                    print(f"order id: {order_id}")
                    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#phoneNumberId'))).clear()
                    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#phoneNumberId'))).send_keys("+"+str(phone_number))
                    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#view_container > div > div > div.pwWryf.bxPAYd > div > div.zQJV3 > div > div > div > div > button'))).click()
                    try:
                        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#view_container > div > div > div.pwWryf.bxPAYd > div > div.WEQkZc > div > form > span > section > div > div > div.bAnubd.Jj6Lae > div > div.gFxJE > div.jPtpFe')))
                        print("nomer tidak valid")
                        time.sleep(5)
                        if providers == 1:
                            status_cancel = cancel_order(order_id)
                            print(status_cancel)
                        driver.get("https://myaccount.google.com/signinoptions/recoveryoptions?opendialog=collectphone")
                        order_id, phone_number = get_phone()
                        wait_and_send(driver, "#c6", phone_number)
                        wait_and_click(driver, "#yDmH0d > div.uW2Fw-Sx9Kwc.uW2Fw-Sx9Kwc-OWXEXe-n2to0e.iteLLc.uW2Fw-Sx9Kwc-OWXEXe-FNFY6c > div.uW2Fw-wzTsW > div > div.uW2Fw-T0kwCb > div.qsqhnc > div > button")
                        print(f"new phone: {phone_number}")
                        print(f"new order id: {order_id}")
                        max_loop = max_loop + 1
                        time.sleep(7)
                    except:
                        status_otp, otp_code = get_inbox(order_id)
                        while True : 
                            if otp_code_2 == otp_code  :
                                status_otp, otp_code = get_inbox(order_id)
                            else :
                                break 
                        if not status_otp:
                            if providers == 1:
                                status_cancel = cancel_order(order_id)
                                print(status_cancel)
                            elif providers == 0:
                                change_status(0, order_id)
                            print("Can't Get OTP Code Loop Use New Number")
                            max_loop = max_loop + 1
                            driver.get("https://myaccount.google.com/signinoptions/recoveryoptions?opendialog=collectphone")
                            order_id, phone_number = get_phone()
                            wait_and_send(driver, "#c6", phone_number)
                            wait_and_click(driver, "#yDmH0d > div.uW2Fw-Sx9Kwc.uW2Fw-Sx9Kwc-OWXEXe-n2to0e.iteLLc.uW2Fw-Sx9Kwc-OWXEXe-FNFY6c > div.uW2Fw-wzTsW > div > div.uW2Fw-T0kwCb > div.qsqhnc > div > button")
                            break
                        try:
                            wait_and_send(driver, '#code', otp_code)
                            time.sleep(1)
                            wait_and_click(driver, '#next > div > button')
                            time.sleep(3)
                            try:
                                time.sleep(1)
                                wait_and_click(driver, "#view_container > div > div > div.pwWryf.bxPAYd > div > div.WEQkZc > div > form > span > section:nth-child(7) > div > div > div:nth-child(2) > div.ci67pc > div")
                                wait_and_click(driver, "#view_container > div > div > div.pwWryf.bxPAYd > div > div.WEQkZc > div > form > span > section:nth-child(7) > div > div > div:nth-child(1) > div.ci67pc > div")
                                wait_and_click(driver, "#dnpPage-next > div > button")
                                time.sleep(2)
                            except:
                                slos = 0
                            try:
                                wait_and_send(driver, "#password > div.aCsJod.oJeWuf > div > div.Xb9hP > input", "123456tujuh")
                                time.sleep(1)
                                wait_and_click(driver, "#passwordNext > div > button")
                                time.sleep(3)
                                wait_and_click(driver, "#view_container > div > div > div.pwWryf.bxPAYd > div > div.zQJV3 > div > div > div > div > button")
                                time.sleep(2)
                                wait_and_click(driver, "#view_container > div > div > div.pwWryf.bxPAYd > div > div.WEQkZc > div > form > span > section > div > div > div > ul > li:nth-child(1) > div")
                                time.sleep(2)
                                wait_and_click(driver, "#view_container > div > div > div.pwWryf.bxPAYd > div > div.zQJV3 > div > div.qhFLie > div > div > button")
                                time.sleep(8)
                                try : 
                                    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#view_container > div > div > div.pwWryf.bxPAYd > div > div.WEQkZc > div > form > span > section > div > div > div > div > div.aCsJod.oJeWuf > div > div.Xb9hP > input'))).clear()

                                    status_otp, otp_code_2 = get_inbox(order_id)
                                    while True : 
                                        if otp_code_2 == otp_code  :
                                            status_otp, otp_code_2 = get_inbox(order_id)
                                        else :
                                            break 
                                    
                                    wait_and_send(driver, "#view_container > div > div > div.pwWryf.bxPAYd > div > div.WEQkZc > div > form > span > section > div > div > div > div > div.aCsJod.oJeWuf > div > div.Xb9hP > input", otp_code_2)
                                    time.sleep(1)
                                    wait_and_click(driver, "#view_container > div > div > div.pwWryf.bxPAYd > div > div.zQJV3 > div > div.qhFLie > div > div > button")
                                    time.sleep(10)

                                except :
                                    h_done = True
                                    break
                            except:
                                slos = 0
                        except:
                            print("otp salah")
                            input("Done")
                    break
                except:
                    print("can't Create")
                    max_loop = max_loop + 1
                    break
        driver.quit()
            # driver.quit()


main()
