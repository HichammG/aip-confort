# Projet AIP-Confort

mettez votre description ici

## Avant de lancer le serveur

Avant tout lancement du serveur, verifiez tout dabord que votre serveur n'est pas déja lancer avant
```bash
screen -list
```
si votre serveur est déja en marche vous allez le voir avec cette commande
si il y est déja copier le PID de votre "screen" et faite `screen -r {VotrePID}`
sinon utiliser la commande suivante pour créer une nouvelle instance
```bash
screen -R pythonRunWebsite
```
ensuite faite
```bash
. ./venv/bin/activate
sudo ./venv/bin/python apiconfort.py
```
pour sortir de votre écran sans arreter votre script faite Ctrl+A -> Ctrl+D

