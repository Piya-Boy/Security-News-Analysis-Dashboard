import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from io import BytesIO
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

# URL ของ API
API_URL = "https://piyamianglae.pythonanywhere.com/data"

# Function to load and preprocess data from API
@st.cache_data(ttl=86400) 
def load_data_from_api():
    try:
        # ดึงข้อมูลจาก API
        response = requests.get(API_URL)
        if response.status_code != 200:
            st.error(f"Error fetching data from API: {response.text}")
            return None
        
        data = response.json()

        # เปลี่ยนข้อมูลเป็น DataFrame
        df = pd.DataFrame(data)

        # แปลงคอลัมน์ Date เป็น datetime
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

        # เพิ่มคอลัมน์ Month และ Year
        df["Month"] = df["Date"].dt.strftime("%B") 
        df["Year"] = df["Date"].dt.year.fillna(0).astype(int)

        return df
    except requests.RequestException as e:
        st.error(f"Error fetching data from API: {e}")
        return None
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None



# Function to convert DataFrame to CSV, JSON, or Excel
def convert_df(df, file_format):
    if file_format == 'CSV':
        return df.to_csv(index=False).encode('utf-8')
    elif file_format == 'JSON':
        return df.to_json(orient='records').encode('utf-8')
    elif file_format == 'Excel':
        # Use BytesIO to create an in-memory bytes buffer
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Sheet1')
        output.seek(0)  # Move cursor to the beginning of the buffer
        return output.read()
    else:
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

    # เพิ่มตัวเลือกประเภทการโจมตี
    available_categories = ["All"] + list(df["Category"].unique())
    selected_category = st.sidebar.selectbox("Select Attack Type", options=available_categories, index=0)

    # Filter data based on selected Month, Year, and Category
    filtered_df = df.copy()
    # Sort by Year in descending order◘
    filtered_df = filtered_df.sort_values(by="Year", ascending=False)
    if selected_month != "All":
        filtered_df = filtered_df[filtered_df["Month"] == selected_month]
    if selected_year != "All":
        filtered_df = filtered_df[filtered_df["Year"] == int(selected_year)]
    if selected_category != "All":
        filtered_df = filtered_df[filtered_df["Category"] == selected_category]


    # Group by Source and get the latest update for each source
    latest_updates = df.groupby('Source')['Date'].max().reset_index()
    
    # Sort the updates by Date in descending order
    latest_updates = latest_updates.sort_values(by='Date', ascending=False)
    
    # Display the updates
    st.sidebar.markdown("---", unsafe_allow_html=True)  # Add a single divider line
    for _, row in latest_updates.iterrows():
        full_source = row['Source']
        
        # Split the URL to get the domain or use the original source
        source = full_source.split('/')[2].replace("www.", "") if full_source.startswith(("http://", "https://")) else full_source
        
        # Format the domain with 'www.' if it's not already present
        formatted_source = f"www.{source}" if not source.startswith("www.") else source
        
        last_updated = row['Date'].strftime("%B %d, %Y")
        st.sidebar.markdown(f"**{formatted_source}**  \nUpdated on {last_updated}", unsafe_allow_html=True)  # Note the double space before \n

     # Add download button with format selection
    st.sidebar.markdown("---", unsafe_allow_html=True)
    file_format = st.sidebar.selectbox("Select Type", ["CSV", "Excel", "JSON"])
 
    # Convert DataFrame to selected format
    converted_data = convert_df(df, file_format)

    # Set MIME type and file extension
    if file_format == 'CSV':
        mime_type = 'text/csv'
        file_extension = 'csv'
    elif file_format == 'JSON':
        mime_type = 'application/json'
        file_extension = 'json'
    elif file_format == 'Excel':
        mime_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        file_extension = 'xlsx'

    # Download button
    st.sidebar.download_button(
        label=f"Download {file_format}",
        data=converted_data,
        file_name=f"security_news.{file_extension}",
        mime=mime_type
    )
    # Summary
    st.subheader(f"Yearly Summary" if selected_month == "All" or selected_year == "All" else "Monthly Summary")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Articles", len(filtered_df))
    with col2:
        unique_attack_types = len(filtered_df["Category"].unique())
        st.metric("Unique Attack Types", unique_attack_types)

    # Attack Types Trend
    col1, col2 = st.columns(2)
    with col1:
        st.subheader(f"{selected_month} {selected_year} Attack Types Trend" 
                    if selected_month != "All" and selected_year != "All" 
                    else "Attack Types Trend")
        
        if selected_month == "All" and selected_year != "All":
            # กรณีเลือกปีแต่ไม่เลือกเดือน: รวมตามเดือนในปีที่เลือก
            attack_timeline = (
                filtered_df[filtered_df["Year"] == int(selected_year)]
                .groupby("Month")["Category"]
                .value_counts()
                .unstack(fill_value=0)
            )
        elif selected_month != "All" and selected_year == "All":
            # กรณีเลือกเดือนแต่ไม่เลือกปี: รวมข้อมูลของเดือนนั้นๆ ในทุกปี
            attack_timeline = (
                filtered_df[filtered_df["Month"] == selected_month]
                .groupby("Year")["Category"]
                .value_counts()
                .unstack(fill_value=0)
            )
        elif selected_month == "All" and selected_year == "All":
            # กรณีไม่ได้เลือกทั้งเดือนและปี: รวมข้อมูลทั้งหมดตามปี
            attack_timeline = (
                filtered_df.groupby("Year")["Category"]
                .value_counts()
                .unstack(fill_value=0)
            )
        else:
            # กรณีเลือกทั้งเดือนและปี: แสดงข้อมูลเฉพาะเดือนในปีที่เลือก
            attack_timeline = (
                filtered_df[
                    (filtered_df["Year"] == int(selected_year)) &
                    (filtered_df["Month"] == selected_month)
                ]
                .groupby("Date")["Category"]
                .value_counts()
                .unstack(fill_value=0)
            )


        # Create line chart without markers
        fig_attack_timeline = go.Figure()
        for category in attack_timeline.columns:
            fig_attack_timeline.add_trace(
                go.Scatter(
                    x=attack_timeline.index,
                    y=attack_timeline[category],
                    name=category,
                    mode="lines",  # Line without points
                )
            )
        
        # Update chart layout
        fig_attack_timeline.update_layout(
            title=f"Attack Types Trend - {selected_month} {selected_year}",
            xaxis_title="Date" if selected_month != "All" and selected_year != "All" else "Year",
            hovermode="x unified",
        )
        # ไม่เอา xaxis แสดงเป็น 2021-01-01D00:00:00 แต่แสดงเป็น january 2021
        if selected_month == "All" and selected_year == "All":
            fig_attack_timeline.update_xaxes(type="category")
        elif selected_month == "All" and selected_year != "All":
            # Format for months in a single year
            fig_attack_timeline.update_xaxes(tickformat="%B-%Y")
        elif selected_month != "All" and selected_year == "All":
            # Format for years
            fig_attack_timeline.update_xaxes(tickformat="%Y")
        else:
            # Format for specific dates
            fig_attack_timeline.update_xaxes(tickformat="%B-%d-%Y")

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

    # if selected_month == "All" and selected_year == "All" show year 
    for _, row in displayed_df.iterrows():
        # with st.expander(f"{row['Date'].strftime('%B %d')} - {row['Title']}"):
        with st.expander(f"{row['Date'].strftime('%B %d %Y' if selected_month == 'All' and selected_year == 'All' else '%B %d')} - {row['Title']}"):
            st.write("", row["Summary"])

    # Show "More" button if there are more news articles to display
    if st.session_state.news_limit < len(filtered_df):
        st.button("More", on_click=load_more_news)


if __name__ == "__main__":
    main()
