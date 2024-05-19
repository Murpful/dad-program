import pandas as pd
import streamlit as st
from datetime import datetime
import icalendar
from io import StringIO

# Function to create iCalendar file content
def create_icalendar(df):
    cal = icalendar.Calendar()
    
    for index, row in df.iterrows():
        event = icalendar.Event()
        event.add('summary', row['Schedule Event'])
        event.add('dtstart', row['Start'])
        event.add('dtend', row['End'])
        event.add('location', row['Location'])
        event.add('description', f"Device: {row['Device']}")
        cal.add_component(event)
    
    return cal.to_ical()

# Streamlit app
st.title('Event Schedule Upload and iCalendar Export')

# File upload
uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

if uploaded_file is not None:
    # Load the data from the uploaded CSV file
    data = pd.read_csv(uploaded_file, skiprows=2, delimiter=';')

    # Filter out rows where 'Start' or 'End' cannot be parsed as datetime
    def is_valid_datetime(date_str):
        try:
            pd.to_datetime(date_str)
            return True
        except ValueError:
            return False

    data = data[data['Start'].apply(is_valid_datetime) & data['End'].apply(is_valid_datetime)]

    # Convert the 'Start' and 'End' columns to datetime
    data['Start'] = pd.to_datetime(data['Start'])
    data['End'] = pd.to_datetime(data['End'])

    # Create new columns for date and time range
    data['Date'] = data['Start'].dt.date
    data['Time'] = data.apply(lambda row: "All day" if row['Start'].time() == row['End'].time() == pd.to_datetime('00:00').time() 
                              else f"{row['Start'].strftime('%H%M')} - {row['End'].strftime('%H%M')}", axis=1)

    # Select relevant columns for display
    display_data = data[['Schedule Event', 'Date', 'Time', 'Location', 'Device']]

    # Create the iCalendar file content
    ical_content = create_icalendar(data)

    # Display the data
    st.dataframe(display_data)

    # Provide download link for the iCalendar file
    st.download_button(label="Download iCalendar file", data=ical_content, file_name='event_schedule.ics', mime='text/calendar')
