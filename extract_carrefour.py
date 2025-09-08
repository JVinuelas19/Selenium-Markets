import xml.etree.ElementTree as ET
from dotenv import load_dotenv
import os
import mysql.connector
from utils import PROVINCE_TO_REGION, CP_TO_PROVINCE

CARREFOUR_MARKET_CATEGORIES = [
    "Hipermercado", "Supermercado Carrefour Market", "Supermercado Carrefour Express", 
    "Supermercado Carrefour Express CEPSA", "Supermercado Carrefour BIO"]

load_dotenv()
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_PORT = os.getenv("MYSQL_PORT")
MYSQL_DB = os.getenv("MYSQL_DB")
mydb = mysql.connector.connect(host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD, database=MYSQL_DB)
mycursor = mydb.cursor()
mycursor.execute("TRUNCATE tiendas_carrefour")

tree = ET.parse('carrefour_stores.xml')
root = tree.getroot()

for child in root:
    if child.attrib['category'] in CARREFOUR_MARKET_CATEGORIES:
        try:
            data = []
            data.append(child.attrib['ccaa'])
            data.append(child.attrib['state'])
            data.append(child.attrib['city'])
            data.append(child.attrib['address'])
            data.append(child.attrib['postal'])
            data.append(round(float(child.attrib['lat']), 5))
            data.append(round(float(child.attrib['lng']), 5))
            data.append(child.attrib['phone'].replace(" ", ""))
            data.append(child.attrib['web'])
            data.append(child.attrib['category'])
            data.append(str(child.attrib['features'].split(',')))

            # Save entry to the database
            query = "INSERT INTO tiendas_carrefour (region, provincia, ciudad, " \
            "direccion, codigo_postal, latitud, longitud, telefono, url, tipo_mercado, servicios) " \
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            mycursor.execute(query, data)
            mydb.commit()
        except:
            mydb.rollback()
            print("An error occured while extracting data or saving it to the DB.")
    else:
        print("Gas station or travel agency. Skipping item...")
    
