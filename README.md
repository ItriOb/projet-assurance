# Système d'IA pour l'Évaluation des Dommages Automobiles

## À propos du projet

Ce système intelligent utilise l'intelligence artificielle pour analyser les dommages sur les véhicules accidentés. Grâce à une technologie avancée de reconnaissance visuelle, notre plateforme identifie automatiquement les composants endommagés et fournit une estimation précise des coûts de réparation.


## Capacités principales

Notre système est capable de détecter et d'évaluer les dommages sur les éléments suivants :

| Composant | Description |
|-----------|-------------|
| Capot | Partie avant supérieure du véhicule |
| Pare-chocs | Protection avant et arrière |
| Coffre | Espace de rangement arrière |
| Portières | Accès latéral au véhicule |
| Ailes | Parties entourant les roues |
| Phares | Système d'éclairage |
| Pare-brise | Vitre frontale |

## Architecture technique

### Technologies principales
- **Moteur d'IA** : YOLOv11 (You Only Look Once v8)
- **Plateforme web** : Flask (Python)
- **Stockage de données** : MySQL
- **Traitement d'images** : OpenCV & Matplotlib

### Fonctionnement du système
1. L'utilisateur télécharge une image du véhicule endommagé
2. L'algorithme YOLOv11 analyse l'image et identifie les zones de dommage
3. Le système calcule une estimation des coûts basée sur les pièces détectées
4. Les résultats sont présentés avec une visualisation des zones endommagées

## Guide d'utilisation

### Pour les utilisateurs
1. **Inscription** : Créez votre compte personnel
2. **Connexion** : Accédez à votre espace utilisateur
3. **Analyse** : Téléchargez les photos du véhicule endommagé
4. **Résultats** : Consultez l'estimation détaillée des réparations
5. **Exportation** : Téléchargez votre rapport d'analyse

### Pour les développeurs

#### Prérequis
- Python 3.11.8
- Serveur MySQL
- Dépendances Python (voir fichier requirements.txt)

#### Installation


```bash
# Cloner le dépôt
git clone https://github.com/accident-detection-system.git
cd accident-detection-system

# Installer les dépendances
pip install -r requirements.txt

# Configurer la base de données
mysql -u root -p < db_setup.sql

# Lancer l'application
python app.py
```
#### Configuration de la clé secrète
Créez un fichier .env avec les variables suivantes :
```env
YOUR_SECRET_KEY = votre_clé_secrète
```
#### Configuration de la base de données
Créez un fichier `config.py` avec le contenu suivant :

```python
# Configuration de la base de données
DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = 'votre_mot_de_passe'
DB_NAME = 'systeme_detection_dommages'
```

## Performances et précision

Notre modèle a été entraîné sur un vaste ensemble de données d'images de véhicules endommagés, lui permettant d'atteindre un taux de précision remarquable dans l'identification des composants affectés.

## Évolutions prévues

- **Application mobile** pour l'analyse sur site
- **Interface multilingue** pour une accessibilité internationale
- **Analyse de gravité** pour une évaluation plus précise des dommages
- **Intégration avec les systèmes d'assurance** pour un traitement accéléré des réclamations

## Contribution et développement

Nous accueillons favorablement les contributions à ce projet. Pour participer :

1. Consultez la liste des problèmes ouverts
2. Créez une branche pour votre contribution
3. Soumettez une demande de fusion avec une description détaillée

---

*Ce projet est développé avec le soutien de la communauté open-source dédiée à l'application de l'intelligence artificielle dans le secteur automobile.*