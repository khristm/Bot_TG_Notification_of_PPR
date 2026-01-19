import aiohttp
import asyncio
import re
import json
from config import config


class ModifyUrl:
    """Класс для работы со ссылкой абонента"""
    def __init__(self, url_user:str):
        self.url_user = url_user
        self.url_with_gid=None
        self.id_sheet=None
        self.errors=False
        self.__check_url()
        self.__get_id_sheet()
    def __check_gid(self):
        """Проверяем наличие gid= в ссылке, если есть формируем готовую ссылку для запроса cvs"""
        if 'gid=' in self.url_user:
            self.url_with_gid = self.url_user.replace('edit?', 'export?format=csv&')
            return self
        else:
            return None
    def __check_url(self):
        """Проверка что ссылка на гугл таблицы, если нет меняем значение error на True"""
        google_sheet_url = "https://docs.google.com/spreadsheets/d/"
        try:
            if google_sheet_url in self.url_user:
                self.__check_gid()
            else:
                self.errors = True
        except Exception:
            self.errors=True
    def __get_id_sheet(self):
        """Выдергиваем значение id гугл таблицы из ссылки абонента"""
        pattern = r'/spreadsheets/d/([a-zA-Z0-9-_]+)'
        match = re.search(pattern, self.url_user)
        if match:
            self.id_sheet=match.group(1)
        else:
            self.errors=True
        return self
    def create_url_with_gid(self,gid):
        self.url_with_gid="https://docs.google.com/spreadsheets/d/"+self.id_sheet+"/export?format=csv&"+gid
        return self


class RequestToGoogle:
    """Отдельный класс для запросов к гугл"""
    def __init__(self, url_user:str|None, session_obj:aiohttp.ClientSession,sheet_id:str|None):
        self.url_user = url_user
        self.session = session_obj
        self.sheet_id = sheet_id
    async def get_cvs(self):
        """Отправляем готовую ссылку для cvs"""
        try:
            async with self.session.get(self.url_user) as response:
                data = await response.read()
                return data
        except Exception as e:
            print(f"Ошибка сетевого запроса: {e}")
    async def get_gid(self):
        """Запрос на получение списка листов из таблицы если ссылка без указания на лист"""
        try:
            url = f"https://sheets.googleapis.com/v4/spreadsheets/{self.sheet_id}"
            params = {
                'key': config.api_key,
                'fields': 'sheets.properties(sheetId,title)'}
            async with self.session.get(url,params=params) as response:
                if response.status==200:
                    data = await response.json()
                    sheets=[{'title': sheet['properties']['title'],
                        'gid': 'gid='+str(sheet['properties']['sheetId'])} for sheet in data.get('sheets',[])]
                    return sheets
                else:
                    return []
        except Exception as e:
            print(f"Ошибка сетевого запроса: {e}")
            return []

async def test(user_sheet_url):
    """Имитация логики загрузки данных с гугл таблицы"""
    async with aiohttp.ClientSession() as session:
        url=ModifyUrl(user_sheet_url)
        if url.errors:
            #битая ссылка
            print("Я вернул None")
            return None
        elif url.url_with_gid is None:
            #gid не было в ссылке
            request = RequestToGoogle(url_user=url.url_with_gid, session_obj=session,sheet_id=url.id_sheet)
            gid_list = await request.get_gid()
            url.create_url_with_gid(gid_list[1]['gid'])###в реальном приложения конкретный лист выберет пользователь,
            # здесь выберу я, потому что знаю что в списке будет лист с таким индексом
        #выше данные полготовили теперь просто запрос на получение cvs
        request=RequestToGoogle(url_user=url.url_with_gid, session_obj=session,sheet_id=url.id_sheet)
        result = await request.get_cvs()
        #здесь будет функция обработки cvs
        print(result)
        return result





if __name__ == '__main__':
    true_url_with_gid="https://docs.google.com/spreadsheets/d/1LYEW_Ma5dUwfwhqN6lcT6WAd1yF6spGa9vp1qYAb-pQ/edit?gid=1725907990#gid=1725907990"
    url_none_gid="https://docs.google.com/spreadsheets/d/1LYEW_Ma5dUwfwhqN6lcT6WAd1yF6spGa9vp1qYAb-pQ/edit?usp=drivesdk"
    false_url="https://abracydabra.ru/bullsheet"
    asyncio.run(test(true_url_with_gid))
    asyncio.run(test(url_none_gid))
    asyncio.run(test(false_url))
