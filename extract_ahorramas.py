from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time, os, random
import mysql.connector
from dotenv import load_dotenv

# Constants
SERVICES = ['Recarga de Moviles', 'Servicio a Domicilio', 'Amazon Locker', 'Cajas Autocobro',
            'Aparcamiento', 'Recarga Vehiculos Electricos']
SECTIONS = ['Alimentación', 'Carnicería', 'Pescadería', 'Charcutería', 'Pollería', 
            'Frutería', 'Congelados','Panadería', 'Droguería', 'Cosmética', 'A comer']
MAX_WAIT = 10

def get_store_data(driver: webdriver.Chrome):
    """Returns store info: address, city, services and sections

    Args:
        driver (selenium.webdriver.Chrome): The driver to navigate the HTML 
        and automate actions

    Returns:
        address (str): Store address
        city (str): City where the address is located
        store_services (list): Services offered by the store
        store_sections (list): Available sections in this store
    """
    address = driver.find_element(By.CSS_SELECTOR, '.store-address.mb-1').text
    city = address.split(" - ")[0]
    address = address.split(" - ")[1]
    #phone = driver.find_element(By.CLASS_NAME, 'icon-tel').text
    services = driver.find_elements(By.CLASS_NAME, "image-container")
    for service in services:
        service = service.get_attribute("title")
        if service in SERVICES:
            store_services.append(service)
        else:
            store_sections.append(service)
    
    return address, city, store_services, store_sections

# Creates connection with the DB
load_dotenv()
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_PORT = os.getenv("MYSQL_PORT")
MYSQL_DB = os.getenv("MYSQL_DB")
mydb = mysql.connector.connect(host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD, database=MYSQL_DB)
mycursor = mydb.cursor()
#sql = "TRUNCATE TABLE tiendas;" -> Reset the database
#mycursor.execute(sql)

# Creates the Selenium driver
service = Service(executable_path="chromedriver.exe")
driver = webdriver.Chrome(service=service)
wait = WebDriverWait(driver, MAX_WAIT)

# Open browser and reject cookies
WEB_AHORRAMAS = os.getenv("WEB_AHORRAMAS")
driver.get(WEB_AHORRAMAS)
time.sleep(8)
try:
    driver.find_element(By.ID, "onetrust-reject-all-handler").click()
except:
    print("Cookies button not found.")
time.sleep(5)

# Open store search bar
try:
    search_btn = driver.find_element(By.CSS_SELECTOR, ".btn-ahm.btn-ahm-primary.btn-storelocator-search")
    search_btn.click()
except:
    print("Store search button not found.")
time.sleep(3)

# Scrape every store and save it to a database
stores = driver.find_elements(By.CSS_SELECTOR, ".store-results-wrapper")
store_dict = {}
store_id = 1
print(f"{len(stores)} stores found")
for store in stores:
    try:
        store_services, store_sections = [], []
        wait.until(EC.element_to_be_clickable(store))
        store.click()
        address, city, store_services, store_sections = get_store_data(driver)
        sql="INSERT INTO tiendas_ahorramas (ciudad, direccion, servicios, secciones) VALUES (%s, %s, %s, %s)"
        data=[]
        data.append(city)
        data.append(address)
        data.append(str(store_services))
        data.append(str(store_sections))
        mycursor.execute(sql, data)
        mydb.commit()
    except:
        print(f"Something wrong happened with store {store_id}")
    
    time.sleep(random.random()*4)
    print(f"{city} - {address}\n{store_services}\n{store_sections}")
    store_id += 1

# Kill the driver and end the script
time.sleep(5)
driver.quit()