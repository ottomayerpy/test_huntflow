from reader import FullNameField, Salary, StatsField, StringField

# Инициализация чтеца и клиента
FIELDS = (
    StringField('vacancy'),
    FullNameField('full name'),
    Salary('money', 'руб'),
    StringField('comment'),
    StatsField('status'),
)

API_ENDPOINT = 'https://dev-100-api.huntflow.dev/'

STATUS_FILE = 'status'

LOGGER_FORMAT = '%(asctime)s | %(name)s | %(levelname)-8s | %(message)s'
