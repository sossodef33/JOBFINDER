import datetime
import requests
from bs4 import BeautifulSoup
import unicodecsv as csv
import urllib3
import os
from requests import get
from bs4 import BeautifulSoup as soup


user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
headers    = {'user-Agent': user_agent}
#racine du site web minajobs
homePage = 'https://cameroun.minajobs.net'
fichierGeneral = 'resultatScraping_' + str(datetime.date.today())


##################################################################################################
#####################################    MINAJOBS    #############################################
##################################################################################################


#fonction qui recupere les liens des differentes categories d'offres d'emploi sur minajobs
def scraper():

    res = requests.get(homePage, headers=headers)
    print(res.status_code)
    soup = BeautifulSoup(res.content, 'html.parser')
    #print(soup.prettify())
    #dictionnaire contenant les liens vers les differentes categories d'offres d'emploi. i est la cle
    dico,i = {},1
    allCategory = (soup.find_all('div','sidebar-padding')[1]) # elle renvoie un tableau de "div",on prend le 2e element
    for link in allCategory.find_all('a'): # on boucle sur toutes les balises <a> contenues dans le div "side bar padding"
        nbjobs = link.span.text.replace('(','').replace(')','')    # on recupere directement les nombre de jobs
        dico[i] = {'link':homePage+link.get('href'),'category':link.text,'nbjobs':int(nbjobs)}  #on insere le lien vers , le nom  et le nombre de job de la categorie
        i = i+1

    return dico

companylist = []#liste d'entreprises pour controler le telechargement de leurs logos de facon a ce qu'il ne se fait qu'une seule fois

#creation d'un dossier images pour les logos recupérés
try:
    basedir = os.getcwd() + '\images'
    print(basedir)
    os.mkdir(basedir)
except FileExistsError:
        print('existant')

#fonction qui prend en parametre un element de dico (URLs d'une catagorie de job) et renvoie une liste d'offres d'emploi

def recuperateurJob(dicoLink,date):
    '''nbpages = int(dicoLink['nbjobs']/15)
    print(nbpages)'''
    end = False #variable pour tester la fin des pages
    i = 0
    jobList = [] #la liste des offres d'emploi scrapes
    fichierSauvegarge = 'minajob/%s-job-results.txt' % dicoLink['category'].replace(" / ","-") #fichier texte de jobs
    fichierTextJob1 = open(fichierSauvegarge , 'a' , encoding="utf-8")


    while not end:
        i = i+1
        url = dicoLink['link'] + '/?p=%d' % i #url d'une page dans la categorie
        #fichierTextJob1.write('\n\nPAGE %d \n\n' % i) le numero de page dans la navigation sur le site minajobs
        #print(url)
        response = requests.get(url,headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        nombreDeSpot = len(soup.find_all('li','spotlight'))


        elements = soup.find_all('div','desktop-listing-content')
        print('le nombre de jobs trouvés est:',len(elements))#le div qui contient les jobs
        j=0
        dateInferieure = False
        for element in elements:
            if not dateInferieure:
                companyName = element.find('div', 'listing-info').find_all('span', 'opaque')[0].text.replace('/',
                                                                                                             '').replace(
                    "\\", '').replace(' ', '').replace(':', '').replace('*', '')  # extraction du nom de l'entreprise
                jobLocalisation = element.find('div', 'listing-info').find_all('span', 'opaque')[
                    1].text  # extraction de la localisation de l'interface
                # pubDate = element.find('div','listing-info').find_all('span','opaque')[2].text  #extraction de la dete de publication
                companyLogo = 'https://cameroun.minajobs.net' + element.find('div', 'listing-logo').find('img').get(
                    'src')  # extraction du logo de l'entreprise

                if (companyName not in companylist):
                    print(companyName)
                    try:
                        os.mkdir(basedir + '/' + companyName)
                        path = basedir + '/' + companyName + '/logo.jpg'
                        response = requests.get(companyLogo, headers=headers)
                        with open(path, 'wb') as output:
                            output.write(response.content)
                            output.close()
                        companylist.append(companyName)
                    except FileExistsError:
                        print('entreprise existant')
                    print('Done.')

                liens = element.find_all('a')
                if (len(liens) == 3):  # si le div contient 3 lien on prend le premier
                    lien = homePage + liens[1].get('href')
                    response = requests.get(lien, headers=headers)
                    soup1 = BeautifulSoup(response.content, 'html.parser')
                    # remplacer les retours à la ligne du navigateur <br\> par les retours à la ligne des editeurs de texte '\n'
                    soup1 = str(soup1).replace('<br/>', '\n').replace('<br>', '\n')
                    soup1 = BeautifulSoup(soup1, 'html.parser')
                    info = soup1.find('div', 'job-detail-icons mbDetail').text.split(':')
                    dateScrap = info[2][0:10].split('/')
                    pubDate = datetime.date(int(dateScrap[2]), int(dateScrap[1]),
                                            int(dateScrap[0]))  # extraction de la dete de publication
                    if (pubDate <= date and nombreDeSpot > 0) or (pubDate >= date):
                        nombreDeSpot = nombreDeSpot - 1
                        title = soup1.find('h4', 'job-detail-headline').text
                        category = soup1.find('span', 'jobtype-detail').text
                        salary = soup1.find('span', 'list-salary').text
                        jobDescription = soup1.find('div', 'detail-font').text
                        job = {
                            "title": title,
                            "company": companyName,
                            "localisation": jobLocalisation,
                            "pubdate": pubDate,
                            "category": category,
                            "salary": salary,
                            "description": jobDescription,
                            "link" : lien,
                            "formation" : 'none',
                            "experience": 'none',
                            "type" : 'none',
                            "metier" : 'none',
                            "target": 'minajobs',
                            "sector": 'none'
                            #  "companylogo": companyLogo
                        }
                        print(job)
                        jobList.append(job)  # ajout du job dans la liste de job
                        fichierTextJob1.write(lien + '\n\n' + jobDescription + '\n\n')
                        # fichierTextJob1.write('\n\n')
                        # fichierTextJob1.write(lien)
                        # print(lien)
                    else:
                        dateInferieure = True
                else:
                    lien = homePage + liens[0].get('href')  # si le div ne contient pas 3 liens on prend le premier
                    response = requests.get(lien, headers=headers)
                    soup1 = BeautifulSoup(response.content, 'html.parser')
                    # remplacer les retours à la ligne du navigateur <br\> par les retours à la ligne des editeurs de texte '\n'
                    soup1 = str(soup1).replace('<br/>', '\n').replace('<br>', '\n')
                    soup1 = BeautifulSoup(soup1, 'html.parser')
                    info = soup1.find('div', 'job-detail-icons mbDetail').text.split(':')
                    dateScrap = info[2][0:10].split('/')
                    pubDate = datetime.date(int(dateScrap[2]), int(dateScrap[1]),
                                            int(dateScrap[0]))  # extraction de la dete de publication
                    if (pubDate <= date and nombreDeSpot > 0) or (pubDate >= date):
                        nombreDeSpot = nombreDeSpot - 1
                        title = soup1.find('h4', 'job-detail-headline').text
                        category = soup1.find('span', 'jobtype-detail').text
                        salary = soup1.find('span', 'list-salary').text
                        jobDescription = soup1.find('div', 'detail-font').text
                        job = {
                            "title": title,
                            "company": companyName,
                            "localisation": jobLocalisation,
                            "pubdate": pubDate,
                            "category": category,
                            "salary": salary,
                            "description": jobDescription,
                            "link": lien,
                            "formation": 'none',
                            "experience": 'none',
                            "type": 'none',
                            "metier": 'none',
                            "target": 'minajobs',
                            "sector": 'none'
                            #  "companylogo": companyLogo
                        }
                        print(job)
                        jobList.append(job)  # ajout du job dans la liste de jobs
                        fichierTextJob1.write(lien + '\n\n' + jobDescription + '\n\n')
                        # fichierTextJob1.write('\n\n')
                        # fichierTextJob1.write(lien)
                    else:
                        dateInferieure = True


                #j = j + 1
                # teste de la fin des pages
                # print(len(soup.find('div','pagination').ul.find_all('li')))
                # if(len(soup.find('div','pagination').ul.find_all('li')) == 8 and i!=1):
        if (len(soup.find('div', 'pagination').ul.select('li a.fui-arrow-right')) == 0) or dateInferieure == True:
            end = True
                # if(soup.find_all('div','pagination'))
    fichierTextJob1.close()
    return jobList


############################ EMPLOI.CM  ######################
####################################################################


def emploiScraper():
    print(
        'ENTRER UNE DATE(JOUR/MOIS/ANNEE) A PARTIR DE LAQUELLE LES OFFRES D\'EMPLOI SERONT RECUPEREES\nEXEMPLE : 16/01/2020 POUR 16 JANVIER 2020\n')
    dateLimite = input('DATE : ')
    dateLimite = dateLimite.split('/')
    dateScraping = datetime.date(int(dateLimite[2]), int(dateLimite[1]), int(dateLimite[0]))
    print('dateScraping :', dateScraping)

    # racine du site web emploi.cm
    homePage = 'https://www.emploi.cm/'
    res = requests.get(homePage, headers=headers)
    print(res.status_code)
    soup = BeautifulSoup(res.content, 'html.parser')

    # print(soup.prettify())
    # dictionnaire contenant les liens vers les differentes categories d'offres d'emploi. i est la cle

    dico, i = {}, 1
    allCategory = soup.find('ul', 'content-search-job-frontpage')
    del allCategory[len(allCategory) - 1]
    print(len(allCategory))
    for link in allCategory.find_all(
            'a'):  # on boucle sur toutes les balises <a> contenues dans le div "side bar padding"
        # nbjobs = link.span.text.replace('(','').replace(')','')    # on recupere directement le nombre de jobs
        dico[i] = {'link': homePage + link.get('href'),
                   'category': link.text}  # on insere le lien vers , le nom  et le nombre de job de la categorie
        i = i + 1
    del dico[len(dico)]
    print(dico)

    # jobs = []  # liste des jobs pour chaque categorie.
    for key in dico.keys():
        print(dico[key])
        numPage = 0
        end = False
        jobs = []  # liste des jobs pour chaque categorie.
        while not end:
            categoryUrl = dico[key]['link'] + '&page=' + str(numPage)
            pageJob = requests.get(categoryUrl, headers=headers)
            soup = BeautifulSoup(pageJob.content, 'html.parser')
            liens = soup.find_all('div', 'job-description-wrapper')
            dateInferieure = False
            for lien in liens:
                if not dateInferieure:
                    jobUrl = lien.get('data-href')
                    jobDescription = requests.get(jobUrl, headers=headers)
                    jobContent = BeautifulSoup(jobDescription.content, 'html.parser')
                    jobTitle = jobContent.find('h1', 'title').text
                    print(jobTitle)
                    dateOffre = jobContent.find('div', 'job-ad-publication-date').text.replace('Publiée le', '')
                    dateOffre = dateOffre.split('.')
                    pubDate = datetime.date(int(dateOffre[2]), int(dateOffre[1]), int(dateOffre[0]))
                    print(pubDate)
                    if pubDate >= dateScraping:
                        # companySector  = jobContent.find('div','field-name-field-entreprise-secteur')
                        jobSector = jobContent.find('div', 'field-name-field-offre-secteur').text
                        # print(companySector)
                        print(jobSector)
                        metiers = jobContent.find('div', 'field-name-field-offre-metiers').text
                        print(metiers)
                        typeContrat = jobContent.find('div', 'field-name-field-offre-contrat-type').text
                        print(typeContrat)
                        region = jobContent.find('div', 'field-name-field-offre-region').text
                        print(region)
                        niveauExperience = jobContent.find('div', 'field-name-field-offre-niveau-experience').text
                        print(niveauExperience)
                        niveauEtude = jobContent.find('div', 'field-name-field-offre-niveau-etude').text
                        print(niveauEtude)
                        description = jobContent.find('div', 'jobs-ad-details').text
                        # intro = corpus.find('ul')
                        # print(intro)
                        print(description)
                        # print(jobContent)
                        print(lien.get('data-href'))
                        jobCompany = jobContent.find('div', 'company-title').text
                        jobCategory = dico[key]['category'].replace(',', '').replace(' ', '')
                        jobSite = 'emploi.cm'
                        job = {"title": jobTitle, "company": jobCompany, "localisation": region, "pubdate": pubDate,
                               "category": jobCategory,
                               "type": typeContrat, "salary": "A negocier", "link": jobUrl, "target": jobSite,
                               "metier": metiers, "sector": jobSector, "experience": niveauExperience,
                               "formation": niveauEtude, "description": description}
                        jobs.append(job)
                    else:
                        dateInferieure = True
                        end = True
            if end == False and jobContent.find('li', 'pager-next') != 'None':
                numPage = numPage + 1
                end = False
        with open('emploicm/' + jobCategory + '.csv', 'wb') as file:
            fieldnames = ['title', 'company', 'localisation', 'pubdate', 'category', 'type', 'salary',
                          'metier', 'sector', 'experience', 'formation', 'link', 'target', 'description']
            csv_writer = csv.DictWriter(file, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
            csv_writer.writeheader()

            for job in jobs:
                csv_writer.writerow(job)

        with open(fichierGeneral + '.csv', 'ab+') as csvfile:
            fieldnames = ['title', 'company', 'localisation', 'pubdate', 'category', 'type', 'salary',
                          'metier', 'sector', 'experience', 'formation', 'link', 'target', 'description']
            csv_writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
            csv_writer.writeheader()

            for job in jobs:
                csv_writer.writerow(job)
            csvfile.close()

########################################################################
#######################        JOBINFOCAMER     ########################
########################################################################


def jobinfocamerScraper():
    print(
        'ENTRER UNE DATE(JOUR/MOIS/ANNEE) A PARTIR DE LAQUELLE LES OFFRES D\'EMPLOI SERONT RECUPEREES\nEXEMPLE : 16/01/2020 POUR 16 JANVIER 2020\n')
    dateLimite = input('DATE : ')
    dateLimite = dateLimite.split('/')
    dateScraping = datetime.date(int(dateLimite[2]), int(dateLimite[1]), int(dateLimite[0]))
    print('dateScraping :', dateScraping)

    main_url = 'https://www.jobinfocamer.com/'
    main_res = get(main_url, headers=headers)

    main_page_soup = soup(main_res.content, 'html.parser')
    menu_container = main_page_soup.find("ul", {"class": "nav navbar-nav"})

    # Recuperation des liens des categories
    menu_links = menu_container.find_all('a')

    # Scraping par categories

    for menu_link in menu_links:
        #jobCategor =
        page_id = 1
        jobs = []
        there_is_jobs = True
        menu_ref = menu_link.get('href')
        n = len(menu_ref) - 1

        print(menu_ref[6:n] + ' --->')
        jobCategory = menu_ref[6:n]
        arretScraping = False

        while there_is_jobs and not arretScraping:

            href = str(menu_link.get('href'))
            menu_url = main_url + href + '?p=' + str(page_id)
            menu_res = get(menu_url, headers=headers)
            menu_page_soup = soup(menu_res.content, 'html.parser')
            container = menu_page_soup.find_all('table',
                                                {'class': 'table table-hover table-responsive table-offre-categories'})

            print('Page id = ' + str(page_id))

            if container:
                job_links = container[0].find_all('a') + container[1].find_all('a')

                for link in job_links:

                    job_ref = str(link.get('href'))

                    if job_ref != '#':

                        description_url = main_url + job_ref
                        description_res = get(description_url, headers=headers)
                        description_page_soup = soup(description_res.content, 'html.parser')

                        description_title_container = description_page_soup.find('div', {'class': 'headline'})
                        description_headline_container = description_page_soup.find('table', {'class': 'table'})
                        description_container = description_page_soup.find('div', {'class': 'job-description'})

                        if description_headline_container and description_container and description_title_container:

                            title = description_title_container.get_text().replace(' Nouveau', '')
                            description = description_container.get_text()
                            headlines = description_headline_container.find_all('td')

                            for headline in headlines:
                                info = headline.get_text()
                                if info.startswith('Posté : '):
                                    tmp = info.replace('Posté : ', '').replace('\n', '').split('-')[::-1]
                                    pubdate = datetime.date(int(tmp[0]), int(tmp[1]), int(tmp[2]))
                                    print(pubdate)

                                elif info.startswith('Nom de l’employeur : '):
                                    company = info.replace('Nom de l’employeur : ', '').replace('\n', '')

                                elif info.startswith('Lieu : '):
                                    localisation = info.replace('Lieu : ', '').replace('\n', '')


                                elif info.startswith("Type d'emploi : "):
                                    type = info.replace("Type d'emploi : ", '').replace('\n', '')

                            if pubdate >= dateScraping :
                                # job = {"Title": title, "Company": company, "Localisation": localisation, "Pubdate": pubdate,"Type": type, "Salary": "A negocier", "Description": description}
                                job = {"title": title, "company": company, "localisation": localisation,
                                       "pubdate": pubdate,
                                       "category": jobCategory,
                                       "type": type, "salary": "A negocier", "link": job_ref, "target": 'jobinfocamer',
                                       "metier": 'none', "sector": 'none', "experience": 'none',
                                       "formation": 'none', "description": description}
                                jobs.append(job)
                            else :
                                arretScraping = True

                page_id = page_id + 1

            else:
                there_is_jobs = False

        if not jobs:
            print('No job found')

        else:
            with open('jobinfocamer/' + menu_ref[6:n] + '.csv', 'wb') as file:
                        fieldnames = ['title', 'company', 'localisation', 'pubdate', 'category', 'type','salary', 'metier', 'sector', 'experience','formation', 'link', 'target', 'description']
                        #fieldnames = ['Title', 'Company', 'Localisation', 'Pubdate', 'Type', 'Salary', 'Description']
                        csv_writer = csv.DictWriter(file, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
                        csv_writer.writeheader()

                        for job in jobs:
                            csv_writer.writerow(job)

            try:
                with open(fichierGeneral + '.csv', 'ab+')as csvfile:
                    fieldnames = ['title', 'company', 'localisation', 'pubdate', 'category', 'type',
                                  'salary',
                                  'metier', 'sector', 'experience', 'formation', 'link', 'target',
                                  'description']
                    # fieldnames = ['Title', 'Companyname', 'Joblocation', 'Pubdate', 'Category', 'Salary', 'Jobdescription',
                    # 'Lien']

                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
                    writer.writeheader()
                    for job in jobs:
                        writer.writerow(job)
                        # fichier.write(data['Jobdescription'])
                    csvfile.close()
            except FileExistsError:
                print('resultat existant')
                    # fichier.close()



if __name__=="__main__":
    continueScrap  = True
    while (continueScrap):
        print('CHOISIR LE SITE CIBLE\n\n --> 1 POUR MINAJOBS\n\n --> 2 POUR EMPLOI.CM\n\n --> 3 POUR JOBINFOCAMER\n\n --> 0 POUR TERMINER\n\n')
        cible = input('CIBLE: ')
        if (cible == '1'):
            print(
                'ENTRER UNE DATE(JOUR/MOIS/ANNEE) A PARTIR DE LAQUELLE LES OFFRES D\'EMPLOI SERONT RECUPEREES\nEXEMPLE : 16/01/2020 POUR 16 JANVIER 2020\n')
            dateLimite = input('DATE : ')
            dateLimite = dateLimite.split('/')
            dateScraping = datetime.date(int(dateLimite[2]), int(dateLimite[1]), int(dateLimite[0]))
            print('dateScraping :', dateScraping)
            dictionnary = scraper()  # recuperation des differents liens de categories
            print(dictionnary)
            for i in range(1, len(dictionnary)):
                scrapedData = recuperateurJob(dictionnary[i],dateScraping)  # recuperation de la liste de job
                filename = 'minajobs/%s-job-results.csv' % dictionnary[i]['category'].replace(" / ", "-")  # fichier csv de jobs
                print(filename)
                # fichierTextJob2 = '%s-job-results.csv' % dictionnary[14]['category'].replace(" / ","-") #fichier texte de jobs
                # fichier = open('fichierTextJob2' , 'a' , encoding="utf-8")
                try:
                    with open(filename, 'wb')as file:
                        fieldnames = ['title', 'company', 'localisation', 'pubdate', 'category', 'type', 'salary',
                                      'metier', 'sector', 'experience', 'formation', 'link', 'target', 'description']
                        # fieldnames = ['Title', 'Companyname', 'Joblocation', 'Pubdate', 'Category', 'Salary', 'Jobdescription',
                        # 'Lien']

                        writer = csv.DictWriter(file, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
                        writer.writeheader()
                        for data in scrapedData:
                            writer.writerow(data)
                            # fichier.write(data['Jobdescription'])
                except FileExistsError:
                    print('resultat existant')
                # fichier.close()

                try:
                    with open(fichierGeneral + '.csv', 'ab+')as csvfile:
                        fieldnames = ['title', 'company', 'localisation', 'pubdate', 'category', 'type', 'salary',
                                      'metier', 'sector', 'experience', 'formation', 'link', 'target', 'description']
                        # fieldnames = ['Title', 'Companyname', 'Joblocation', 'Pubdate', 'Category', 'Salary', 'Jobdescription',
                        # 'Lien']

                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
                        writer.writeheader()
                        for data in scrapedData:
                            writer.writerow(data)
                            # fichier.write(data['Jobdescription'])
                        csvfile.close()
                except FileExistsError:
                    print('resultat existant')
                # fichier.close()


        elif(cible == '2'):
            emploiScraper()
        elif(cible == '3'):
            jobinfocamerScraper()
        elif(cible == '0'):
            continueScrap = False
        else:
            continueScrap  = True