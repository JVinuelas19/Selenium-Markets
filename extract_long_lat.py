from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import UnexpectedAlertPresentException, NoSuchElementException
import time, os, random
import mysql.connector
from dotenv import load_dotenv

# Constantes
PROVINCIAS_A_REGION = {
    "Almeria": "Andalucía", "Cadiz": "Andalucía", "Cordoba": "Andalucía",
    "Granada": "Andalucía", "Huelva": "Andalucía", "Jaen": "Andalucía",
    "Malaga": "Andalucía", "Sevilla": "Andalucía",
    "Huesca": "Aragón", "Teruel": "Aragón", "Zaragoza": "Aragón",
    "Asturias": "Asturias", "Baleares": "Islas Baleares", 
    "Cantabria": "Cantabria", "Avila": "Castilla y León", 
    "Burgos": "Castilla y León", "Leon": "Castilla y León",
    "Palencia": "Castilla y León", "Salamanca": "Castilla y León", 
    "Segovia": "Castilla y León", "Soria": "Castilla y León", 
    "Valladolid": "Castilla y León", "Zamora": "Castilla y León",
    "Albacete": "Castilla-La Mancha", "Ciudad Real": "Castilla-La Mancha",
    "Cuenca": "Castilla-La Mancha", "Guadalajara": "Castilla-La Mancha",
    "Toledo": "Castilla-La Mancha",
    "Barcelona": "Cataluña", "Gerona": "Cataluña", "Lerida": "Cataluña",
    "Tarragona": "Cataluña", "Alicante": "Comunidad Valenciana",
    "Castellon": "Comunidad Valenciana", "Valencia": "Comunidad Valenciana",
    "Badajoz": "Extremadura", "Caceres": "Extremadura",
    "Coruna": "Galicia", "Lugo": "Galicia", "Orense": "Galicia",
    "Pontevedra": "Galicia", "Madrid": "Madrid", "Murcia": "Murcia",
    "Navarra": "Navarra", "Alava": "País Vasco", "Vizcaya": "País Vasco",
    "Guipuzcoa": "País Vasco", "Rioja": "La Rioja", "Ceuta": "Ceuta", 
    "Melilla": "Melilla"
}

ABREVIATURA_VIAS = {
    "Avenida": "AV",
    "Calle": "CL",
}

# Establece conexión con la base de datos
load_dotenv()
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_PORT = os.getenv("MYSQL_PORT")
MYSQL_DB = os.getenv("MYSQL_DB")
mydb = mysql.connector.connect(host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD, database=MYSQL_DB)
mycursor = mydb.cursor()
# Borrado de la base de datos (opcional)
#sql = "TRUNCATE TABLE tiendas_dia;"
#mycursor.execute(sql)


# Inicializar el driver de Selenium
service = Service(executable_path="chromedriver.exe")
driver = webdriver.Chrome(service=service)
timeout = WebDriverWait(driver, 100)

# Abrir el navegador 
driver.get("https://www.bing.com/maps")
time.sleep(5)

# Rechazar Cookies
boton_cookies = driver.find_element(By.ID, "bnp_btn_reject")
timeout.until(EC.element_to_be_clickable(boton_cookies))
boton_cookies.click()

for i in range(2314):
    #Extracción de la base de datos y formateo para la busqueda
    sql = f"SELECT direccion, codigo_postal, ciudad, provincia, region FROM empleados.tiendas_dia WHERE id_tienda = %s"
    mycursor.execute(sql, (id_tienda,))
    datos = mycursor.fetchone()
    #Función para procesar los datos y crear el string de busqueda
    direccion = datos[0]
    #Transformar tipo de via a formato genérico: Calle a C., Avenida a Av., etc
    try:
        abreviatura = ABREVIATURA_VIAS.get(direccion.split(" ")[0])
        direccion_busqueda = direccion.replace(direccion.split(" ")[0], abreviatura, 1)
    except:
        direccion_busqueda = direccion
    cp = datos[1]
    ciudad = datos[2]
    provincia = datos[3]
    region = str(datos[4])
    string_busqueda = f"{direccion_busqueda}, {cp} {ciudad}, España"
    print(string_busqueda)
    
    # Acceso a la barra de búsqueda y 
    barra_busqueda = driver.find_element(By.ID, "maps_sb")
    timeout.until(EC.element_to_be_clickable(barra_busqueda))
    barra_busqueda.click()
    time.sleep(1)
    barra_busqueda.send_keys(Keys.CONTROL, "a", Keys.DELETE)
    time.sleep(1)
    barra_busqueda.send_keys(string_busqueda)
    time.sleep(1)
    barra_busqueda.send_keys(Keys.ENTER)
    time.sleep(3)

    # Obtención de las coordenadas
    card = driver.find_elements(By.CSS_SELECTOR, ".cardWrapper.expand.taskCardLane")[-1]
    try:
        coords = card.find_element(By.CLASS_NAME, "geochainModuleLatLong")
        latitud = coords.text.split(", ")[0]
        longitud = coords.text.split(", ")[1]
        region = PROVINCIAS_A_REGION.get(provincia)
        print(f"{id_tienda} - {latitud} - {longitud} - {region}")
        direccion_obtenida = driver.find_elements(By.CLASS_NAME, "nameContainer")[-1].text
        # Check del código postal
        if direccion_obtenida.find(cp) == -1:
            cp = direccion_obtenida.split(", ")[-2].split(" ")[0]
            if len(cp) == 5:
                sql=("UPDATE empleados.tiendas_dia SET region = %s, longitud = %s, "
                    "latitud = %s, codigo_postal = %s WHERE id_tienda = %s")
                mycursor.execute(sql, (region, longitud, latitud, cp, id_tienda))
            else:
                raise ValueError("El código postal no se ajusta al formato")
        else:
            sql="UPDATE empleados.tiendas_dia SET region = %s, longitud = %s, latitud = %s WHERE id_tienda = %s"
            mycursor.execute(sql, (region, longitud, latitud, id_tienda))
        mydb.commit()

    # Control de errores: manipulación de strings y excepciones propias
    except (ValueError, IndexError) as error:
        with open("latitud_longitud_fallidas.txt", "a", encoding="utf-8") as e:
            e.write(f"{error}:\nBusqueda hecha: {string_busqueda}\n")
    # Control de errores: Dialogos de Chrome con Selenium
    except UnexpectedAlertPresentException as e:
        time.sleep(2)
        with open("latitud_longitud_fallidas.txt", "a", encoding="utf-8") as e:
            e.write(f"{id_tienda} - Error:{e}\nBusqueda hecha: {string_busqueda}\nResultado: La localización no existe\n")
    except NoSuchElementException as e:
        time.sleep(2)
        with open("latitud_longitud_fallidas.txt", "a", encoding="utf-8") as e:
            e.write(f"{e}:\nBusqueda hecha: {string_busqueda}\nResultado: No se ha podido ubicar\n")
    
    #Se aumenta el id_tienda
    id_tienda += 1

time.sleep(3)
driver.quit()

