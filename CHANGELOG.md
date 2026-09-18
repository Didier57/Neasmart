# Changelog

Toutes les modifications notables de ce projet sont documentées dans ce
fichier. Le format s'appuie sur [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/)
et le projet respecte le [versionnage sémantique](https://semver.org/lang/fr/).

## [1.0.2] - 2026-09-18

### Modifié

- Capteur **Date et heure** (`DATETIME`) : il est désormais affiché sous forme de
  date et d'heure absolues, par exemple `2026-09-18 08:21:21`, au lieu d'un
  temps relatif qui donnait l'impression d'un compteur de secondes.

## [1.0.1] - 2026-09-18

### Corrigé

- Capteur **Date et heure** (`DATETIME`) : la valeur est désormais renvoyée avec
  un fuseau horaire, condition requise par Home Assistant pour un capteur de
  type horodatage. Le capteur remontait auparavant sans valeur.
- Interrupteur **Refroidissement** (`COOLING`) : il n'est plus proposé que si la
  fonction **CO Pilot** est active sur le relais, car la base rejette la commande
  dans le cas contraire (erreur sur l'interface web).

## [1.0.0] - 2026-09-18

### Ajouté

- Configuration via l'adresse IP ou le nom d'hôte de la base.
- Découverte automatique des zones de chauffe à partir de `static.xml`.
- Entités par zone : température ambiante, capteur externe, consigne, consigne
  de base, mode de fonctionnement, état, programme, fête, présence,
  verrouillage.
- Entités de base : refroidissement (COOLING), fonction du relais (CO PILOT),
  mode vacances, consigne de vacances, date et heure, nombre d'erreurs.
- Services `write_zone_value` et `write_device_value`.
- Options : intervalle de scrutation et zones exposées.
- Traductions française et anglaise.

[1.0.2]: https://github.com/Didier57/Neasmart/releases/tag/v1.0.2
[1.0.1]: https://github.com/Didier57/Neasmart/releases/tag/v1.0.1
[1.0.0]: https://github.com/Didier57/Neasmart/releases/tag/v1.0.0
