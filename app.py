import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Connexion à Google Sheets via streamlit-gsheets
st.title("Application de Gestion des Checklists d'Inspection avec Google Sheets")

# Connexion à Google Sheets
conn = st.experimental_connection("gsheets", type=GSheetsConnection)
df = conn.read(worksheet="<worksheet-name>")  # Remplace par le nom de ton worksheet
st.write("Données récupérées depuis Google Sheets:")
st.dataframe(df)

# Connexion à Google Drive
def connect_to_gdrive():
    credentials = Credentials.from_service_account_info(st.secrets["connections"]["gsheets"])
    service = build("drive", "v3", credentials=credentials)
    return service

drive_service = connect_to_gdrive()

# Fonction pour uploader une photo sur Google Drive
def upload_photo(file, folder_id):
    file_metadata = {
        'name': file.name,
        'parents': [folder_id]
    }
    media = MediaFileUpload(file, mimetype=file.type)
    uploaded_file = drive_service.files().create(body=file_metadata, media_body=media, fields="id").execute()
    return uploaded_file.get("id")

# Étape 1 : Ajout de données à partir d'un fichier Excel
uploaded_file = st.file_uploader("Charger le fichier Excel contenant les zones et critères", type="xlsx")
if uploaded_file:
    df_upload = pd.read_excel(uploaded_file)
    st.write("Fichier chargé avec succès")
    st.write(df_upload)

    # Ajouter la nouvelle checklist dans Google Sheets
    st.write("Modifiez les points si nécessaire :")
    edited_df = st.experimental_data_editor(df_upload, num_rows="dynamic")

    if st.button("Enregistrer la checklist"):
        conn.write(worksheet="<LISTCONTROLE>", data=edited_df)
        st.success("Checklist enregistrée avec succès.")

# Étape 2 : Sélection d'une checklist et gestion des inspections
if st.button("Charger les checklists"):
    checklists = conn.read(worksheet="<worksheet-name>")
    st.dataframe(checklists)

    if not checklists.empty:
        selected_checklist = st.selectbox("Choisir une checklist", options=checklists["Checklist Name"].unique())
        if selected_checklist:
            st.write(f"Checklist sélectionnée : {selected_checklist}")
            filtered_checklist = checklists[checklists["Checklist Name"] == selected_checklist]
            st.dataframe(filtered_checklist)

            # Uploader une photo pour l'inspection
            photo = st.file_uploader("Ajouter une photo pour cette inspection", type=["jpg", "jpeg", "png"])
            if photo:
                folder_id = "<https://drive.google.com/drive/folders/1hwT-4Xszxu7QCnb9jw7M2eVOnQ-kq-8c?hl=fr>"  # ID du dossier dans lequel tu veux stocker les photos
                file_id = upload_photo(photo, folder_id)
                st.success(f"Photo téléchargée avec succès. File ID: {file_id}")

# Étape 3 : Finaliser l'inspection et enregistrer les résultats
st.header("Finaliser l'inspection")

# Récapitulatif des résultats de l'inspection
if 'filtered_checklist' in locals() and not filtered_checklist.empty:
    st.subheader("Résumé de l'inspection")
    inspection_results = filtered_checklist.copy()

    # Ajout de colonnes pour les résultats (conformité, commentaires, lien photo)
    inspection_results['Conformité'] = ""
    inspection_results['Commentaires'] = ""
    inspection_results['Lien Photo'] = ""

    for index, row in inspection_results.iterrows():
        conformity_status = st.radio(
            f"Évaluation pour {row['Critère']}",
            ["Conforme", "Non Conforme", "Non Applicable"],
            key=f"conformity_{index}"
        )
        comment = st.text_area(f"Ajouter un commentaire pour {row['Critère']}", key=f"comment_{index}")
        photo_link = st.text_input(f"Lien photo pour {row['Critère']}", key=f"photo_link_{index}", value=row['Lien Photo'])

        inspection_results.at[index, 'Conformité'] = conformity_status
        inspection_results.at[index, 'Commentaires'] = comment
        inspection_results.at[index, 'Lien Photo'] = photo_link

    if st.button("Enregistrer les résultats de l'inspection"):
        # Enregistrer les résultats dans une nouvelle feuille ou dans un onglet spécifique
        conn.write(worksheet="resultat", data=inspection_results)
        st.success("Résultats de l'inspection enregistrés avec succès.")
