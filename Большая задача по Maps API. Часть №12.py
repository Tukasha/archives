import sys
import os
import requests
from PyQt6.QtWidgets import QWidget, QApplication, QPushButton, QLineEdit, QLabel, QCheckBox
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import QSize
from PyQt6.QtCore import Qt


class Example(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setGeometry(300, 300, 600, 450)
        self.setWindowTitle("Map")
        self.setFocus()
        self.setMouseTracking(True)

        self.x, self.y = 0, 0
        self.z = 1
        self.themes = ["light", "dark"]
        self.theme = 0
        self.pt = ""

        self.map = QLabel(self)
        self.map.setPixmap(map_edit(self.x, self.y, self.z, self.themes[self.theme], self.pt))

        self.search_result = QLabel(self)
        self.search_result.move(10, 420)
        self.search_result.resize(600, 25)
        self.search_result.setText("Адрес: ")

        self.ask = QLineEdit(self)
        self.ask.move(500, 0)
        self.ask.resize(90, 25)

        self.button_1 = QPushButton(self)
        self.button_1.move(500, 50)
        self.button_1.setText("Искать")
        self.button_1.clicked.connect(self.run)

        self.button_2 = QPushButton(self)
        self.button_2.setIconSize(QSize(20, 20))
        self.button_2.move(20, 20)
        self.button_2.setText("Сменить тему")
        self.button_2.clicked.connect(self.run1)

        self.reset_button = QPushButton(self)
        self.reset_button.move(500, 26)
        self.reset_button.setText("Сброс поиска")
        self.reset_button.clicked.connect(self.reset)

        self.checkbox1 = QCheckBox(self)
        self.checkbox1.move(500, 75)
        self.checkbox1.setText("почт. индекс")
        self.checkbox1.clicked.connect(self.run)

    def mousePressEvent(self, event):
        lon, lat = self.pixel_to_coords(event.pos().x(), event.pos().y(),
                                    self.width(), self.height(),
                                    self.x, self.y, self.z)
        info = get_info(f"{lon},{lat}")
        if info[1] is None:
            info = list(info)
            info[1] = "не найден"
            info = tuple(info)

        if mode or not self.pt:
            self.pt = f"{lon},{lat}"
        elif f"{lon},{lat}" not in self.pt:
            self.pt += "~" + f"{lon},{lat}"

        if event.button() == Qt.MouseButton.LeftButton:
            
            if self.checkbox1.isChecked():
                self.search_result.setText(f"Адрес: {info[0]}, индекс: {info[1]}")
            else:
                self.search_result.setText(f"Адрес: {info[0]}")
            
            self.map.setPixmap(map_edit(self.x, self.y, self.z, self.themes[self.theme], self.pt))

        elif event.button() == Qt.MouseButton.RightButton:
            
            organization = get_organizations(self.pt.split("~")[-1],{info[0]})
            print(organization)
            if organization:
                if self.checkbox1.isChecked():
                    self.search_result.setText(f"Адрес: {info[0]}, организация: {organization}, индекс: {info[1]}")
                else:
                    self.search_result.setText(f"Адрес: {info[0]}, организация: {organization}")
            else:
                if self.checkbox1.isChecked():
                    self.search_result.setText(f"Адрес: {info[0]}, индекс: {info[1]}")
                else:
                    self.search_result.setText(f"Адрес: {info[0]}")

            self.map.setPixmap(map_edit(self.x, self.y, self.z, self.themes[self.theme], self.pt))

        self.setFocus()

    def pixel_to_coords(self, pixel_x, pixel_y, map_width, map_height, x, y, z):
        lon = x + (pixel_x - map_width / 2) * (360 / (256 * 2 ** z))
        lat = y - (pixel_y - map_height / 2) * (180 / (256 * 2 ** z))

        return lon, lat

    def keyPressEvent(self, e):
        if e.key() == 16777220:
            self.run()

        if e.key() == 16777238 and self.z < 21:
            self.z += 1
        elif e.key() == 16777239 and self.z > 1:
            self.z -= 1

        if e.key() == 16777235 and self.y < 85:
            self.y += 1
        elif e.key() == 16777237 and self.y > -85:
            self.y -= 1
        elif e.key() == 16777236 and self.x < 175:
            self.x += 1
        elif e.key() == 16777234 and self.x > -175:
            self.x -= 1

        self.map.setPixmap(map_edit(self.x, self.y, self.z, self.themes[self.theme], self.pt))

    def run(self):
        info = get_info(self.ask.text())
        try:
            adress = info[0]
        except Exception:
            adress = ""
        try:
            if self.checkbox1.isChecked():
                self.search_result.setText(f"Адрес: {adress}, индекс: {info[1]}")
            else:
                self.search_result.setText(f"Адрес: {adress}")
        except Exception:
            pass
        try:
            self.x, self.y = float(pt_edit(self.ask.text()).split(",")[0]), float(pt_edit(self.ask.text()).split(",")[1])
        except Exception:
            pass
        try:
            if mode or not self.pt:
                self.pt = pt_edit(self.ask.text())
            elif pt_edit(self.ask.text()) not in self.pt:
                self.pt += "~" + pt_edit(self.ask.text())
        except Exception:
            pass
        try:
            self.map.setPixmap(map_edit(self.x, self.y, self.z, self.themes[self.theme], self.pt))
        except Exception:
            pass

    def run1(self):
        self.theme = 1 - self.theme
        self.map.setPixmap(map_edit(self.x, self.y, self.z, self.themes[self.theme], self.pt))

    def reset(self):
        if self.pt:
            if mode:
                self.pt = ""
            else:
                self.pt = "~".join(self.pt.split("~")[:-1])
            self.map.setPixmap(map_edit(self.x, self.y, self.z, self.themes[self.theme], self.pt))
            self.search_result.setText(f"Адрес: ")


def map_edit(x, y, z, theme, pt):
    if pt != "":
        geocoder_params = {
            "ll": f"{x},{y}",
            "z": z,
            "pt": pt,
            "l": "map",
            "theme": theme,
            "api_key": "7712150f-250c-4509-9858-86bcc92fa44b"
        }

        response = requests.get("http://static-maps.yandex.ru/1.x/", params=geocoder_params)

    else:
        geocoder_params = {
            "api_key": "7712150f-250c-4509-9858-86bcc92fa44b",
            "ll": f"{x},{y}",
            "z": z,
            "l": "map",
            "theme": theme
        }

        response = requests.get("http://static-maps.yandex.ru/1.x/", params=geocoder_params)
    if response:
        map_file = "map.png"
        with open("map.png", "wb") as file:
            file.write(response.content)
        return QPixmap(map_file)


def pt_edit(answer):
    geocoder_params = {
        "apikey": "8013b162-6b42-4997-9691-77b7074026e0",
        "geocode": answer,
        "results": 1,
        "format": "json"
    }
    
    response = requests.get("http://geocode-maps.yandex.ru/1.x/", params=geocoder_params)
    
    if response:
        json_response = response.json()
        x, y = json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]["Point"]["pos"].split()
        return f"{x},{y}"
    

def get_info(geo):
    geocoder_params = {
        "apikey": "8013b162-6b42-4997-9691-77b7074026e0",
        "geocode": geo,
        "results": 1,
        "format": "json"
    }
    
    response = requests.get("http://geocode-maps.yandex.ru/1.x/", params=geocoder_params)
    if response:
        json_response = response.json()
        toponym = json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
        toponym_address = toponym["metaDataProperty"]["GeocoderMetaData"]["text"]
        try:
            toponym_index = toponym["metaDataProperty"]["GeocoderMetaData"]["Address"]["postal_code"]
        except Exception:
            toponym_index = None
        return (toponym_address, toponym_index)
    

def get_organizations(point, adress):
    search_api_server = "https://search-maps.yandex.ru/v1/"
    api_key = "dda3ddba-c9ea-4ead-9010-f43fbc15c6e3"
    degree_distance = 50 / (111 * 100)
    spn = f"{degree_distance},{degree_distance}"
    search_params = {
        "apikey": api_key,
        "lang": "ru_RU",
        "text": adress,
        "ll": point,
        "spn": spn,
        "rspn": "1",
        "results": "1",
        "type": "biz"
    }

    response = requests.get(search_api_server, params=search_params)
    print(response, response.url)
    try:
        return response.json()["features"][0]["properties"]["CompanyMetaData"]["name"]
    except Exception:
        return None
    


if __name__ == "__main__":
    mode = 0
    app = QApplication(sys.argv)
    ex = Example()
    ex.show()
    app.exec()
    os.remove("map.png")