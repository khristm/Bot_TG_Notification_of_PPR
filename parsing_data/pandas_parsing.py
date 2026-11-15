from schemas import TaskSchema, WorkersSchema
from io import BytesIO
import pandas
from datetime import datetime, timedelta
import calendar
from loguru import logger

class ReadCVSToObject:
    """Читаем cvs и преобразуем в список объектов класса TaskSchema"""
    def __init__(self,data_cvs,month=None):
        self.errors=False
        self.list_dicts=[]
        self.list_object=[]
        self.month=month
        self.__read_cvs(data_cvs)
    def __read_cvs(self,data_cvs):
        try:
           data=pandas.read_csv(BytesIO(data_cvs))
           data=data.replace({pandas.NA: None, float('nan'): None})#пытаемся проглотить пустые ячейки из таблицы
           data_dict=data.to_dict(orient="records")
        except Exception as e:
            logger.error(f"Не смогли прочитать cvs с ошибкой: {e}")
            self.errors=True
            return None
        self.list_dicts=data_dict
        return self
    def parse_tasks(self):
        """Конвертация словаря в объекты класса унаследованного от BaseModel"""
        """Сначала меняем ключи в словаре на имена атрибутов конечного класса"""
        new_list=[]
        logger.debug(f"таблица из пандас: \n{self.list_dicts}")
        try:
            for el in self.list_dicts:
                # имена столбцов должны строго соответствовать структуре, данные нужны точно полные
                # поэтому при любом несовпадении прервемся с ошибкой поэтому не метод .get()
                new_dict = {
                    "number":el["№ задания"],
                    "address" : el["Адрес"],
                    "month" : self.month,
                    "date_time" : el["Дата и время"],
                    "workers":el["Исполнители"],
                    "type":el["Тип работ"]
                }
                new_list.append(new_dict)
            self.list_dicts=new_list
        except Exception as e:
            logger.exception(e)
            logger.error(f"Ошибка на этапе перебора значений из гугл таблицы, не верные названия столбцов, ошибка: {e}")
            self.errors=True
            return None
        """Перед преобразованием проверим значения ключа date_time что конвертируются в объекты datetime
        и находятся в месяце указанном в аргументе month"""
        try:
            #параметр month планирую получать в формате 2026-01
            self.month=datetime.strptime(self.month.strip(),"%Y-%m")
        except Exception as e:
            logger.error(f"Месяц пришел не в верном формате, ошибка: {e}")
            self.errors = True
            return None
        #проверка полей даты ппр на соотвествие формату даты
        try:
            for el in self.list_dicts:
                el["date_time"]=datetime.strptime(el["date_time"],"%d.%m.%Y %H:%M:%S")
        except Exception as e:
            logger.exception(e)
            logger.error(f"Даты ППР пришли из гугл таблиц не в верном формате, ошибка: {e}")
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
            logger.debug(f"Даты ППР не в указанном месяце, ошибка: {e}")
            self.errors = True
            return None
        #создаем объекты и добавляем в список
        try:
            for el in self.list_dicts:
                obj=TaskSchema(**el)
                self.list_object.append(obj)
        except Exception as e:
            logger.exception(e)
            logger.error(f"Ошибка в создании объекта при парсинге: {e}")
            self.errors = True
        return self
    def parse_workers(self):
        list_obj = []
        logger.debug(f"Словари сотрудников из пандас: {self.list_dicts}")
        try:
            for el in self.list_dicts:
                name_worker = el["ФИО"]
                nickname_worker = el["Ник"]
                worker = WorkersSchema(name=name_worker, nickname=nickname_worker)
                list_obj.append(worker)
        except Exception as e:
            logger.info(f"Не смогли распарсить данные из гугл таблицы сотрудников c ошибкой: {e}")
            self.errors = True
            return
        self.list_object=list_obj
        return