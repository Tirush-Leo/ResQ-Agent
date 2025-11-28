import streamlit as st
import os
from database import init_db, add_user, verify_user, create_session, get_user_sessions, get_session_details, save_message, get_session_messages
from backend import get_image_data, chat_with_context

# Initialize DB
init_db()
st.set_page_config(page_title="RescueAI Analyst", page_icon="🚁", layout="wide")

# --- STATE ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "username" not in st.session_state: st.session_state.username = ""
if "current_session_id" not in st.session_state: st.session_state.current_session_id = None

# --- UI HELPER: LEGEND ---
def display_floodnet_legend():
    """Renders legend for the map."""
    legend_html = """
    <style>
        .legend-container {
            display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px;
            margin-top: 10px; padding: 10px; background-color: #f0f2f6;
            border-radius: 8px; font-size: 14px; color: #000000; font-weight: 500;
        }
        .legend-item { display: flex; align-items: center; }
        .color-box { width: 18px; height: 18px; margin-right: 8px; border-radius: 4px; border: 1px solid #ccc; }
    </style>
    <div class="legend-container">
        <div class="legend-item"><div class="color-box" style="background: #FF0000;"></div>Flooded Bldg</div>
        <div class="legend-item"><div class="color-box" style="background: #8B4513;"></div>Safe Bldg</div>
        <div class="legend-item"><div class="color-box" style="background: #00008B;"></div>Flooded Road</div>
        <div class="legend-item"><div class="color-box" style="background: #808080;"></div>Safe Road</div>
        <div class="legend-item"><div class="color-box" style="background: #00BFFF;"></div>Water</div>
        <div class="legend-item"><div class="color-box" style="background: #FFD700;"></div>Vehicle</div>
        <div class="legend-item"><div class="color-box" style="background: #228B22;"></div>Tree</div>
        <div class="legend-item"><div class="color-box" style="background: #00FFFF;"></div>Pool</div>
    </div>
    """
    st.markdown(legend_html, unsafe_allow_html=True)

# --- LOGIN ---
def login_page():
    st.title("🔐 RescueAI Analyst Login")
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    with tab1:
        user = st.text_input("Username", key="l_user")
        pw = st.text_input("Password", type="password", key="l_pw")
        if st.button("Login"):
            if verify_user(user, pw):
                st.session_state.logged_in = True
                st.session_state.username = user
                st.rerun()
            else:
                st.error("Invalid credentials")
    with tab2:
        new_u = st.text_input("New Username", key="n_user")
        new_p = st.text_input("New Password", type="password", key="n_pw")
        if st.button("Create Account"):
            if add_user(new_u, new_p):
                st.success("Created! Log in now.")
            else:
                st.error("User exists.")

# --- NEW ANALYSIS ---
def start_new_analysis(uploaded_file):
    save_dir = "uploaded_images"
    os.makedirs(save_dir, exist_ok=True)
    file_path = os.path.join(save_dir, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    with st.spinner("🚀 Analyzing Terrain & Structures..."):
        try:
            data = get_image_data(file_path)
            
            title = f"Scan: {uploaded_file.name}"
            session_id = create_session(st.session_state.username, title, file_path)
            
            # --- FULL CONTEXT STRING ---
            context_str = f"""
            [DETAILED VISION REPORT]
            OBJECTS DETECTED:
            - Flooded Buildings: {data['flooded_bldgs']}
            - Safe Buildings: {data['safe_bldgs']}
            - Vehicles Trapped: {data['vehicles']}
            - Swimming Pools: {data['pools_count']}

            TERRAIN ANALYSIS (Coverage %):
            - Tree Coverage: {data['trees_pct']}%
            - Grass/Land: {data['grass_pct']}%
            - Natural Water Body: {data['water_pct']}%

            INFRASTRUCTURE STATUS:
            - Building Damage Rate: {data['bldg_damage_pct']:.1f}%
            - ROAD STATUS: {data['road_flood_severity_pct']:.1f}% of roads are SUBMERGED.
            
            MAP FILE: {data['map_path']}
            """
            save_message(session_id, "system", context_str)
            
            # REMOVED: No automatic greeting. 
            # We just set the session and let the user speak first.
            
            st.session_state.current_session_id = session_id
            st.rerun()
            
        except Exception as e:
            st.error(f"Analysis Failed: {e}")

# --- MAIN APP ---
def main_app():
    with st.sidebar:
        st.header("🗂️ Case Files")
        if st.button("➕ New Analysis", type="primary"):
            st.session_state.current_session_id = None
            st.rerun()
        
        st.divider()
        sessions = get_user_sessions(st.session_state.username)
        for s_id, title, date in sessions:
            if st.button(title, key=s_id):
                st.session_state.current_session_id = s_id
                st.rerun()
        
        st.divider()
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

    if st.session_state.current_session_id is None:
        st.title("🚁 New Disaster Analysis")
        uploaded_file = st.file_uploader("Select Aerial Image", type=['jpg', 'png'])
        if uploaded_file and st.button("Process Image"):
            start_new_analysis(uploaded_file)

    else:
        s_id = st.session_state.current_session_id
        details = get_session_details(s_id)
        if not details:
            st.error("Session error.")
            return
        
        img_path, title = details
        messages = get_session_messages(s_id)
        
        system_context = ""
        chat_history_display = []
        for role, content in messages:
            if role == "system":
                system_context = content
            else:
                chat_history_display.append((role, content))

        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("👁️ Visual Intel")
            if os.path.exists(img_path):
                st.image(img_path, caption="Original Scene", use_container_width=True)
                
                try:
                    if "MAP FILE: " in system_context:
                        map_path = system_context.split("MAP FILE: ")[1].strip()
                        if os.path.exists(map_path):
                            st.image(map_path, caption="AI Segmentation Mask", use_container_width=True)
                            display_floodnet_legend()
                except:
                    pass

        with col2:
            st.subheader("💬 Analyst Chat")
            container = st.container(height=600)
            
            with container:
                # If no history yet, show a welcome tip
                if not chat_history_display:
                    st.info("Analysis Complete. Ask me about damage, roads, or vehicles.")
                else:
                    for role, content in chat_history_display:
                        with st.chat_message(role):
                            st.write(content)

            if user_input := st.chat_input("Ask about trees, pools, roads..."):
                save_message(s_id, "user", user_input)
                with container:
                    with st.chat_message("user"):
                        st.write(user_input)

                with st.spinner("Consulting data..."):
                    response = chat_with_context(system_context, user_input)
                    save_message(s_id, "assistant", response)
                    with container:
                        with st.chat_message("assistant"):
                            st.write(response)
                    st.rerun()

if st.session_state.logged_in:
    main_app()
else:
    login_page()