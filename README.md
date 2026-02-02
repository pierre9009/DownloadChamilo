# 📂 Chamilo Downloader (Grenoble INP)

Petit outil pour télécharger tous les documents de cours Chamilo en un clic.

## ⚙️ Prérequis (Obligatoire)

* **Google Chrome** doit être installé : [Télécharger Chrome](https://www.google.com/chrome/)


## 🚀 Option 1 : Utilisation rapide (Windows)

*Aucune installation de Python requise.*

1. Télécharge [`Downloader_Chamilo.exe`].
2. Lance le fichier (Si Windows affiche une alerte : *Informations complémentaires* -> *Exécuter quand même*).


## 🐍 Option 2 : Utilisation via Python

*Pour ceux qui sont sur Mac/Linux.*

1. Installe les bibliothèques nécessaires :
```bash
pip install -r requirements.txt

```


2. Lance le script :
```bash
python main.py

```


---

## 🛡️ Sécurité & Confidentialité

* **Zéro mot de passe stocké :** Tu te connectes toi-même dans Chrome, le script ne voit jamais tes identifiants.
* **Local :** Tes fichiers sont téléchargés directement dans ton dossier `Téléchargements`.