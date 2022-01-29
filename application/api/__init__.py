from .api import Applicants, Directory, File, Requester, User, Vacancies


class Client:

    def __init__(self, token: str, api_endpoint: str):
        """ Инициализация клиента.

        :param token: персональный токен
        :type token: str
        :param api_endpoint: точка доступа к АПИ
        :type api_endpoint: str
        """
        self._requester = Requester(token, api_endpoint)
        self._vacancies = None
        self._directory = None
        self._user = None
        self._file = None
        self._applicants = None

    @property
    def vacancies(self) -> Vacancies:
        """ Свойство для методов работы с вакансиями.

        https://github.com/huntflow/api/blob/master/ru/vacancies.md
        """
        if self._vacancies is None:
            self._vacancies = Vacancies(self._requester)
        return self._vacancies

    @property
    def user(self) -> User:
        """ Свойство для методов информации о пользователе.

        https://github.com/huntflow/api/blob/master/ru/user.md
        """
        if self._user is None:
            self._user = User(self._requester)
        return self._user

    @property
    def directory(self) -> Directory:
        """ Свойство для методов справочников.

        https://github.com/huntflow/api/blob/master/ru/dicts.md
        """
        if self._directory is None:
            self._directory = Directory(self._requester)
        return self._directory

    @property
    def file(self) -> File:
        """ Свойство для методов загрузки и распознавания файлов.

        https://github.com/huntflow/api/blob/master/ru/upload.md
        """
        if self._file is None:
            self._file = File(self._requester)
        return self._file

    @property
    def applicants(self) -> Applicants:
        """ Свойство для методов работы с кандидатами.

        https://github.com/huntflow/api/blob/master/ru/applicants.md
        """
        if self._applicants is None:
            self._applicants = Applicants(self._requester)
        return self._applicants
