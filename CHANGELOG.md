# Changelog

Toutes les modifications notables de ce projet sont documentées dans ce
fichier. Le format s'appuie sur [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/)
et le projet respecte le [versionnage sémantique](https://semver.org/lang/fr/).

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

[1.0.0]: https://github.com/Didier57/Neasmart/releases/tag/v1.0.0
