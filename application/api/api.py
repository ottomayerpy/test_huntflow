import json
import subprocess
from typing import Dict, List, Union
from urllib import parse
from urllib import parse as urllib_parse

import requests


class RequesterError(Exception):
    pass


class Requester:
    """ Класс-обертка над библиотекой requests. """

    # Имя агента пользователя для отладки
    USER_AGENT = 'TestTask/1.0 (test@huntflow.ru)'

    def __init__(self, token: str, api_endpoint: str):
        """ Инициализация класса-обертки.

        :param token: персональный токен
        :type token: str
        :param api_endpoint: точка доступа к АПИ
        :type api_endpoint: str
        """
        self.token = token
        self.api_endpoint = api_endpoint

    def _get_headers(self, headers: Dict[str, str] = None) -> Dict[str, str]:
        """ Обновление словаря заголовков.

        Добавляет в словарь заголовков данные об авторизации (токен) и агенте пользователя.

        :param headers: входной словарь заголовков, defaults to None
        :type headers: dict, optional
        :return: словарь заголовков
        :rtype: dict
        """
        res = {
            'User-Agent': self.USER_AGENT,
            'Authorization': f'Bearer {self.token}'
        }
        if headers:
            res.update(headers)
        return res

    def request(
            self,
            url: str,
            http_method: str = 'GET',
            body: dict = None,
            headers: dict = None,
            files: dict = None,
            **params
        ) -> dict:
        """ Сделать запрос к АПИ.

        :param url: путь для запроса
        :type url: str
        :param http_method: используемый HTTP метод, defaults to 'GET'
        :type http_method: str, optional
        :param body: тело запроса (json), defaults to None
        :type body: dict, optional
        :param headers: заголовки запроса, defaults to None
        :type headers: dict, optional
        :param files: отправляемые файлы, defaults to None
        :type files: dict, optional
        :raises RequesterError: если получен неудовлетворительный статус
        :return: словарь ответа от API
        :rtype: dict
        """
        url = parse.urljoin(self.api_endpoint, url)
        req = requests.request(
            method=http_method,
            url=url,
            headers=self._get_headers(headers),
            json=body,
            params=params,
            files=files
        )
        if not req.ok:
            message = f'Client get not ok status code "{req.status_code}"\n' + \
            f'Returned content: {req.content.decode()}\n' + \
            f'Sended headers: {dict(req.request.headers)}\n' + \
            f'Sended content: {req.request.body}'
            raise RequesterError(message)
        return req.json()


class BaseAPIClass:
    """ Базовый класс для методов АПИ клиента. """

    def __init__(self, requester: Requester):
        """ Инициализация базового класса методов АПИ клиента.

        :param requester: экземпляр класса-обертки requests
        :type requester: Requester
        """
        self.requester = requester


class Applicants(BaseAPIClass):

    def add(self, account_id: str, last_name: str, first_name: str, **kwargs) -> Dict[str, Union[int, str, List[Dict[str, int]]]]:
        """ Добавить кандидата в базу.

        https://github.com/huntflow/api/blob/master/ru/applicants.md#добавление-кандидата-в-базу

        Остальные именованные параметры в соответствие с документацией.

        :param account_id: идентификатор организации
        :type account_id: str
        :param last_name: фамилия
        :type last_name: str
        :param first_name: имя
        :type first_name: str
        :return: [description]
        :rtype: Dict[str, Union[int, str, List[Dict[str, int]]]]
        """
        # обязательные поля
        body = {
            'last_name': last_name,
            'first_name': first_name
        }
        # опциональные поля
        for field in (
            'middle_name',
            'phone',
            'email',
            'position',
            'company',
            'money',
            'birthday_day',
            'birthday_month',
            'birthday_year',
            'photo',
            'externals'
        ):
            value = kwargs.get(field)
            if value is not None:
                body[field] = value
        # URL
        url = f'account/{account_id}/applicants'
        return self.requester.request(url, http_method='POST', body=body)

    def add_to_vacancy(
            self,
            account_id: str,
            applicant_id: str,
            vacancy: int,
            status: int,
            **kwargs
        ) -> Dict[str, Union[int, str]]:
        """ Добавить кандидата на вакансию.

        https://github.com/huntflow/api/blob/master/ru/applicants.md#добавление-кандидата-на-вакансию

        Остальные именованные параметры в соответствие с документацией.

        :param account_id: идентификатор организации
        :type account_id: str
        :param applicant_id: идентификатор кандидата
        :type applicant_id: str
        :param vacancy: идентификатор вакансии
        :type vacancy: int
        :param status: этап подбора
        :type status: int
        :return: [description]
        :rtype: Dict[str, Union[int, str]]
        """
        # обязательные поля
        body = {
            'vacancy': vacancy,
            'status': status
        }
        # опциональные поля
        for field in (
            'comment',
            'files',
            'rejection_reason',
            'fill_quota'
        ):
            value = kwargs.get(field)
            if value is not None:
                body[field] = value
        # URL
        url = f'account/{account_id}/applicants/{applicant_id}/vacancy'
        return self.requester.request(url, http_method='POST', body=body)


class Directory(BaseAPIClass):

    def statuses(self, account_id: str) -> Dict[str, List[Dict[str, Union[str, int]]]]:
        """ Получить этапы подбора организации.

        https://github.com/huntflow/api/blob/master/ru/dicts.md#vacancy_statuses

        :param account_id: идентификатор организации
        :type account_id: str
        :return: список этапов подбора организаций
        :rtype: Dict[str, Union[int, List[Dict[str, Union[str, int]]]]]
        """
        url = f'account/{account_id}/vacancy/statuses'
        return self.requester.request(url)

    def sources(self, account_id: str) -> Dict[str, List[Dict[str, Union[str, int]]]]:
        """ Получить список источников резюме.

        https://github.com/huntflow/api/blob/master/ru/dicts.md#источники-резюме

        :param account_id: идентификатор организации
        :type account_id: str
        :return: список источников резюме
        :rtype: Dict[str, List[Dict[str, Union[str, int]]]]
        """
        url = f'/account/{account_id}/applicant/sources'
        return self.requester.request(url)


class File(BaseAPIClass):

    def upload(self, account_id: str, fp: str, parse: bool = True) -> Dict[str, Union[str, int, Dict[str, Union[str, int, List[str], Dict[str, Union[str, int]]]]]]:
        """ Загрузить файл.
        https://github.com/huntflow/api/blob/master/ru/upload.md#загрузка-и-распознавание-файлов

        :param account_id: идентификатор организации
        :type account_id: str
        :param fp: путь до файла
        :type fp: str
        :param parse: распознать поля, defaults to True
        :type parse: bool, optional
        :return: ответ на запрос
        :rtype: Dict[str, Union[str, int, Dict[str, Union[str, int, List[str], Dict[str, Union[str, int]]]]]]
        """
        url = f'account/{account_id}/upload'
        return self.upload_file(fp, url, parse)

    def upload_file(self, fp: str, url: str, parse: bool = True) -> Dict[str, Union[str, int, Dict[str, Union[str, int, List[str], Dict[str, Union[str, int]]]]]]:
        """ Загрузить файл на сервер.

        Читерский способ, использует curl в подпроцессе.

        :param fp: путь до файла
        :type fp: str
        :param url: путь для запроса
        :type url: str
        :param parse: True, чтобы парсить файл, иначе False, defaults to True
        :type parse: bool, optional
        :return: ответ на запрос
        :rtype: Dict[str, Union[str, int, Dict[str, Union[str, int, List[str], Dict[str, Union[str, int]]]]]]
        """
        url = urllib_parse.urljoin(self.requester.api_endpoint, url)
        if parse:
            parse = 'true'
        else:
            parse = 'false'
        command = [
            'curl', '-s', '-X', 'POST',
            '-H', 'User-Agent: {}'.format(self.requester.USER_AGENT),
            '-H', 'Content-Type: multipart/form-data',
            '-H', 'X-File-Parse: {}'.format(parse),
            '-H', 'Authorization: Bearer {}'.format(self.requester.token),
            '-F', 'file=@{}'.format(fp),
            url
        ]
        popen = subprocess.Popen(command, stdout=subprocess.PIPE)
        data = popen.stdout.read()
        if popen.poll() is None:
            popen.terminate()
            popen.wait(1)
            popen.kill()
            popen.wait(1)
        return json.loads(data)


class User(BaseAPIClass):

    def me(self) -> Dict[str, Union[str, int]]:
        """ Получить информацию о текущем пользователе.
        https://github.com/huntflow/api/blob/master/ru/user.md#получение-информации-о-текущем-пользователе

        :return: словарь с информацией о текущем пользователе
        :rtype: Dict[str, Union[str, int]]
        """
        return self.requester.request('me')

    def accounts(self) -> Dict[str, List[Dict[str, Union[str, int]]]]:
        """ Получить список доступных организаций текущего пользователя.
        https://github.com/huntflow/api/blob/master/ru/user.md#получение-информации-о-доступных-организациях

        :return: словарь со списком доступных организаций текущего пользователя
        :rtype: Dict[str, List[Dict[str, Union[str, int]]]]
        """
        return self.requester.request('accounts')


class Vacancies(BaseAPIClass):

    def get_list(
            self,
            account_id: str,
            mine: bool = False,
            opened: bool = False,
            count: int = 1,
            page: int = 1
        ) -> Dict[str, Union[int, List[Dict[str, Union[str, int]]]]]:
        """ Получить список вакансий.

        https://github.com/huntflow/api/blob/master/ru/vacancies.md#получение-списка-вакансий

        :param account_id: идентификатор организации
        :type account_id: str
        :param mine: вернуть вакансии, над которыми работает текущий пользователь, defaults to False
        :type mine: bool, optional
        :param opened: вернуть только открытые вакансии, defaults to False
        :type opened: bool, optional
        :param count: число объектов на странице, defaults to 1
        :type count: int, optional
        :param page: номер страницы, defaults to 1
        :type page: int, optional
        :return: список вакансий
        :rtype: Dict[str, Union[int, List[Dict[str, Union[str, int]]]]]
        """
        url = f'/account/{account_id}/vacancies'
        body = {}
        if mine:
            body['mine'] = True
        if opened:
            body['opened'] = True
        return self.requester.request(url, body=body, count=count, page=page)
