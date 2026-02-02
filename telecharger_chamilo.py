import os
import re
import time
import requests
import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from tqdm import tqdm
from urllib.parse import urljoin
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException

class ChamiloDownloader:
    def __init__(self):
        self.base_url = "https://chamilo.grenoble-inp.fr"
        self.session = requests.Session()
        self.courses = []
        self.download_dir = os.path.join(os.path.expanduser("~"), "Downloads", "Cours-Chamilo")
        self.visited_folders = set()
        
        # Configuration du navigateur
        options = Options()
        options.add_argument("--window-size=1920,1080")
        # On peut ajouter cette option pour éviter des logs inutiles dans la console
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        print("Vérification de l'environnement...")
        try:
            # Initialisation du navigateur
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()), 
                options=options
            )
        except Exception as e:
            print("\n" + "!"*50)
            print("ERREUR : Google Chrome n'a pas été détecté.")
            print("Ce script nécessite que Google Chrome soit installé sur votre PC.")
            print("Lien : https://www.google.com/chrome/")
            print("!"*50 + "\n")
            # On attend un peu que l'utilisateur puisse lire avant de fermer
            input("Appuyez sur ENTRÉE pour quitter...")
            sys.exit(1)
    
    def login_manually(self):
        """Permettre à l'utilisateur de se connecter manuellement"""
        print("Ouverture de la page de connexion...")
        self.driver.get(f"{self.base_url}/index.php")
        
        print("\n=== CONNEXION MANUELLE ===")
        print("1. Veuillez vous connecter manuellement dans la fenêtre du navigateur.")
        print("2. Une fois connecté, accédez à la page 'Mes Cours'.")
        print("3. Appuyez sur ENTRÉE dans ce terminal quand vous êtes prêt à continuer.")
        input("\nAppuyez sur ENTRÉE pour continuer...")
        
        # Vérifier si l'utilisateur est connecté
        if "user_portal.php" in self.driver.current_url or "my_courses" in self.driver.current_url:
            print("Connexion détectée avec succès!")
            
            # Récupérer les cookies de session
            cookies = self.driver.get_cookies()
            for cookie in cookies:
                self.session.cookies.set(cookie['name'], cookie['value'])
            
            return True
        else:
            print("Vous ne semblez pas être sur la page 'Mes Cours'. Assurez-vous d'être connecté.")
            return False
    
    def get_courses(self):
        """Récupérer la liste des cours disponibles"""
        print("Récupération de la liste des cours...")
        
        # S'assurer que nous sommes sur la page des cours
        if "user_portal.php" not in self.driver.current_url:
            self.driver.get(f"{self.base_url}/user_portal.php")
        
        try:
            # Attendre que la page soit chargée
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".panel-body"))
            )
            
            # Sauvegarder la page pour pouvoir l'analyser
            html_content = self.driver.page_source
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Trouver tous les panneaux de cours
            course_panels = soup.select('.panel-body')
            
            course_id = 1
            for panel in course_panels:
                # Chercher le titre du cours et le lien
                title_elem = panel.select_one('.course-items-title a')
                if title_elem:
                    course_url = title_elem.get('href')
                    course_title = title_elem.get_text().strip()
                    
                    # Extraire le code du cours de l'URL
                    course_code_match = re.search(r'courses/([^/]+)/index\.php', course_url)
                    if course_code_match:
                        course_code = course_code_match.group(1)
                        self.courses.append({
                            'id': course_id,
                            'title': course_title,
                            'code': course_code,
                            'url': course_url
                        })
                        course_id += 1
            
            print(f"Récupération de {len(self.courses)} cours terminée!")
            
        except Exception as e:
            print(f"Erreur lors de la récupération des cours: {e}")
    
    def display_courses(self):
        """Afficher la liste des cours disponibles"""
        if not self.courses:
            print("Aucun cours disponible.")
            return
            
        print("\nListe des cours disponibles:")
        print("----------------------------")
        for course in self.courses:
            print(f"{course['id']}. {course['title']} [{course['code']}]")
    
    def select_courses(self):
        """Permettre à l'utilisateur de sélectionner les cours à télécharger"""
        self.display_courses()
        
        if not self.courses:
            print("Aucun cours à sélectionner.")
            return []
            
        while True:
            print("\nOptions de sélection:")
            print("1. Sélectionner tous les cours")
            print("2. Sélectionner des cours spécifiques")
            print("3. Sélectionner tous les cours SAUF certains")
            choice = input("Votre choix (1-3): ")
            
            if choice == "1":
                return self.courses
            elif choice == "2":
                selection = input("Entrez les numéros des cours séparés par des virgules (ex: 1,3,5): ")
                try:
                    selected_ids = [int(id.strip()) for id in selection.split(",")]
                    selected_courses = [course for course in self.courses if course['id'] in selected_ids]
                    
                    if not selected_courses:
                        print("Aucun cours valide sélectionné.")
                        continue
                    
                    return selected_courses
                except ValueError:
                    print("Format invalide. Veuillez réessayer.")
            elif choice == "3":
                exclusion = input("Entrez les numéros des cours à EXCLURE séparés par des virgules (ex: 2,4,6): ")
                try:
                    excluded_ids = [int(id.strip()) for id in exclusion.split(",")]
                    selected_courses = [course for course in self.courses if course['id'] not in excluded_ids]
                    
                    if not selected_courses:
                        print("Tous les cours ont été exclus. Veuillez réessayer.")
                        continue
                    
                    print(f"Sélection de {len(selected_courses)} cours (exclusion de {len(excluded_ids)} cours).")
                    return selected_courses
                except ValueError:
                    print("Format invalide. Veuillez réessayer.")
            else:
                print("Choix invalide. Veuillez réessayer.")
    
    def clean_filename(self, filename):
        """Nettoyer un nom de fichier/dossier des caractères problématiques"""
        return re.sub(r'[\\/*?:"<>|]', "_", filename)

    def download_file(self, url, target_path):
        """Télécharger un fichier à partir de son URL"""
        try:
            # Récupérer le document avec la session établie
            response = self.session.get(url, stream=True)
            
            if response.status_code != 200:
                print(f"Erreur lors du téléchargement vers {target_path} (code {response.status_code})")
                return False
            
            # Extraire le nom de fichier depuis Content-Disposition s'il existe
            content_disp = response.headers.get('Content-Disposition')
            if content_disp and 'filename=' in content_disp:
                filename_match = re.search(r'filename="(.+?)"', content_disp)
                if filename_match:
                    original_filename = filename_match.group(1)
                    # Mettre à jour le nom du fichier cible si nécessaire
                    target_path = os.path.join(os.path.dirname(target_path), self.clean_filename(original_filename))
            
            # Vérifier si le fichier existe déjà avec la même taille
            total_size = int(response.headers.get('content-length', 0))
            if os.path.exists(target_path) and os.path.getsize(target_path) == total_size and total_size > 0:
                print(f"Fichier déjà téléchargé (même taille): {os.path.basename(target_path)}")
                return True
            
            # Créer le dossier parent si nécessaire
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            
            # Télécharger le fichier avec une barre de progression
            block_size = 1024  # 1 Kibibyte
            
            with open(target_path, 'wb') as file:
                if total_size > 0:  # Seulement afficher la barre si la taille est connue
                    with tqdm(total=total_size, unit='iB', unit_scale=True, desc=os.path.basename(target_path)) as progress_bar:
                        for data in response.iter_content(block_size):
                            progress_bar.update(len(data))
                            file.write(data)
                else:
                    # Si la taille n'est pas connue, télécharger sans barre de progression
                    for data in response.iter_content(block_size):
                        file.write(data)
            
            return True
            
        except Exception as e:
            print(f"Erreur lors du téléchargement vers {target_path}: {e}")
            return False

    def explore_folder(self, course_code, folder_url, current_path, base_path):
        """Explorer un dossier et ses sous-dossiers pour télécharger les fichiers"""
        # Éviter les boucles infinies
        folder_key = f"{course_code}_{folder_url}"
        if folder_key in self.visited_folders:
            return
        
        self.visited_folders.add(folder_key)
        
        print(f"Exploration du dossier: {current_path or 'Racine'}")
        
        try:
            # Naviguer vers la page du dossier
            self.driver.get(folder_url)
            
            # Attendre que la table des fichiers/dossiers soit chargée
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table.data_table"))
            )
            
            # Analyser le contenu de la page
            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            
            # Trouver la table des fichiers/dossiers
            table = soup.select_one("table.data_table")
            if not table:
                print(f"Pas de table trouvée dans le dossier {current_path}")
                return
            
            # Parcourir les lignes du tableau (ignorer l'en-tête)
            rows = table.select("tr")[1:]  # Ignorer l'en-tête
            
            for row in rows:
                cells = row.select("td")
                if len(cells) < 2:
                    continue
                
                icon_cell = cells[0]
                name_cell = cells[1]
                
                # Trouver les liens dans la cellule nom
                links = name_cell.select("a")
                if not links:
                    continue
                
                # Le premier lien est généralement le lien vers le dossier/fichier
                main_link = links[0]
                item_name = main_link.text.strip()
                item_url = main_link.get("href")
                
                # Vérifier si c'est un dossier à partir de l'icône
                is_folder = "folder_document.gif" in str(icon_cell)
                
                if is_folder:
                    # C'est un dossier - créer le dossier localement
                    folder_name = self.clean_filename(item_name)
                    new_path = os.path.join(current_path, folder_name)
                    folder_full_path = os.path.join(base_path, new_path)
                    
                    # Créer le dossier
                    os.makedirs(folder_full_path, exist_ok=True)
                    
                    # Explorer ce dossier récursivement
                    if item_url and not item_url.startswith("javascript"):
                        full_url = urljoin(self.base_url, item_url)
                        self.explore_folder(course_code, full_url, new_path, base_path)
                    
                else:
                    # C'est un fichier - chercher le lien de téléchargement (dans les autres liens)
                    download_link = None
                    for link in links:
                        href = link.get("href", "")
                        # Chercher spécifiquement les liens de téléchargement
                        if "action=download" in href or "download=1" in href:
                            download_link = link
                            break
                    
                    if download_link:
                        # Construire l'URL complète du téléchargement
                        download_url = urljoin(self.base_url, download_link.get("href"))
                        
                        # Construire le chemin de destination
                        file_name = self.clean_filename(item_name)
                        file_path = os.path.join(base_path, current_path, file_name)
                        
                        # Télécharger le fichier
                        success = self.download_file(download_url, file_path)
                        if success:
                            relative_path = os.path.relpath(file_path, base_path)
                            print(f"Fichier téléchargé: {relative_path}")
                        
                        # Pause pour éviter de surcharger le serveur
                        time.sleep(0.2)
                    
                    else:
                        # Si pas de lien de téléchargement direct, extraire l'ID du fichier et construire l'URL
                        file_id_match = re.search(r'[?&]id=(\d+)', item_url)
                        if file_id_match:
                            file_id = file_id_match.group(1)
                            download_url = f"{self.base_url}/main/document/document.php?cidReq={course_code}&id_session=0&gidReq=0&gradebook=0&origin=&action=download&id={file_id}"
                            
                            # Construire le chemin de destination
                            file_name = self.clean_filename(item_name)
                            file_path = os.path.join(base_path, current_path, file_name)
                            
                            # Télécharger le fichier
                            success = self.download_file(download_url, file_path)
                            if success:
                                relative_path = os.path.relpath(file_path, base_path)
                                print(f"Fichier téléchargé (méthode ID): {relative_path}")
                            
                            # Pause pour éviter de surcharger le serveur
                            time.sleep(0.2)
                        else:
                            print(f"Impossible de trouver un lien de téléchargement pour: {item_name}")
        
        except Exception as e:
            print(f"Erreur lors de l'exploration du dossier {current_path}: {e}")
            import traceback
            traceback.print_exc()
    
    def download_course_documents(self, course):
        """Télécharger tous les documents d'un cours"""
        print(f"\n=== Téléchargement des documents pour: {course['title']} ===")
        
        # Créer le dossier du cours
        course_folder = os.path.join(self.download_dir, self.clean_filename(course['title']))
        os.makedirs(course_folder, exist_ok=True)
        
        # URL de la page de documents du cours
        document_url = f"{self.base_url}/main/document/document.php?cidReq={course['code']}&id_session=0&gidReq=0"
        
        # Réinitialiser les dossiers visités
        self.visited_folders = set()
        
        # Explorer le dossier racine et tous les sous-dossiers
        self.explore_folder(course['code'], document_url, "", course_folder)
        
        print(f"Téléchargement terminé pour {course['title']}!")
    
    def close(self):
        """Fermer le navigateur"""
        self.driver.quit()
        print("Session terminée.")

def main():
    downloader = ChamiloDownloader()
    
    print("=== Robot de téléchargement pour Chamilo Grenoble INP ===")
    
    try:
        # Connexion manuelle
        if not downloader.login_manually():
            print("Connexion échouée. Fin du programme.")
            downloader.close()
            return
        
        # Récupérer la liste des cours
        downloader.get_courses()
        
        # Sélectionner les cours à télécharger
        selected_courses = downloader.select_courses()
        
        if not selected_courses:
            print("Aucun cours sélectionné. Fin du programme.")
            downloader.close()
            return
        
        # Télécharger les documents pour chaque cours sélectionné
        for course in selected_courses:
            downloader.download_course_documents(course)
        
        # Fermer le navigateur
        downloader.close()
        
        print("\nTéléchargement terminé! Vos documents sont disponibles dans:", downloader.download_dir)
        
    except KeyboardInterrupt:
        print("\nOpération interrompue par l'utilisateur.")
        downloader.close()
    except Exception as e:
        print(f"\nUne erreur est survenue: {e}")
        import traceback
        traceback.print_exc()
        downloader.close()

if __name__ == "__main__":
    main()