import matplotlib.pyplot as plt
from datetime import datetime
import aiohttp

BASE_URL = "https://api.openweathermap.org/"


async def fetch_json(url):
    # Асинхронный запрос к API
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()


async def get_city_weather(city, api_key):
    # Получение информации о городе и температуре
    location_url = f"{BASE_URL}geo/1.0/direct?q={city}&appid={api_key}"
    location_data = await fetch_json(location_url)

    if not location_data or ('cod' in location_data and location_data['cod'] == 401):
        return 401, None, None, None

    lat, lon = location_data[0]['lat'], location_data[0]['lon']
    localized_name = location_data[0]['local_names'].get('ru', city)

    weather_url = f"{BASE_URL}data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={api_key}"
    weather_data = await fetch_json(weather_url)

    sunrise_time = datetime.fromtimestamp(weather_data['sys']['sunrise'])
    current_temperature = weather_data['main']['temp']

    return 200, localized_name, sunrise_time, current_temperature


def modify(df):
    # Добавление статистических данных в DataFrame(скользящего среднего и стандартного отклонения для сглаживания температурных колебаний)
    # Определение аномалий на основе отклонений температуры от скользящее среднее±2σ
    df['mean_temp'] = df.groupby('city')['temperature'].transform(lambda t: t.rolling(window=30).mean())
    df['std_temp'] = df.groupby('city')['temperature'].transform(lambda t: t.rolling(window=30).std())

    df['lower_limit'] = df['mean_temp'] - 2 * df['std_temp']
    df['upper_limit'] = df['mean_temp'] + 2 * df['std_temp']
    df['is_anomaly'] = (df['temperature'] < df['lower_limit']) | (df['temperature'] > df['upper_limit'])
    return df


def process_seasonal_data(df):
    return df.groupby(['city', 'season'])['temperature'].agg(average='mean', std='std', min='min',
                                                               max='max').reset_index()


def get_season(date):
    # Определение сезона по месяцу по дате
    month = date.month
    if month in (12, 1, 2):
        return 'winter'
    if month in (3, 4, 5):
        return 'spring'
    if month in (6, 7, 8):
        return 'summer'
    return 'autumn'


def visualize_temperature(data, city_name):
    # Визуализация временного ряда температуры
    fig, ax = plt.subplots(figsize=(18, 8))

    plt.plot(data['timestamp'], data['temperature'], label='Температура')
    plt.plot(data['timestamp'], data['mean_temp'], label='Скользящее среднее (30 дней)', color='purple')

    anomalies = data[data['is_anomaly']]
    plt.scatter(anomalies['timestamp'], anomalies['temperature'], color='red', label='Аномалии', zorder=5)

    plt.title(f'Динамика температуры в {city_name}')
    plt.xlabel('Дата')
    plt.ylabel('Температура (°C)')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)

    plt.tight_layout()
    return fig
