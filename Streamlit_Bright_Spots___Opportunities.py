import os
import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# Configuring Streamlit page settings
st.set_page_config(
    page_title="GPT-4o Chat",
    page_icon=":)",
    layout="centered"
)

# Initialize chat session in Streamlit if not already present
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Streamlit page title
st.title("Data Analysis")

# Load the data
@st.cache_data
def load_data(file_path):
    data = pd.read_csv(file_path)
    return data

data = load_data('C:/Users/5hja5j/Documents/2024 Data as of 8.12.24.csv')

# Sidebar for filtering data
st.sidebar.header("Filter Data")

# Multi-select for Parent Company
parent_companies = st.sidebar.multiselect(
    "Select Parent Company",
    options=data['Parent Company Name'].unique(),
    default=data['Parent Company Name'].unique()
)

# Multi-select for Business Unit
business_units = st.sidebar.multiselect(
    "Select Business Unit",
    options=data['Aptiv Business Unit'].unique(),
    default=data['Aptiv Business Unit'].unique()
)

# Multi-select for Department
departments = st.sidebar.multiselect(
    "Select Department",
    options=data['Department'].unique(),
    default=data['Department'].unique()
)

# Text input for searching specific words/phrases
search_query = st.sidebar.text_input("Search for a word or phrase:")

# Filter the data based on selections
filtered_data = data[
    (data['Parent Company Name'].isin(parent_companies)) & 
    (data['Aptiv Business Unit'].isin(business_units)) & 
    (data['Department'].isin(departments))
]

# Apply search filter across specified columns
if search_query:
    search_columns = [col for col in filtered_data.columns if col not in ['Department', 'Flow Question (Updated)']]
    filtered_data = filtered_data[
        filtered_data[search_columns].apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)
    ]

# Header for total count of responses after filtering
total_responses = len(filtered_data)
st.header(f"Total Responses: {total_responses}")

# Exclude 'N/A' literal values for Flow Analysis
filtered_flow_data = filtered_data[(filtered_data['Flow Question (Updated)'] != "N/A") & filtered_data['Flow Question (Updated)'].notna()]

# Debug: Check if filtered_flow_data has any rows and the column exists
st.write("### Filtered Flow Data")
st.write(filtered_flow_data.head())  # Display first few rows of filtered_flow_data

# Bubble chart for Flow information
st.write("### Flow Analysis")
if not filtered_flow_data.empty:
    flow_summary = filtered_flow_data.groupby('Flow Question (Updated)').agg(
        count=('NPS Rating', 'size'),
        avg_nps=('NPS Rating', 'mean')
    ).reset_index()

    fig = px.scatter(
        flow_summary,
        x="Flow Question (Updated)",
        y="count",
        size="count",
        color="avg_nps",
        color_continuous_scale=px.colors.diverging.RdYlGn,
        range_color=[0, 10],
        labels={"Flow Question (Updated)": "Flow", "count": "Number of Responses"},
        title="Flow Analysis: NPS and Response Distribution",
        height=600
    )
    fig.update_layout(
        title_x=0.5,
        xaxis_title="Flow",
        yaxis_title="Number of Responses",
        showlegend=False,
        coloraxis_colorbar=dict(title="Average NPS", tickvals=[0, 5, 10])
    )
    st.plotly_chart(fig)
else:
    st.write("No valid data for 'Flow Question (Updated)' after filtering.")

# NPS Analysis with Stoplight Chart
# Helper function to categorize NPS ratings
def categorize_nps(nps):
    if nps <= 6:
        return "Detractor"
    elif nps <= 8:
        return "Passive"
    else:
        return "Promoter"

# Apply the categorization to the filtered data
filtered_data['NPS Category'] = filtered_data['NPS Rating'].apply(categorize_nps)

# NPS Analysis with Stoplight Chart
nps_summary = filtered_data.groupby(['Aptiv Business Unit', 'Department']).agg(
    avg_nps=('NPS Rating', 'mean'),
    median_nps=('NPS Rating', 'median'),
    detractors=('NPS Category', lambda x: (x == 'Detractor').sum()),
    passives=('NPS Category', lambda x: (x == 'Passive').sum()),
    promoters=('NPS Category', lambda x: (x == 'Promoter').sum()),
    total_responses=('NPS Rating', 'size')
).reset_index()

# Calculate percentages
nps_summary['detractor_percent'] = nps_summary['detractors'] / nps_summary['total_responses'] * 100
nps_summary['passive_percent'] = nps_summary['passives'] / nps_summary['total_responses'] * 100
nps_summary['promoter_percent'] = nps_summary['promoters'] / nps_summary['total_responses'] * 100

# Function to create stoplight chart using emojis
def stoplight_chart(row):
    detractors = f"🔴 {row['detractors']} ({row['detractor_percent']:.1f}%)"
    passives = f"🟡 {row['passives']} ({row['passive_percent']:.1f}%)"
    promoters = f"🟢 {row['promoters']} ({row['promoter_percent']:.1f}%)"
    return f"{detractors} | {passives} | {promoters}"

nps_summary['stoplight'] = nps_summary.apply(stoplight_chart, axis=1)

# Display the enhanced NPS summary
st.write("### NPS Summary with Stoplight Chart")
st.dataframe(
    nps_summary[['Aptiv Business Unit', 'Department', 'stoplight', 'avg_nps', 'median_nps', 'total_responses']].style
    .background_gradient(cmap="RdYlGn", subset=['avg_nps', 'median_nps'])
    .format(precision=2)
)

# Function to generate categorized insights
def generate_insights(flow_data):
    # Define a helper function to format the feedback string
    def format_feedback(row):
        # Extract the necessary fields
        why_response = row['Why? EN']
        what_better_response = row['What can Aptiv do to serve you better? EN']
        customer_tell = row['What did the customer tell you?']
        worth_sharing = row['What did you learn that\'s worth sharing?']
        unresolved_issue = row['If there is an unresolved issue, please provide further details']
        opportunities = row['Are there any opportunities you can identify']
        immediate_actions = row['Ticket FollowUp: What immediate actions are you taking to address the feedback?']
        customer_name = row['Customer Full Name']
        department = row['Department']
        
        # Format the string with the customer's name, department, and responses
        feedback_string = (
            f"\n\n"
            f"**Why? EN**: {why_response}\n\n"
            f"**What can Aptiv do to serve you better? EN**: {what_better_response}\n\n"
            f"**What did the customer tell you?**: {customer_tell}\n\n"
            f"**What did you learn that's worth sharing?**: {worth_sharing}\n\n"
            f"**If there is an unresolved issue, please provide further details**: {unresolved_issue}\n\n"
            f"**Are there any opportunities you can identify?**: {opportunities}\n\n"
            f"**Ticket FollowUp: What immediate actions are you taking to address the feedback?**: {immediate_actions}\n\n"
            f"-({customer_name}, {department})"
        )
        return feedback_string

    # Generate the formatted feedback for each category
    detractor_feedback = flow_data[flow_data['NPS Rating'] <= 6].apply(format_feedback, axis=1).tolist()
    passive_feedback = flow_data[flow_data['NPS Rating'].between(7, 8)].apply(format_feedback, axis=1).tolist()
    promoter_feedback = flow_data[flow_data['NPS Rating'] > 8].apply(format_feedback, axis=1).tolist()

    # Build the insights string
    insights = ""
    
    if promoter_feedback:
        insights += f"\n\n**Promoter Feedback (9-10):**\n- " + "\n\n- ".join(promoter_feedback) + "\n"
    if passive_feedback:
        insights += f"\n\n**Passive Feedback (7-8):**\n- " + "\n\n- ".join(passive_feedback) + "\n"
    if detractor_feedback:
        insights += f"\n\n**Detractor Feedback (0-6):**\n- " + "\n\n- ".join(detractor_feedback) + "\n"

    return insights or "No significant feedback available."

# Customer Feedback and Journey Insights
st.write("### Customer Feedback and Journey Insights")

if not filtered_flow_data.empty:
    # Iterate over each unique flow and display the relevant customer feedback
    for flow in filtered_flow_data['Flow Question (Updated)'].unique():
        st.write(f"#### Flow: {flow}")
        flow_data = filtered_flow_data[filtered_flow_data['Flow Question (Updated)'] == flow][
            ['Customer Full Name', 'NPS Rating', 'Why? EN', 'What can Aptiv do to serve you better? EN', 'What did the customer tell you?', 'What did you learn that\'s worth sharing?',
             'If there is an unresolved issue, please provide further details', 'Are there any opportunities you can identify', 'Ticket FollowUp: What immediate actions are you taking to address the feedback?', 
             'Department']
        ]
        st.dataframe(flow_data.style.set_properties(**{
            'background-color': '#f9f9f9',
            'color': '#000000',
            'border-color': '#d3d3d3',
            'border-width': '1px',
            'border-style': 'solid'
        }))
        
        # Generate and display insights
        insights = generate_insights(flow_data)
        st.markdown(f"**Insights for {flow}:**\n{insights}")
else:
    st.write("No customer feedback available for the selected flows.")

# Chat Interface
st.write("## Chat with GPT-4o")

# Display chat history
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input field for user's message
user_prompt = st.chat_input("Ask GPT-4o...")

if user_prompt:
    # Add user's message to chat and display it
    st.chat_message("user").markdown(user_prompt)
    st.session_state.chat_history.append({"role": "user", "content": user_prompt})

    # Simulate a response (if needed, replace this with actual response logic)
    assistant_response = "This is a simulated response."
    st.session_state.chat_history.append({"role": "assistant", "content": assistant_response})

    # Display GPT-4o's response
    with st.chat_message("assistant"):
        st.markdown(assistant_response)
