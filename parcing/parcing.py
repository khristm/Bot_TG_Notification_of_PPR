import aiohttp
import asyncio
import re
import json


class ModifyUrl:
    def __init__(self, url_user:str):
        self.url_user = url_user
        self.url_with_gid=None
        self.errors=False
        self.__check_url()
    def __check_gid(self):
        if 'gid=' in self.url_user:
            self.url_with_gid = self.url_user.replace('edit?', 'export?format=csv&')
            return self
        else:
            return None
    def __check_url(self):
        google_sheet_url = "https://docs.google.com/spreadsheets/d/"
        try:
            if google_sheet_url in self.url_user:
                self.__check_gid()
            else:
                self.errors = True
        except Exception:
            self.errors=True

class RequestToGoogle:
    def __init__(self, url_user:str, session_obj:aiohttp.ClientSession):
        self.url_user = url_user
        self.session = session_obj
    async def get_cvs(self):
        try:
            async with self.session.get(self.url_user) as response:
                data = await response.read()
                return data
        except Exception as e:
            print(f"Ошибка сетевого запроса: {e}")
    async def get_gid(self):
        try:
            async with self.session.get(self.url_user) as response:
                if response.status != 200:
                    print(f"Ошибка доступа: статус {response.status}")
                    return []

                html = await response.text()

                # 1. Ищем блок bootstrapData
                match = re.search(r'bootstrapData\s*=\s*(\{.*?\});', html, re.DOTALL)

                result = []
                if match:
                    # Ищем внутри JSON паттерны: "sheetId": цифры и "title": "текст"
                    # Это самый стабильный способ, так как эти ключи Google меняет редко
                    raw_data = match.group(1)

                    # Регулярка ищет блоки свойств листов
                    # Она найдет все sheetId и title, даже если они глубоко запрятаны
                    titles = re.findall(r'"title"\s*:\s*"(.*?)"', raw_data)
                    gids = re.findall(r'"sheetId"\s*:\s*(\d+)', raw_data)

                    # Сопоставляем найденные данные (обычно их количество совпадает)
                    for title, gid in zip(titles, gids):
                        # Исключаем технические заголовки, если нужно
                        if title not in result:
                            result.append({'title': title, 'gid': gid})

                # 2. Если JSON не нашелся, используем "грубый" поиск по всему HTML
                if not result:
                    # В HTML Google Sheets часто встречаются массивы вида [1725907990, "Название"]
                    fallback_matches = re.findall(r'\[(\d{7,15}),\s*"(.*?)"', html)
                    for gid, title in fallback_matches:
                        result.append({'title': title, 'gid': gid})

                # Убираем дубликаты
                unique_result = list({v['gid']: v for v in result}.values())
                return unique_result
        except Exception as e:
            print(f"Ошибка сетевого запроса: {e}")

if __name__ == '__main__':
    async def main():
        async with aiohttp.ClientSession() as session:
            user_url = "https://docs.google.com/spreadsheets/d/1LYEW_Ma5dUwfwhqN6lcT6WAd1yF6spGa9vp1qYAb-pQ/edit?usp=drivesdk"
            modify_url = ModifyUrl(url_user=user_url)
            if modify_url.url_with_gid is not None:
                print(modify_url.url_with_gid)
                result = await RequestToGoogle(url_user=modify_url.url_with_gid,session_obj=session).get_cvs()
                print(result)
            elif modify_url.errors == False and modify_url.url_with_gid is None:
                print("Запущу скрипт на получение gid")
                result = await RequestToGoogle(url_user=user_url, session_obj=session).get_gid()
                print(result)
            else:
                print("Тут я скажу юзеру дай нормальную ссылку")

    asyncio.run(main())