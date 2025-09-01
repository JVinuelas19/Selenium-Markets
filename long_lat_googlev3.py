from geopy.geocoders import GoogleV3
from dotenv import load_dotenv
import os
import mysql.connector
import time

# Creates connection with the DB
load_dotenv()
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_PORT = os.getenv("MYSQL_PORT")
MYSQL_DB = os.getenv("MYSQL_DB")
DATABASE = os.getenv("TIENDAS_ALDI")
mydb = mysql.connector.connect(host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD, database=MYSQL_DB)
mycursor = mydb.cursor()

geolocator = GoogleV3(api_key=os.getenv("GOOGLE_MAPS_API_KEY"))

# Extract key data from database for geocoding
query = f"SELECT id_tienda, direccion, ciudad FROM {DATABASE} WHERE latitud = 0;"
mycursor.execute(query)
registros = mycursor.fetchall()

# Search for all entrys a fixed address and update database with latitude and longitude
for r in registros:
    id_tienda, direccion, ciudad = r
    query_busqueda = f"{id_tienda} - {direccion}, {ciudad}"
    try:
        coords = geolocator.geocode(query=query_busqueda, exactly_one=True)
        latitude = round(coords.latitude, 5)
        longitude = round(coords.longitude, 5)
        update_query = "UPDATE empleados.tiendas_aldi SET latitud = %s, longitud = %s WHERE id_tienda = %s"
        print(f"{id_tienda} - {latitude}, {longitude}")
        mycursor.execute(update_query, (latitude, longitude, id_tienda))
        mydb.commit()
        time.sleep(0.25)
    except:
        print("An error occured while extracting coordinates.")

