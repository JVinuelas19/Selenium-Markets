from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from utils import LIDL_SERVICES, CP_TO_PROVINCE, PROVINCE_TO_REGION, MAX_WAIT
import time, os, re
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
sql = "TRUNCATE TABLE tiendas_lidl;"
mycursor.execute(sql)

# Creates the Selenium driver
service = Service(executable_path="chromedriver.exe")
driver = webdriver.Chrome(service=service)
wait = WebDriverWait(driver, MAX_WAIT)

# Open browser and maximize window
driver.get(os.getenv("WEB_LIDL"))
time.sleep(8)
driver.maximize_window()
time.sleep(1)

# Store extraction
stores = driver.find_elements(By.CSS_SELECTOR, ".brxe-tbmwob.brxe-section")
time.sleep(1)
latitude = 0
longitude = 0
for store in stores:
    services = []
    try:
        # CP, city, province and region
        info = store.find_element(By.CLASS_NAME, "title").text
        cp_city = re.findall("[0-9]{5}.*,", info)
        if not cp_city:
            cp_city = re.findall("[0-9]{5}.*", info)
            cp = cp_city[0].split(" ")[0]
            city = cp_city[0].replace(f"{cp} ", "")
        else:
            cp_city = cp_city[0].replace(",", "")
            cp = cp_city.split(" ")[0]
            city = cp_city.replace(f"{cp} ", "")
        province = CP_TO_PROVINCE.get(cp[:2])
        region = PROVINCE_TO_REGION.get(province)
        # Address
        if info.count(", ") == 1:
            address = info.split(", ")[0]
        else:
            address = f"{info.split(", ")[0]}, {info.split(", ")[1]}"
        # Clear numberless addresses and cities as CPs
        if re.search("[0-9]{5}.*", address) != None:
            extra_cp = re.findall("[0-9]{5}.*", address)
            address = address.replace(extra_cp[0], "S/N")
        if re.search("[0-9]{5}", city) != None:
            city = province
        #URL
        store_link = store.find_element(By.CSS_SELECTOR, ".brxe-ucxrfb.brxe-button.btn-degrade.bricks-button")
        url = store_link.get_attribute("href")

        icons = store.find_elements(By.TAG_NAME, "svg")
        for icon in icons:
            try:
                service = LIDL_SERVICES.get(icon.get_attribute("class"))
                if service:
                    services.append(service)
            except:
                print("Not a service")

        # Save to the DB
        sql="INSERT INTO tiendas_lidl (region, provincia, ciudad, codigo_postal, direccion, " \
            "latitud, longitud, servicios, url) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        data=[]
        data.append(region)
        data.append(province)
        data.append(str(city))
        data.append(str(cp))
        data.append(str(address))
        data.append(latitude)
        data.append(longitude)
        data.append(str(services))
        data.append(url)
        mycursor.execute(sql, data)
        mydb.commit()
   
    except:
        mydb.rollback()
        with open("errores.txt", "a", encoding="utf-8") as e:
            e.write(f"Bad address: {info}\n{cp}\n{address}\n"
                    f"{city}\n{region}\n{province}\n{url}\n{services}\n"
                    f"{latitude} - {longitude}")
            e.write("\n")
       
# Close the browser
time.sleep(5)
driver.quit()