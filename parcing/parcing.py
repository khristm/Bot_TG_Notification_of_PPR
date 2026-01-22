import aiohttp
import asyncio
import re
from config import config
from schemas import TaskSchema
from io import BytesIO
import pandas
from datetime import datetime, timedelta
import calendar
from database.crud import create_schedule_from_list
from database.database import async_session

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

class ReadCVSToObject:
    """Читаем cvs и преобразуем в список объектов класса TaskSchema"""
    def __init__(self,data_cvs,month):
        self.errors=False
        self.list_dicts=[]
        self.list_object=[]
        self.month=month
        self.__read_cvs(data_cvs)
        self.__convert_dict_to_object()
    def __read_cvs(self,data_cvs):
        try:
           data=pandas.read_csv(BytesIO(data_cvs))
           data_dict=data.to_dict(orient="records")
        except Exception as e:
            print(f"Не смогли прочитать cvs с ошибкой: {e}")
            self.errors=True
            return None
        self.list_dicts=data_dict
        return self
    def __convert_dict_to_object(self):
        """Конвертация словаря в объекты класса унаследованного от BaseModel"""
        """Сначала меняем ключи в словаре на имена атрибутов конечного класса"""
        new_list=[]
        try:
            for el in self.list_dicts:
                new_dict = {}
                # имена столбцов должны строго соответствовать структуре, данные нужны точно полные
                # поэтому при любом несовпадении прервемся с ошибкой поэтому не метод .get()
                new_dict["number"]=el["№ задания"]
                new_dict["adress"] = el["Адрес"]
                new_dict["month"]=self.month
                new_dict["date_time"]=el["Дата"]
                new_dict["workers"]=el["Исполнители"]
                new_dict["type"]=el["Тип работ"]
                new_list.append(new_dict)
            self.list_dicts=new_list
        except Exception as e:
            print(f"Ошибка на этапе перебора значений из гугл таблицы, не верные названия столбцов, ошибка: {e}")
            self.errors=True
            return None
        """Перед преобразованием проверим значения ключа date_time что конвертируются в объекты datetime
        и находятся в месяце указанном в аргументе month"""
        try:
            #параметр month планирую получать в формате 2026-01
            self.month=datetime.strptime(self.month.strip(),"%Y-%m")
        except Exception as e:
            print(f"Месяц пришел не в верном формате, ошибка: {e}")
            self.errors = True
            return None
        #проверка полей даты ппр на соотвествие формату даты
        try:
            for el in self.list_dicts:
                el["date_time"]=datetime.strptime(el["date_time"],"%d.%m.%Y %H:%M:%S")
        except Exception as e:
            print(f"Даты ППР пришли из гугл таблиц не в верном формате, ошибка: {e}")
            self.errors = True
            return None
        #проверка что ппр проводятся в указанном пользователем месяце
        try:
            day_in_month=calendar.monthrange(self.month.year,self.month.month)[1]
            end_month = self.month + timedelta(days=day_in_month)
            for el in self.list_dicts:
                if el["date_time"] > end_month or el["date_time"]<self.month:
                    raise ValueError(f"{el["date_time"]} не в пределах указанного месяца {self.month}")
        except Exception as e:
            print(f"Даты ППР не в указанном месяце, ошибка: {e}")
            self.errors = True
            return None
        #создаем объекты и добавляем в список
        for el in self.list_dicts:
            obj=TaskSchema(**el)
            self.list_object.append(obj)
        return self

async def test(user_sheet_url,session):
    """Имитация логики загрузки данных с гугл таблицы"""
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
    data=ReadCVSToObject(result,"2025-12")
    if not data.errors:
        print(data.list_object)
        return data.list_object
    else:
        print("Пустой лист")
        return None

async def main():
    true_url_with_gid = "https://docs.google.com/spreadsheets/d/1LYEW_Ma5dUwfwhqN6lcT6WAd1yF6spGa9vp1qYAb-pQ/edit?gid=1725907990#gid=1725907990"
    url_none_gid = "https://docs.google.com/spreadsheets/d/1LYEW_Ma5dUwfwhqN6lcT6WAd1yF6spGa9vp1qYAb-pQ/edit?usp=drivesdk"
    false_url = "https://abracydabra.ru/bullsheet"
    telegram_id='someid'
    async with aiohttp.ClientSession() as session:
        await test(true_url_with_gid, session)
        data = await test(url_none_gid, session)
        await test(false_url, session)
    if data is not None:
        async with async_session() as s:
            await create_schedule_from_list(s,data,telegram_id)
            print("Я добавил все дерьмо в БД")

if __name__ == '__main__':
    asyncio.run(main())
