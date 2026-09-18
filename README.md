# Nea Smart pour Home Assistant

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/v/release/Didier57/Neasmart)](https://github.com/Didier57/Neasmart/releases)
[![License](https://img.shields.io/github/license/Didier57/Neasmart)](LICENSE)
[![Validate](https://github.com/Didier57/Neasmart/actions/workflows/validate.yml/badge.svg)](https://github.com/Didier57/Neasmart/actions/workflows/validate.yml)
[![Hassfest](https://github.com/Didier57/Neasmart/actions/workflows/hassfest.yml/badge.svg)](https://github.com/Didier57/Neasmart/actions/workflows/hassfest.yml)

Intégration Home Assistant pour la régulation de chauffage **Nea Smart Alpha 2**.
Elle s'appuie sur l'interface XML locale de la base et permet de **lire et de
modifier les paramètres de chaque zone de chauffe (HEATAREA)** directement
depuis Home Assistant.

Aucun compte, aucun cloud : tout se passe sur le réseau local.

## Sommaire

- [Fonctionnalités](#fonctionnalités)
- [Prérequis](#prérequis)
- [Installation](#installation)
- [Configuration](#configuration)
- [Entités créées](#entités-créées)
- [Services](#services)
- [Points importants](#points-importants)
- [Dépannage](#dépannage)
- [Avertissement](#avertissement)
- [Licence](#licence)

## Fonctionnalités

- Découverte automatique des zones de chauffe à partir de `static.xml`.
- Une entité par paramètre, regroupée dans un appareil par zone.
- Lecture périodique de `dynamic.xml` (intervalle réglable, 60 s par défaut).
- Écriture des consignes, modes et réglages via `changes.xml`.
- Mise à jour optimiste des entités après une écriture.
- Intervalle de scrutation et zones exposées configurables dans les options.
- Deux services génériques pour écrire n'importe quel élément XML.

## Prérequis

- Une base **Nea Smart Alpha 2** avec l'interface XML active
  (logiciel SW 01.60 / Lan 01.50 / Web 01.21 ou version ultérieure).
- La base doit être joignable depuis Home Assistant sur le réseau local
  (adresse IP ou nom d'hôte).
- Home Assistant 2024.6 ou version ultérieure.

## Installation

### Via HACS

[![Ouvrir votre instance Home Assistant et ajouter un dépôt au Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Didier57&repository=Neasmart&category=integration)

1. Dans Home Assistant, ouvrez **HACS** puis **Intégrations**.
2. Ouvrez le menu (trois points en haut à droite) puis
   **Dépôts personnalisés**.
3. Ajoutez l'URL `https://github.com/Didier57/Neasmart` avec la catégorie
   **Integration**.
4. Recherchez **Nea Smart** dans HACS et installez-le.
5. Redémarrez Home Assistant.

### Manuellement

1. Copiez le dossier `custom_components/neasmart` dans
   `<config>/custom_components/`.
2. Redémarrez Home Assistant.

`custom_components/neasmart` doit contenir `manifest.json` et les fichiers
`.py` de l'intégration.

## Configuration

1. Allez dans **Paramètres** → **Appareils et services** → **Ajouter une
   intégration**.
2. Recherchez **Nea Smart**.
3. Saisissez l'**adresse IP** (ou le nom d'hôte) de la base. Le port par
   défaut est `80`.
4. Validez : l'intégration lit `static.xml`, récupère l'identifiant de la base
   et crée automatiquement les appareils et entités.

### Options

Après l'ajout, cliquez sur **Configurer** sur la carte de l'intégration :

- **Intervalle de scrutation** : fréquence de lecture de `dynamic.xml`
  (entre 10 et 3600 secondes).
- **Zones de chauffe** : sélection des zones exposées dans Home Assistant.

Toute modification d'option recharge automatiquement l'intégration.

## Entités créées

Chaque zone de chauffe devient un appareil nommé d'après `HEATAREA_NAME`. Les
entités partagent ce nom, par exemple `sensor.cuisine_temperature_ambiante`.

### Par zone

| Entité | Plateforme | Accès | Description |
| --- | --- | --- | --- |
| Température ambiante (`T_ACTUAL`) | sensor | lecture | Température mesurée |
| Température capteur externe (`T_ACTUAL_EXT`) | sensor | lecture | Capteur externe |
| Consigne (`T_TARGET`) | number | écriture | Consigne de température |
| Consigne de base (`T_TARGET_BASE`) | sensor | lecture | Consigne calculée |
| Mode de fonctionnement (`HEATAREA_MODE`) | select | écriture | Auto / Jour / Nuit |
| État de la zone (`HEATAREA_STATE`) | binary_sensor | lecture | État courant |
| Source du programme (`PROGRAM_SOURCE`) | sensor | lecture | Programme actif |
| Programme semaine / week-end | sensor | lecture | Version de programme |
| Mode fête (`PARTY`) | binary_sensor | lecture | Fête en cours |
| Temps de fête restant | sensor | lecture | Temps restant |
| Présence (`PRESENCE`) | binary_sensor | lecture | Présence |
| Verrouillage enfants (`ISLOCKED`) | binary_sensor | lecture | Zone verrouillée |
| Code de verrouillage requis | binary_sensor | lecture | Désactivé par défaut |
| Capteur externe | binary_sensor | lecture | Désactivé par défaut |

### Pour la base

| Entité | Plateforme | Accès | Description |
| --- | --- | --- | --- |
| Refroidissement (`COOLING`) | switch | écriture | Mode rafraîchissement |
| Fonction du relais (`RELAIS/FUNCTION`) | select | écriture | Arrêt / CO Pilot |
| Mode vacances (`VACATION_STATE`) | binary_sensor | lecture | Vacances actives |
| Consigne de vacances (`T_HEAT_VACATION`) | number | écriture | Consigne hors gel |
| Date et heure (`DATETIME`) | sensor | lecture | Horloge de la base |
| Nombre d'erreurs (`ERRORCOUNT`) | sensor | lecture | Désactivé par défaut |

## Services

### `neasmart.write_zone_value`

Écrit un élément XML dans une section `HEATAREA`.

| Champ | Requis | Description |
| --- | --- | --- |
| `entry_id` | non | Entrée cible si plusieurs bases |
| `zone` | oui | Numéro de la zone (attribut `nr`) |
| `tag` | oui | Élément XML, par exemple `T_TARGET` |
| `value` | oui | Valeur à envoyer, par exemple `20.5` |

### `neasmart.write_device_value`

Écrit un élément au niveau de la base, éventuellement imbriqué.

| Champ | Requis | Description |
| --- | --- | --- |
| `entry_id` | non | Entrée cible si plusieurs bases |
| `path` | oui | Chemin, par exemple `COOLING` ou `RELAIS/FUNCTION` |
| `value` | oui | Valeur à envoyer, par exemple `1` |

## Points importants

- **Sans authentification** : l'interface XML locale n'utilise ni compte ni
  jeton. À réserver à un réseau de confiance.
- **Délai de prise en compte** : après une écriture, le régulateur de pièce
  peut mettre **jusqu'à 10 minutes** à refléter la nouvelle valeur, car il
  interroge la base par intermittence pour économiser sa batterie. Les entités
  sont mises à jour de façon optimiste en attendant.
- **Paramètres non exposés** : les codes de verrouillage (`LOCK_CODE`) et les
  codes experts ne sont volontairement pas exposés.
- **Régulateurs analogiques** (`IODEVICE_TYPE` 1 ou 3) : leurs valeurs ne
  peuvent pas être modifiées par l'interface XML.

## Dépannage

- **Impossible de joindre la base** : vérifiez l'adresse IP, que l'interface
  web est accessible et que le port est correct.
- **Document XML invalide** : vérifiez que le firmware prend en charge
  l'interface XML (SW 01.60 minimum).
- **Entités absentes** : la zone n'est peut-être pas exposée. Vérifiez
  **Configurer** → **Zones de chauffe**.
- **Valeur non appliquée** : patientez jusqu'à 10 minutes, puis vérifiez sur
  l'écran de la base.

Les journaux détaillés sont disponibles via
**Paramètres** → **Journaux**, en filtrant sur `neasmart`.

## Avertissement

Ce projet n'est ni affilié ni soutenu par Nea Smart. Utilisez-le à vos risques.
L'auteur ne saurait être tenu responsable d'un mauvais réglage de votre
installation de chauffage.

## Licence

Ce projet est distribué sous licence MIT. Voir [LICENSE](LICENSE).
