from openai import AsyncClient
from config import config
from loguru import logger
from schemas import AIParsingTaskSchema, WorkersSchema
from typing import cast, Any
import json
import time

async def request_to_ai(response_schema, content):
    async with AsyncClient(base_url=config.ai_api_url, api_key=config.ai_token) as client:
        logger.debug(f"Запрос к ИИ на {config.ai_api_url}, к модели {config.ai_model}")
        start_time = time.monotonic()
        response = await client.chat.completions.create(
            model=config.ai_model,  # Модель строго из твоего личного кабинета
            messages=cast(Any, [{"role": "user", "content": content}]),
            temperature=0.1,
            max_tokens=3000,
            # не поддерживает api ai провайдера
            # response_format=cast(Any, {"type":response_schema.model_json_schema()})
                        )
    end_time = time.monotonic()
    logger.debug(f"Пришел ответ на запрос от ИИ, время ответа {end_time - start_time}")
    raw_json = response.choices[0].message.content
    logger.debug(f"raw_json: {raw_json}")
    json_data = json.loads(raw_json)
    logger.debug(f"json_data: {json_data}")
    validated_data = []
    if isinstance(json_data, dict):
        error_parsing = json_data.get("error_parsing")
    elif isinstance(json_data, list):
        error_parsing = json_data[0].get("error_parsing")
    else:
        error_parsing = None
    if error_parsing:
        logger.error(error_parsing)
        return [], error_parsing
    try:
        for data in json_data:
            validated_data.append(response_schema.model_validate(data))
    except Exception as e:
        logger.error(f"ИИ при парсинге ответила в неверном формате, ошибка: {e}")
        return [], "Ошибка при парсинге со стороны ИИ"
    return validated_data, None

async def ai_parsing_tasks(csv, month):
    content = (f"Проанализируй CSV, очисти данные, пропусти пустые или заполненые строки со случайно заполнеными ячейками, "
           f"ячейки с содержимым: '.',',','/' и подобными принимай значение за None, "
           f"не изменяй фамилий исполнителей, номера заданий и адреса, проверь что даты заданий находятся "
           f"в одном календарном месяце {month}, если какую то строку с заполнеными ячейками не можешь распарсить, csv пустой"
           f"или лежат данные с пропущеными ячейками, например нет номера задания, даты, адреса или исполнителей,"
           f"верни только в формате: JSON error_parsing: str, где в значении краткое описание "
           f"того что тебе не понравилось в данных, и прерви проверку, данные должны прилететь либо все либо ничего"
           f"если данные норм верни строго в формате JSON по схеме:\n"
           f"address: str - адрес задания"
           f"month: str - месяц задания {month}"
            f"date_time: datetime дата и время задания в питоновском формате datetime"
            f"number: int - номер задания"
            f"workers: str - исполнители, перечисленные через запятую"
            f"type: str \nвот исходный грязный CSV:\n{csv}")
    try:
        result, errors = await request_to_ai(AIParsingTaskSchema, content)
    except Exception as e:
        error_str = f"Ошибка при запросе к ИИ на парсинг: {e}"
        logger.error(error_str)
        return [], error_str
    return result, errors

async def ai_parsing_workers(csv):
    content = (f"Проанализируй CSV, очисти данные, пропусти пустые или заполненые строки со случайно заполнеными ячейками, "
                f"ячейки с содержимым: '.',',','/' и подобными принимай значение за None, "
                f"не изменяй имен, фамилий, никнеймов"
                f"если данные норм верни строго в формате JSON по схеме:\n"
                f"name: str"
                f"nickname: str"
                f"Если что-то пошло не так: не нашел нужных столбцов и прочее верни только "
                f"в формате: JSON error_parsing: str, где в значении краткое описание "
                f"того что тебе не понравилось в данных, и прерви проверку, данные должны прилететь либо все либо ничего"
                f"\nвот исходный грязный CSV:\n{csv}")
    try:
        result, errors = await request_to_ai(WorkersSchema, content)
    except Exception as e:
        error_str = f"Ошибка при запросе к ИИ на парсинг: {e}"
        logger.error(error_str)
        return [], error_str
    return result, errors