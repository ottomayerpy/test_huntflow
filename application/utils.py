import argparse
import os
from logging import DEBUG, Formatter, Logger, StreamHandler
from sys import stdout
from typing import Union

from reader import normalize
from settings import LOGGER_FORMAT


def find_resume(base: str, position: str, last_name: str, first_name: str, middle_name: str = None) -> Union[str, None]:
    """ Получить путь резюме.

    Подразумеваем, что резюме кандидатов сгруппированы в директориях, название которых соответствуют названиям вакансий,
    эти директории находятся в той же директории, что файл БД. Файлы резюме должны иметь названия, которые начинаются с
    полного имени кандидата в БД. Допустимо полное имя без отчества:

    "<фамилия_кандидата> <имя_кандидата> [<отчество_кандидата>]"

    :param base: абсолютный путь до файла БД
    :type base: str
    :param position: название вакансии
    :type position: str
    :param last_name: фамилия кандидата
    :type last_name: str
    :param first_name: имя кандидата
    :type first_name: str
    :param middle_name: отчество кандидата, defaults to None
    :type middle_name: str, optional
    :return: абсолютный путь до резюме, если найдено, иначе None
    :rtype: Union[str, None]
    """
    path = os.path.join(base, position)
    full_name = ' '.join((last_name, first_name))
    if middle_name:
        full_name += ' ' + middle_name
    for file in os.scandir(path):
        fn = normalize(file.name)
        if fn.startswith(full_name):
            return file.path


def update_applicant_from_resume(applicant: dict, resume: dict):
    """ Обновить словарь кандидата данными, полученными после парсинга резюме.

    :param applicant: словарь кандидата
    :type applicant: dict
    :param resume: словарь данных из резюме
    :type resume: dict
    """

    if not resume:
        return

    # если в резюме нашлось фото, то добавляем к кандидату
    if resume['photo']:
        applicant['photo'] = resume['photo']['id']

    # добавляем ссылку на резюме. Предполагаем, что это просто резюме в тестовом формате (нужно дополнить документацию
    # в части указания обязательного параметра "auth_type")
    external = {
        'files': [
            {
                'id': resume['id']
            }
        ],
        'auth_type': 'NATIVE'
    }
    applicant['externals'] = [external]

    # если получен текст резюме, то его тоже добавляем
    if resume['text']:
        external['data'] = {
            'body': resume['text']
        }

    # разбираемся с данными о кандидате, которые получены из резюме
    applicant_data = resume.get('fields')
    if applicant_data:

        # если в БД не указано отчество, а оно есть в резюме, то добавляем
        if 'middle_name' not in applicant:
            if 'name' in applicant_data and 'middle' in applicant_data['name']:
                applicant['middle_name'] = applicant_data['name']['middle']

        # если получена электронная почта, то добавляем
        if 'email' in applicant_data:
            applicant['email'] = applicant_data['email']

        # если получены телефоны, то добавляем первый
        if 'phones' in applicant_data:
            applicant['phone'] = applicant_data['phones'][0]

        # если получена дата рождения, то добавляем ее
        if 'birthdate' in applicant_data and applicant_data['birthdate'] is not None:
            birthdate = applicant_data['birthdate']
            for period in ('year', 'month', 'day'):
                if period in birthdate:
                    applicant[f'birthday_{period}'] = birthdate[period]
                else:
                    break


def agruments_parse():
    """ Парсинг аргументов командной строки """
    arg_parser = argparse.ArgumentParser(
        description='Candidate loader.',
    )
    arg_parser.add_argument(
        'token',
        help='Personal token',
    )
    arg_parser.add_argument(
        'database_path',
        help='Path to database',
    )
    return arg_parser.parse_args()


def load_logger() -> Logger:
    """ Инициализация логгера """
    logger = Logger('Applicants loader', DEBUG)
    formatter = Formatter(LOGGER_FORMAT)
    handler = StreamHandler(stdout)
    handler.setFormatter(formatter)
    handler.setLevel(DEBUG)
    logger.addHandler(handler)
    logger.debug('Логгер инициализирован')
    return logger
