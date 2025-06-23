
# Azure : Présentation et Services

Azure est une offre d'hébergement (applications et données) et de services (workflow, stockage, synchronisation des données, bus de messages, contacts…).

## Infrastructure

La plateforme Azure repose sur l'infrastructure de Microsoft contenant plus de 4 millions de serveurs.

## Accès et gestion

Un ensemble d'API permet d'utiliser et d'accéder à cette plate-forme et aux services associés. Ces API sont exposées au travers d'un portail web ([https://portal.azure.com](https://portal.azure.com)) qui permet de gérer l'ensemble des services Azure. 

Pour une utilisation plus opérationnelle, il est recommandé d'utiliser **Azure (Remote) PowerShell** qui permet d'effectuer des actions plus granulaires, scriptables et pouvant être regroupées dans une boîte à outils.

## Environnement d'exécution

Un environnement d'exécution (le « Live Operating Environment ») permet une intégration étroite avec les principaux systèmes d'exploitation existants (Windows, Mac OS et Windows Phone).

## Offres Cloud : PaaS et IaaS

La plate-forme Windows Azure correspond aux offres d'informatique en nuage publiques de type **PaaS** (maintenant) et **IaaS** de Microsoft. Elle est composée des éléments suivants :

### Services principaux

- **Entra ID** (anciennement Azure Active Directory) :
  - Service d'authentification unifié, gestion des identités et des accès
  - Fonctionnalités : SSO, gestion des utilisateurs/groupes, gouvernance des identités, authentification multi-facteur
- **WebApps (PaaS)** :
  - Déploiement d'applications Web (PHP, Node.js, ASP.NET, etc.) via FTP, WebDeploy, Git, TFS
  - Prise en charge de CMS et blogs prêts à l'emploi
  - Association possible à une base de données relationnelle :
    - Windows Azure SQL Database
    - MySQL
- **Rôles applicatifs (services cloud, PaaS)** :
  - Web Role : exécution d'applications Web dans IIS
  - Worker Role : exécution de services Windows
  - VM Role : possibilité de charger une image de machine virtuelle (stateless)
- **Machines virtuelles (IaaS)** :
  - Windows Server (hébergement de SharePoint, SQL Server, Active Directory, etc.)
  - Linux (distributions partenaires)
- **Réseau virtuel (IaaS)** :
  - Configuration des plages d'adresses pour les VM et rôles
  - Connexion possible par VPN au réseau de l'entreprise
- **Compte de stockage (Windows Azure Storage)** :
  - Blobs (fichiers)
  - Tables (non relationnelles, clefs/valeurs)
  - Queues (MOM)
  - Partage de fichiers (SMB)
  - Lecteurs (drives, VHD stocké dans un blob)
  - Stockage "Premium" SSD pour VM
- **Windows Azure SQL Database** :
  - Serveur de bases de données relationnelles (PaaS)
  - Pas de gestion directe de VM

### Autres services

- **Service Bus** :
  - Connectivité vers des Web Services avec connexion sortante
  - Permet de relier Azure au SI de l'entreprise
- **Azure Active Directory** :
  - Annuaire pour la gestion des identités
  - Option de liaison avec Windows Active Directory (fédération d'identité)
- **Access Control Services (ACS)** :
  - Gestion du contrôle d'accès à Service Bus (OAuth, SWT, SAML, WS-Federation, WS-Trust)
  - Authentification via Facebook, Google, Windows Live, Yahoo!, OpenID, etc.
- **Cache distribué** :
  - Stockage d'objets sérialisables en mémoire vive
  - Utilisé pour la session ASP.NET dans une ferme Web
  - Peut être hébergé dans les VM des web/worker roles
  - Compatible memcache
- **Service Bus EAI et EDI** :
  - Portage de fonctionnalités BizTalk Server dans le cloud
- **Azure Marketplace** :
  - DataMarket : place de marché pour les données (AtomPub / OData)
  - Applications : place de marché pour applications, services, composants, formations
- **Windows Azure Mobile Services** :
  - Création de services Web et base de données cloud pour applications mobiles (Windows, iOS, Android)
  - Authentification live ID, notifications push
- **Windows Azure Media Services** :
  - Gestion de médias (vidéos, sons), transcodage, diffusion live
- **Hadoop On Azure** :
  - Distribution Hadoop sur Azure (HDFS, Map/Reduce, HIVE, PIG, Mahout, Pegasus)
  - Console interactive, pilote ODBC, add-in Excel pour HIVE