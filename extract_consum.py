import xml.etree.ElementTree as ET
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import os, time
import mysql.connector
from utils import PROVINCE_TO_REGION, CP_TO_PROVINCE, MAX_WAIT

load_dotenv()
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_PORT = os.getenv("MYSQL_PORT")
MYSQL_DB = os.getenv("MYSQL_DB")
mydb = mysql.connector.connect(host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD, database=MYSQL_DB)
mycursor = mydb.cursor()
print("Conexion BBDD correcta")
mycursor.execute("TRUNCATE tiendas_consum")

# Creates the Selenium driver
service = Service(executable_path="chromedriver.exe")
driver = webdriver.Chrome(service=service)
wait = WebDriverWait(driver, MAX_WAIT)

driver.get(os.getenv("WEB_CONSUM"))
driver.maximize_window()
time.sleep(2)
try:
    cookies_dialog = driver.find_element(By.ID, "onetrust-reject-all-handler")
    wait.until(EC.element_to_be_clickable(cookies_dialog))
    cookies_dialog.click()
    print("Cookies rejected")
except:
    print("Cookies button not found")
time.sleep(2)

next_page = driver.find_element(By.CSS_SELECTOR, ".page-item.pager__item.pager__item--next")
last_page_container = driver.find_element(By.CSS_SELECTOR, ".page-item.pager__item.pager__item--last")
last_page_data = last_page_container.find_element(By.TAG_NAME, "a")
print(last_page_data.get_attribute("href"))
last_page = int(last_page_data.get_attribute("href").split("/")[-2])
print(last_page)
for i in range(1, last_page):
    stores = driver.find_elements(By.CSS_SELECTOR, ".col-md-6.item-center")
    for store in stores:
        store_services = []
        store_info = store.find_element(By.CLASS_NAME, "supermarket-data")
        address_data = store_info.find_element(By.TAG_NAME, "p").text
        if len(address_data.split(", ")) == 4:
            address = address_data.split(", ")[0]
        elif len(address_data.split(", ")) == 5:
            address = f"{address_data.split(", ")[0]}, {address_data.split(", ")[1]}"
        else:
            driver.quit()
            print(f"Se fue a la mierda: {address_data}")
        # Parse address
        cp = address_data.split(", ")[-3]
        province = CP_TO_PROVINCE.get(cp[:2])
        region = PROVINCE_TO_REGION.get(province)
        city = address_data.split(", ")[-2].capitalize()
        print(f"{cp} - {province} - {region} - {city} - {address}")
        phone = store_info.find_element(By.TAG_NAME, "a").text
        fixed_phone = phone.replace(" ", "")
        store_services_container = store.find_element(By.CLASS_NAME, "supermarket-services")
        services_container = store_services_container.find_elements(By.TAG_NAME, "img")
        for service in services_container:
            store_services.append(service.get_attribute("alt"))
        url = store.find_element(By.CLASS_NAME, "supermarket-goto-button3").get_attribute("href")
        longitude = 0
        latitude = 0
        """
        try:
            sql="INSERT INTO tiendas_consum (region, provincia, ciudad, direccion, codigo_postal, latitud, longitud, telefono, servicios, url) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            data=[]
            data.append(region)
            data.append(province)
            data.append(city)
            data.append(address)
            data.append(region)
            data.append(province)
            data.append(region)
            data.append(province)
            mycursor.execute(sql, data)
            mydb.commit()
        except:
            print(f"Something wrong happened with store {store_id}")
        """
    driver.execute_script('arguments[0].scrollIntoView(true);', next_page)
    wait.until(EC.element_to_be_clickable(next_page))
    next_page.click()
    time.sleep(20)

time.sleep(5)

    
