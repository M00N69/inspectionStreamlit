import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Définir les scopes OAuth pour Google Sheets et Google Drive
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# Charger les credentials du service account depuis le fichier secrets.toml
credentials = Credentials.from_service_account_info(
    st.secrets["connections"]["gsheets"], scopes=SCOPES
)

# Connexion à Google Sheets via gspread
gc = gspread.authorize(credentials)
try:
    sheet = gc.open("LISTCONTROLE").worksheet("table")  # Remplace "table" par le nom réel de ton worksheet
    result_sheet = gc.open("LISTCONTROLE").worksheet("resultat")
except Exception as e:
    st.error(f"Erreur lors de la connexion à Google Sheets : {e}")
    st.stop()

# Récupérer les données depuis Google Sheets
try:
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
except Exception as e:
    st.error(f"Erreur lors de la récupération des données de Google Sheets : {e}")
    st.stop()

st.title("Application de Gestion des Checklists d'Inspection avec Google Sheets")

# Chargement des Checklists
if 'df_checklists' not in st.session_state:
    st.session_state.df_checklists = df

st.write("Données récupérées depuis Google Sheets:")
st.dataframe(st.session_state.df_checklists)

# Connexion à Google Drive
def connect_to_gdrive():
    try:
        service = build("drive", "v3", credentials=credentials)
        return service
    except Exception as e:
        st.error(f"Erreur lors de la connexion à Google Drive : {e}")
        st.stop()

drive_service = connect_to_gdrive()

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

# Étape 1 : Ajout de données à partir d'un fichier Excel
uploaded_file = st.file_uploader("Charger le fichier Excel contenant les zones et critères", type="xlsx")
if uploaded_file:
    df_upload = pd.read_excel(uploaded_file)
    st.write("Fichier chargé avec succès")
    st.write(df_upload)

    # Modifier les points si nécessaire
    if st.button("Enregistrer la checklist"):
        try:
            sheet.update([df_upload.columns.values.tolist()] + df_upload.values.tolist())
            st.success("Checklist enregistrée avec succès.")
            st.session_state.df_checklists = df_upload
        except Exception as e:
            st.error(f"Erreur lors de l'enregistrement de la checklist : {e}")

# Étape 2 : Sélection d'une checklist et gestion des inspections
if st.button("Charger les checklists"):
    st.session_state.df_checklists = pd.DataFrame(sheet.get_all_records())
    st.dataframe(st.session_state.df_checklists)

if not st.session_state.df_checklists.empty:
    selected_zone = st.selectbox("Choisir une ZONE", options=st.session_state.df_checklists["ZONE"].unique())
    if selected_zone:
        st.write(f"ZONE sélectionnée : {selected_zone}")
        filtered_checklist = st.session_state.df_checklists[st.session_state.df_checklists["ZONE"] == selected_zone]
        st.dataframe(filtered_checklist)

        # Stocker les résultats de conformité dans session_state
        if 'inspection_results' not in st.session_state:
            st.session_state.inspection_results = filtered_checklist.copy()
            st.session_state.inspection_results['Conformité'] = ""
            st.session_state.inspection_results['Commentaires'] = ""
            st.session_state.inspection_results['Lien Photo'] = ""

        # Uploader une photo pour l'inspection
        photo = st.file_uploader("Ajouter une photo pour cette inspection", type=["jpg", "jpeg", "png"])
        if photo:
            folder_id = "1hwT-4Xszxu7QCnb9jw7M2eVOnQ-kq-8c"  # ID du dossier Google Drive
            file_id = upload_photo(photo, folder_id)
            if file_id:
                st.success(f"Photo téléchargée avec succès. File ID: {file_id}")

# Étape 3 : Finaliser l'inspection et enregistrer les résultats
st.header("Finaliser l'inspection")

if 'inspection_results' in st.session_state:
    st.subheader("Résumé de l'inspection")
    for index, row in st.session_state.inspection_results.iterrows():
        conformity_status = st.radio(
            f"Évaluation pour {row['Critere']}",
            ["Conforme", "Non Conforme", "Non Applicable"],
            key=f"conformity_{index}"
        )
        comment = st.text_area(f"Ajouter un commentaire pour {row['Critere']}", key=f"comment_{index}")
        photo_link = st.text_input(f"Lien photo pour {row['Critere']}", key=f"photo_link_{index}")

        st.session_state.inspection_results.at[index, 'Conformité'] = conformity_status
        st.session_state.inspection_results.at[index, 'Commentaires'] = comment
        st.session_state.inspection_results.at[index, 'Lien Photo'] = photo_link

    if st.button("Enregistrer les résultats de l'inspection"):
        try:
            result_sheet.update([st.session_state.inspection_results.columns.values.tolist()] + st.session_state.inspection_results.values.tolist())
            st.success("Résultats de l'inspection enregistrés avec succès.")
        except Exception as e:
            st.error(f"Erreur lors de l'enregistrement des résultats de l'inspection : {e}")


