from typing import Optional
import pandas as pd
import streamlit as st
import asyncio
import weather as wth

API_KEY: Optional[str] = None
data: Optional[pd.DataFrame] = None

st.set_page_config(layout="wide")  # позволим себе устанавливать ширину окна выводимых данных
st.title("Анализ температурных данных и мониторинг текущей температуры через OpenWeatherMap API")
st.header("Шаг 1: Загрузка данных")
uploaded_file = st.file_uploader("Выберите CSV-файл", type=["csv"])

if uploaded_file is not None:
    st.success("CSV-файл успешно загружен!")
    data = pd.read_csv(uploaded_file)
    data['timestamp'] = pd.to_datetime(data['timestamp'])
    st.write("Загруженный CSV-файл:")
    st.dataframe(data.head())
else:
    st.write("Загрузите CSV-файл")

if data is not None:
    st.header("Шаг 2: Выбор города")
    city = st.selectbox("Выберите город для мониторинга текущей температуры", data['city'].unique())
    if city is None:
        st.write("Выберите город!")
    else:
        st.header("Шаг 3: API-ключ OpenWeatherMap")

        API_KEY = st.text_input("Введите API-ключ")
        if API_KEY is not None and API_KEY != '':
            code, locale_city_name, date_time, temperature = asyncio.run(wth.get_city_weather(city, API_KEY))

            if code == 200:
                st.success("API-ключ успешно получен!")
                st.header(f"Шаг 4: Cтатистика для города {city}")
                st.header("Описательная статистика по историческим данным")
                st.write(data[data["city"] == city].drop(['timestamp'], axis=1).describe())
                data = wth.modify(data.copy())  # модифицируем датафрейм (добавляем точки аномальных температур, скользящее среднее и стандартное отклонение для дальнейшей визуализации)
                st.header("Cтатистика по сезонам для города")
                season_data = wth.process_seasonal_data(data[data['city'] == city]).drop('city', axis=1)
                st.table(season_data)
                st.header("Визуализация")
                fig = wth.visualize_temperature(data[data['city'] == city], city)
                st.pyplot(fig, use_container_width=True)
                st.write(f"Город: ${locale_city_name}$")
                st.write(f"Время: {date_time}")
                st.write(f"Температура в городе: ${temperature}$ градусов")
                season = wth.get_season(date_time)
                historical_season_data = season_data[season_data['season'] == season]
                lower_bound = historical_season_data['average'].iloc[0] - 2 * historical_season_data['std'].iloc[0]
                upper_bound = historical_season_data['average'].iloc[0] + 2 * historical_season_data['std'].iloc[0]

                if temperature < lower_bound:
                    st.write("**Аномально низкая температура**")
                elif temperature > upper_bound:
                    st.write("**Аномально высокая температура**")
                else:
                    st.write("**Температура соответствует историческим данным**")

            else:
                st.write(
                    '{"cod":401, "message": "Invalid API key. Please see https://openweathermap.org/faq#error401 for more info."}')
        else:
            st.write("Для дальнейшего анализа вам необходимо ввести API-ключ")
else:
    st.write(
        """
            **CSV-файл должен быть следующего формата:**
            - `city`: Название города.
            - `timestamp`: Дата (с шагом в 1 день).
            - `temperature`: Среднесуточная температура (в °C).
            - `season`: Сезон года (зима, весна, лето, осень).

        """
    )