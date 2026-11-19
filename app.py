"""Mini-projet de synthèse S7 : analyse d'un registre biomédical.

Application pédagogique Streamlit ; seuils et score issus du support de séance 7.
Les données de démonstration sont entièrement fictives.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
import unicodedata

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st


COLONNES = ["nom", "age", "poids", "taille", "temperature", "fc", "spo2", "glycemie"]
PARAMETRES = {
    "age": ("Âge", "ans"),
    "poids": ("Poids", "kg"),
    "taille": ("Taille", "m"),
    "temperature": ("Température", "°C"),
    "fc": ("Fréquence cardiaque", "bpm"),
    "spo2": ("SpO₂", "%"),
    "glycemie": ("Glycémie", "g/L"),
    "imc": ("IMC", "kg/m²"),
}
NIVEAUX = ["Faible", "Modéré", "Élevé", "Critique"]
ALIASES = {
    "temperature_c": "temperature", "temp": "temperature", "t": "temperature",
    "frequence_cardiaque": "fc", "frequence": "fc", "frequence_cardiaque_bpm": "fc",
    "saturation": "spo2", "spo_2": "spo2", "sao2": "spo2",
    "glycemie_gl": "glycemie", "glycemie_g_l": "glycemie",
    "nom_du_patient": "nom", "patient": "nom", "sexe": "sexe",
}


def nom_normalise(nom: str) -> str:
    valeur = unicodedata.normalize("NFKD", str(nom))
    valeur = "".join(c for c in valeur if not unicodedata.combining(c))
    valeur = valeur.strip().lower().replace(" ", "_").replace("/", "_")
    return ALIASES.get(valeur, valeur)


def charger_csv(source) -> pd.DataFrame:
    """Lit un CSV à séparateur virgule ou point-virgule."""
    return pd.read_csv(source, sep=None, engine="python", encoding="utf-8-sig")


def preparer_dataframe(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str], list[str]]:
    """Nettoie les colonnes sans inventer de mesures manquantes."""
    data = df.copy()
    data.columns = [nom_normalise(c) for c in data.columns]
    if data.columns.duplicated().any():
        return data, [], ["Noms de colonnes en double après normalisation."]
    ajouts = []
    for col in COLONNES:
        if col not in data.columns:
            data[col] = np.nan
            ajouts.append(col)
    if "sexe" not in data.columns:
        data["sexe"] = "Non précisé"
    if "nom" in data.columns:
        data["nom"] = data["nom"].fillna("").astype(str).str.strip()
    for col in COLONNES[1:]:
        data[col] = pd.to_numeric(
            data[col].astype("string").str.replace(",", ".", regex=False),
            errors="coerce",
        ).astype(float)
    data = data[["nom", "sexe"] + COLONNES[1:]]
    return data, ajouts, []


def valider_et_convertir(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str], list[str]]:
    """Vérifie les valeurs et convertit une taille en cm si nécessaire."""
    data = df.copy()
    remarques, erreurs = [], []
    if data.empty:
        erreurs.append("Ajoute au moins un patient.")
        return data, remarques, erreurs
    data["nom"] = data["nom"].fillna("").astype(str).str.strip()
    for col in COLONNES[1:]:
        data[col] = pd.to_numeric(
            data[col].astype("string").str.replace(",", ".", regex=False),
            errors="coerce",
        ).astype(float)
    for col in COLONNES:
        if col == "nom":
            manquantes = data["nom"].eq("").sum()
        else:
            manquantes = data[col].isna().sum()
        if manquantes:
            erreurs.append(f"{col} : {manquantes} valeur(s) manquante(s) ou invalide(s).")
    if erreurs:
        return data, remarques, erreurs

    cm = data["taille"].between(3.01, 250, inclusive="both")
    if cm.any():
        data.loc[cm, "taille"] = data.loc[cm, "taille"] / 100
        remarques.append(f"Taille convertie automatiquement de cm vers m pour {cm.sum()} patient(s).")
    if (data["taille"] <= 0).any() or (data["taille"] > 3).any():
        erreurs.append("La taille doit être exprimée en mètres (ex. 1.65, ou 165 cm).")
    if (data["poids"] <= 0).any():
        erreurs.append("Le poids doit être strictement positif.")
    if (data["age"] < 0).any() or (data["age"] > 120).any():
        erreurs.append("L'âge doit être compris entre 0 et 120 ans.")
    if (data["fc"] <= 0).any():
        erreurs.append("La fréquence cardiaque doit être positive.")
    if (data["spo2"] < 0).any() or (data["spo2"] > 100).any():
        erreurs.append("La SpO₂ doit être comprise entre 0 et 100 %.")
    if (data["glycemie"] < 0).any():
        erreurs.append("La glycémie ne peut pas être négative.")
    data["sexe"] = data["sexe"].fillna("Non précisé").astype(str)
    return data, remarques, erreurs


def calculer_imc(poids: pd.Series, taille: pd.Series) -> pd.Series:
    return (poids / (taille ** 2)).round(2)


def classer_imc(imc: float) -> str:
    if imc < 18.5:
        return "Insuffisance pondérale"
    if imc < 25:
        return "Corpulence normale"
    if imc < 30:
        return "Surpoids"
    return "Obésité"


def classer_temperature(temperature: float) -> str:
    if temperature < 36:
        return "Hypothermie"
    if temperature <= 37.5:
        return "Normale"
    if temperature <= 38.5:
        return "Fièvre légère"
    if temperature <= 39.5:
        return "Fièvre modérée"
    return "Fièvre élevée"


def classer_fc(fc: float) -> str:
    if fc < 60:
        return "Bradycardie"
    if fc <= 100:
        return "Normale"
    return "Tachycardie"


def niveau_risque(score: int) -> str:
    if score == 0:
        return "Faible"
    if score <= 2:
        return "Modéré"
    if score <= 4:
        return "Élevé"
    return "Critique"


def enrichir_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Calcule les six colonnes exigées dans le mini-projet."""
    data = df.copy()
    data["imc"] = calculer_imc(data["poids"], data["taille"])
    data["statut_imc"] = data["imc"].map(classer_imc)
    data["statut_temp"] = data["temperature"].map(classer_temperature)
    data["statut_fc"] = data["fc"].map(classer_fc)
    # Seuils pédagogiques exacts du support : 1 point par facteur.
    data["score_risque"] = (
        (data["glycemie"] > 1.26).astype(int)
        + (data["imc"] >= 30).astype(int)
        + (data["fc"] > 100).astype(int)
        + (data["temperature"] > 38.0).astype(int)
        + (data["spo2"] < 95).astype(int)
        + (data["age"] > 55).astype(int)
    )
    data["niveau_risque"] = data["score_risque"].map(niveau_risque)
    return data


def creer_rapport(df: pd.DataFrame) -> str:
    lignes = [
        "MINI-PROJET SÉANCE 7 — RAPPORT D'ANALYSE DES PATIENTS",
        "=" * 56,
        f"Nombre total de patients : {len(df)}",
        "",
        "STATISTIQUES GLOBALES",
        "-" * 24,
    ]
    for col, (libelle, unite) in PARAMETRES.items():
        s = df[col]
        lignes.append(
            f"{libelle} ({unite}) : moyenne = {s.mean():.2f} | "
            f"minimum = {s.min():.2f} | maximum = {s.max():.2f}"
        )
    lignes += ["", "PATIENTS PAR NIVEAU DE RISQUE", "-" * 29]
    for niveau in NIVEAUX:
        lignes.append(f"{niveau} : {(df['niveau_risque'] == niveau).sum()}")
    lignes += ["", "PATIENTS À RISQUE ÉLEVÉ OU CRITIQUE", "-" * 38]
    risques = df[df["niveau_risque"].isin(["Élevé", "Critique"])]
    if risques.empty:
        lignes.append("Aucun patient dans ces catégories selon le score du cours.")
    else:
        for _, p in risques.iterrows():
            lignes.append(
                f"{p['nom']} | âge : {p['age']:.0f} ans | IMC : {p['imc']:.2f} | "
                f"score : {int(p['score_risque'])}/6 | {p['niveau_risque']}"
            )
    lignes += [
        "", "Note : score pédagogique de la séance 7, non validé cliniquement.",
        "Ce rapport ne constitue pas un diagnostic médical.",
    ]
    return "\n".join(lignes) + "\n"


def creer_tableau_de_bord(df: pd.DataFrame):
    """Quatre graphiques sur une seule figure, comme demandé."""
    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    fig.suptitle("Tableau de bord biomédical — Séance 7", fontsize=16, fontweight="bold")
    a, b, c, d = axes.flat

    a.hist(df["imc"], bins=min(max(len(df) // 2, 5), 14), edgecolor="white")
    for seuil in [18.5, 25, 30]:
        a.axvline(seuil, linestyle="--", linewidth=1.5, label=f"IMC {seuil}")
    a.set(title="Distribution de l'IMC", xlabel="IMC (kg/m²)", ylabel="Patients")
    a.legend(fontsize=8)

    b.hist(df["glycemie"], bins=min(max(len(df) // 2, 5), 14), edgecolor="white")
    b.axvline(1.26, linestyle="--", color="red", label="Seuil du cours : 1,26 g/L")
    b.set(title="Distribution de la glycémie", xlabel="Glycémie (g/L)", ylabel="Patients")
    b.legend(fontsize=8)

    for niveau in NIVEAUX:
        sous_groupe = df[df["niveau_risque"] == niveau]
        if not sous_groupe.empty:
            c.scatter(sous_groupe["imc"], sous_groupe["glycemie"], s=60, alpha=0.85, label=niveau)
    c.axhline(1.26, linestyle=":", color="gray")
    c.axvline(30, linestyle=":", color="gray")
    c.set(title="IMC vs glycémie, couleur = risque", xlabel="IMC (kg/m²)", ylabel="Glycémie (g/L)")
    c.legend(fontsize=8)

    comptes = df["niveau_risque"].value_counts().reindex(NIVEAUX, fill_value=0)
    d.bar(comptes.index, comptes.values)
    d.set(title="Répartition des niveaux de risque", xlabel="Niveau de risque", ylabel="Nombre de patients")
    d.tick_params(axis="x", labelrotation=12)
    d.yaxis.get_major_locator().set_params(integer=True)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    return fig


def lire_donnees():
    with st.sidebar:
        st.header("📁 Source des données")
        mode = st.radio("Choisir la source", ["Exemple fictif", "Importer mon CSV"], index=0)
        if mode == "Exemple fictif":
            st.info("Les patients de l'exemple sont fictifs, uniquement pour tester le projet.")
            try:
                return charger_csv(Path(__file__).with_name("patients_biomedical.csv"))
            except (OSError, ValueError, pd.errors.ParserError) as exc:
                st.error(f"Impossible de lire l'exemple : {exc}")
                return None
        fichier = st.file_uploader("Importer patients_biomedical.csv", type=["csv"])
        st.caption("La séance 6 a 5 colonnes : il faudra ajouter âge, SpO₂ et glycémie.")
        if fichier is None:
            return None
        try:
            return charger_csv(fichier)
        except (OSError, ValueError, UnicodeError, pd.errors.ParserError) as exc:
            st.error(f"CSV illisible : {exc}")
            return None


def saisir_et_valider(df):
    data, manquantes, erreurs = preparer_dataframe(df)
    if erreurs:
        st.error(" ".join(erreurs))
        return None
    st.subheader("1. Registre des patients")
    if manquantes:
        st.warning(
            "Colonnes absentes du fichier : " + ", ".join(manquantes) +
            ". Complète les cases vides dans le tableau avant de continuer."
        )
    st.caption("Tu peux modifier les cellules, compléter les mesures et ajouter des lignes. Taille en m (1.65), glycémie en g/L.")
    modifie = st.data_editor(data, num_rows="dynamic", hide_index=True, use_container_width=True)
    propre, remarques, erreurs = valider_et_convertir(modifie)
    for note in remarques:
        st.info(note)
    if erreurs:
        st.warning("Analyse en attente : " + " ".join(erreurs))
        return None
    return propre


def afficher_indicateurs(df):
    st.subheader("2. Statistiques générales")
    a, b, c, d = st.columns(4)
    a.metric("Patients", len(df))
    b.metric("IMC moyen", f"{df['imc'].mean():.2f}")
    c.metric("Glycémie moyenne", f"{df['glycemie'].mean():.2f} g/L")
    d.metric("Risque élevé / critique", int(df["niveau_risque"].isin(["Élevé", "Critique"]).sum()))
    with st.expander("Détail : moyenne, minimum et maximum de chaque paramètre"):
        tableau = pd.DataFrame({
            "Paramètre": [label for label, _ in PARAMETRES.values()],
            "Unité": [unite for _, unite in PARAMETRES.values()],
            "Moyenne": [round(df[col].mean(), 2) for col in PARAMETRES],
            "Minimum": [round(df[col].min(), 2) for col in PARAMETRES],
            "Maximum": [round(df[col].max(), 2) for col in PARAMETRES],
        })
        st.dataframe(tableau, hide_index=True, use_container_width=True)


def afficher_resultats(df):
    st.subheader("3. Résultats et classifications")
    st.dataframe(df, hide_index=True, use_container_width=True)
    risques = df[df["niveau_risque"].isin(["Élevé", "Critique"])]
    st.markdown("**Patients à risque élevé ou critique (selon le score du cours)**")
    if risques.empty:
        st.success("Aucun patient dans ces catégories.")
    else:
        st.dataframe(
            risques[["nom", "age", "imc", "score_risque", "niveau_risque"]],
            hide_index=True, use_container_width=True,
        )


def afficher_graphes(df) -> bytes:
    st.subheader("4. Tableau de bord — quatre graphiques")
    figure = creer_tableau_de_bord(df)
    st.pyplot(figure)
    image = BytesIO()
    figure.savefig(image, format="png", dpi=170, bbox_inches="tight")
    plt.close(figure)
    return image.getvalue()


def afficher_exports(df, image_png):
    st.subheader("5. Télécharger les livrables")
    rapport = creer_rapport(df)
    col1, col2, col3 = st.columns(3)
    col1.download_button("📄 Rapport .txt", rapport.encode("utf-8-sig"),
                         file_name="rapport_patients.txt", mime="text/plain")
    col2.download_button("🖼️ Tableau de bord .png", image_png,
                         file_name="tableau_de_bord.png", mime="image/png")
    col3.download_button("📊 Registre enrichi .csv", df.to_csv(index=False).encode("utf-8-sig"),
                         file_name="patients_biomedical_enrichi.csv", mime="text/csv")
    with st.expander("Afficher le rapport textuel"):
        st.text(rapport)


def main():
    st.set_page_config(page_title="Mini-projet biomédical — Séance 7", page_icon="🩺", layout="wide")
    st.title("🩺 Mini-projet — Analyse du registre patients")
    st.caption("Séance 7 • Python / pandas / NumPy / matplotlib • Application Streamlit")
    st.warning("Projet pédagogique. Le score du cours n'est pas un outil de diagnostic médical. Utilise uniquement des données fictives ou anonymisées.")
    source = lire_donnees()
    if source is None:
        st.info("Importe un CSV depuis la barre latérale, ou choisis l'exemple fictif.")
        return
    propre = saisir_et_valider(source)
    if propre is None:
        return
    analyse = enrichir_dataframe(propre)
    afficher_indicateurs(analyse)
    afficher_resultats(analyse)
    image_png = afficher_graphes(analyse)
    afficher_exports(analyse, image_png)


if __name__ == "__main__":
    main()
