import asyncio
import requests
from bs4 import BeautifulSoup as bs
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from telethon import TelegramClient
from telethon.tl.functions.photos import UploadProfilePhotoRequest, DeletePhotosRequest
from telethon.tl.types import InputPhoto
import configparser
config = configparser.ConfigParser()
config.read("settings.ini")
api_id = config["Tg"]["api_id"]
api_hash = config["Tg"]["api_hash"].replace('"', '')
city = config["Tg"]["city"].replace('"', '')
url_yandex = f"https://yandex.ru/pogoda/ru/{city.lower()}"
url_mail = f"https://pogoda.mail.ru/prognoz/{city.lower()}/24hours/"
FONT_LARGE = ImageFont.truetype("FranksRus-Regular_0.otf", 70)
FONT_SMALL = ImageFont.truetype("segoe-ui-emoji_0.ttf", 30)
client = TelegramClient("anon", api_id, api_hash)

weater_and_icons = {
    'Пасмурно' : '☁️',
    'Облачно' : '☁️',
    'Ясно' : '☀️',
    'Дождь' : '🌧️',
    'Снег' : '🌨️'
}

weather = ""

def osad_parse():
    try:  
        r = requests.get(url_yandex)
        soup = bs(r.text, "html.parser")
        weather = soup.find(
                    'p', class_='AppFact_warning__8kUUn')
        weath = weather.text.split('.')[0].split(' ')[0]
        return weath
    except:   
        return ""

def weather_parse():
    try:
        r = requests.get(url_yandex)
        soup = bs(r.text, "html.parser")
        temperature = soup.find_all(
            'span', class_='AppFactTemperature_value__2qhsG')[0]
        if temperature.text.strip() == "0":
            return "0"
        znak = soup.find_all(
            'span', class_='AppFactTemperature_sign__1MeN4')[0]
        return f"{znak.text}{temperature.text}°"
    except:
        r = requests.get(url_mail)
        soup = bs(r.text, "html.parser")
        temperature = soup.find_all(
            'span', class_='p-forecast__temperature-value')[0]
        return temperature.text


def img_weather(hour, show=False):
    temperature = weather_parse()
    weather = osad_parse()
    print(temperature)
    if hour < 6:
        color = "#FF0050"
    elif hour < 12:
        color = "#FFD000"
    elif hour < 18:
        color = "#8300FF"
    else:
        color = "#0001CC"
    image = Image.new('RGB', (256, 256), color='black')
    draw = ImageDraw.Draw(image)
    text_width = draw.textlength(temperature, font=FONT_LARGE)
    draw.text(((256 - text_width) // 2, 80),
              temperature, font=FONT_LARGE, fill="white")
    subtext = f"{weater_and_icons[weather]}{city}"
    subtext_width = draw.textlength(subtext, font=FONT_SMALL)
    draw.text(((256 - subtext_width) // 2, 160),
              subtext, font=FONT_SMALL, fill=color, embedded_color=True)
    if show:
        image.show()
    return image


async def update_profile_photo(hour):
    try:
        try:
            photos = await client.get_profile_photos('me')
            if photos:
                await client(DeletePhotosRequest(
                    id=[InputPhoto(
                        id=photos[0].id,
                        access_hash=photos[0].access_hash,
                        file_reference=photos[0].file_reference
                    )]
                ))
        except Exception as e:
            print("Ошибочка:", e)
        image = img_weather(hour)
        image.save("vrem.png")
        with open("vrem.png", 'rb') as file:
            file1 = await client.upload_file(file)
            await client(UploadProfilePhotoRequest(file=file1))
        return "True"
    except Exception as e:
        return str(e)


async def main():
    await client.start()
    last_time = ""
    while True:
        current_time = datetime.now().hour
        if current_time != last_time:
            last_time = current_time
            result = await update_profile_photo(current_time)
            if result != "True":
                print(f"Ошибка: {result}")
            else:
                print(f"{current_time}hour - Победа!\n")
        await asyncio.sleep(20)
if __name__ == "__main__":
    with client:
        client.loop.run_until_complete(main())
