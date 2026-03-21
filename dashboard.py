import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from fpdf import FPDF
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import mean_absolute_error, accuracy_score

import requests
import base64

def save_to_github(new_row_list):
    # 1. Setup GitHub Details
    token = st.secrets["GITHUB_TOKEN"]
    repo = "namansharma-23/project-auditor-ai" # Ensure this matches your repo name
    path = "project_training.csv"
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    headers = {"Authorization": f"token {token}"}

    # 2. Get the current file content
    resp = requests.get(url, headers=headers).json()
    content = base64.b64decode(resp['content']).decode('utf-8')
    sha = resp['sha'] # GitHub needs this 'sha' to know which version to update

    # 3. Add the new data row
    new_row_str = ",".join(map(str, new_row_list))
    updated_content = content.strip() + "\n" + new_row_str

    # 4. Push back to GitHub
    message = "New project data added via AI Dashboard"
    payload = {
        "message": message,
        "content": base64.b64encode(updated_content.encode('utf-8')).decode('utf-8'),
        "sha": sha
    }
    
    r = requests.put(url, json=payload, headers=headers)
    return r.status_code == 200

st.set_page_data = "wide"
st.title("🚀 Naman's AI Project Auditor")
st.write("This dashboard automatically analyzes project risks and budget.")

# --- DATA LOADING ---
df = pd.read_csv("projects.csv")
df["Budget"] = df["Budget"].fillna(0)

def analyze_risk(budget):
    if budget > 10000: return "🔴 High Risk"
    if budget > 5000: return "🟡 Medium Risk"
    return "🟢 Low Risk"

df["Risk_Level"] = df["Budget"].apply(analyze_risk)

# --- METRICS ---
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Projects", len(df))
with col2:
    total_budget = df["Budget"].sum()
    st.metric("Total Budget", f"${total_budget:,.0f}")
with col3:
    high_risk_count = len(df[df["Risk_Level"] == "🔴 High Risk"])
    st.metric("High Risk Alerts", high_risk_count)

st.divider()
st.subheader("Project Data Overview")
st.dataframe(df, use_container_width=True)

st.subheader("Budget Visualizer")
fig, ax = plt.subplots()
ax.bar(df["Project"], df["Budget"], color='skyblue')
st.pyplot(fig)

st.divider()
selected_project = st.selectbox("Select a project to audit: ", df["Project"])
project_info = df[df["Project"] == selected_project]
st.write(f"The AI suggests: **{project_info['Risk_Level'].values[0]}**")

st.markdown("---")
st.header("🔮 Project Predictor (AI Model)")
st.info("Adjust the sliders to see how Team Size and Duration affect project risk.")

# --- SMART MODEL LOADER (V3: Categorical & Feature Sync) ---
@st.cache_resource 
def get_trained_models_with_metrics():
    try:
        tdf = pd.read_csv("project_training.csv")
        # Ensure Project_Type is encoded
        tdf_encoded = pd.get_dummies(tdf, columns=["Project_Type"])
        
        # Drop targets and irrelevant columns
        # We use errors='ignore' so it doesn't crash if columns are missing
        X = tdf_encoded.drop(columns=["Actual_Cost", "On_Time", "Project"], errors='ignore')
        y_cost = tdf_encoded['Actual_Cost']
        y_time = tdf_encoded['On_Time']
        
        # SAVE THE COLUMN NAMES - This is critical for the chart length
        model_cols = list(X.columns)
        
        X_train, X_test, y_train, y_test = train_test_split(X, y_cost, test_size=0.2, random_state=42)
        c_model = LinearRegression().fit(X_train, y_train)
        cost_error = mean_absolute_error(y_test, c_model.predict(X_test))
        
        X_train_l, X_test_l, y_train_l, y_test_l = train_test_split(X, y_time, test_size=0.4, random_state=42)
        t_model = LogisticRegression().fit(X_train_l, y_train_l)
        time_accuracy = accuracy_score(y_test_l, t_model.predict(X_test_l))
        
        return c_model, t_model, cost_error, time_accuracy, model_cols
    except Exception as e:
        st.error(f"Model Loading Error: {e}")
        return None, None, 0, 0, []

# Initialize
cost_model, time_model, mae, acc, cols = get_trained_models_with_metrics()

# --- PREDICTION LOGIC ---
if cost_model and time_model:
    col_in1, col_in2 = st.columns(2)
    with col_in1:
        input_days = st.slider("Project Duration (Days)", 1, 150, 40)
    with col_in2:
        input_team = st.slider("Team Size", 1, 20, 5)

    project_types = ["Web", "Mobile", "ML_Model", "Audit"]
    selected_type = st.selectbox("What type of Project is this?", project_types)
    
    # Build the "Switchboard" dictionary
    input_data = {'Days': input_days, 'Team_Size': input_team}
    for p_type in project_types:
        input_data[f'Project_Type_{p_type}'] = 1 if p_type == selected_type else 0

    # Convert to DataFrame and ALIGN columns with the training set
    feature_df = pd.DataFrame([input_data])
    feature_df = feature_df.reindex(columns=cols, fill_value=0)

    # Calculate Predictions
    pred_cost = cost_model.predict(feature_df)[0]
    pred_time = time_model.predict(feature_df)[0]

    # Metrics Display
    res_col1, res_col2 = st.columns(2)
    res_col1.metric("Predicted Budget", f"${pred_cost:,.2f}")
    
    if pred_time == 1:
        res_col2.success("Status: Likely On-Time")
        time_label = "On-Time"
    else:
        res_col2.error("Status: High Risk of Delay")
        time_label = "Delayed/High Risk"

    # AI Confidence
    st.markdown("### 📊 AI Model Confidence")
    conf_col1, conf_col2 = st.columns(2)
    with conf_col1:
        st.write(f"**Cost Reliability:** ±${mae:.0f}")
    with conf_col2:
        st.write(f"**Risk Accuracy:** {acc*100:.0f}%")

    st.divider()
    st.subheader("💡 What drives the Cost?")
    st.write("This chart shows which factor has the biggest impact on your budget.")

    # 1. Get the raw factors and impacts
    all_factors = cols 
    all_impacts = np.abs(cost_model.coef_)

    # 2. Create the DataFrame
    importance_df = pd.DataFrame({
            'Factor': all_factors,
            'Impact Score': all_impacts
    })

    # --- NEW: LABEL CLEANING SECTION ---
    # This turns 'Project_Type_ML_Model' into 'ML Model'
    importance_df['Factor'] = importance_df['Factor'].str.replace('Project_Type_', '', regex=False)
    importance_df['Factor'] = importance_df['Factor'].str.replace('_', ' ', regex=False)
    # -----------------------------------

    # 3. Sort and Display
    importance_df = importance_df.sort_values(by='Impact Score', ascending=False)
    st.bar_chart(data=importance_df, x='Factor', y='Impact Score', color='#FF4B4B')

    st.caption("Note: The labels above show the cleaned category names for better readability.")

    # --- PDF GENERATOR ---
    def create_pdf(days, team, cost, t_status):
        pdf = FPDF()
        pdf.add_page()
        try:
            pdf.image("naman_logo.jpg", 10, 8, 33) 
        except:
            pass
            
        pdf.set_font("Arial", 'B', 16)
        pdf.ln(20) 
        pdf.cell(200, 10, "Project Audit Report", ln=True, align='C')
        pdf.set_draw_color(0, 80, 180)
        pdf.line(10, 40, 200, 40)
        pdf.ln(10)

        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, f"Project Duration: {days} Days", ln=True)
        pdf.cell(200, 10, f"Team Size: {team} Members", ln=True)
        pdf.cell(200, 10, f"Predicted Budget: ${cost:,.2f}", ln=True)
        pdf.cell(200, 10, f"Timeline Status: {t_status}", ln=True)
        
        pdf.ln(20)
        pdf.set_font("Arial", 'I', 10)
        pdf.cell(200, 10, "Generated by Naman's AI Project Auditor", ln=True, align='C')
        return pdf.output(dest='S').encode('latin-1')

    pdf_data = create_pdf(input_days, input_team, pred_cost, time_label)
    st.download_button(
        label="📥 Download Audit Report (PDF)",
        data=pdf_data,
        file_name="project_audit.pdf",
        mime="application/pdf"
    )
else:
    st.warning("Please ensure 'project_training.csv' is correctly formatted on GitHub.")

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100)
    st.title("Engineer Profile")
    st.write("**Name:** Naman")
    st.write("**Role:** Data Science & Viz Engineer")
    st.info("Turning complex datasets into interactive visual stories.")
    st.write("📍 Based in India")
    st.divider()
    st.subheader("Contribute Data")
    with st.form("data_form",clear_on_submit=True):
        new_days = st.number_input("Actual Days", min_value=1)
        new_team = st.number_input("Team Size", min_value=1)
        new_cost = st.number_input("Actual Cost ($)", min_value=100)
        new_type = st.selectbox("Type", ["Web", "Mobile", "ML_Model", "Audit"])
        new_ontime = st.radio("Was it on time?", [1, 0], format_func=lambda x: "Yes" if x==1 else "No")
        
        submitted = st.form_submit_button("Add to Training Set")
        if submitted:
            # Create the list in the same order as your CSV: Days, Team, Cost, On_Time, Type
            new_data = [new_days, new_team, new_cost, new_ontime, new_type]
            
            with st.spinner("Writing to GitHub..."):
                success = save_to_github(new_data)
                
            if success:
                st.success("✅ Project saved! Refresh the page to retrain the AI.")
                # Clear cache so the AI reloads the new CSV
                st.cache_resource.clear() 
            else:
                st.error("❌ Failed to save. Check your GitHub Token.")
                
            st.success("Project added! The AI will learn from this on the next refresh.")