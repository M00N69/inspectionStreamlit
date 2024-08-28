import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Charger les credentials du service account depuis le fichier secrets.toml
credentials = Credentials.from_service_account_info(st.secrets["connections"]["gsheets"])

# Connexion à Google Sheets via gspread
gc = gspread.authorize(credentials)
sheet = gc.open("LISTCONTROLE").worksheet("Sheet1")  # Remplace "Sheet1" par le nom de ton worksheet réel
data = sheet.get_all_records()
df = pd.DataFrame(data)

st.title("Application de Gestion des Checklists d'Inspection avec Google Sheets")
st.write("Données récupérées depuis Google Sheets:")
st.dataframe(df)

# Connexion à Google Drive
def connect_to_gdrive():
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

    # Modifier les points si nécessaire
    if st.button("Enregistrer la checklist"):
        sheet.update([df_upload.columns.values.tolist()] + df_upload.values.tolist())
        st.success("Checklist enregistrée avec succès.")

# Étape 2 : Sélection d'une checklist et gestion des inspections
if st.button("Charger les checklists"):
    checklists = sheet.get_all_records()
    df_checklists = pd.DataFrame(checklists)
    st.dataframe(df_checklists)

    if not df_checklists.empty:
        selected_checklist = st.selectbox("Choisir une checklist", options=df_checklists["Checklist Name"].unique())
        if selected_checklist:
            st.write(f"Checklist sélectionnée : {selected_checklist}")
            filtered_checklist = df_checklists[df_checklists["Checklist Name"] == selected_checklist]
            st.dataframe(filtered_checklist)

            # Uploader une photo pour l'inspection
            photo = st.file_uploader("Ajouter une photo pour cette inspection", type=["jpg", "jpeg", "png"])
            if photo:
                folder_id = "1hwT-4Xszxu7QCnb9jw7M2eVOnQ-kq-8c"  # ID du dossier Google Drive
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
        result_sheet = gc.open("LISTCONTROLE").worksheet("resultat")
        result_sheet.update([inspection_results.columns.values.tolist()] + inspection_results.values.tolist())
        st.success("Résultats de l'inspection enregistrés avec succès.")

