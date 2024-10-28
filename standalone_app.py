import streamlit as st

# Page config
st.set_page_config(page_title="Racing Dashboard", layout="wide")

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def main():
    if not st.session_state.logged_in:
        st.title("Racing Dashboard Login")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            
            if submit and username and password:
                st.session_state.logged_in = True
                st.rerun()
    else:
        st.title("Racing Dashboard")
        
        # Sidebar
        with st.sidebar:
            st.header("Navigation")
            page = st.radio("Select Page", ["Dashboard", "Race Analysis", "Betting"])
            
            if st.button("Logout"):
                st.session_state.logged_in = False
                st.rerun()
        
        # Main content
        if page == "Dashboard":
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Today's P/L", "$523.40", "12.3%")
            with col2:
                st.metric("Win Rate", "34%", "2.1%")
            with col3:
                st.metric("Active Bets", "5", "-2")
            
            st.write("Welcome to the Racing Dashboard!")
            
        elif page == "Race Analysis":
            st.header("Race Analysis")
            track = st.selectbox("Select Track", ["Melbourne", "Sydney", "Brisbane"])
            race = st.selectbox("Select Race", [f"Race {i}" for i in range(1, 11)])
            
            st.write(f"Analyzing {track} - Race {race}")
            
        elif page == "Betting":
            st.header("Betting Dashboard")
            with st.form("betting_form"):
                amount = st.number_input("Bet Amount ($)", min_value=0.0, step=10.0)
                horse = st.selectbox("Select Horse", [f"Horse {i}" for i in range(1, 6)])
                bet_type = st.selectbox("Bet Type", ["Win", "Place", "Each Way"])
                
                if st.form_submit_button("Place Bet"):
                    st.success(f"Bet placed: ${amount} on {horse} to {bet_type}")

if __name__ == "__main__":
    main()
