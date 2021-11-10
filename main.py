import os
import time
from OSMPythonTools.overpass import Overpass
import selenium
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from openpyxl import Workbook
import gmaps.datasets
from ipywidgets.embed import embed_minimal_html
import pandas as pd

# name of country taken from openstreetmap.org
COUNTRY = "United Kingdom"
# name of created file with all locations, names and types
FILE_NAME = "locations.xlsx"

# selenium setup
DRIVER_PATH = "C:\Program Files\JetBrains\chromedriver.exe"
serv = Service(DRIVER_PATH)

chrome_options = Options()
chrome_options.add_argument("start-maximized")
chrome_options.add_argument("disable-infobars")
chrome_options.add_argument("--disable-extensions")


# openstreetmap.org request
overpass = Overpass()
result = overpass.query(f'area[name="{COUNTRY}"];(way[landuse="military"](area););out;', timeout=600)
all_results = result.elements()
way = result.ways()

# excel creation
wb = Workbook()
ws = wb.active
ws.append(["name", "type", "id", "url", "lon", "lat"])

driver = selenium.webdriver.Chrome(service=serv, options=chrome_options)

def get_cords(location_id):
    """
    military locations do not show their coordinates, so function opens with selenium your chrome and checks the
    coords from url. Time.sleep's are needed to let the browser to load and update url.
    :param location_id: id of every location
    :return: list with url to the location and its longitiude and latitiude
    """
    driver.get(f'https://www.openstreetmap.org/way/{location_id}')
    time.sleep(0.2)
    driver.find_element(By.XPATH, '//*[@id="map"]/div[2]/div[2]/div[1]/a[2]').click()
    time.sleep(0.3)
    url = driver.current_url
    if str(location_id) in url:
        try:
            cords = url.split("=")[1].split("/")
            latitude = cords[1]
            longitiude = cords[2]
            return [url, longitiude, latitude]
        except IndexError:
            return [url, 0, 0]
    else:
        get_cords(location_id)


# loop iterate all the results, checks it location by the get_cords function and appends it to workbook in excel
for a in all_results:
    a_id = a.id()
    name = a.tag('name')
    location_type = a.tag('military')
    list_of_cords = get_cords(a_id)
    ws.append([name, location_type, a_id, list_of_cords[0], list_of_cords[1], list_of_cords[2]])
wb.save(FILE_NAME)
driver.quit()

# creating map in google maps (development mode)

columns = ["latitude", "longitude", "magnitude"]
heat = []
marker = []

excel = pd.read_excel(FILE_NAME)
dfe = pd.DataFrame(excel)

# loop appending data to two separate lists. One for google markers, second for heatmap
for v in dfe.iterrows():
    lat = (v[1]["lat"])
    lon = (v[1]["lon"])
    if lat == 0 and lon == 0:
        continue
    mag = 10
    heat.append([lat, lon, mag])
    marker.append((lat, lon))

# paste your own gmaps api-key
gmaps.configure(api_key=os.environ.get('GMAPS_API'))

df = pd.DataFrame(heat, columns=columns)

fig = gmaps.figure()
heatmap_layer = gmaps.heatmap_layer(df[['latitude', 'longitude']], weights=df['magnitude'],
                                    max_intensity=10, point_radius=5)
marker_layer = gmaps.marker_layer(marker)

# adding the layer of map to gmaps. If there is a lot of results I suggest using heatmap. Else use markers.
# Just comment the unused version.

fig.add_layer(heatmap_layer)
fig.add_layer(marker_layer)

# creates simple html with map view
embed_minimal_html('export.html', views=[fig])
