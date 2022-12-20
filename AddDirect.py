# Программа для выгрузки статистики рекламных кампаний из Яндекс.Директа
import requests
import pandas as pd
import os
import time
import sys
import json
import csv
from datetime import datetime, date, time, timedelta
from dateutil.relativedelta import relativedelta
from requests.exceptions import ConnectionError
from time import sleep

# Функция замены значений '--' на 'null'
def change_0(cell):
  if cell == '--':
    cell = 'null'
  return cell

# Путь к папке, где будет сохранен файл с данными
path = 'C:\Users\Professional\Desktop\Директ'

# Метод для корректной обработки строк в кодировке UTF-8 как в Python 3, так и в Python 2
if sys.version_info < (3,):
    def u(x):
        try:
            return x.encode("utf8")
        except UnicodeDecodeError:
            return x
else:
    def u(x):
        if type(x) == type(b''):
            return x.decode('utf8')
        else:
            return x

# Адрес сервиса Reports для отправки JSON-запросов
ReportsURL = 'https://api.direct.yandex.com/json/v5/reports'

# OAuth-токен пользователя, от имени которого будут выполняться запросы
token = 'y0_AgAAAAA3SkdFAAjlMgAAAADXL5gV5kSgvN1XRUqSzGgFWcJxrOkd8Gs'

# Логин рекламного кабинета Яндекс.Директ
clientLogin = 'whitemarker-cpc'

#  Подготовка к запросу
#  Создание заголовка HTTP запроса
headers = {
    # OAuth-токен. Слово "Bearer" обязательно к использованию
    "Authorization": "Bearer " + token,
    # Логин клиента рекламного агентства
    "Client-Login": clientLogin,
    # Язык ответных сообщений
    "Accept-Language": "en",
    # Режим формирования отчета: online, offline или auto.
    "processingMode": "auto",
    # Формат денежных значений в отчете
    "returnMoneyInMicros": "false",
    # Не выводить в отчете строку с названием отчета и диапазоном дат
    "skipReportHeader": "true",
    # Не выводить в отчете строку с названиями полей.
    "skipColumnHeader": "false",
    # Не выводить в отчете строку с количеством строк статистики.
    "skipReportSummary": "true"
}

# Дата начала
dateS = datetime.strptime("2022-10-01", '%Y-%m-%d')

# Дата окончания
dateE = datetime.strptime("2022-10-31", '%Y-%m-%d')

# Создание тела запроса
body = {
    "params": {
        # Критерии отбора данных для отчета. В нашем примере - по дате
        "SelectionCriteria": {
            "DateFrom": dateS.strftime('%Y-%m-%d'),
            "DateTo": dateE.strftime('%Y-%m-%d')
        },
        # Необходимые поля в отчете
        "FieldNames": [
            "Date",
            "CampaignName",
            "CampaignId",
            "CampaignType",
            "AdGroupName",
            "AdGroupId",
            "AdFormat",
            "AdId",
            "CriterionId",
            "Criterion",
            "CriterionType",
            "Age",
            "Gender",
            "AdNetworkType",
            "Device",
            "MobilePlatform",
            "LocationOfPresenceId",
            "RlAdjustmentId",
            "Placement",
            "Slot",
            "Impressions",
            "Clicks",
            "Cost"
        ],
        "ReportName": u("Request1" + dateS.strftime('%Y-%m-%d')),
        "Page": {
            "Limit": 10000000
        },
        "ReportType": "CUSTOM_REPORT",
        "DateRangeType": "CUSTOM_DATE",
        "Format": "TSV",
        "IncludeVAT": "YES",
    }
}

# Преобразование в JSON формат
body = json.dumps(body, indent=4)

# Цикл передачи запроса и обработка ответа от сервера
while True:
    try:
        req = requests.post(ReportsURL, body, headers=headers)
        req.encoding = 'utf-8'  # Принудительная обработка ответа в кодировке UTF-8
        if req.status_code == 400:
            print("Параметры запроса указаны неверно или достигнут лимит отчетов в очереди")
            print("RequestId: {}".format(req.headers.get("RequestId", False)))
            print("JSON-код запроса: {}".format(u(body)))
            print("JSON-код ответа сервера: \n{}".format(u(req.json())))
            break
        elif req.status_code == 200:
            print("Отчет создан успешно")
            print("RequestId: {}".format(req.headers.get("RequestId", False)))
            # print("Содержание отчета: \n{}".format(u(req.text)))
            break
        elif req.status_code == 201:
            print("Отчет успешно поставлен в очередь в режиме офлайн")
            retryIn = int(req.headers.get("retryIn", 60))
            print("Повторная отправка запроса через {} секунд".format('60'))
            print("RequestId: {}".format(req.headers.get("RequestId", False)))
            sleep(60)
        elif req.status_code == 202:
            print("Отчет формируется в режиме офлайн")
            retryIn = int(req.headers.get("retryIn", 60))
            print("Повторная отправка запроса через {} секунд".format(retryIn))
            print("RequestId:  {}".format(req.headers.get("RequestId", False)))
            sleep(retryIn)
        elif req.status_code == 500:
            print("При формировании отчета произошла ошибка. Пожалуйста, попробуйте повторить запрос позднее")
            print("RequestId: {}".format(req.headers.get("RequestId", False)))
            print("JSON-код ответа сервера: \n{}".format(u(req.json())))
            break
        elif req.status_code == 502:
            print("Время формирования отчета превысило серверное ограничение.")
            print(
                "Пожалуйста, попробуйте изменить параметры запроса - уменьшить период и количество запрашиваемых данных.")
            print("JSON-код запроса: {}".format(body))
            print("RequestId: {}".format(req.headers.get("RequestId", False)))
            print("JSON-код ответа сервера: \n{}".format(u(req.json())))
            break

        else:
            print("Произошла непредвиденная ошибка")
            print("RequestId:  {}".format(req.headers.get("RequestId", False)))
            print("JSON-код запроса: {}".format(body))
            print("JSON-код ответа сервера: \n{}".format(u(req.json())))
            break

# Обработка ошибки, если не удалось соединиться с сервером API Директа
except ConnectionError:
    # В данном случае мы рекомендуем повторить запрос позднее
    print("Произошла ошибка соединения с сервером API")
    # Принудительный выход из цикла
    break

    # Если возникла какая-либо другая ошибка
except:
    # В данном случае мы рекомендуем проанализировать действия приложения
    print("Произошла непредвиденная ошибка")
    # Принудительный выход из цикла
    break

# Запись данных в файл формата TSV
with open((os.path.join(path, dateS.strftime('%Y%m%d') + '-' + dateE.strftime('%Y%m%d') + '.tsv')), 'w',
          encoding="utf-8") as f:
    f.write(req.text)