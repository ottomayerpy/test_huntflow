import re
import unicodedata
from abc import ABCMeta, abstractmethod
from typing import Any, Dict, List, Union

from openpyxl import load_workbook


class XLSXReaderException(Exception):
    pass


class XLSXReader:
    """ Класс чтеца файлов XLSX. """

    def __init__(self, fields: List[Field], header_exists: bool = True):
        """ Инициализация чтеца XLSX файлов.

        :param fields: поля, XLSX файла
        :type fields: List[Field]
        :param header_exists: в файле есть заголовок, он будет игнорироваться, defaults to True
        :type header_exists: bool, optional
        """
        self.fields = fields
        self.header_exists = header_exists
        self.workbook = None
        self.sheet = None

    def __enter__(self):
        """ При входе в менеджер контекста проверяет, что файл открыт.

        :raises XLSXReaderException: если файл не открыт
        """
        if self.workbook is None:
            raise XLSXReaderException('Workbook is not open.')
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """ При выходе из контекстного менеджера закрывает файл. """
        self.close()

    def open(self, fp: str, sheet_number: int = 0) -> 'XLSXReader':
        """ Открыть файл для чтения.

        Если уже открыт файл для чтения, закрывает текущий, открывает новый.

        :param fp: путь до файла
        :type fp: str
        :param sheet_number: номер страницы, defaults to 1
        :type sheet_number: int, optional
        """
        if self.workbook is not None:
            self.close()
        self.workbook = load_workbook(filename=fp)
        self.sheet = self.workbook.worksheets[sheet_number]
        return self

    def close(self):
        """ Закрыть файл для чтения.

        :raises XLSXReaderException: если файл не открыт
        """
        if self.workbook is None:
            raise XLSXReaderException('Workbook is not open.')
        self.sheet = None
        self.workbook.close()
        self.workbook = None

    def read_row(self, row_number: int = 1) -> Dict[str, Any]:
        """ Прочитать строку.

        :param row_number: номер строки, defaults to 1
        :type row_number: int, optional
        :raises XLSXReaderException: если не открыт файл для чтения
        :return: данные, извлеченные из строки
        :rtype: Dict[str, Any]
        """
        if self.workbook is None:
            raise XLSXReaderException('Workbook is not open.')
        if self.header_exists:
            row_number = row_number + 1
        row = self.sheet[row_number]
        data = {}
        for col_number, field in enumerate(self.fields):
            col = row[col_number]
            value = field.parse(col.value)
            if value:
                data.update(value)
        return data


def normalize(string: str) -> str:
    """ Провести нормализацию строки.

    Используется форму NFKC (http://unicode.org/reports/tr15/).

    :param string: строка, которую требуется нормализовать
    :type string: str
    :return: нормализованная строка
    :rtype: str
    """
    return unicodedata.normalize('NFKC', string)


class Field(metaclass=ABCMeta):

    def __init__(self, name: str):
        """ Инициализация класса поля.

        :param name: имя поля
        :type name: str
        """
        self.name = name

    @abstractmethod
    def parse(self, value: Any) -> Union[Dict[str, Any], None]:
        """ Парсить значение.

        Предполагается, что метод в потомках должен возвращать словарь с ключом, соответствующим имени поля и значением,
        соответствующим извеченному значению. Если значение не удалось извлечь, возвращает None.

        :param value: значение
        :type value: Any
        :return: словарь с полученным значением или None, если значение не удалось извлечь
        :rtype: Union[Dict[str, Any], None]
        """


class StringField(Field):
    """ Поле, для получения строк. Проводит нормализацию строки. """

    def parse(self, value):
        value = self._parse(value)
        if value:
            return {
                self.name: value
            }
        return None

    def _parse(self, value):
        if value is not None:
            return normalize(str(value))
        return None


class SeparatedIntegerField(StringField):
    """ Поле для получения целого числа из строки. Число может быть разделено пробельными символами, при этом они будут
    игнорироваться. Возвращает первое такое число. """

    def _parse(self, value):
        pattern = r'(\d)+(\s+(\d)+)*'
        search = re.search(pattern, str(value))
        if search is None:
            return None
        else:
            pattern = r'\s'
            return int(re.sub(pattern, '', search[0]))


class Salary(SeparatedIntegerField):
    """ Поле для получения заработной платы из строки. Получает целое число как SeparatedIntegerField. Возвращает
    строку, которая содержит число и указание сокращенного названия валюты через пробел от числа. """

    def __init__(self, name: str, currency: str):
        """ Инициализация поля.

        :param name: имя поля
        :type name: str
        :param currency: сокращенное название валюты
        :type currency: str
        """
        super().__init__(name)
        self.currency = currency

    def _parse(self, value):
        value = super()._parse(value)
        if value is not None:
            return f'{value} {self.currency}'
        return None


class StatsField(StringField):
    """ Поле для трансляции статусов из локальной БД в статусы БД, имеющейся на сервере. """

    NEW_LEAD            = 'New Lead'
    SUBMITTED           = 'Submitted'
    CONTACTED           = 'Contacted'
    HR_INTERVIEW        = 'HR Interview'
    CLIENT_INTERVIEW    = 'Client Interview'
    OFFERED             = 'Offered'
    OFFER_ACCEPTED      = 'Offer Accepted'
    HIRED               = 'Hired'
    TRIAL_PASSED        = 'Trial passed'
    DECLINED            = 'Declined'


class FullNameField(StringField):
    """ Поле для извлечения полного имени. Имя поля игнорируется. Формируется словарь из двух (если отчество
    отсутствует) или из трех полей (если отчество есть) с ключами "last_name", "first_name" и "middle_name". """

    def parse(self, value):
        if not value:
            return None
        value = value.split(' ')
        if len(value) < 2:
            return None
        res = {
            'last_name': normalize(value[0]),
            'first_name': normalize(value[1])
        }
        if len(value) > 2:
            res['middle_name'] = normalize(value[2])
        return res


# Инициализация чтеца и клиента
FIELDS = (
    StringField('vacancy'),
    FullNameField('full name'),
    Salary('money', 'руб'),
    StringField('comment'),
    StatsField('status'),
)
