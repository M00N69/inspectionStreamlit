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
    }
    .conformity-button.selected {
        background-color: #007BFF;
        border-color: #007BFF;
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
        margin-left: 5px;
        cursor: pointer;
    }
    .icon-button:hover {
        background-color: #0056b3;
    }
    .hidden {
        display: none;
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
    st.stop()

# Initialize session state if not already done
if 'df_checklists' not in st.session_state:
    st.session_state.df_checklists = df

# Chargement d'une nouvelle grille à partir d'un fichier Excel
uploaded_file = st.file_uploader("Charger une nouvelle grille d'inspection (fichier Excel)", type="xlsx")
if uploaded_file:
    try:
        new_data = pd.read_excel(uploaded_file)
        st.session_state.df_checklists = new_data
        st.success("Nouvelle grille chargée avec succès.")
    except Exception as e:
        st.error(f"Erreur lors du chargement du fichier Excel : {e}")

# Now you can continue with your app logic
st.title("Application de Gestion des Checklists d'Inspection avec Google Sheets")

# Initialisation de l'audit avec un ID unique et la date actuelle
if 'audit_id' not in st.session_state:
    st.session_state['audit_id'] = str(uuid.uuid4())
    st.session_state['audit_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Sélection de la zone
st.write("Sélectionnez la zone à auditer:")
selected_zone = st.selectbox("Choisir une ZONE", options=st.session_state.df_checklists["ZONE"].unique())

if selected_zone:
    st.write(f"ZONE sélectionnée : {selected_zone}")
    filtered_checklist = st.session_state.df_checklists[st.session_state.df_checklists["ZONE"] == selected_zone]

    # Préparation des résultats d'inspection
    if 'inspection_results' not in st.session_state:
        st.session_state.inspection_results = filtered_checklist.copy()
        st.session_state.inspection_results['Conformité'] = ""
        st.session_state.inspection_results['Commentaires'] = ""
        st.session_state.inspection_results['Lien Photo'] = ""

    # Affichage des critères
    for index, row in st.session_state.inspection_results.iterrows():
        criterion = row['Critere']
        st.subheader(criterion)

        # Initialiser les états si non présents
        if f"conformity_{index}" not in st.session_state:
            st.session_state[f"conformity_{index}"] = "Non Applicable"
            st.session_state[f"show_comment_{index}"] = False
            st.session_state[f"show_photo_{index}"] = False

        # Gestion du statut de conformité
        conformity_status = st.session_state[f"conformity_{index}"]

        st.markdown(f"""
        <div class="button-container">
            <button class="conformity-button {'selected' if conformity_status == 'Conforme' else ''}" onclick="window.location.href='?conformity={index}&value=Conforme'">Conforme</button>
            <button class="conformity-button {'selected' if conformity_status == 'Non Conforme' else ''}" onclick="window.location.href='?conformity={index}&value=Non Conforme'">Non Conforme</button>
            <button class="conformity-button {'selected' if conformity_status == 'Non Applicable' else ''}" onclick="window.location.href='?conformity={index}&value=Non Applicable'">Non Applicable</button>
            <span class="icon-button" onclick="window.location.href='?comment={index}'">✎</span>
            <span class="icon-button" onclick="window.location.href='?photo={index}'">📷</span>
        </div>
        """, unsafe_allow_html=True)

        # Handling the URL query parameters for conformity, comment, and photo actions
        query_params = st.experimental_get_query_params()

        if f'conformity' in query_params and query_params['conformity'][0] == str(index):
            st.session_state[f"conformity_{index}"] = query_params['value'][0]

        if f'comment' in query_params and query_params['comment'][0] == str(index):
            st.session_state[f"show_comment_{index}"] = not st.session_state[f"show_comment_{index}"]

        if f'photo' in query_params and query_params['photo'][0] == str(index):
            st.session_state[f"show_photo_{index}"] = not st.session_state[f"show_photo_{index}"]

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

        st.write(f"Statut sélectionné pour {criterion}: {st.session_state[f'conformity_{index}']}")


    # Gestion des commentaires et des photos
    for index, row in st.session_state.inspection_results.iterrows():
        criterion = row['Critere']

        # Bouton pour afficher le champ de commentaire
        if st.button(f"Ajouter un commentaire {index}", key=f"comment_btn_{index}"):
            st.session_state[f"show_comment_{index}"] = not st.session_state.get(f"show_comment_{index}", False)
        
        # Affichage du champ de commentaire si le bouton est cliqué
        if st.session_state.get(f"show_comment_{index}", False):
            st.session_state.inspection_results.at[index, 'Commentaires'] = st.text_area(f"Commentaire pour {criterion}", key=f"comment_text_{index}")

        # Bouton pour uploader une photo
        if st.button(f"Ajouter une photo {index}", key=f"photo_btn_{index}"):
            st.session_state[f"show_photo_{index}"] = not st.session_state.get(f"show_photo_{index}", False)

        # Affichage du champ d'upload de photo si le bouton est cliqué
        if st.session_state.get(f"show_photo_{index}", False):
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

# Vérifier si toutes les zones ont été auditées
all_audited = all(st.session_state.inspection_results['Conformité'] != "")

# Bouton pour enregistrer les résultats de l'inspection
if st.button("Enregistrer les résultats de l'inspection"):
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

# Try to retrieve data from Google Sheets
try:
    data = sheet.get_all_records()  # Fetch all records from the specified worksheet
    df = pd.DataFrame(data)
    if df.empty:
        st.error("La feuille de calcul est vide ou les données n'ont pas été correctement récupérées.")
        st.stop()
except Exception as e:
    st.error(f"Erreur lors de la récupération des données de Google Sheets : {e}")
    st.stop()

# Initialize session state if not already done
if 'df_checklists' not in st.session_state:
    st.session_state.df_checklists = df

# Ensure data was fetched correctly
if not df.empty:
    st.session_state.df_checklists = df
else:
    st.error("Données non récupérées, la variable 'df' est vide.")
    st.stop()

