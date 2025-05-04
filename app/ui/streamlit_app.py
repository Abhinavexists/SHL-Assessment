import streamlit as st
import requests
import os
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Config for API URL
API_URL = os.environ.get("API_URL", "http://localhost:8000")

# Initialize session state
if "theme" not in st.session_state:
    st.session_state.theme = "light"
if "query_text" not in st.session_state:
    st.session_state.query_text = ""

def select_example(example_text):
    st.session_state.query_text = example_text

st.set_page_config(
    page_title="SHL Assessment Recommendations",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

theme = st.session_state.theme

# Dark mode CSS
dark_mode_css = """
<style>
    /* Dark mode variables */
    :root {
        --background-color: #121212;
        --text-color: #f0f0f0;
        --card-bg: #1e1e1e;
        --card-border: #333;
        --accent-color: #4285f4;
        --header-color: #4285f4;
        --secondary-bg: #262626;
    }

    /* Main containers - Dark */
    .main-container {
        background-color: var(--secondary-bg);
        border-color: var(--card-border);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
    }
    
    .assessment-card {
        background-color: var(--card-bg);
        border-color: var(--card-border);
    }
    
    body {
        color: var(--text-color);
        background-color: var(--background-color);
    }

    /* Headers - Dark */
    .main-header {
        color: var(--header-color);
    }
    
    .sub-header {
        color: var(--header-color);
        border-bottom-color: var(--card-border);
    }
    
    h1, h2, h3, h4, h5, h6 {
        color: var(--header-color) !important;
    }
    
    /* Footer - Dark */
    .footer {
        color: #aaa;
    }
    
    .separator {
        background-color: var(--card-border);
    }
    
    /* Example card - Dark */
    .example-card {
        background-color: var(--card-bg);
        border-color: var(--card-border);
    }
    
    .example-card:hover {
        background-color: #333;
    }
</style>
"""

# Light mode CSS
light_mode_css = """
<style>
    /* Typography */
    h1, h2, h3, h4 {
        font-family: 'Arial', sans-serif;
    }
    
    /* Main containers */
    .main-container {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 2rem;
        margin-bottom: 1rem;
        border: 1px solid #e9ecef;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    }
    
    /* Headers */
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #0f2b5b;
        margin-bottom: 0.5rem;
        letter-spacing: -0.02em;
    }
    
    .sub-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #0f2b5b;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        padding-bottom: 0.3rem;
        border-bottom: 2px solid #e9ecef;
    }
    
    /* Assessment cards */
    .assessment-card {
        background-color: white;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        border: 1px solid #e9ecef;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
    }
    
    .assessment-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
    }
    
    /* Tags and badges */
    .badge {
        display: inline-block;
        padding: 0.35em 0.65em;
        font-size: 0.75em;
        font-weight: 700;
        line-height: 1;
        text-align: center;
        white-space: nowrap;
        vertical-align: baseline;
        border-radius: 0.375rem;
        margin-right: 0.5rem;
    }
    
    .badge-primary {
        color: #fff;
        background-color: #0d6efd;
    }
    
    .badge-success {
        color: #fff;
        background-color: #198754;
    }
    
    .badge-warning {
        color: #000;
        background-color: #ffc107;
    }
    
    .badge-danger {
        color: #fff;
        background-color: #dc3545;
    }
    
    .badge-info {
        color: #000;
        background-color: #0dcaf0;
    }
    
    /* Separators */
    .separator {
        height: 1px;
        background-color: #e9ecef;
        margin: 1.5rem 0;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding-top: 2rem;
        padding-bottom: 1rem;
        color: #6c757d;
        font-size: 0.875rem;
    }
    
    /* Form elements */
    .stTextInput > div > div > input {
        border-radius: 8px;
    }
    
    .stTextArea > div > div > textarea {
        border-radius: 8px;
    }
    
    /* Button styling */
    .stButton > button {
        background-color: #0f2b5b;
        color: white;
        font-weight: 600;
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        border: none;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        background-color: #0d2348;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(15, 43, 91, 0.2);
    }
    
    /* Other styling */
    .highlight {
        background-color: #fff3cd;
        padding: 0.2em 0.4em;
        border-radius: 4px;
    }
    
    /* Example query card */
    .example-card {
        background-color: #f1f5f9;
        border-radius: 8px;
        padding: 0.75rem;
        margin-bottom: 0.5rem;
        border: 1px solid #e2e8f0;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .example-card:hover {
        background-color: #e2e8f0;
        transform: translateX(2px);
    }

    /* Animation keyframes */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
</style>
"""

# Load the appropriate CSS
if theme == "dark":
    st.markdown(light_mode_css + dark_mode_css, unsafe_allow_html=True)
else:
    st.markdown(light_mode_css, unsafe_allow_html=True)

# Toggle theme function
def toggle_theme():
    st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"
    st.rerun()

# Sidebar
with st.sidebar:
    st.markdown("## SHL Assessment Finder")
    
    # Theme toggle
    theme_label = "🌙 Switch to Light Mode" if theme == "dark" else "🌙 Switch to Dark Mode"
    if st.button(theme_label):
        toggle_theme()
    
    st.markdown("---")
    
    st.markdown("### About")
    st.markdown(
        "This tool helps hiring managers find the most relevant SHL assessments "
        "for their roles based on natural language queries."
    )
    
    st.markdown("### Features")
    st.markdown("- 🔍 Semantic search")
    st.markdown("- 🎯 Intelligent filtering")
    st.markdown("- 🚀 Fast recommendations")
    st.markdown("- 📊 Technical & non-technical assessments")
    
    st.markdown("---")
    st.markdown("### API Status")
    
    # API health check
    try:
        response = requests.get(f"{API_URL}/health", timeout=2)
        if response.status_code == 200 and response.json().get("status") == "healthy":
            st.success("API is online")
        else:
            st.error("API is experiencing issues")
    except:
        st.error("Cannot connect to API")

# Main content
# Header with subtle animation effect
st.markdown("""
<div style="animation: fadeIn 1s;">
    <div class="main-header">SHL Assessment Recommendation System</div>
    <p style="font-size: 1.1rem; color: #6c757d; margin-bottom: 2rem;">
        Find the perfect assessment for your hiring needs with our AI-powered recommendation engine
    </p>
</div>
""", unsafe_allow_html=True)

# Main container
st.markdown('<div class="main-container">', unsafe_allow_html=True)

# Two-column layout for input
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 📝 What are you looking for?")
    query = st.text_area(
        "Enter your requirements or job description",
        value=st.session_state.query_text,
        placeholder="Example: I am hiring Java developers who collaborate with business teams. Need an assessment completed in 40 minutes.",
        height=150,
        key="query_area"
    )
    # Update session state when text area changes
    st.session_state.query_text = query

with col2:
    st.markdown("### ⚙️ Options")
    max_results = st.slider("Maximum recommendations", min_value=1, max_value=10, value=5)
    
    st.markdown("### 💡 Try an example:")
    
    # Example queries
    examples = {
        "Java developers": "I am hiring for Java developers who can collaborate with business teams. Looking for assessments that can be completed in 40 minutes.",
        "Python & SQL expert": "Looking to hire professionals proficient in Python, SQL and JavaScript. Need an assessment package with max duration of 60 minutes.",
        "Cognitive abilities": "I am hiring for an analyst role and want to screen using cognitive tests, within 45 mins.",
        "Administrative role": "ICICI Bank Assistant Admin, Experience required 0-2 years, test should be 30-40 mins long",
        "QA Engineer": "Hiring QA engineers with Selenium experience. Looking for technical assessments under 60 minutes."
    }
    
    for label, example_query in examples.items():
        if st.button(label, key=f"example_{label}", help=example_query):
            select_example(example_query)
            st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# API interaction function
def get_recommendations(query, max_results):
    """Get recommendations from the API."""
    try:
        with st.spinner("🔍 Analyzing your requirements..."):
            response = requests.post(
                f"{API_URL}/recommend",
                json={"query": query, "max_results": max_results},
                timeout=15
            )
        
        if response.status_code == 200:
            recommendations = response.json()["recommended_assessments"]
            
            # Make sure the field names match what our display code expects
            for rec in recommendations:
                # Convert test_type to type - careful about field format conversion from list to string
                if "test_type" in rec:
                    if isinstance(rec["test_type"], list) and len(rec["test_type"]) > 0:
                        rec["type"] = rec["test_type"][0]
                    else:
                        rec["type"] = str(rec["test_type"])
                
                # Ensure URLs are properly formatted
                if "url" in rec and not rec["url"].startswith(("http://", "https://")):
                    rec["url"] = "https://" + rec["url"]
                
                # Handle any missing fields with safe defaults
                if "type" not in rec:
                    rec["type"] = "General"
                if "remote_support" not in rec:
                    rec["remote_support"] = "No"
                if "adaptive_support" not in rec:
                    rec["adaptive_support"] = "No"
                if "duration" not in rec:
                    rec["duration"] = "Not specified"
                elif isinstance(rec["duration"], int):
                    rec["duration"] = f"{rec['duration']} minutes"
            
            # Debug: print what we're returning
            print(f"Returning {len(recommendations)} recommendations")
            for i, rec in enumerate(recommendations[:3]):  # Just print first 3 for brevity
                print(f"Rec {i+1}: {rec['name']} - Type: {rec['type']}")
            
            return recommendations
        else:
            st.error(f"Error: API returned status code {response.status_code}")
            st.error(response.text)
            return []
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to API: {e}")
        return []

# Submit button with custom styling
if st.button("🚀 Get Recommendations", type="primary", use_container_width=True) and query:
    # Add loading animation
    with st.spinner("🔍 Searching for the perfect assessments..."):
        # Display a progress bar to indicate processing
        progress_bar = st.progress(0)
        for percent_complete in range(0, 101, 10):
            # Update progress bar
            progress_bar.progress(percent_complete)
            if percent_complete < 90:  # Only sleep if not at 90% yet
                import time
                time.sleep(0.05)  # Small delay for visual effect
        
        # Now get the recommendations
        recommendations = get_recommendations(query, max_results)
    
    # Remove the progress bar after loading completes
    progress_bar.empty()
    
    if recommendations:
        st.markdown('<div class="main-container">', unsafe_allow_html=True)
        st.markdown(f'<div class="sub-header">🏆 Top {len(recommendations)} Recommended Assessments</div>', unsafe_allow_html=True)
        
        # Display the recommendations in a modern card layout
        for i, rec in enumerate(recommendations, 1):
            # Create a unique key for this recommendation
            rec_key = f"rec_{i}_{rec.get('name', 'Assessment').replace(' ', '_')}"
            
            # Format duration
            duration = rec.get('duration', 'Not specified')
            
            # Card container
            with st.container():
                # Title and number
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.markdown(f"### {rec.get('name', 'Assessment')}")
                with col2:
                    st.markdown(f"<div style='text-align: right; padding: 5px; background-color: #f1f8ff; color: #0366d6; border-radius: 15px; font-weight: 600;'>#{i}</div>", unsafe_allow_html=True)
                
                # Use Streamlit native components for badges
                badge_cols = st.columns(4)
                
                # Type badge
                with badge_cols[0]:
                    type_color = {
                        'Technical': '#0366d6',
                        'Cognitive': '#2ea44f',
                        'Personality/Behavioral': '#6f42c1',
                        'Leadership': '#d73a49',
                        'Role-specific': '#1b1f23'
                    }.get(rec.get('type', 'General'), '#1b1f23')
                    
                    st.markdown(
                        f"<div style='text-align: center; padding: 5px; background-color: {type_color}; "
                        f"color: white; border-radius: 15px; font-size: 0.85em;'>"
                        f"{rec.get('type', 'General')}</div>",
                        unsafe_allow_html=True
                    )
                
                # Remote testing badge
                with badge_cols[1]:
                    remote_color = '#2ea44f' if rec.get('remote_support') == 'Yes' else '#d73a49'
                    st.markdown(
                        f"<div style='text-align: center; padding: 5px; background-color: {remote_color}; "
                        f"color: white; border-radius: 15px; font-size: 0.85em;'>"
                        f"Remote Testing</div>",
                        unsafe_allow_html=True
                    )
                
                # Adaptive badge
                with badge_cols[2]:
                    adaptive_color = '#6f42c1' if rec.get('adaptive_support') == 'Yes' else '#586069'
                    st.markdown(
                        f"<div style='text-align: center; padding: 5px; background-color: {adaptive_color}; "
                        f"color: white; border-radius: 15px; font-size: 0.85em;'>"
                        f"Adaptive</div>",
                        unsafe_allow_html=True
                    )
                
                # Duration badge
                with badge_cols[3]:
                    st.markdown(
                        f"<div style='text-align: center; padding: 5px; background-color: #f1f8ff; "
                        f"color: #0366d6; border-radius: 15px; font-size: 0.85em;'>"
                        f"⏱️ {duration}</div>",
                        unsafe_allow_html=True
                    )
                
                # Add a bit of space
                st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
                
                # Streamlit columns for better organization
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # Description section
                    st.markdown("##### Description")
                    description = rec.get('description', 'No description available')
                    # Limit description to two lines with readmore
                    if len(description) > 300:
                        short_desc = description[:300] + "..."
                        with st.expander("Read more"):
                            st.markdown(description)
                        st.markdown(short_desc)
                    else:
                        st.markdown(description)
                
                with col2:
                    # Details section
                    st.markdown("##### Details")
                    
                    # Format specifications in a more readable way
                    st.markdown(f"**Type:** {rec.get('type', 'General')}")
                    st.markdown(f"**Duration:** {duration}")
                    st.markdown(f"**Remote Testing:** {'✅ Yes' if rec.get('remote_support') == 'Yes' else '❌ No'}")
                    st.markdown(f"**Adaptive:** {'✅ Yes' if rec.get('adaptive_support') == 'Yes' else '❌ No'}")
                
                # Action buttons
                col1, col2 = st.columns([1, 1])
                with col1:
                    # Replace button with a direct markdown link
                    st.markdown(f"<a href='{rec.get('url', '#')}' target='_blank'><button style='background-color: #0f2b5b; color: white; font-weight: 600; border-radius: 8px; padding: 0.5rem 1.5rem; border: none; width: 100%;'>🔗 View Assessment</button></a>", unsafe_allow_html=True)
                
                with col2:
                    # Add to comparison feature
                    if st.button(f"📊 Compare", key=f"compare_{rec_key}"):
                        if "comparison_items" not in st.session_state:
                            st.session_state.comparison_items = []
                        
                        # Check if already in comparison
                        if rec_key not in [item['key'] for item in st.session_state.comparison_items]:
                            st.session_state.comparison_items.append({
                                'key': rec_key,
                                'name': rec.get('name', 'Assessment'),
                                'type': rec.get('type', 'General'),
                                'duration': duration,
                                'remote': rec.get('remote_support', 'No'),
                                'adaptive': rec.get('adaptive_support', 'No')
                            })
                            st.success(f"Added {rec.get('name', 'Assessment')} to comparison")
                        else:
                            st.info(f"{rec.get('name', 'Assessment')} is already in comparison")
                
                # Add a divider between assessments
                st.markdown("<hr style='margin: 20px 0; border: 0; height: 1px; background-color: #e1e4e8;'>", unsafe_allow_html=True)
        
        # Comparison section
        if "comparison_items" in st.session_state and st.session_state.comparison_items:
            st.markdown("### Assessment Comparison")
            
            # Create columns for each item in comparison
            comparison_cols = st.columns(len(st.session_state.comparison_items) + 1)
            
            # Header column
            with comparison_cols[0]:
                st.markdown("**Criteria**")
                st.markdown("Type")
                st.markdown("Duration")
                st.markdown("Remote Testing")
                st.markdown("Adaptive Support")
            
            # Data columns
            for i, item in enumerate(st.session_state.comparison_items):
                with comparison_cols[i+1]:
                    st.markdown(f"**{item['name']}**")
                    st.markdown(f"{item['type']}")
                    st.markdown(f"{item['duration']}")
                    st.markdown("✅" if item['remote'] == 'Yes' else "❌")
                    st.markdown("✅" if item['adaptive'] == 'Yes' else "❌")
            
            # Button to clear comparison
            if st.button("Clear Comparison"):
                st.session_state.comparison_items = []
                st.rerun()
        
    else:
        # No recommendations found
        st.warning("⚠️ No matching assessments found. Try a different query or more general requirements.")
        
        # Add a more helpful guidance section with cards
        st.markdown("""
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin-top: 20px;">
            <h3 style="margin-top: 0;">Suggestions to Improve Results</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px; margin-top: 15px;">
                <div style="background-color: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <h4 style="margin-top: 0; color: #0366d6;">📝 Refine Your Query</h4>
                    <p>Try using different keywords or more specific technical skills (e.g., "Java", "Python", "SQL").</p>
                </div>
                <div style="background-color: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <h4 style="margin-top: 0; color: #0366d6;">🎯 Specify Assessment Type</h4>
                    <p>Include the type of assessment you need: Technical, Cognitive, Personality, or Leadership.</p>
                </div>
                <div style="background-color: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <h4 style="margin-top: 0; color: #0366d6;">⏱️ Adjust Duration</h4>
                    <p>If you specified a duration constraint, try increasing it or removing the time limitation.</p>
                </div>
            </div>
            <div style="margin-top: 20px;">
                <h4>Example Queries:</h4>
                <ul>
                    <li>"Java developer assessment for senior engineers"</li>
                    <li>"Cognitive assessment for problem-solving abilities"</li>
                    <li>"Leadership assessment for management roles"</li>
                    <li>"Technical assessment for full-stack developers with React and Node.js"</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)

# Footer with current year
current_year = datetime.now().year
st.markdown("""
<div class="footer">
    <div class="separator"></div>
    <p>SHL Assessment Recommendation System © {year}</p>
    <p>Built with Streamlit, FastAPI, and Sentence Transformers</p>
</div>
""".format(year=current_year), unsafe_allow_html=True) 