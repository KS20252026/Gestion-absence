import streamlit as st
import pandas as pd
import json

# Clé de l'état de session qui simulera le stockage distant
DATA_KEY = "persisted_data"

# --- Fonctions de Persistance (SIMULATION D'UNE BASE DE DONNÉES CLOUD) ---

# NOTE: Dans un environnement Streamlit réel, cette fonction serait remplacée par
# une lecture/écriture vers Google Sheets ou Firestore. Ici, nous utilisons
# l'état du Canvas comme stockage persistant simulé.

def load_initial_data(df_csv):
    """
    Initialise l'état de la base de données simulée.
    Si DATA_KEY n'existe pas, il est créé à partir du CSV initial.
    """
    if DATA_KEY not in st.session_state:
        # Convertit le DataFrame initial en un format JSON pour le stockage
        st.session_state[DATA_KEY] = df_csv.to_json(orient='split', index=False)
        st.info("Données initialisées à partir de 'data.csv'. Les modifications seront sauvegardées dans la mémoire de l'application.")
        

def load_persisted_data():
    """Charge les données depuis le stockage simulé (JSON)."""
    if DATA_KEY in st.session_state:
        # Reconstruit le DataFrame à partir de la chaîne JSON stockée
        data_json = st.session_state[DATA_KEY]
        df = pd.read_json(data_json, orient='split')
        
        # S'assurer que les booléens sont conservés
        for col in df.columns:
            if 'Présence' in col:
                df[col] = df[col].astype(bool)
        
        return df
    return pd.DataFrame()


def save_persisted_data(df):
    """Sauvegarde les données modifiées dans le stockage simulé (JSON)."""
    # Convertit le DataFrame mis à jour en JSON et le stocke
    st.session_state[DATA_KEY] = df.to_json(orient='split', index=False)
    st.success("💾 Modifications sauvegardées dans la mémoire de l'application.")


# --- Fonction de Chargement et de Nettoyage (Utilise le stockage simulé) ---

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
    page_title="Gestion des Notes et Absences",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("👨‍🏫 Gestionnaire de Notes et Absences")
st.caption("Application Web pour le suivi des étudiants. Les données sont persistantes dans cette session.")
st.divider()

# 1. Tenter de charger les données initiales du CSV (ne se fait qu'une fois)
initial_df = load_and_clean_data_from_csv()

# 2. Initialiser le stockage JSON si nécessaire et charger les données modifiées
if not initial_df.empty:
    load_initial_data(initial_df)
    # df_active est le DataFrame que l'utilisateur édite
    df_active = load_persisted_data()
    st.session_state.data_df = df_active

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
            # 4. Bouton pour déclencher la sauvegarde des données modifiées
            save_persisted_data(st.session_state.data_df)

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
    st.info("Le DataFrame est vide. Veuillez vous assurer que 'data.csv' existe et n'est pas corrompu.")
