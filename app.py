import pickle
import gzip
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import streamlit as st
TMDB_API_KEY = st.secrets["TMDB_API_KEY"]


def create_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({"User-Agent": "Mozilla/5.0 (MovieRecommenderApp)"})
    return session


HTTP_SESSION = create_session()
PLACEHOLDER_POSTER = "https://via.placeholder.com/500x750?text=No+Poster"


@st.cache_data(show_spinner=False)
def fetch_poster(movie_id: int) -> str:
    url = f"https://api.themoviedb.org/3/movie/{movie_id}"
    params = {"api_key": TMDB_API_KEY}
    try:
        response = HTTP_SESSION.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        poster_path = data.get("poster_path")
        if poster_path:
            return f"https://image.tmdb.org/t/p/w500/{poster_path}"
    except requests.RequestException:
        pass
    return PLACEHOLDER_POSTER


def recommend(movie: str):
    movie_index = movies[movies["title"] == movie].index[0]
    distances = similarity[movie_index]
    movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

    recommended_movies = []
    recommended_movies_posters = []
    for i in movies_list:
        movie_id = int(movies.iloc[i[0]].movie_id)
        recommended_movies.append(movies.iloc[i[0]].title)
        recommended_movies_posters.append(fetch_poster(movie_id))

    return recommended_movies, recommended_movies_posters


movies_dict = pickle.load(open("movies.pkl","rb"))
movies = pd.DataFrame(movies_dict)
similarity = pickle.load(open("similarity.pkl", "rb"))

st.title("Movie Recommender System")

selected_movie_name = st.selectbox(
    "Select a movie",
    movies["title"].values,
)

if st.button("Recommend"):
    with st.spinner("Fetching recommendations..."):
        recommendation, posters = recommend(selected_movie_name)

    cols = st.columns(6)
    for i in range(6):
        with cols[i]:
            st.text(recommendation[i])
            st.image(posters[i])
