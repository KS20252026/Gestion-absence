import streamlit as st
import pandas as pd
import database_connector as db_connector # Import du nouveau fichier de connecteur
import json

# --- Fonction de Chargement et de Nettoyage (Utilise le CSV local pour l'initialisation) ---

@st.cache_data
def load_and_clean_data_from_csv():
    """
    Lit le CSV une seule fois pour l'initialisation et effectue le nettoyage initial.
    """
    try:
        # Lecture du fichier CSV
        df = pd.read_csv('data.csv', encoding='utf-8')
        
        # Nettoyage des noms de colonnes
        new_columns = {}
        for col in df.columns:
            clean_col = col.strip() 
            if col != clean_col:
                new_columns[col] = clean_col
        df.rename(columns=new_columns, inplace=True)
        
        return df
                
    except FileNotFoundError:
        st.error("⚠️ Erreur : Le fichier 'data.csv' est introuvable. Impossible d'initialiser les données.")
        return pd.DataFrame() 
    except Exception as e:
        st.error(f"Une erreur s'est produite lors du chargement initial du CSV : {e}")
        st.code(e, language='python')
        return pd.DataFrame()


# --- Fonctions de Rapport (Logique Métier) ---

def generate_absence_report(df):
    """Calcule le total des absences par étudiant."""
    absence_cols = [col for col in df.columns if 'Présence' in col]
    
    if not absence_cols:
        st.warning("Aucune colonne 'Présence' trouvée pour le rapport d'absences.")
        return None

    # Compter le nombre d'absences (où la valeur est False) par ligne
    df['Total Absences'] = (~df[absence_cols]).sum(axis=1)

    # Utiliser 'Nom' et 'S1' comme identifiants
    if 'S1' in df.columns:
        report = df[['Nom', 'S1', 'Total Absences']].sort_values(by='Total Absences', ascending=False)
    else:
        report = df[['Nom', 'Total Absences']].sort_values(by='Total Absences', ascending=False)
        
    return report

def generate_notes_report(df):
    """Calcule la moyenne des notes par étudiant."""
    note_cols = [col for col in df.columns if 'Note' in col]

    if not note_cols:
        st.warning("Aucune colonne 'Note' trouvée pour le rapport de notes.")
        return None

    # Calculer la moyenne des notes pour chaque étudiant (ligne)
    df['Moyenne Notes'] = df[note_cols].mean(axis=1).round(2)

    # Utiliser 'Nom' et 'S1' comme identifiants
    if 'S1' in df.columns:
        report = df[['Nom', 'S1', 'Moyenne Notes']].sort_values(by='Moyenne Notes', ascending=False)
    else:
        report = df[['Nom', 'Moyenne Notes']].sort_values(by='Moyenne Notes', ascending=False)
        
    return report

# --- Configuration de l'Application Streamlit ---
st.set_page_config(
    page_title="Absences/Tests GMAT1-MRN (K. SAI-2025)", # <--- TITRE DE L'ONGLET DU NAVIGATEUR MIS À JOUR
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📊 Absences/Tests GMAT1-MRN (K. SAI-2025)") # <--- TITRE PRINCIPAL SUR LA PAGE MIS À JOUR
st.caption("Application Web pour le suivi des étudiants. Architecture prête pour le Cloud.")
st.divider()

# --- LOGIQUE DE CHARGEMENT PRINCIPALE (PRÊTE POUR LE CLOUD) ---

if 'data_df' not in st.session_state:
    db_connector.init_db()
    
    # 1. Tenter de charger les données depuis la base de données simulée (Cloud)
    df_from_cloud = db_connector.fetch_data()

    if df_from_cloud.empty:
        # 2. Si la base de données Cloud est vide (première exécution), charger depuis le CSV local
        initial_df = load_and_clean_data_from_csv()
        
        if not initial_df.empty:
            # 3. Écrire les données initiales du CSV dans la base de données Cloud simulée
            db_connector.write_data(initial_df)
            st.session_state.data_df = initial_df.copy()
            st.info("Initialisation réussie : Données chargées du CSV et écrites dans la base de données simulée.")
        else:
            st.session_state.data_df = pd.DataFrame()
    else:
        # 4. Succès : Les données ont été chargées depuis la base de données Cloud simulée
        st.session_state.data_df = df_from_cloud
        st.success("Données chargées depuis la base de données simulée. Les modifications précédentes sont conservées.")


# Afficher la table complète et la rendre modifiable
if 'data_df' in st.session_state and not st.session_state.data_df.empty:
    st.subheader("Tableau des Notes et Absences (Édition en Temps Réel)")
    
    # Construction de la configuration des colonnes pour les rendre interactives
    column_config = {}
    for col in st.session_state.data_df.columns:
        col_name = col.strip() if isinstance(col, str) else col
        
        if 'Présence' in col_name:
            column_config[col] = st.column_config.CheckboxColumn(
                col,
                help="Cochez si l'étudiant était présent.",
                default=False,
                width="small"
            )
        elif 'Note' in col_name:
            column_config[col] = st.column_config.NumberColumn(
                col,
                help="Saisissez la note de 0 à 20.",
                min_value=0.0,
                max_value=20.0,
                format="%.2f",
                width="small"
            )
        elif col in ['S1', 'Nom']: # Rendre 'Nom' aussi non modifiable pour la cohérence
             column_config[col] = st.column_config.TextColumn(
                col,
                disabled=True
            )


    # st.data_editor remplace la QTableWidget. Les changements sont temporaires ici.
    edited_df = st.data_editor(
        st.session_state.data_df,
        key="data_editor",
        column_config=column_config,
        hide_index=True,
        use_container_width=True,
        num_rows="fixed"
    )
    
    # 3. Mettre à jour l'état de session avec le DataFrame édité
    if not edited_df.equals(st.session_state.data_df):
        st.session_state.data_df = edited_df
    
    st.caption("Vous pouvez maintenant modifier les cases à cocher (Présence) et les notes directement dans le tableau.")
    
    st.markdown("---") 
    st.info("Faites défiler vers le bas si vous ne voyez pas les boutons de rapport.")

    st.subheader("Générer les Rapports")

    # Utilisation de colonnes Streamlit pour aligner les boutons
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("💾 Sauvegarder les Modifications", use_container_width=True):
            # 4. Bouton pour déclencher la sauvegarde des données modifiées dans la base de données simulée
            db_connector.write_data(st.session_state.data_df)

    with col2:
        if st.button("📊 Bilan des Absences", use_container_width=True):
            report_absences = generate_absence_report(st.session_state.data_df.copy()) 
            if report_absences is not None:
                st.success("Rapport d'absences généré :")
                st.dataframe(report_absences, use_container_width=True, hide_index=True)

    with col3:
        if st.button("📈 Bilan des Notes Moyennes", use_container_width=True):
            report_notes = generate_notes_report(st.session_state.data_df.copy())
            if report_notes is not None:
                st.success("Rapport des notes moyennes généré :")
                st.dataframe(report_notes, use_container_width=True, hide_index=True)


else:
    st.info("Le DataFrame est vide. Veuillez vous assurer que 'data.csv' existe et n'est pas corrompu pour l'initialisation.")
