# Para que funcione pon en el terminal:
# streamlit run app.py

from PIL import Image
import streamlit as st
import pandas as pd
import plotly.express as px
import random
import requests

TMDB_API_KEY = "7aea10942638f813719584d6a2f512c0"


st.set_page_config(page_title='Selector de pelis', page_icon="🎥", layout="wide")

# Header ----------------------------------

with st.container():
    st.title('¿Qué peli ver hoy?')
    st.write('Más fácil, más películas, menos drama')
    #st.write("[Google Drive >](https://docs.google.com/spreadsheets/d/1F2DuBLlwMgnVOZ7ALzqTzw-r2aaBNe9gKUBOBQKuvx8/edit#gid=0)")


with st.container():
    st.write("---")
    
    #st.subheader('Selector de películas')
    #st.write("##")


# Filtros ----------------------------------

movies = pd.read_csv('pelis_plot.csv')

movies['Country'] = movies['Country'].fillna("")

unique_movies = ['Drama', 'Comedia', 'Suspense', 'Romance', 'Crimen', 'Terror',
       'Misterio', 'Acción', 'Ciencia ficción', 'Aventura', 'Fantasía',
       'Historia', 'Animación', 'Bélica', 'Documental', 'Familia', 'Música',
       'Western', 'Película de TV' ]

unique_countries = ['United States of America', 'United Kingdom', 'France', 'Spain',
       'Germany', 'Japan', 'Italy', 'Canada', 'China', 'Hong Kong',
       'South Korea', 'Belgium', 'Australia', 'Mexico', 'India', 'Brazil',
       'New Zealand', 'Soviet Union', 'Luxembourg', 'South Africa', 'Norway',
       'Denmark', 'Ireland', 'Czech Republic', 'Argentina', 'Iceland',
       'Thailand', 'Sweden', 'Israel', 'Singapore', 'Netherlands', 'Taiwan',
       'Greece', 'Switzerland', 'Finland', 'Austria', 'Poland',
       'United Arab Emirates', 'Chile', 'Lebanon', 'Botswana', 'Nigeria',
       'Czechoslovakia']

unique_info = ['LGTB', 'plot twist', 'carcel', 'Serie', 'Anime', 'Plano secuencia',
       'mamá', 'thriller', 'tom cruise', 'clasicas que no vi']


# Sliders ----------------------------------

col1, col2, col3 = st.columns(3)

with col1:
    runtime_selection = st.slider(
        'Duración (mins):',
        min_value=int(movies['Runtime'].min()),
        max_value=int(movies['Runtime'].max()),
        value=(
            int(movies['Runtime'].min()),
            int(movies['Runtime'].max())
        )
    )

with col2:
    year_selection = st.slider(
        'Año de la peli:',
        min_value=int(movies['Year'].min()),
        max_value=int(movies['Year'].max()),
        value=(
            int(movies['Year'].min()),
            int(movies['Year'].max())
        ),
        step=1
    )

with col3:
    rating_selection = st.slider(
        'Puntuación:',
        min_value=float(movies['Rating'].min()),
        max_value=float(movies['Rating'].max()),
        value=(
            float(movies['Rating'].min()),
            float(movies['Rating'].max())
        )
    )



# Desplegables ----------------------------------

column1, column2, column3 = st.columns(3)

with column1:
    genre_selection = st.multiselect('Género: ', unique_movies, placeholder='Selecciona uno o más géneros')

with column2:
    country_selection = st.multiselect('País: ', unique_countries, placeholder='Selecciona uno o más países')

with column3:
    info_selection = st.multiselect('Categoría especial: ', unique_info, placeholder='Selecciona una categoría personal')




# Create a condition that requires all selected genres to be present in a movie
genre_conditions = [movies['Genre'].str.contains(genre, case=False) for genre in genre_selection]



# Combine the conditions with an "AND" condition (all conditions must be met)
if genre_conditions:
    genre_condition = pd.concat(genre_conditions, axis=1).any(axis=1)
else:
    # If no genres are selected, include all movies
    genre_condition = pd.Series(True, index=movies.index)

country_conditions = [movies['Country'].str.contains(country, case=False) for country in country_selection]

if country_conditions:
    country_condition = pd.concat(country_conditions, axis=1).any(axis=1)
else:
    country_condition = pd.Series(True, index=movies.index)


info_conditions = [movies['mi_info'].str.contains(info, case=False) for info in info_selection]

if info_conditions:
    info_condition = pd.concat(info_conditions, axis=1).any(axis=1)
else:
    info_condition = pd.Series(True, index=movies.index)




# Lógica filtros ----------------------------------


mask = (
    movies['Runtime'].between(*runtime_selection) &
    genre_condition &
    country_condition &
    info_condition &
    movies['Year'].between(*year_selection) &
    movies['Rating'].between(*rating_selection)
)

number_result = movies[mask].shape[0]


st.markdown(f'Resultados: {number_result}')
movies_filter = movies[mask].sort_values(by=['Rating'], ascending=False)
movies_filter = movies_filter.reset_index()

movies_filter = movies_filter.copy()

# Rating con 1 decimal
movies_filter['Rating'] = movies_filter['Rating'].round(1)

# Año sin decimales (entero)
movies_filter['Year'] = movies_filter['Year'].astype(int)



# Gráfico ----------------------------------


st.subheader("📊 Distribución de ratings")

chart_df = movies_filter.copy()

fig_data = chart_df["Rating"].round(1).value_counts().sort_index()

chart_df_plot = pd.DataFrame({
    "Rating": fig_data.index,
    "Número de pelis": fig_data.values
})

st.bar_chart(chart_df_plot.set_index("Rating"))



# Dataframe ----------------------------------


st.subheader("🍿 Películas disponibles")

st.dataframe(
    movies_filter,
    use_container_width=True,
    hide_index=True
)

st.write("")

@st.cache_data(show_spinner=False)
def get_poster(movie_name):
    url = "https://api.themoviedb.org/3/search/movie"
    params = {
        "api_key": TMDB_API_KEY,
        "query": movie_name,
        "language": "es-ES"
    }

    try:
        r = requests.get(url, params=params, timeout=5).json()

        if r.get("results"):
            poster_path = r["results"][0].get("poster_path")
            if poster_path:
                return f"https://image.tmdb.org/t/p/w500{poster_path}"
    except:
        return None

    return None


@st.cache_data(show_spinner=False)
def add_posters(df):
    df = df.copy()
    df["poster"] = df["Movie Spanish"].apply(get_poster)
    return df

if "seen_movies" not in st.session_state:
    st.session_state.seen_movies = set()

if number_result > 0:

    if st.button("🎲 Elegir una película al azar"):

        # quitar las ya vistas del filtro actual
        available_movies = movies_filter[
            ~movies_filter["Movie Spanish"].isin(st.session_state.seen_movies)
        ]

        # si ya viste todas
        if available_movies.empty:
            st.warning("Ya has visto todas las películas de este filtro 🎬")
        else:
            peli_aleatoria = available_movies.sample(1).iloc[0]

            # guardar como vista
            st.session_state.seen_movies.add(peli_aleatoria["Movie Spanish"])

            poster = get_poster(peli_aleatoria["Movie Spanish"])

            with st.container(border=True):

                col1, col2 = st.columns([1, 3])

                with col1:
                    if poster:
                        img = Image.open(requests.get(poster, stream=True).raw)
                        st.image(img, use_container_width=True)

                with col2:
                    st.subheader(f"🎬 {peli_aleatoria['Movie Spanish']}")

                    st.write(
                        f"⭐ {peli_aleatoria['Rating']}   |   "
                        f"📅 {peli_aleatoria['Year']}   |   "
                        f"⏱️ {peli_aleatoria['Runtime']} min"
                    )

                    if pd.notna(peli_aleatoria.get('mi_info')):
                        st.info(peli_aleatoria['mi_info'])

                    st.write(peli_aleatoria['sinopsis'])
else:
    st.warning("No hay películas que cumplan los filtros seleccionados.")



if st.button("🔄 Reset películas vistas"):
    st.session_state.seen_movies = set()