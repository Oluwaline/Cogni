# streamlit_report.py
import streamlit as st
from urllib.parse import unquote
import requests

# Configure page
st.set_page_config(
    page_title="Cogni Package Recommendation",
    page_icon="🧠",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .header-text { font-size: 24px !important; }
    .feature-list { margin-left: 20px; }
    .alternative-card { 
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# Get URL parameters
def get_url_param(param, default=""):
    params = st.query_params
    return unquote(params.get(param, [default])[0])

# Main function
def main():
    st.title("🧠 Cogni Mental Health Package Recommendation")
    st.markdown("---")
    
    # Get all parameters from URL
    package = get_url_param("package")
    seats = get_url_param("seats")
    org_type = get_url_param("org_type")
    team_size = get_url_param("team_size")
    client_volume = get_url_param("client_volume")
    service_model = get_url_param("service_model", "Not specified")
    specialization = get_url_param("specialization", "Not specified")

    if not package:
        st.warning("No recommendation parameters found. Please complete the chatbot assessment first.")
        st.markdown("[Go to Chatbot](#)")
        return

    # Header section
    st.header(f"Recommended Package: {package}")
    st.subheader(f"Recommended seats: {seats}")
    
    # User inputs summary
    with st.expander("📋 Your Assessment Summary", expanded=True):
        col1, col2, col3 = st.columns(3)
        col1.metric("Organization Type", org_type)
        col2.metric("Team Size", team_size)
        col3.metric("Client Volume", client_volume)
        
        if service_model != "Not specified":
            st.write(f"**Service Model:** {service_model}")
        if specialization != "Not specified":
            st.write(f"**Specialization:** {specialization}")
    
    # Get full recommendation details from API
    try:
        response = requests.post(
            "http://localhost:8000/getRecommendation",
            json={
                "org_type": org_type,
                "team_size": team_size,
                "client_volume": client_volume,
                "service_model": service_model if service_model != "Not specified" else None,
                "specialization": specialization if specialization != "Not specified" else None
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data["status"] == "success":
                rec = data["recommendation"]
                
                # Package details section
                st.markdown("---")
                st.header("✨ Package Details")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Key Features")
                    for feature in rec["features"]:
                        st.markdown(f"✓ {feature}")
                    
                    st.subheader("Pricing")
                    st.metric("Monthly Cost", f"${rec['monthly_price']}")
                    st.caption(f"For {rec['seats']} seats | Volume discounts available")
                
                with col2:
                    st.subheader("Why This Package?")
                    st.info(rec["explanation"])
                    
                    if st.button("📞 Contact Sales Team", type="primary"):
                        st.session_state.contact_requested = True
                
                # Alternatives section
                st.markdown("---")
                st.header("🔍 Compare Alternatives")
                
                for alt in data["alternatives"]:
                    if alt["name"] != rec["package"]:
                        with st.expander(f"{alt['name']}: {alt['best_for']}"):
                            st.markdown(f"**Price:** {alt['price']}")
                            st.markdown(f"**Best for:** {alt['best_for']}")
                            
                            # Update query parameters for alternative view
                            if st.button(f"View {alt['name']} Details", key=f"view_{alt['name']}"):
                                st.query_params["package"] = alt["name"]
                                st.query_params["seats"] = seats
                                st.query_params["org_type"] = org_type
                                st.query_params["team_size"] = team_size
                                st.query_params["client_volume"] = client_volume
                                st.query_params["service_model"] = service_model
                                st.query_params["specialization"] = specialization
                                st.rerun()
                
                # Next steps section
                st.markdown("---")
                st.header("🚀 Next Steps")
                
                steps_col1, steps_col2 = st.columns(2)
                
                with steps_col1:
                    st.markdown("""
                    1. **Review** the package details
                    2. **Compare** with alternatives
                    3. **Contact** our team for implementation
                    """)
                
                with steps_col2:
                    if st.button("📧 Email This Recommendation"):
                        st.success("A copy has been sent to your email!")
                    
                    if st.button("🔄 Restart Assessment"):
                        for param in list(st.query_params.keys()):
                            st.query_params.pop(param)
                        st.rerun()
            
            else:
                st.error(f"API Error: {data['message']}")
        else:
            st.error("Failed to connect to recommendation service")
    
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()