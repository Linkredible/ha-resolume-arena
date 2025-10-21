# Intégration Resolume Arena pour Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

Connectez et contrôlez votre logiciel de VJing [Resolume Arena](https://resolume.com/) directement depuis Home Assistant.

Cette intégration se connecte à l'API REST de Resolume Arena pour récupérer l'état de la composition, des couches et des clips, et vous permet de déclencher des clips à distance.

## Fonctionnalités

* **Découverte automatique :** Détecte récursivement toutes les couches et tous les clips, même s'ils sont dans des groupes.
* **Boutons de Clips :** Crée une entité `button` pour chaque clip (slot) dans votre composition. Appuyer sur le bouton déclenche le clip dans Resolume.
* **Capteurs de Clip Actif :** Crée une entité `sensor` pour chaque couche, affichant le nom du clip en cours de lecture.
* **Capteurs d'État :** Crée des entités `binary_sensor` pour chaque couche pour surveiller son état `Bypass` et `Solo`.
* **Miniatures :** Affiche la miniature du clip comme icône d'entité pour les boutons (si disponible via l'API).
* **Appareil (Device) :** Regroupe toutes les entités sous un seul appareil "Resolume Arena" dans Home Assistant.

## Installation

### Méthode 1 : HACS (Recommandé)

Cette intégration n'est pas (encore) dans le dépôt HACS par défaut. Vous devez l'ajouter en tant que **dépôt personnalisé**.

1.  Allez dans `HACS` > `Intégrations`.
2.  Cliquez sur le menu à trois points en haut à droite et sélectionnez `Dépôts personnalisés`.
3.  Dans le champ `Dépôt`, collez l'URL de ce dépôt GitHub.
4.  Dans le champ `Catégorie`, sélectionnez `Intégration`.
5.  Cliquez sur `Ajouter`.
6.  L'intégration "Resolume Arena" devrait apparaître. Cliquez sur `Installer`.
7.  Redémarrez Home Assistant.

### Méthode 2 : Manuelle

1.  Téléchargez la dernière "Release" depuis la page GitHub.
2.  Décompressez l'archive.
3.  Copiez le dossier `custom_components/resolume_arena` dans le dossier `config/custom_components` de votre installation Home Assistant.
4.  Redémarrez Home Assistant.

## Configuration

L'installation se fait entièrement via l'interface utilisateur de Home Assistant.

1.  Allez dans `Paramètres` > `Appareils et services`.
2.  Cliquez sur `Ajouter une intégration` (en bas à droite).
3.  Recherchez et sélectionnez `Resolume Arena`.
4.  Une boîte de dialogue s'ouvrira :
    * **Hôte** : L'adresse IP de la machine exécutant Resolume Arena.
    * **Port** : Le port de l'API Resolume (par défaut : `8080`).
5.  Cliquez sur `Valider`. L'intégration tentera de se connecter à l'API.
6.  Si la connexion réussit, l'intégration sera ajoutée et commencera à créer vos entités.

## Utilisation des Entités

Une fois configurée, l'intégration crée les entités suivantes :

### Boutons (`button`)

* **`button.clip_NOM_COUCHE_cCOLONNE_NOM_CLIP`**
    * **Action :** Appuyer sur ce bouton déclenche (connecte) le clip correspondant dans Resolume.
    * **Icône :** L'icône `mdi:play-box` est pleine si le clip est actif, et `mdi:play-box-outline` s'il est inactif.
    * **Attributs :** Contient des informations utiles comme `layer_name`, `clip_name`, `column_index`, `clip_id`, et `is_active`.

### Capteurs (`sensor`)

* **`sensor.resolume_NOM_COUCHE_clip_actif`**
    * **État :** Le nom du clip actuellement en lecture sur cette couche (ex: "Clip 1", "Vide", "MonClip.mov").
    * **Attributs :** `layer_name`, `layer_id`, `active_clip_id`.

### Capteurs Binaires (`binary_sensor`)

* **`binary_sensor.resolume_NOM_COUCHE_bypass`**
    * **État :** `On` si la couche est en mode "Bypass" (désactivée). `Off` sinon.
* **`binary_sensor.resolume_NOM_COUCHE_solo`**
    * **État :** `On` si la couche est en mode "Solo". `Off` sinon.

## Remarques importantes

* **Intervalle de mise à jour :** L'intégration interroge Resolume toutes les 2 secondes pour mettre à jour l'état des clips actifs, du solo et du bypass.
* **Ajout de nouvelles couches/clips :** Si vous ajoutez de nouvelles couches ou de nouveaux clips à votre composition Resolume *après* avoir configuré l'intégration, vous devez **recharger l'intégration** pour que les nouvelles entités (boutons, capteurs) soient créées.
    * Pour ce faire, allez dans `Paramètres` > `Appareils et services`, trouvez l'intégration Resolume, cliquez sur les trois points et sélectionnez `Recharger`.