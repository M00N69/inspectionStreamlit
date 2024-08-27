import streamlit as st
import pandas as pd
from supabase import create_client, Client

# Connexion à Supabase
url = "https://nlpofscrwwvubtugcrqa.supabase.co"  # Remplace par l'URL de ton projet Supabase
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5scG9mc2Nyd3d2dWJ0dWdjcnFhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjQ3ODQ1NTUsImV4cCI6MjA0MDM2MDU1NX0.YUyPvm96JrZ7NJpYyLhgXmrN8gEQ_SVcpUlHVPHToBg"  # Remplace par ta clé API publique
supabase: Client = create_client(url, key)

st.title("Application de Gestion des Checklists d'Inspection")

# Étape 1 : Chargement du fichier Excel pour créer une checklist
uploaded_file = st.file_uploader("Charger le fichier Excel contenant les zones et critères", type="xlsx")
if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    
    if len(df.columns) < 2:
        st.error("Le fichier doit contenir au moins deux colonnes : 'ZONE' et 'Critère'.")
    else:
        df.columns = ['ZONE', 'Critère']
        st.write("Aperçu de la checklist :")
        st.write(df)

        # Modification des Points
        st.write("Modifiez les points si nécessaire :")
        edited_df = st.experimental_data_editor(df, num_rows="dynamic")

        # Nommer et Enregistrer la Checklist
        checklist_name = st.text_input("Nom de la checklist")
        if st.button("Enregistrer la checklist"):
            if not checklist_name:
                st.error("Veuillez entrer un nom pour la checklist.")
            else:
                checklist_data = {
                    "name": checklist_name,
                    "points": edited_df.to_dict('records')
                }
                res = supabase.table("checklists").insert(checklist_data).execute()
                if res.status_code == 201:
                    st.success("Checklist enregistrée avec succès.")
                else:
                    st.error("Une erreur s'est produite lors de l'enregistrement.")

# Étape 2 : Sélection et gestion des checklists pour une inspection
st.header("Démarrer une nouvelle inspection")
checklists = supabase.table("checklists").select("*").execute()

if checklists.data:
    selected_checklist = st.selectbox("Choisir une checklist", options=[cl['name'] for cl in checklists.data])

    if st.button("Démarrer l'inspection"):
        selected_checklist_data = next(cl for cl in checklists.data if cl['name'] == selected_checklist)
        
        # Système d'onglets pour chaque zone
        zones = pd.DataFrame(selected_checklist_data['points'])['ZONE'].unique()
        tabs = st.tabs(list(zones))

        inspection_results = []

        for i, zone in enumerate(zones):
            with tabs[i]:
                st.header(f"Zone : {zone}")
                points_in_zone = [p for p in selected_checklist_data['points'] if p['ZONE'] == zone]
                
                for point in points_in_zone:
                    st.subheader(f"Critère : {point['Critère']}")
                    
                    conformity_status = st.radio(
                        f"Évaluation pour {point['Critère']}",
                        ["Conforme", "Non Conforme", "Non Applicable"],
                        key=f"conformity_{point['Critère']}"
                    )

                    comment = st.text_area("Ajouter un commentaire (optionnel)", key=f"comment_{point['Critère']}")
                    photo = st.file_uploader("Ajouter une photo", type=["jpg", "jpeg", "png"], key=f"photo_{point['Critère']}")

                    if st.button("Sauvegarder ce point", key=f"save_{point['Critère']}"):
                        result = {
                            "point": point['Critère'],
                            "zone": zone,
                            "conformity_status": conformity_status,
                            "comment": comment,
                            "photo_url": None  # Logique pour gérer le stockage de la photo
                        }
                        # Gérer l'upload de la photo sur Supabase Storage
                        if photo:
                            photo_name = f"{selected_checklist}_{zone}_{point['Critère']}.jpg"
                            res_upload = supabase.storage.from_("inspection-photos").upload(photo_name, photo)
                            if res_upload.status_code == 201:
                                result['photo_url'] = f"https://nlpofscrwwvubtugcrqa.supabase.co/storage/v1/object/sign/photos/legume.jpg?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1cmwiOiJwaG90b3MvbGVndW1lLmpwZyIsImlhdCI6MTcyNDc4NzA2NSwiZXhwIjoxNzU2MzIzMDY1fQ.vnB84NzG7VTe2PmKNSSWnWsVrnVYNtax-GTqQF5NZqI&t=2024-08-27T19%3A31%3A06.227Z"
                        inspection_results.append(result)
                        st.success(f"Point {point['Critère']} sauvegardé avec succès.")

        if st.button("Finaliser l'inspection"):
            inspection_data = {
                "checklist_id": selected_checklist_data['id'],
                "results": inspection_results,
                "status": "completed"
            }
            res = supabase.table("inspections").insert(inspection_data).execute()
            if res.status_code == 201:
                st.success("Inspection finalisée et enregistrée avec succès.")
            else:
                st.error("Une erreur s'est produite lors de la finalisation de l'inspection.")

else:
    st.write("Aucune checklist disponible.")
