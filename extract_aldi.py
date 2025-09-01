from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from utils import CP_TO_PROVINCE, PROVINCE_TO_REGION, MAX_WAIT
import time, os
import mysql.connector
from dotenv import load_dotenv

# Creates connection with the DB
load_dotenv()
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_PORT = os.getenv("MYSQL_PORT")
MYSQL_DB = os.getenv("MYSQL_DB")
mydb = mysql.connector.connect(host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD, database=MYSQL_DB)
mycursor = mydb.cursor()
#sql = "TRUNCATE TABLE tiendas_aldi;"
#mycursor.execute(sql)

# Creates the Selenium driver
service = Service(executable_path="chromedriver.exe")
driver = webdriver.Chrome(service=service)
wait = WebDriverWait(driver, MAX_WAIT)

# Open browser and accept cookies
driver.get(os.getenv("WEB_ALDI"))
time.sleep(8)
driver.maximize_window()
time.sleep(1)


# Scrolls the entire store list to load them all in the HTML
scroll = driver.find_element(By.CLASS_NAME, "ubsf_locations-list")
last_height = 0
while True:
    driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scroll)
    time.sleep(1)  
    new_height = driver.execute_script("return arguments[0].scrollHeight", scroll)
    if new_height == last_height: 
        break
    last_height = new_height

# Store extraction
stores = driver.find_elements(By.CSS_SELECTOR, ".ubsf_locations-list-item.ubsf_locations-list-item-with-hover-effect")
for store in stores:
    try:
        address = store.find_element(By.CLASS_NAME, "ubsf_locations-list-item-street").text
        cp_city = store.find_element(By.CLASS_NAME, "ubsf_locations-list-item-zip-city").text
        cp = cp_city.split(" ")[0]
        city = cp_city.replace(f"{cp} ", "")
        province = CP_TO_PROVINCE.get(cp[:2])
        region = PROVINCE_TO_REGION.get(province)
        latitude = 0
        longitude = 0
        print(f"{address}, {cp} {city}, {province} - {region}")

        # Save to the DB
        sql="INSERT INTO tiendas_aldi (region, provincia, ciudad, codigo_postal, direccion, " \
            "latitud, longitud) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        data=[]
        data.append(region)
        data.append(province)
        data.append(str(city))
        data.append(str(cp))
        data.append(str(address))
        data.append(latitude)
        data.append(longitude)
        mycursor.execute(sql, data)
        mydb.commit()
    except:
        print("Something wrong happened.")
       
# Close the browser
time.sleep(5)
driver.quit()