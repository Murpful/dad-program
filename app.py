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
        event.add('description', row['Description'])
        cal.add_component(event)
    
    return cal.to_ical()

# Streamlit app
st.title('Event Schedule Upload and iCalendar Export')

# Initialize session state if not already initialized
if 'data' not in st.session_state:
    st.session_state['data'] = None
if 'additional_info' not in st.session_state:
    st.session_state['additional_info'] = {}

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
    
    # Initialize empty columns for additional information
    data['Description'] = ""

    # Save data to session state
    st.session_state['data'] = data

# Load data from session state
if st.session_state['data'] is not None:
    data = st.session_state['data']
    
    # Default instructor name
    default_instructor = "Stephen LePrell"

    # Iterate through each event to gather additional information
    for index, row in data.iterrows():
        if row['Schedule Event'] == 'Requested Off' or row['Schedule Event'] == 'Day Off':
            data.at[index, 'Description'] = "Non-teaching event"
            continue
        
        st.write(f"Event: {row['Schedule Event']}, Date: {row['Date']}")
        
        # Initialize session state variables before creating widgets
        if f'is_teaching_event_{index}' not in st.session_state:
            st.session_state[f'is_teaching_event_{index}'] = 'No'
        is_teaching_event = st.radio(f"Is this a teaching event?", options=['No', 'Yes'], index=0 if st.session_state[f'is_teaching_event_{index}'] == 'No' else 1, key=f"is_teaching_event_{index}")

        if is_teaching_event == 'Yes':
            if f'instructor_name_{index}' not in st.session_state:
                st.session_state[f'instructor_name_{index}'] = default_instructor
            instructor_name = st.text_input("Instructor Name", value=st.session_state[f'instructor_name_{index}'], key=f"instructor_name_{index}")

            if f'seat_support_name_{index}' not in st.session_state:
                st.session_state[f'seat_support_name_{index}'] = ""
            seat_support_name = st.text_input("Seat Support Name", value=st.session_state[f'seat_support_name_{index}'], key=f"seat_support_name_{index}")

            if f'students_{index}' not in st.session_state:
                st.session_state[f'students_{index}'] = ""
            students = st.text_area("Students (comma separated)", value=st.session_state[f'students_{index}'], key=f"students_{index}")

            if f'location_{index}' not in st.session_state:
                st.session_state[f'location_{index}'] = ""
            location = st.text_input("Location", value=st.session_state[f'location_{index}'], key=f"location_{index}")

            # Update the description with the entered values
            description = f"Instructor: {instructor_name}\nSeat Support: {seat_support_name}\nStudents: {students}\nLocation: {location}"
            data.at[index, 'Description'] = description
        else:
            data.at[index, 'Description'] = "Non-teaching event"
        
        # Add a horizontal line between entries
        st.markdown("<hr style='border: 2px solid black;'>", unsafe_allow_html=True)

    # Save updated data back to session state
    st.session_state['data'] = data

    # Select relevant columns for display
    display_data = data[['Schedule Event', 'Date', 'Time', 'Description']]

    # Create the iCalendar file content
    ical_content = create_icalendar(data)

    # Display the data
    st.dataframe(display_data)

    # Provide download link for the iCalendar file
    st.download_button(label="Download iCalendar file", data=ical_content, file_name='event_schedule.ics', mime='text/calendar')
