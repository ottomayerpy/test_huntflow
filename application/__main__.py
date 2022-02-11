import os

from api import Client
from reader import XLSXReader, FIELDS
from settings import API_ENDPOINT, STATUS_FILE
from utils import (agruments_parse, find_resume, load_logger,
                   update_applicant_from_resume)

# Загружаем логгер
logger = load_logger()

args = agruments_parse()
base_path, _ = os.path.split(args.database_path)

reader = XLSXReader(FIELDS)
client = Client(args.token, API_ENDPOINT)

# Идентификатор организации
account_id = client.user.accounts()['items'][0]['id']

# Словарь вакансий. Ключ - название вакансии, значение - словарь с данными вакансии
vacancies = client.vacancies.get_list(account_id, count=100)['items']
vacancies = {vacancy['position']: vacancy for vacancy in vacancies}

# Словарь этапов согласования кандидата. Ключ - название этапа, значение - словарь с данными этапа
statuses = client.directory.statuses(account_id)['items']
statuses = {statuse['name']: statuse for statuse in statuses}

# Получение строки, с которой будет начато чтение
status_file = os.path.join(base_path, STATUS_FILE)
if os.path.exists(status_file):
    with open(status_file) as file:
        row_number = int(file.read())
else:
    row_number = 1

if __name__ == "__main__":
    try:
        with reader.open(args.database_path):
            while True:
                # Чтение строки данных о кандидате
                logger.debug(f'Обработка записи №{row_number}.')
                candidate = reader.read_row(row_number)
                if not candidate:
                    logger.info('Данные о кандидате не получены, похоже, все кандидаты загружены.')
                    break

                # Получаем вакансии и статус
                vacancy = vacancies.get(candidate['vacancy'])
                if vacancy is None:
                    logger.warning('Ошибка при опеределении вакансии кандидата, кандидат не будет зарегистрирован на вакансию.')

                status = statuses.get(candidate['status'])
                if status is None:
                    logger.warning('Ошибка при опеределении статуса кандидата, кандидат не будет зарегистрирован на вакансию.')

                # Создаем словарь персональных данных
                applicant = {
                    'last_name': candidate['last_name'],
                    'first_name': candidate['first_name'],
                    'money': candidate['money']
                }
                if 'middle_name' in candidate:
                    applicant['middle_name'] = candidate['middle_name']

                # Получаем файл с резюме и загружаем (запрашиваем парсинг)
                resume_fp = find_resume(
                    base_path,
                    candidate['vacancy'],
                    applicant['last_name'],
                    applicant['first_name'],
                    applicant.get('middle_name')
                )
                if resume_fp is None:
                    logger.warning('Ошибка при получении файла резюме, резюме не будет загружено.')
                    resume = {}
                else:
                    resume = client.file.upload(account_id, resume_fp)

                # Обновляем данные кандидата из БД данными из резюме
                update_applicant_from_resume(applicant, resume)

                # Добавляем кандидата в базу
                applicant = client.applicants.add(account_id, **applicant)
                logger.debug('Кандидат добавлен на сервер.')

                if status and vacancy:
                    # Добавляем кандидата на вакансию
                    applicant_to_vacancy_data = {
                        'vacancy': vacancy['id'],
                        'status': status['id'],
                        'comment': candidate['comment'],
                        'files': [{'id': resume['id']}]
                    }
                    request = client.applicants.add_to_vacancy(account_id, applicant['id'], **applicant_to_vacancy_data)
                    logger.debug(f'Кандидат зарегистрирован на вакансию.')

                row_number += 1
    finally:
        # Сохраняем строку, на которой остановились
        with open(status_file, 'wt') as file:
            file.write(str(row_number))
