# Cinq erreurs qui rendent un backtest artificiellement rentable

Une courbe de capital reguliere ne prouve pas qu'une strategie etait
realisable. Avant d'interpreter un rendement, il faut verifier que les donnees,
la chronologie et les hypotheses d'execution respectent ce qui etait reellement
connaissable et tradable au moment de chaque decision.

Voici cinq erreurs frequentes et les preuves minimales qui permettent de les
detecter.

## 1. Une information future entre dans la decision

Le cas le plus direct est une feature calculee avec une cloture qui n'existait
pas encore lorsque l'ordre aurait ete decide. Le decalage peut etre minuscule :
une barre, une revision de donnee ou un alignement de fuseau horaire incorrect.
Il suffit pourtant a transformer une prediction en lecture du futur.

**Preuve attendue :** pour chaque signal, conserver le timestamp de decision,
le debut et la fin de la fenetre de calcul. La fin de la fenetre ne doit jamais
depasser le timestamp de decision.

## 2. Le backtest ne conserve que les survivants

Tester aujourd'hui les instruments encore cotes retire silencieusement ceux
qui ont disparu, fusionne ou ete liquides. Le resultat mesure alors un univers
selectionne par son succes futur.

**Preuve attendue :** reconstruire l'univers point-in-time et associer chaque
observation a une vie d'instrument explicite, avec date de debut et date de fin.
Un meme ticker reutilise plus tard doit rester separe par un identifiant de vie.

## 3. Des lignes existent apres la fin officielle de l'instrument

Certaines archives conservent des lignes plates, nulles ou synthetiques apres
la cessation d'un contrat. Un pipeline peut les accepter comme des prix
tradables, prolonger artificiellement une position ou fabriquer une sortie qui
n'aurait jamais pu etre executee.

**Preuve attendue :** comparer chaque ligne aux bornes officielles de la vie de
l'instrument. Toute ligne posterieure a la cessation doit etre expliquee,
exclue ou classee comme anomalie, jamais absorbee silencieusement.

## 4. Le prix simule n'etait pas executable

Utiliser la cloture de la barre comme prix d'entree suppose souvent une
execution instantanee, sans spread, sans glissement et avec une liquidite
illimitee. Une petite erreur par trade peut suffire a renverser un avantage
faible lorsque la strategie tourne souvent.

**Preuve attendue :** documenter l'heure de decision, l'heure d'execution, le
cote du carnet utilise, les frais, le spread, le slippage et la regle appliquee
quand le volume disponible est insuffisant. Une hypothese non verifiee doit
rester marquee `NON VERIFIE`.

## 5. Le resultat n'est pas reproductible

Un notebook qui depend d'un fichier modifiable, d'un ordre implicite ou d'un
parametre non consigne peut produire une autre reponse le lendemain. Sans
empreinte des entrees et sans commande canonique, il est impossible de savoir
si deux executions ont reellement teste la meme chose.

**Preuve attendue :** geler les parametres, enregistrer les versions, calculer
les empreintes des fichiers d'entree et conserver une commande de reproduction.
Le meme paquet doit produire le meme verdict sur une installation propre.

## Ce qu'un audit peut conclure

Un audit d'integrite peut conclure que la chronologie, le cycle de vie des
instruments, les fichiers et certaines hypotheses d'execution sont coherents.
Il peut aussi produire un verdict `FAIL` ou `NON VERIFIE` avec des preuves
localisables.

Il ne peut pas certifier un edge, une rentabilite future ou l'adequation d'une
strategie au trading reel. Son role est plus modeste et plus utile : empecher
une simulation techniquement fausse d'etre prise pour une preuve economique.

Le demonstrateur associe a cet article utilise uniquement des donnees
synthetiques. Il accepte un cas propre et rejette deux contaminations deliberees
sans connexion a un exchange, cle API ou donnee de client.
