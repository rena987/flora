

def assess_severity(disease_name: str, confidence_score: float, symptoms: list) -> dict:
    if confidence_score < 0.5: 
        risk_level = "UNKNOWN"
        urgency = "Cannot assess - escalation recommended"
        spread_risk = "cannot assess spread risk without confident diagnosis"
        recommendation = "cannot give recommendation without confident diagnosis"
    elif "Late Blight" in disease_name or "Yellow Leaf Curl Virus" in disease_name:
        risk_level = "CRITICAL"
        urgency = "Act immediately - within 24 hours"
        spread_risk = "spreads within days"
        recommendation = "destroy affected plants immediately"
    elif "Early Blight" in disease_name or "Bacterial Spot" in disease_name or "Root Rot" in disease_name:
        risk_level = "HIGH"
        urgency = "Act within 48 hours"
        spread_risk = "spreads via spores/wind"
        recommendation = "treat within 48 hours"
    elif "Septoria" in disease_name or "Rust" in disease_name or "Leaf Mold" in disease_name or "Target Spot" in disease_name:
        risk_level = "MEDIUM"
        urgency = "Act within 1 week"
        spread_risk = "spreads slowly"
        recommendation = "monitor and treat within a week"
    elif disease_name == "healthy":
        risk_level = "NONE"
        urgency = "No action needed"
        spread_risk = "no spread risk"
        recommendation = "maintain current care"
    else:
        risk_level = "LOW"
        urgency = "Monitor closely"
        spread_risk = "minimal spread risk"
        recommendation = "observe closely"
    
    return {
        "risk_level": risk_level,
        "urgency": urgency,
        "spread_risk": spread_risk,
        "recommendation": recommendation
    }

if __name__ == "__main__":
    print(assess_severity("Late Blight", 0.85, ["dark patches"]))
    print(assess_severity("Early Blight", 0.87, ["concentric spots"]))
    print(assess_severity("healthy", 0.95, []))
    print(assess_severity("Early Blight", 0.3, ["unclear spots"]))
 