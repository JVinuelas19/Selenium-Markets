import json, os
from utils import CP_TO_PROVINCE, PROVINCE_TO_REGION, GADIS_SERVICES
from dotenv import load_dotenv
import mysql.connector

load_dotenv()
# Connect to the Database
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_PORT = os.getenv("MYSQL_PORT")
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_DB = os.getenv("MYSQL_DB")
mydb = mysql.connector.connect(
    user=MYSQL_USER, 
    password=MYSQL_PASSWORD, 
    port=MYSQL_PORT, 
    host=MYSQL_HOST, 
    database=MYSQL_DB
)
mycursor = mydb.cursor()

# Parse the JSON to get each store values
with open("tiendas_gadis.json", "r", encoding="utf-8") as file:
    doc = json.load(file)
    for store in doc['stores']:
        services, data = [], []
        cp = store['cp']
        province = CP_TO_PROVINCE.get(cp[:2])
        data.append(PROVINCE_TO_REGION.get(province))
        data.append(province)
        data.append(store['pob'])
        data.append(store['dir'])
        data.append(cp)
        data.append(round(float(store['coordenada'].split(",")[0]), 5))
        data.append(round(float(store['coordenada'].split(",")[1]), 5))
        data.append(store['tel'].replace(" ", ""))
        for key in GADIS_SERVICES.keys():
            if store[key] == '1':
                services.append(GADIS_SERVICES.get(key))
        data.append(str(services))
       
        # Save it to the database
        query = "INSERT INTO tiendas_gadis (region, provincia, ciudad, direccion, codigo_postal, latitud, longitud, telefono, servicios) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        mycursor.execute(query, data)
        mydb.commit()