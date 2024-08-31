import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from datetime import datetime
import uuid

# CSS personnalisé pour styliser les boutons et les éléments de l'interface
st.markdown("""
    <style>
    .button-container {
        display: flex;
        justify-content: space-between;
        margin-bottom: 10px;
    }
    .conformity-button {
        width: 150px;
        height: 50px;
        border-radius: 8px;
        background-color: #444;
        border: 2px solid #bbb;
        font-size: 16px;
        color: white;
        cursor: pointer;
        margin-right: 5px;
    }
    .conformity-button.selected-conforme {
        background-color: #28a745; /* Green for Conforme */
        border-color: #28a745;
    }
    .conformity-button.selected-non-conforme {
        background-color: #dc3545; /* Red for Non Conforme */
        border-color: #dc3545;
    }
    .conformity-button.selected-na {
        background-color: #6c757d; /* Grey for Non Applicable */
        border-color: #6c757d;
    }
    .icon-button {
        display: inline-block;
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background-color: #007BFF;
        color: white;
        font-size: 18px;
        text-align: center;
        line-height: 40px;
        cursor: pointer;
    }
    .icon-button:hover {
        background-color: #0056b3;
    }
    </style>
""", unsafe_allow_html=True)

# Configuration des scopes OAuth pour accéder à Google Sheets et Google Drive
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# Chargement des credentials du service account depuis les secrets stockés
credentials = Credentials.from_service_account_info(
    st.secrets["connections"]["gsheets"], scopes=SCOPES
)

# Connexion à Google Sheets via gspread
gc = gspread.authorize(credentials)
try:
    sheet = gc.open("LISTCONTROLE").worksheet("table")  # Remplace "table" par le nom de ton worksheet
    result_sheet = gc.open("LISTCONTROLE").worksheet("resultat")

    # Récupérer les données depuis Google Sheets
    data = sheet.get_all_records()  # Fetch all records from the specified worksheet
    df = pd.DataFrame(data)
    if df.empty:
        st.error("La feuille de calcul est vide ou les données n'ont pas été correctement récupérées.")
        st.stop()
except Exception as e:
    st.error(f"Erreur lors de la récupération des données de Google Sheets : {e}")
    df = pd.DataFrame()  # Fallback to empty DataFrame

# Initialize session state if not already done
if 'df_checklists' not in st.session_state:
    st.session_state.df_checklists = df

# Initialisation de l'audit avec un ID unique et la date actuelle
if 'audit_id' not in st.session_state:
    st.session_state['audit_id'] = str(uuid.uuid4())
    st.session_state['audit_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Track the previously selected zone
if 'selected_zone' not in st.session_state:
    st.session_state.selected_zone = None

# Sélection de la zone
st.write("Sélectionnez la zone à auditer:")
selected_zone = st.selectbox("Choisir une ZONE", options=st.session_state.df_checklists["ZONE"].unique())

# Check if the zone has changed
if st.session_state.selected_zone != selected_zone:
    st.session_state.selected_zone = selected_zone
    # Filter the checklist based on the selected zone
    filtered_checklist = st.session_state.df_checklists[st.session_state.df_checklists["ZONE"] == selected_zone]
    st.session_state.inspection_results = filtered_checklist.copy()
    st.session_state.inspection_results['Conformité'] = ""
    st.session_state.inspection_results['Commentaires'] = ""
    st.session_state.inspection_results['Lien Photo'] = ""

# Now you can continue with your app logic
st.title("Application de Gestion des Checklists d'Inspection avec Google Sheets")

if selected_zone:
    st.write(f"ZONE sélectionnée : {selected_zone}")
    filtered_checklist = st.session_state.df_checklists[st.session_state.df_checklists["ZONE"] == selected_zone]

    # Affichage des critères
    for index, row in st.session_state.inspection_results.iterrows():
        criterion = row['Critere']
        st.subheader(criterion)

        # Initialiser les états si non présents
        if f"conformity_{index}" not in st.session_state:
            st.session_state[f"conformity_{index}"] = "Non Applicable"
            st.session_state[f"show_comment_{index}"] = False
            st.session_state[f"show_photo_{index}"] = False

        conformity_status = st.session_state[f"conformity_{index}"]

        # Dynamic classes for button colors
        conform_class = "selected-conforme" if conformity_status == "Conforme" else ""
        non_conform_class = "selected-non-conforme" if conformity_status == "Non Conforme" else ""
        na_class = "selected-na" if conformity_status == "Non Applicable" else ""

        # Create buttons and handle click events
        col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 1, 1])
        with col1:
            if st.button("Conforme", key=f"conforme_{index}"):
                st.session_state[f"conformity_{index}"] = "Conforme"
        with col2:
            if st.button("Non Conforme", key=f"non_conforme_{index}"):
                st.session_state[f"conformity_{index}"] = "Non Conforme"
        with col3:
            if st.button("Non Applicable", key=f"na_{index}"):
                st.session_state[f"conformity_{index}"] = "Non Applicable"
        with col4:
            if st.button("✎", key=f"comment_btn_{index}"):
                st.session_state[f"show_comment_{index}"] = not st.session_state[f"show_comment_{index}"]
        with col5:
            if st.button("📷", key=f"photo_btn_{index}"):
                st.session_state[f"show_photo_{index}"] = not st.session_state[f"show_photo_{index}"]

        st.write(f"Statut sélectionné pour {criterion}: {st.session_state[f'conformity_{index}']}")

        # Affichage conditionnel des champs de commentaire et de photo
        if st.session_state[f"show_comment_{index}"]:
            st.session_state.inspection_results.at[index, 'Commentaires'] = st.text_area(f"Commentaire pour {criterion}", key=f"comment_text_{index}")

        if st.session_state[f"show_photo_{index}"]:
            photo = st.file_uploader(f"Uploader une photo pour {criterion}", key=f"photo_upload_{index}", type=["jpg", "jpeg", "png"])
            if photo:
                folder_id = "1hwT-4Xszxu7QCnb9jw7M2eVOnQ-kq-8c"  # Dossier Google Drive constant
                file_id = upload_photo(photo, folder_id)
                if file_id:
                    st.session_state.inspection_results.at[index, 'Lien Photo'] = f"https://drive.google.com/file/d/{file_id}/view"
                    st.success(f"Photo téléchargée avec succès. [Voir la photo](https://drive.google.com/file/d/{file_id}/view)")

# Fonction pour uploader une photo sur Google Drive
def upload_photo(file, folder_id):
    try:
        file_metadata = {
            'name': file.name,
            'parents': [folder_id]
        }
        media = MediaFileUpload(file, mimetype=file.type)
        uploaded_file = drive_service.files().create(body=file_metadata, media_body=media, fields="id").execute()
        return uploaded_file.get("id")
    except Exception as e:
        st.error(f"Erreur lors de l'upload de la photo : {e}")
        return None

# Bouton pour enregistrer les résultats de l'inspection
if st.button("Enregistrer les résultats de l'inspection"):
    all_audited = all(st.session_state.inspection_results['Conformité'] != "")
    if not all_audited:
        st.error("L'audit est incomplet. Veuillez finaliser toutes les zones.")
    else:
        # Ajouter l'ID de l'audit et la date aux résultats
        st.session_state.inspection_results['Audit ID'] = st.session_state['audit_id']
        st.session_state.inspection_results['Date'] = st.session_state['audit_date']
        try:
            # Mise à jour de la feuille de résultats sur Google Sheets
            result_sheet.update([st.session_state.inspection_results.columns.values.tolist()] + st.session_state.inspection_results.values.tolist())
            st.success("Résultats de l'inspection enregistrés avec succès.")
        except Exception as e:
            st.error(f"Erreur lors de l'enregistrement des résultats de l'inspection : {e}")



