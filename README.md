# Mini-projet de synthèse — Séance 7, Génie biomédical

Application **Streamlit** correspondant au mini-projet des pages 22-23 du cours :
- lecture de `patients_biomedical.csv` dans pandas ;
- calcul des colonnes `imc`, `statut_imc`, `statut_temp`, `statut_fc`, `score_risque`, `niveau_risque` ;
- rapport textuel avec statistiques, effectifs par risque et liste des patients à risque élevé/critique ;
- une figure avec **quatre graphiques** ;
- téléchargement de `rapport_patients.txt`, `tableau_de_bord.png` et du CSV enrichi.

## Utiliser sur le site Streamlit (Community Cloud)

1. Dans GitHub, crée un dépôt, par exemple `mini-projet-biomedical`.
2. Envoie les **trois fichiers** `app.py`, `requirements.txt`, `patients_biomedical.csv` à la racine du dépôt.
3. Ouvre https://share.streamlit.io et connecte ton compte GitHub.
4. Clique **Create app** puis **Yup, I have an app**.
5. Choisis ton dépôt, la branche `main` et le fichier principal `app.py`, puis **Deploy**.
6. Teste avec l'exemple fictif, ou choisis **Importer mon CSV** dans la barre latérale.

## Tester sur un ordinateur

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

## Structure CSV

Colonnes requises : `nom, age, poids, taille, temperature, fc, spo2, glycemie`.
La colonne `sexe` est facultative. **Taille en mètres**, **glycémie en g/L**.

Si tu importes un ancien CSV de la séance 6 (`nom, poids, taille, temp, fc`),
l'application ajoute les colonnes manquantes : il faut **renseigner les mesures
réelles (ou fictives pour un test)** d'âge, SpO2 et glycémie dans le tableau
éditable. Elle ne remplit pas automatiquement des mesures médicales manquantes.

## Score pédagogique du cours (non validé cliniquement)

1 point par facteur : glycémie > 1,26 g/L, IMC >= 30,
FC > 100 bpm, température > 38 °C, SpO2 < 95 %, âge > 55 ans.
Niveaux : 0 = Faible, 1-2 = Modéré, 3-4 = Élevé, 5-6 = Critique.

Les données d'exemple sont **100 % fictives**. Ne jamais publier de données de patients identifiables dans un dépôt public. Pour un devoir, l'application permet de télécharger les exports ; les modifications du CSV dans l'interface ne sont pas stockées de façon permanente sur Streamlit Community Cloud.
