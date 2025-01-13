import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import requests
import nltk
import calendar
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import re

# Download NLTK data
nltk.download("punkt")
nltk.download("stopwords")

# Page configuration
logo="https://img5.pic.in.th/file/secure-sv1/logos02edf0d066b19226.png"
st.set_page_config(page_title="Security News Analysis", page_icon=logo, layout="wide", )
# tab_logo="logos.png"

# URL ของ API
API_URL = "https://piyamianglae.pythonanywhere.com/data"

# Function to load and preprocess data from API
@st.cache_data(ttl=86400)  # Cache data for 24 hours
def load_data_from_api():
    try:
        # ดึงข้อมูลจาก API
        response = requests.get(API_URL)
        # response.raise_for_status()  # ตรวจสอบว่าการเรียก API สำเร็จหรือไม่
        if response.status_code != 200:
            st.error(f"Error fetching data from API: {response.text}")
            return None
        
        data = response.json()

        # เปลี่ยนข้อมูลเป็น DataFrame
        df = pd.DataFrame(data)

        # แปลงคอลัมน์ Date เป็น datetime
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

        # เพิ่มคอลัมน์ Month และ Year
        df["Month"] = df["Date"].dt.strftime("%B")  # เช่น January, February
        df["Year"] = df["Date"].dt.year.fillna(0).astype(int)

        return df
    except requests.RequestException as e:
        st.error(f"Error fetching data from API: {e}")
        return None
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None


def main():
    st.title("Security News Analysis Dashboard")

    # Load data from API
    df = load_data_from_api()

    if df is None or df.empty:
        st.error("No data to display.")
        return

    # Logo
    st.sidebar.image(logo,caption="")

    # Sidebar filter
    st.sidebar.header("Filter")
    # เพิ่มตัวเลือก "All" สำหรับ Month และ Year
    available_months = ["All"] + list(df["Month"].unique())
    available_years = ["All"] + list(df["Year"].unique())

    selected_month = st.sidebar.selectbox("Select Month", options=available_months, index=0)
    selected_year = st.sidebar.selectbox("Select Year", options=available_years, index=0)

    # Sort by Year in descending order
    df = df.sort_values(by=["Year"], ascending=False)

    # Filter data based on selected Month and Year
    if selected_month != "All" and selected_year != "All":
        filtered_df = df[(df["Month"] == selected_month) & (df["Year"] == int(selected_year))]
    elif selected_month != "All":
        filtered_df = df[df["Month"] == selected_month]
    elif selected_year != "All":
        filtered_df = df[df["Year"] == int(selected_year)]
    else:
        filtered_df = df  # ถ้าเลือก "All" ทั้ง Month และ Year

    # Display last updated date
    last_updated = df["Date"].max().strftime("%B %d, %Y")
    st.sidebar.markdown(f"---\n**Updated:** {last_updated}", unsafe_allow_html=True)

    #  Summary
    st.subheader(f"Yearly Summary" if selected_month == "All" or selected_year == "All" else "Monthly Summary")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Articles", len(filtered_df))
    with col2:
        unique_attack_types = len(filtered_df["Category"].unique())
        st.metric("Unique Attack Types", unique_attack_types)

    # Trend and Distribution Charts
    col1, col2 = st.columns(2)
    with col1:
        st.subheader(f"{selected_month} {selected_year} Attack Types Trend" if selected_month != "All" and selected_year != "All" else "Attack Types Trend")
        attack_timeline = filtered_df.groupby("Date")["Category"].value_counts().unstack(fill_value=0)
        fig_attack_timeline = go.Figure()
        for category in attack_timeline.columns:
            fig_attack_timeline.add_trace(
                go.Scatter(
                    x=attack_timeline.index,
                    y=attack_timeline[category],
                    name=category,
                    mode="lines+markers",
                )
            )
        fig_attack_timeline.update_layout(
            title=f"Daily Attack Types Trend - {selected_month} {selected_year}",
            xaxis_title="Date",
            yaxis_title="Number of Articles",
            hovermode="x unified",
        )
        st.plotly_chart(fig_attack_timeline, use_container_width=True)

    with col2:
        st.subheader("Attack Types Distribution")
        attack_counts = filtered_df["Category"].value_counts()
        fig_attacks = px.pie(
            values=attack_counts.values,
            names=attack_counts.index,
            title=f"Distribution of Attack Types - {selected_month}",
        )
        st.plotly_chart(fig_attacks, use_container_width=True)

    # Yearly Attacks
    st.subheader("Yearly Attacks")
    attacks_by_year = df.groupby("Year").size().reset_index(name="count")
    # Sort by Year in descending order◘
    attacks_by_year = attacks_by_year.sort_values(by="Year", ascending=False)
    fig_yearly_attacks = px.bar(attacks_by_year, x="Year", y="count")
    fig_yearly_attacks.update_xaxes(type="category")
    st.plotly_chart(fig_yearly_attacks, use_container_width=True)

    # Initialize session state for news limit
    if "news_limit" not in st.session_state:
        st.session_state.news_limit = 5
    
    # Function to load more news
    def load_more_news():
        st.session_state.news_limit += 5
    
    # Display news articles
    st.subheader(f"Security News - {selected_month} {selected_year}")
    displayed_df = filtered_df.head(st.session_state.news_limit)
    
    for _, row in displayed_df.iterrows():
        with st.expander(f"{row['Date'].strftime('%B %d %Y' if selected_month == 'All' and selected_year == 'All' else '%B %d')} - {row['Title']}"):
            st.write("", row["Summary"])
    
    # Show "More" button if there are more news articles to display
    if st.session_state.news_limit < len(filtered_df):
        st.button("More", on_click=load_more_news)


if __name__ == "__main__":
    main()
