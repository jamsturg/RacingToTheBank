def run(self):
        """Run the dashboard application"""
        self.render_header()
        
        if not st.session_state.logged_in:
            self.render_login()
        else:
            self.render_navigation()
            
            if st.session_state.page == "Dashboard":
                self.render_dashboard()
            elif st.session_state.page == "Race Analysis":
                self.render_race_analysis()
            elif st.session_state.page == "Form Guide":
                self.render_form_guide()
            elif st.session_state.page == "Statistics":
                self.render_statistics()
            elif st.session_state.page == "Betting":
                self.render_betting()
            elif st.session_state.page == "Account":
                self.render_account()
            
            self.render_footer()

if __name__ == "__main__":
    dashboard = RacingDashboard()
    dashboard.run()
