# Détection de faux billets

Programme de détection automatique de faux billets basé sur les caractéristiques
géométriques des billets. Interface desktop développée avec PyQt6.

---

## Contexte / besoin métier

L'ONCFM (Office national de lutte contre le faux-monnayage) a besoin d'un outil
capable d'identifier les faux billets à partir de mesures physiques (dimensions,
marges) afin d'aller plus vite dans cette lutte.

## Données

- **Source** : 1500 billets scannés
- **Variables** : diagonal, height_left, height_right, margin_low, margin_up, length
- **Qualité** : données propres, peu de valeurs manquantes
- **Limites** : échantillon limité, pas de billets d'autres devises

## Démarche

1. **Exploration** : statistiques descriptives, corrélations entre variables
2. **Test d'algorithmes** : régression logistique, KNN, Kmeans, Random Forest
4. **Évaluation** : matrice de confusion, courbe ROC, accuracy
5. **Choix de l'algorithme** : régression logistique
6. **Interface PyQt6** : input fichier avec dimensions, output fichier avec prédiction

## Résultats

- Modèle de régression logistique retenu (meilleure précision)
- Interface fonctionnelle : l'utilisateur choisit un fichier, le programme
  vérifie sa conformité et ajoute la prédiction

## Limites & pistes

- Modèle entraîné sur une seule devise (euros)
- **Pistes** : ajouter d'autres devises, intégrer des données d'image, tester
  des modèles plus avancés (XGBoost par exemple)
