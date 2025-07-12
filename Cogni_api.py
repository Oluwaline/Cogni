from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import uvicorn

# --- Mapping helper ---
def map_chatbot_to_api_values(org_type, team_size, client_volume=None):
    org_type_mapping = {
        "Insurance Provider / EAS": "Insurance Provider/EAS",
        "Mental Health Practitioner – Private Practice": "Private Practice",
        "Mental Health or Healthcare Provider – Public System": "Public Health Provider",
        "Home Care or Specialized Residential Services": "Home Care/Group Home",
        "Other": "Home Care/Group Home",
    }
    team_size_mapping = {
        "1 (Solo practice)": "1",
        "2–5 providers": "2–5",
        "6–15 providers": "6–15",
        "16–50 providers": "16–50",
        "51+ providers": "51+",
        "Not sure yet": "6–15",
    }
    client_volume_mapping = {
        "Less than 100": "Low",
        "100–500": "Medium",
        "501–1,000": "High",
        "Over 1,000": "Very High",
    }
    mapped_org_type = org_type_mapping.get(org_type.strip(), org_type.strip()) if org_type else ""
    mapped_team_size = team_size_mapping.get(team_size.strip(), team_size.strip()) if team_size else ""
    mapped_client_volume = client_volume_mapping.get(client_volume.strip(), client_volume.strip()) if client_volume else ""

    return mapped_org_type, mapped_team_size, mapped_client_volume

# --- Package Prediction Logic ---
def predict_package(org_type, team_size, client_volume=None, specialization=None, service_model=None):
    mapped_org_type, mapped_team_size, mapped_client_volume = map_chatbot_to_api_values(org_type, team_size, client_volume)
    print(f"Mapped values → Org: {mapped_org_type}, Team: {mapped_team_size}, Volume: {mapped_client_volume}")

    if not mapped_org_type or not mapped_team_size:
        raise ValueError("Invalid mapping: org_type or team_size not recognized.")

    if specialization and "trauma" in specialization.lower():
        return 'Practice Plus', 8

    if mapped_client_volume == "Very High":
        return 'Enterprise Care (Public Health)', 20

    if service_model and "group" in service_model.lower() and mapped_team_size in ['16–50', '51+']:
        return 'Community Access', 20

    if mapped_org_type == "Private Practice":
        if mapped_team_size in ['1', '2–5']:
            return 'Fresh Start', 4
        elif mapped_team_size == '6–15':
            return 'Practice Plus', 8
        elif mapped_team_size == '16–50':
            return 'Community Access', 16
        else:
            return 'Community Access', 20

    elif mapped_org_type == "Public Health Provider":
        if mapped_team_size in ['1', '2–5', '6–15']:
            return 'Practice Plus', 6
        else:
            return 'Enterprise Care (Public Health)', 20

    elif mapped_org_type == "Insurance Provider/EAS":
        return 'Enterprise Access (Insurance & EAS)', 20

    # Fallback
    if mapped_team_size in ['1', '2–5']:
        return 'Fresh Start', 4
    elif mapped_team_size == '6–15':
        return 'Practice Plus', 8
    elif mapped_team_size == '16–50':
        return 'Community Access', 16
    else:
        return 'Community Access', 20

# --- Pricing and Content ---
PACKAGE_PRICE_TABLE = {
    ('Fresh Start', 4): 196,
    ('Practice Plus', 8): 392,
    ('Practice Plus', 6): 294,
    ('Community Access', 20): 980,
    ('Community Access', 16): 784,
    ('Enterprise Care (Public Health)', 20): 980,
    ('Enterprise Access (Insurance & EAS)', 20): 980,
}

PACKAGE_FEATURES = {
    "Fresh Start": [
        "Self-guided mental health tools",
        "Basic AI self-assessment",
        "1 group session per month",
        "Provider dashboard",
        "Email support"
    ],
    "Practice Plus": [
        "Full AI assessment suite",
        "Customizable group modules",
        "Advanced analytics dashboard",
        "Priority email support",
        "Monthly progress reports"
    ],
    "Community Access": [
        "Multilingual support",
        "Unlimited group sessions",
        "Client monitoring tools",
        "Dedicated account manager",
        "Volume discounts"
    ],
    "Enterprise Care (Public Health)": [
        "Unlimited users",
        "API integration",
        "Custom reporting",
        "24/7 support",
        "Training sessions"
    ],
    "Enterprise Access (Insurance & EAS)": [
        "White-label solution",
        "Claims integration",
        "Outcome tracking",
        "Dedicated support team",
        "Custom SLAs"
    ]
}

# --- FastAPI Setup ---
app = FastAPI(
    title="Cogni API",
    description="AI-powered mental health package recommender",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class InputData(BaseModel):
    org_type: str
    team_size: str
    client_volume: str
    service_model: Optional[str] = None
    specialization: Optional[str] = None
    timeline: Optional[str] = None
    features: Optional[str] = None

# --- API Endpoints ---
@app.get("/")
def read_root():
    return {"message": "Cogni API is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/getRecommendation")
def get_recommendation(data: InputData):
    try:
        package, seats = predict_package(
            data.org_type,
            data.team_size,
            data.client_volume,
            data.specialization,
            data.service_model
        )

        # Generate Streamlit URL with all parameters
        streamlit_url = (
            f"https://your-streamlit-app.streamlit.app/"
            f"?package={package.replace(' ', '%20')}"
            f"&seats={seats}"
            f"&org_type={data.org_type.replace(' ', '%20')}"
            f"&team_size={data.team_size.replace(' ', '%20')}"
            f"&client_volume={data.client_volume.replace(' ', '%20')}"
            f"&service_model={data.service_model.replace(' ', '%20') if data.service_model else ''}"
            f"&specialization={data.specialization.replace(' ', '%20') if data.specialization else ''}"
        )

        price = PACKAGE_PRICE_TABLE.get((package, seats), seats * 49)
        features = PACKAGE_FEATURES.get(package, [])
        
        explanation = (
            f"Based on your organization type ({data.org_type}), team size ({data.team_size}), "
            f"and client volume ({data.client_volume}), the {package} package is recommended. "
            f"This package is ideal because it provides {features[0].lower()} and {features[1].lower()}."
        )

        return {
            "status": "success",
            "recommendation": {
                "package": package,
                "seats": seats,
                "monthly_price": price,
                "features": features,
                "explanation": explanation,
                "streamlit_url": streamlit_url
            },
            "alternatives": [
                {
                    "name": "Fresh Start",
                    "best_for": "Small practices (1-5 providers)",
                    "price": "$49/seat"
                },
                {
                    "name": "Practice Plus", 
                    "best_for": "Growing practices (6-15 providers)",
                    "price": "$49/seat"
                },
                {
                    "name": "Community Access",
                    "best_for": "Group practices (16+ providers)",
                    "price": "Volume pricing"
                }
            ],
            "next_steps": [
                "Review the detailed report",
                "Compare with alternatives",
                "Contact sales for implementation"
            ]
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    uvicorn.run("cogni_api:app", host="0.0.0.0", port=8000, reload=True)