from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time, os, random
import mysql.connector
from dotenv import load_dotenv

PROVINCIAS = [
    # ESPAÑA
    "Álava", "Albacete", "Alicante", "Almería", "Asturias", "Ávila",
    "Badajoz", "Barcelona", "Burgos",
    "Cáceres", "Cádiz", "Cantabria", "Castellón", "Ceuta", "Ciudad Real", 
    "Córdoba", "Cuenca", "Fuerteventura",
    "Gerona", "Granada", "Gran Canaria", "Guadalajara", "Guipúzcoa", 
    "Huelva", "Huesca", "Illes Balears", "Jaén",
    "La Coruña", "La Rioja", "Las Palmas", "León", "Lérida", "Lugo", 
    "Madrid", "Málaga", "Melilla", "Murcia", 
    "Navarra", "Orense", "Palencia", "Pontevedra",
    "Salamanca", "Santa Cruz de Tenerife", "Segovia", "Sevilla", "Soria",
    "Tarragona", "Teruel", "Toledo",
    "Valencia", "Valladolid", "Vizcaya",
    "Zamora", "Zaragoza",
    # PORTUGAL
    "Aveiro", "Braga", "Coimbra", "Évora", "Guarda", "Leiria", "Lisboa",
    "Porto", "Santarém", "Setúbal", "Viana do Castelo", "Viseu", 
]
MAX_WAIT = 10

def get_coords(hidden_coords):
    full_link = str(hidden_coords.get_attribute("href"))
    left_trim = full_link.replace(os.getenv("WEB_MAPS"), "")
    right_trim = left_trim.split("/")[0]
    latitud, longitud = right_trim.split((","))
    return float(latitud), float(longitud)

def get_city_info(city_info):
    post_code_and_city, province = city_info.split("(")
    province = province.replace(")", "") 
    post_code = post_code_and_city.split(" ")[0]
    city = city_info.replace(f" ({province})", "").replace(f"{post_code} ", "")
    return post_code, city, province

def extract_data (driver):
    """Extracts all the data from a store and fixes it as a dict

    Args:
        driver (selenium.webdriver.Chrome): Driver to inspect the web

    Returns:
        _type_: _description_
    """
    country = str(driver.find_element(
        By.CSS_SELECTOR, ".supermercadoPais").text).lower().capitalize()
    address = str(driver.find_element(
        By.CLASS_NAME, "panelDetalleCalle").text)
    city_info = str(driver.find_element(
        By.CLASS_NAME, "panelDetalleCiudad").text)
    post_code, city_name, province = get_city_info(city_info)
    hidden_coords = driver.find_element(
        By.CSS_SELECTOR, 
        ".green-border-transparent-button.supermercadoComoLlegar.otro")
    latitude, longitude = get_coords(hidden_coords)
    phone = str(driver.find_element(
        By.CSS_SELECTOR, 
        ".panelDetalleElemento.panelDetalleElementoHeader.supermercadoTelefono").text)
    parking = str(driver.find_element(
        By.CSS_SELECTOR, 
        ".panelDetalleElemento.panelDetalleElementoHeader.supermercadoParking").text)
    if parking == "Parking disponible":
        parking = "Si"
    else:
        parking = "No"

    info = {
        "country": country,
        "province":province,
        "city_name":city_name,
        "post_code":post_code,
        "address":address,
        "latitude":latitude,
        "longitude":longitude,
        "phone":phone,
        "parking":parking
    }
    return info

# Database load  
load_dotenv()
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_PORT = os.getenv("MYSQL_PORT")
MYSQL_DB = os.getenv("MYSQL_DB")
mydb = mysql.connector.connect(host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD, database=MYSQL_DB)
mycursor = mydb.cursor()

# Creates the Selenium driver
service = Service(executable_path="chromedriver.exe")
driver = webdriver.Chrome(service=service)
wait = WebDriverWait(driver, MAX_WAIT)

# Open browser, fix size and reject cookies
driver.get(os.getenv("WEB_MERCADONA"))
time.sleep(8)
driver.execute_script("document.body.style.zoom='75%'")
driver.maximize_window()
time.sleep(2)
try:
    cookies_dialog = driver.find_element(By.ID, "first-btn")
    wait.until(EC.element_to_be_clickable(cookies_dialog))
    cookies_dialog.click()
    print("Cookies rejected")
except:
    print("Cookies button not found")
time.sleep(5)

# Open the search bar and enter city
for ciudad in PROVINCIAS:
    scroll_into_view_text = driver.find_element(By.CLASS_NAME, "supermercadosTitulo")
    driver.execute_script('arguments[0].scrollIntoView(true);', scroll_into_view_text)
    search_bar = driver.find_element(By.ID, "busquedaInputSuper")
    wait.until(EC.element_to_be_clickable(search_bar))
    search_bar.send_keys(Keys.CONTROL, 'a', Keys.DELETE )
    time.sleep(random.random()*5)
    search_bar.send_keys(ciudad)
    time.sleep(random.random()*5)
    search_button = driver.find_element(By.CLASS_NAME, "busquedaBoton")
    wait.until(EC.element_to_be_clickable(search_button))
    search_button.click()
    # If more than 10 stores are loaded, press the "Show more" button
    try:
        time.sleep(5)
        show_more_button = driver.find_elements(By.CSS_SELECTOR, ".botonEnlace.botonEnlaceBot")
        if len(show_more_button) > 1:
            if str(show_more_button[1].text) == "Ver todos":
                wait.until(EC.element_to_be_clickable(show_more_button[1]))
                driver.execute_script('arguments[0].click();', show_more_button[1])
            else: 
                pass
    # Save store info to the database
    finally:
        stores = driver.find_elements(By.CLASS_NAME, "panelLateralResultadosElemento")
        print(f"There are {len(stores)} in {ciudad}")
        num_stores = 0
        for store in stores:
            driver.execute_script('arguments[0].scrollIntoView(true);', store)
            wait.until(EC.element_to_be_clickable(store))
            store.click()
            time.sleep(random.random()*8)
            extracted_data = extract_data(driver)
            """ If you want to console check if the extracted data is correct 
                uncomment this section    
            print(f"Country: {extracted_data.get("country")}\n"
                  f"Address: {extracted_data.get("address")}\n"
                  f"Post code: {extracted_data.get("post_code")}\n"
                  f"City: {extracted_data.get("city_name")}\n"
                  f"Province: {extracted_data.get("province")}\n"
                  f"Latitude: {extracted_data.get("latitude")}\n"
                  f"Longitude: {extracted_data.get("longitude")}\n"
                  f"Phone: {extracted_data.get("phone")}\n"
                  f"Parking available: {extracted_data.get("parking")}")
            """ 
            sql=("INSERT INTO tiendas_mercadona (pais, provincia, ciudad, codigo_postal, direccion, "\
                 "latitud, longitud, telefono, parking) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)")
            data = list(extracted_data.values())
            # Check if store is already registered in the database
            try:
                mycursor.execute("SELECT EXISTS(SELECT 1 FROM tiendas_mercadona WHERE direccion = %s)", (data[4],))
                check_if_exists = mycursor.fetchone()[0]
                if check_if_exists == 0:
                    mycursor.execute(sql, data)
                    mydb.commit()
                else:
                    print("The store is already saved in the database.")
            # Errors will be registered in a txt to have failure traceability
            except:
                with open("errores.txt", "a", encoding="utf-8") as e:
                    e.write(data[4])
                    e.write("\n")
       
            time.sleep(random.randint(2,5))

