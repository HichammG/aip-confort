import json
import re
import time
from datetime import datetime
from datetime import timedelta

import jwt  # pip install pyjwt
import pymongo
from flask import Flask, jsonify, request
from flask_bcrypt import Bcrypt
from flask_cors import CORS, cross_origin
from flask_restful import Api
from fuzzy_logic.mamdani_fs import MamdaniFuzzySystem
from fuzzy_logic.mf import TrapezoidMF
from fuzzy_logic.mf import TriangularMF
from fuzzy_logic.terms import Term
from fuzzy_logic.variables import FuzzyVariable

app = Flask(__name__)
api = Api(app)
CORS(app, resources={r"*": {"origins": "*"}})
bcrypt = Bcrypt(app)
secret = "***************"

mongo = pymongo.MongoClient("mongodb://aip-confort.milebits.com:3002/")
db = mongo['BaseConfort']  # py_api is the name of the db


@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.access_control_allow_origin = '*'
    return response


def MADM(Temperature, Acoustique, Luminosite, CO2, Humidite):
    # Température
    t1 = Term('TemperatureTropFraiche', TrapezoidMF(0, 0, 17 / 50, 17 / 50))
    t2 = Term('TemperatureOptimale', TrapezoidMF(0 / 50, 21 / 50, 21 / 50, 40 / 50))
    t3 = Term('TemperatureTropChaude', TrapezoidMF(26 / 50, 26 / 50, 50 / 50, 50 / 50))

    # Acoustique
    A1 = Term('BruitOptimal', TrapezoidMF(0, 0, 38 / 150, 90 / 150))
    A2 = Term('TropBruyant', TrapezoidMF(70 / 150, 150 / 150, 150 / 150, 150 / 150))

    # Luminosité
    L1 = Term('TropPeuLumineux', TrapezoidMF(0, 0, 250 / 1000, 500 / 1000))
    L2 = Term('LuminositeOptimale', TrapezoidMF(0 / 1000, 300 / 1000, 700 / 1000, 1000 / 1000))
    L3 = Term('TropLumineux', TrapezoidMF(500 / 1000, 750 / 1000, 1000 / 1000, 1000 / 1000))

    # C02
    C1 = Term('CO2Optimal', TrapezoidMF(0, 0, 1000 / 2000, 2000 / 2000))
    C2 = Term('TropDeCO2', TriangularMF(1350 / 2000, 2000 / 2000, 2000 / 2000))

    # Humidité
    H1 = Term('PasAssezHumide', TriangularMF(0, 0, 20 / 100))
    H2 = Term('HumiditeOptimale', TrapezoidMF(0, 30 / 100, 60 / 100, 100 / 100))
    H3 = Term('TropHumide', TriangularMF(70 / 100, 100 / 100, 100 / 100))

    input1: FuzzyVariable = FuzzyVariable('input1', 0, 1, t1, t2, t3)
    input2: FuzzyVariable = FuzzyVariable('input2', 0, 1, A1, A2)
    input3: FuzzyVariable = FuzzyVariable('input3', 0, 1, L1, L2, L3)
    input4: FuzzyVariable = FuzzyVariable('input4', 0, 1, C1, C2)
    input5: FuzzyVariable = FuzzyVariable('input5', 0, 1, H1, H2, H3)

    output = FuzzyVariable(
        'output', 0, 50,
        Term('Inconfortable', TriangularMF(0, 0, 1)),
        Term('Confortable', TriangularMF(49, 50, 50))
    )

    mf: MamdaniFuzzySystem = MamdaniFuzzySystem([input1, input2, input3, input4, input5], [output])
    mf.rules.append(mf.parse_rule(
        'if (input1 is TemperatureOptimale) and (input2 is BruitOptimal) and (input3 is LuminositeOptimale) and (input4 is CO2Optimal) and (input5 is HumiditeOptimale) then (output is Confortable)'))
    mf.rules.append(mf.parse_rule(
        'if (input1 is not TemperatureOptimale) or (input2 is not BruitOptimal) or (input3 is not LuminositeOptimale) or (input4 is not CO2Optimal) or (input5 is not HumiditeOptimale)then (output is Inconfortable)'))
    result = mf.calculate({input1: Temperature, input2: Acoustique, input3: Luminosite, input4: CO2, input5: Humidite})

    s = str(re.findall(": .*", str(result))).replace("[': ", "").replace("}']", "")
    # print("Score : "+s)

    #    if float(s) >= 40.00:
    #       print("Très Confortable")

    #    if float(s) >= 30.00 and float(s) < 40.00:
    #        print("Confortable")

    #    if float(s) >= 20.00 and float(s) < 30.00:
    #        print("Pas incroyable")

    #    if float(s) >= 10.00 and float(s) < 20.00:
    #        print("Peu vivable")

    #    if float(s) > 0.00 and float(s) < 10.00:
    #        print("Fuir")

    r = 1 - abs((float(s) - 49.5) / 49.5)
    # print("Note : "+ str(round(r*10,2)))
    return (round(r * 10, 2))


@app.route('/')
@cross_origin('*')
def func():
    return "Bienvenue sur l'API du projet AIPConfort 😺", 200


# get 'salle'' last value
@app.route('/salle', methods=['GET'])
@cross_origin('*')
def indexsalle():
    res = []
    token = request.args.get('token')
    salle = request.args.get('salle')
    code = 500
    status = "fail"
    message = ""
    try:
        for row in db.users.find_one({'token': token}, {'_id': 0}):
            User = row;
    except:
        User = None
    if User != None:
        try:
            for r in db[salle].find({}, {'_id': 0}).sort('Time', -1).limit(10):
                res.append(r)
            if res:
                message = "salle retrieved"
                status = 'successful'
                code = 200
            else:
                message = "no value found"
                status = 'successful'
                code = 204
        except Exception as ee:
            res = {"error": str(ee)}
    else:
        if token != None:
            message = "wrong token"
            status = 'fail'
            code = 401
        else:
            message = "any token"
            status = 'fail'
            code = 401
    return jsonify({"status": status, 'data': res, "message": message}), code


@app.route('/sallelast', methods=['GET'])
@cross_origin('*')
def indexsallelast():
    res = []
    token = request.args.get('token')
    salle = request.args.get('salle')
    code = 500
    status = "fail"
    message = ""
    try:
        for row in db.users.find_one({'token': token}, {'_id': 0}):
            User = row;
    except:
        User = None
    if User != None:
        try:
            for r in db[salle].find({}, {'_id': 0}).sort('Time', -1).limit(1):
                res.append(r)
            if res:
                message = "salle retrieved"
                status = 'successful'
                code = 200
            else:
                message = "no value found"
                status = 'successful'
                code = 204
        except Exception as ee:
            res = {"error": str(ee)}
    else:
        if token != None:
            message = "wrong token"
            status = 'fail'
            code = 401
        else:
            message = "any token"
            status = 'fail'
            code = 401
    return jsonify({"status": status, 'data': res, "message": message}), code


@app.route('/MADM', methods=['POST'])
@cross_origin('*')
def indexMADM():
    res = []
    sortRes = []
    token = request.args.get('token')
    salle = []
    nbRaspSalle = []
    ip = []
    code = 500
    status = "fail"
    message = ""
    tooSoon = False

    for r in db['MADM'].find():
        lastMADM = r['Time']

    data = request.get_json()
    # Fix issue : data is empty with CORS in browser
    if data is None:
        data = request.form.to_dict()
    if isinstance(data, str):  # check if data is str
        data = json.loads(data)  # convert data to dict
    if time.time() - 60 < lastMADM:
        tooSoon = True

    demandeTemperature = bool(data['demandeTemperature'])
    demandeAcoustique = bool(data['demandeAcoustique'])
    demandeLuminosite = bool(data['demandeLuminosite'])
    demandeCO2 = bool(data['demandeCO2'])
    demandeHumidite = bool(data['demandeHumidite'])

    if demandeTemperature == True and demandeAcoustique == True and demandeLuminosite == True and demandeCO2 == True and demandeHumidite == True and tooSoon == True:

        for r in db['MADM'].find():
            res = r['data']
        return jsonify({"status": status, 'Resultat': res, "message": message}), 200


    else:
        dataCapteurs = db['Capteurs'].find()
        for rows in dataCapteurs:
            rep = re.findall('S\d\d\d', str(rows))
            if rep[0] not in salle and rep != []:
                salle.append(str(rep[0]))
            rep = re.findall(r'\d+_\d+_\d+_\d+', str(rows))
            if rep != []:
                if rep[0] not in ip:
                    ip.append(str(rep[0]))

        for r in range(int(len(salle))):
            nbRaspSalle.append(0)

        for i in range(int(len(ip))):
            data_2 = db['Capteurs'].find()
            for rows in data_2:
                if ip[i] in str(rows):
                    dummy = re.findall('S\d\d\d', str(rows))
                    for j in range(int(len(nbRaspSalle))):
                        if dummy[0] == salle[j]:
                            nbRaspSalle[j] = nbRaspSalle[j] + 1

        User = db.users.find_one({'token': token}, {'_id': 0});
        if User != None:
            try:
                for i in range(int(len(salle))):
                    FraicheurValeurs = "Aucune valeur pour cette salle MADM impossible"
                    dataCapteurs = db['Capteurs'].find()
                    EtatCapteurs = []

                    for rows in dataCapteurs:
                        test = "'" + salle[i] + "': ["
                        if test in str(rows):
                            StatutTemperature = rows[salle[i]][0]['Temperature']
                            StatutAcoustique = rows[salle[i]][0]['Son']
                            StatutLuminosite = rows[salle[i]][0]['Luminosite']
                            StatutCO2 = rows[salle[i]][0]['CO2']
                            StatutHumidite = rows[salle[i]][0]['Humidite']

                    Temperature = None
                    Acoustique = None
                    Luminosite = None
                    Humidite = None
                    CO2 = None
                    AnyData = False

                    ValeursTemperature_SansNone = []
                    ValeursAcoustique_SansNone = []
                    ValeursLuminosite_SansNone = []
                    ValeursHumidite_SansNone = []
                    ValeursCO2_SansNone = []
                    ValeurNulle = [0, 0, 0, 0, 0]

                    if nbRaspSalle[i] == 0:
                        AnyData = True

                    for j in range(nbRaspSalle[i]):

                        ValeursTemperature = []
                        ValeursAcoustique = []
                        ValeursLuminosite = []
                        ValeursHumidite = []
                        ValeursCO2 = []

                        for k in range(int(len(ip))):
                            ip[k] = str(ip[k]).replace('.', '_')

                        dataCapteurs = db['Capteurs'].find()

                        for rows in dataCapteurs:
                            for k in range(int(len(ip))):
                                EtatCapteurTemperature = True
                                EtatCapteurAcoustique = True
                                EtatCapteurLuminosite = True
                                EtatCapteurCO2 = True
                                EtatCapteurHumidite = True

                                if salle[i] in str(rows):
                                    if ip[k] in str(rows):
                                        if rows[ip[k]][0]['Temperature'] == False:
                                            EtatCapteurTemperature = False
                                        if rows[ip[k]][0]['Son'] == False:
                                            EtatCapteurAcoustique = False
                                        if rows[ip[k]][0]['Luminosite'] == False:
                                            EtatCapteurLuminosite = False
                                        if rows[ip[k]][0]['CO2'] == False:
                                            EtatCapteurCO2 = False
                                        if rows[ip[k]][0]['Humidite'] == False:
                                            EtatCapteurHumidite = False

                                        EtatCapteurs.append(
                                            [EtatCapteurTemperature, EtatCapteurAcoustique, EtatCapteurLuminosite,
                                             EtatCapteurCO2, EtatCapteurHumidite])

                        for k in range(int(len(ip))):
                            ip[k] = str(ip[k]).replace('_', '.')

                        for k in range(int(len(ip))):
                            for r in db[salle[i]].find({'ip': ip[k]}, {'_id': 0}).sort('Time', -1).limit(5):

                                FraicheurValeurs = r['Time']
                                FraicheurValeurs = datetime.fromtimestamp(FraicheurValeurs / 1e3)

                                #TODO: ce que romain à demander
                                if (StatutTemperature == True and EtatCapteurs[j][0] == True and 'temperature' in r['capteur temperature'] and r['capteur temperature']['temperature']['temperature'] !="off"):
                                    ValeursTemperature.append(r['capteur temperature']['temperature']['temperature'])
                                else:
                                    ValeursTemperature.append(None)
                                    ValeurNulle[0] = ValeurNulle[0] + 1

                                if (StatutAcoustique == True and EtatCapteurs[j][1] == True and 'bruit' in r[
                                    'capteur bruit'] and r['capteur bruit']['bruit']['bruit'] != "off"):
                                    ValeursAcoustique.append(r['capteur bruit']['bruit']['bruit'])
                                else:
                                    ValeursAcoustique.append(None)
                                    ValeurNulle[1] = ValeurNulle[1] + 1

                                if (StatutLuminosite == True and EtatCapteurs[j][2] == True and 'luminosite' in r[
                                    'capteur luminosite'] and r['capteur luminosite']['luminosite']['luminosite'] != "off"):
                                    ValeursLuminosite.append(r['capteur luminosite']['luminosite']['luminosite'])
                                else:
                                    ValeursLuminosite.append(None)
                                    ValeurNulle[2] = ValeurNulle[2] + 1

                                if (StatutCO2 == True and EtatCapteurs[j][3] == True and 'co2' in r['capteur co2'] and r['capteur co2']['co2']['co2'] !="off"):
                                    ValeursCO2.append(r['capteur co2']['co2']['co2'])
                                else:
                                    ValeursCO2.append(None)
                                    ValeurNulle[3] = ValeurNulle[3] + 1

                                if (StatutHumidite == True and EtatCapteurs[j][4] == True and 'humidite' in r[
                                    'capteur humidite'] and r['capteur humidite']['humidite']['humidite'] != "off"):
                                    ValeursHumidite.append(r['capteur humidite']['humidite']['humidite'])
                                else:
                                    ValeursHumidite.append(None)
                                    ValeurNulle[4] = ValeurNulle[4] + 1

                        for k in range(int(len(ValeursTemperature))):

                            if ValeursTemperature[k] != None:
                                ValeursTemperature_SansNone.append(ValeursTemperature[k])

                            if ValeursAcoustique[k] != None:
                                ValeursAcoustique_SansNone.append(ValeursAcoustique[k])

                            if ValeursLuminosite[k] != None:
                                ValeursLuminosite_SansNone.append(ValeursLuminosite[k])

                            if ValeursCO2[k] != None:
                                ValeursCO2_SansNone.append(ValeursCO2[k])

                            if ValeursHumidite[k] != None:
                                ValeursHumidite_SansNone.append(ValeursHumidite[k])

                    if AnyData == False:

                        if demandeTemperature == True:
                            if int(len(ValeursTemperature_SansNone)) > ValeurNulle[0]:
                                if (int(len(ValeursTemperature_SansNone)) - ValeurNulle[0]) != 0:
                                    Temperature = sum(ValeursTemperature_SansNone) / (
                                            int(len(ValeursTemperature_SansNone)) - ValeurNulle[0])
                        if Temperature == None:
                            Temperature = 21

                        if demandeAcoustique == True:
                            if int(len(ValeursAcoustique_SansNone)) > ValeurNulle[1]:
                                if (int(len(ValeursAcoustique_SansNone)) - ValeurNulle[1]) != 0:
                                    Acoustique = sum(ValeursAcoustique_SansNone) / (
                                            int(len(ValeursAcoustique_SansNone)) - ValeurNulle[1])
                        if Acoustique == None:
                            Acoustique = 0

                        if demandeLuminosite == True:
                            if int(len(ValeursLuminosite_SansNone)) > ValeurNulle[2]:
                                if (int(len(ValeursLuminosite_SansNone)) - ValeurNulle[2]) != 0:
                                    Luminosite = sum(ValeursLuminosite_SansNone) / (
                                            int(len(ValeursLuminosite_SansNone)) - ValeurNulle[2])

                        if Luminosite == None:
                            Luminosite = 500

                        if demandeCO2 == True:
                            if int(len(ValeursLuminosite_SansNone)) > ValeurNulle[3]:
                                if (int(len(ValeursCO2_SansNone)) - ValeurNulle[3]) != 0:
                                    CO2 = sum(ValeursCO2_SansNone) / (int(len(ValeursCO2_SansNone)) - ValeurNulle[3])

                        if CO2 == None:
                            CO2 = 0

                        if demandeHumidite == True:
                            if int(len(ValeursLuminosite_SansNone)) > ValeurNulle[4]:
                                if (int(len(ValeursHumidite_SansNone)) - ValeurNulle[4]) != 0:
                                    Humidite = sum(ValeursHumidite_SansNone) / (
                                            int(len(ValeursHumidite_SansNone)) - ValeurNulle[4])

                        if Humidite == None:
                            Humidite = 50

                        dummy = MADM(Temperature / 50, Acoustique / 150, Luminosite / 1000, CO2 / 2000, Humidite / 100)

                        EtatCapteursGlobal = [True, True, True, True, True]
                        for l in range(int(len(EtatCapteurs))):
                            if EtatCapteurs[l][0] == False:
                                EtatCapteursGlobal[0] = False
                            if EtatCapteurs[l][1] == False:
                                EtatCapteursGlobal[1] = False
                            if EtatCapteurs[l][2] == False:
                                EtatCapteursGlobal[2] = False
                            if EtatCapteurs[l][3] == False:
                                EtatCapteursGlobal[3] = False
                            if EtatCapteurs[l][4] == False:
                                EtatCapteursGlobal[4] = False

                        InfoProbleme = []

                        if demandeTemperature == True:
                            if (StatutTemperature == False):
                                Temperature = "Capteur désactivé par l'administrateur"
                            else:
                                Temperature = round(Temperature, 2)
                            if (EtatCapteursGlobal[0] == False):
                                InfoProbleme.append(" | Au moins 1 capteur de température H.S. |")
                        else:
                            Temperature = "Valeur Non Demandé"
                            if (StatutTemperature == False):
                                InfoProbleme.append("Capteur désactivé par l'administrateur")
                            if (EtatCapteursGlobal[0] == False):
                                InfoProbleme.append(" | Au moins 1 capteur de température H.S. |")

                        if demandeAcoustique == True:
                            if (StatutAcoustique == False):
                                Acoustique = "Capteur désactivé par l'administrateur"
                            else:
                                Acoustique = round(Acoustique, 2)
                            if (EtatCapteursGlobal[1] == False):
                                InfoProbleme.append(" | Au moins 1 capteur de son H.S. |")
                        else:
                            Acoustique = "Valeur Non Demandé"
                            if (StatutAcoustique == False):
                                InfoProbleme.append("Capteur désactivé par l'administrateur")
                            if (EtatCapteursGlobal[1] == False):
                                InfoProbleme.append(" | Au moins 1 capteur de son H.S. |")

                        if demandeLuminosite == True:
                            if (StatutLuminosite == False):
                                Luminosite = "Capteur désactivé par l'administrateur"
                            else:
                                Luminosite = round(Luminosite, 2)
                            if (EtatCapteursGlobal[2] == False):
                                InfoProbleme.append(" | Au moins 1 capteur de luminosité H.S. |")
                        else:
                            Luminosite = "Valeur Non Demandé"
                            if (StatutLuminosite == False):
                                Luminosite = "Capteur désactivé par l'administrateur"
                            if (EtatCapteursGlobal[2] == False):
                                InfoProbleme.append(" | Au moins 1 capteur de luminosité H.S. |")

                        if demandeCO2 == True:
                            if (StatutCO2 == False):
                                CO2 = "Capteur désactivé par l'administrateur"
                            else:
                                CO2 = round(CO2, 2)
                            if (EtatCapteursGlobal[3] == False):
                                InfoProbleme.append(" | Au moins 1 capteur de CO2 H.S. |")
                        else:
                            CO2 = "Valeur Non Demandé"
                            if (EtatCapteursGlobal[3] == False):
                                InfoProbleme.append(" | Au moins 1 capteur de CO2 H.S. |")
                            if (EtatCapteursGlobal[3] == False):
                                InfoProbleme.append(" | Au moins 1 capteur de CO2 H.S. |")

                        if demandeHumidite == True:
                            if (StatutHumidite == False):
                                Humidite = "Capteur désactivé par l'administrateur"
                            else:
                                Humidite = round(Humidite, 2)
                            if (EtatCapteursGlobal[4] == False):
                                InfoProbleme.append(" | Au moins 1 capteur d'humidité H.S. |")
                        else:
                            Humidite = "Valeur Non Demandé"
                            if (StatutHumidite == False):
                                InfoProbleme.append("Capteur désactivé par l'administrateur")
                            if (EtatCapteursGlobal[4] == False):
                                InfoProbleme.append(" | Au moins 1 capteur d'humidité H.S. |")

                        Materiel = None

                        for r in db['Materiel_Salle'].find({salle[i]: {"$exists": True}}):
                            Materiel = r[salle[i]]

                        if Materiel is None:
                            Materiel = []

                        sortRes.append(({salle[i]: {'Note': dummy,
                                                    'Temperature': Temperature,
                                                    'Acoustique': Acoustique,
                                                    'Luminosite': Luminosite,
                                                    'CO2': CO2,
                                                    'Humidite': Humidite,
                                                    'Fraicheur des données': FraicheurValeurs,
                                                    'Informations Problemes': InfoProbleme,
                                                    'Materiel': Materiel

                                                    }}, dummy))
                    else:
                        Note = 0
                        for r in db['Materiel_Salle'].find({salle[i]: {"$exists": True}}):
                            Materiel = r[salle[i]]
                        if Materiel is None:
                            Materiel = []
                        sortRes.append(({salle[i]: {'Note': Note, 'Informations Problemes': "Any value",
                                                    'Materiel': Materiel}}, Note))

                if sortRes:
                    message = "data retrieved"
                    status = 'successful'
                    code = 200

                    sortRes = sorted(sortRes, key=lambda result: result[1], reverse=True)

                    for i in range(int(len(sortRes))):
                        res.append(sortRes[i][0])

                    if demandeTemperature == True and demandeAcoustique == True and demandeLuminosite == True and demandeCO2 == True and demandeHumidite == True:
                        db['MADM'].delete_many({})
                        res2 = {"Time": time.time(), "data": res}
                        db['MADM'].insert_one(res2)

                else:
                    message = "no value found"
                    status = 'successful'
                    code = 200

            except Exception as ee:
                res = {"error": str(ee)}
        else:
            if token != None:
                message = "wrong token"
                status = 'fail'
                code = 401
            else:
                message = "any token"
                status = 'fail'
                code = 401
        return jsonify({"status": status, 'Resultat': res, "message": message}), code


@app.route('/Capteurs', methods=['GET'])
@cross_origin('*')
def indexCapteurs():
    res = []
    token = request.args.get('token')
    code = 500
    status = "fail"
    message = ""
    User = db.users.find_one({'token': token, 'administrator': True}, {'_id': 0});
    if User != None:
        try:
            for r in db['Capteurs'].find({}, {'_id': 0}):
                res.append(r)
            if res:
                message = "Capteurs retrieved"
                status = 'successful'
                code = 200
            else:
                message = "no value found"
                status = 'successful'
                code = 204
        except Exception as ee:
            res = {"error": str(ee)}
    else:
        if token is not None:
            message = "wrong token"
            status = 'fail'
            code = 401
        else:
            message = "any token"
            status = 'fail'
            code = 401
    return jsonify({"status": status, 'data': res, "message": message}), code


@app.route('/signup', methods=['POST'])
@cross_origin('*')
def save_user():
    message = ""
    code = 500
    status = "fail"
    try:
        data = request.get_json()
        if isinstance(data, str):  # check if data is str
            data = json.loads(data)  # convert data to dict
        if "@univ-lorraine.fr" in data['email'] or "@admin.univ-lorraine.fr" in data['email']:
            check = db['users'].find({"email": data['email']})
            Compteur = 0
            for rows in check:
                Compteur = Compteur + 1
            if Compteur >= 1:
                message = "user with that email exists"
                code = 401
                status = "fail"
            else:
                # hashing the password so it's not stored in the db as it was
                data['password'] = bcrypt.generate_password_hash(data['password']).decode('utf-8')
                data['created'] = datetime.now()
                if "@admin.univ-lorraine.fr" in data['email']:
                    data['administrator'] = True
                else:
                    data['administrator'] = False

                res = db["users"].insert_one(data)

                user = db['users'].find_one({"email": f'{data["email"]}'})
                time = datetime.utcnow() + timedelta(hours=24)
                token = jwt.encode({
                    "user": {
                        "email": f"{user['email']}",
                        "id": f"{user['_id']}",
                    },
                    "exp": time
                }, secret)
                del user['password']
                db.users.update_one({'email': user['email']}, {'$set': {'token': token}})

                if res.acknowledged:
                    status = "successful"
                    message = "user created successfully"
                    code = 201
        else:
            message = "user denied"
            code = 401
            status = "fail"

    except Exception as ex:
        message = f"{ex}"
        status = "fail"
        code = 500
    return jsonify({'status': status, "message": message}), code


@app.route('/login', methods=['POST'])
@cross_origin('*')
def login():
    message = "fail"
    res_data = {}
    code = 500
    status = "fail"
    try:
        data = request.get_json()
        if isinstance(data, str):  # check if data is str
            data = json.loads(data)  # convert data to dict
        user = db['users'].find_one({"email": f'{data["email"]}'})

        if user:
            user['_id'] = str(user['_id'])
            if user and bcrypt.check_password_hash(user['password'], data['password']):

                del user['password']
                message = f"user authenticated"
                code = 200
                status = "successful"
                res_data['user'] = user

            else:
                message = "wrong password"
                code = 401
                status = "fail"
        else:
            message = "invalid login details"
            code = 401
            status = "fail"

    except Exception as ex:
        message = f"{ex}"
        code = 500
        status = "fail"
    return jsonify({'status': status, "data": res_data, "message": message}), code


@app.route('/modifierCapteurs', methods=['POST'])
@cross_origin('*')
def indexmodifierCapteurs():
    res = []
    token = request.args.get('token')
    salle = request.args.get('salle')
    data = request.get_json()
    # Fix issue : data is empty with CORS in browser
    if data is None:
        data = request.form.to_dict()
    code = 500
    status = "fail"
    message = ""
    User = db.users.find_one({'token': token, 'administrator': True}, {'_id': 0});
    if User is not None:
        try:
            res = db['Capteurs'].update_one({data['Salle']: {"$exists": True}},
                                            {"$set": {data['Salle']: [{'Temperature': bool(data['Temperature']),
                                                                       'Son': bool(data['Acoustique']),
                                                                       'CO2': bool(data['CO2']),
                                                                       'Luminosite': bool(data['Luminosite']),
                                                                       'Humidite': bool(data['Humidite'])}]}})
            if res:
                message = "Capteurs modified"
                status = 'successful'
                code = 200
            else:
                message = "no modifications"
                status = 'successful'
                code = 204
        except Exception as ee:
            res = {"error": str(ee)}
    else:
        if token is not None:
            message = "wrong token"
            status = 'fail'
            code = 401
        else:
            message = "any token"
            status = 'fail'
            code = 401
    return jsonify({"status": status, 'data': "Done", "message": message}), code


@app.route('/ajouterCapteurs', methods=['POST'])
@cross_origin('*')
def indexajouterCapteurs():
    res = []
    token = request.args.get('token')
    data = request.get_json()
    # Fix issue : data is empty with CORS in browser
    if data is None:
        data = request.form.to_dict()

    if isinstance(data, str):  # check if data is str
        data = json.loads(data)  # convert data to dict
    ip = str(data['ip']).replace('.', '_')
    code = 500
    status = "fail"
    message = ""
    User = db.users.find_one({'token': token, 'administrator': True}, {'_id': 0});
    if User != None:
        try:
            check = db['Capteurs'].find({ip: {"$exists": True}})
            Compteur = 0
            for rows in check:
                Compteur = Compteur + 1
            if Compteur >= 1:
                message = "Raspberry with this ip exists"
                code = 401
                status = "fail"

            else:
                res = db['Capteurs'].insert_one({ip: [{'Temperature': bool(data['Temperature']),
                                                       'Son': bool(data['Acoustique']),
                                                       'CO2': bool(data['CO2']),
                                                       'Luminosite': bool(data['Luminosite']),
                                                       'Salle': data['Salle'],
                                                       'Humidite': bool(data['Humidite'])}]})
                if res:
                    message = "Capteurs modified"
                    status = 'successful'
                    code = 200
                else:
                    message = "no modifications"
                    status = 'successful'
                    code = 204
        except Exception as ee:
            res = {"error": str(ee)}
    else:
        if token != None:
            message = "wrong token"
            status = 'fail'
            code = 401
        else:
            message = "any token"
            status = 'fail'
            code = 401
    return jsonify({"status": status, 'data': "Done", "message": message}), code


@app.route('/ajouterSalle', methods=['POST'])
@cross_origin('*')
def indexajouterSalle():
    res = []
    token = request.args.get('token')
    data = request.get_json()
    if isinstance(data, str):  # check if data is str
        data = json.loads(data)  # convert data to dict
    code = 500
    # Fix issue : data is empty with CORS in browser
    if data is None:
        data = request.form.to_dict()

    if isinstance(data, str):  # check if data is str
        data = json.loads(data)  # convert data to dict
    Salle = data['Salle']
    code = 500
    status = "fail"
    message = ""
    User = db.users.find_one({'token': token, 'administrator': True}, {'_id': 0});
    if User != None:
        try:
            check = db['Capteurs'].find({Salle: {"$exists": True}})
            Compteur = 0
            for rows in check:
                Compteur = Compteur + 1
            if Compteur >= 1:
                message = "Salle already exists"
                code = 401
                status = "fail"

            else:
                res = db['Capteurs'].insert_one({Salle: [{'Temperature': bool(data['Temperature']),
                                                          'Son': bool(data['Acoustique']),
                                                          'CO2': bool(data['CO2']),
                                                          'Luminosite': bool(data['Luminosite']),
                                                          'Humidite': bool(data['Humidite'])}]})
                if res:
                    message = "Salle modified"
                    status = 'successful'
                    code = 200
                else:
                    message = "no modifications"
                    status = 'successful'
                    code = 204
        except Exception as ee:
            res = {"error": str(ee)}
    else:
        if token != None:
            message = "wrong token"
            status = 'fail'
            code = 401
        else:
            message = "any token"
            status = 'fail'
            code = 401
    return jsonify({"status": status, 'data': "Done", "message": message}), code


@app.route('/supprimerCapteurs', methods=['POST'])
@cross_origin('*')
def indexsupprimerCapteurs():
    res = []
    token = request.args.get('token')
    data = request.get_json()
    # Fix issue : data is empty with CORS in browser
    if data is None:
        data = request.form.to_dict()
    ip = str(data['ip']).replace('.', '_')
    code = 500
    status = "fail"
    message = ""
    User = db.users.find_one({'token': token, 'administrator': True}, {'_id': 0});
    if User != None:
        try:
            check = db['Capteurs'].find({ip: {"$exists": True}})
            Compteur = 0
            for rows in check:
                Compteur = Compteur + 1
            if Compteur == 0:
                message = "Any Raspberry with this ip"
                code = 401
                status = "fail"

            else:
                res = db['Capteurs'].delete_one({ip: {"$exists": True}})
                if res:
                    message = "Capteurs delete"
                    status = 'successful'
                    code = 200
                else:
                    message = "no modifications"
                    status = 'successful'
                    code = 204
        except Exception as ee:
            res = {"error": str(ee)}

    else:
        if token != None:
            message = "wrong token"
            status = 'fail'
            code = 401
        else:
            message = "any token"
            status = 'fail'
            code = 401
    return jsonify({"status": status, 'data': "Done", "message": message}), code


@app.route('/supprimerSalle', methods=['POST'])
@cross_origin('*')
def indexsupprimerSalle():
    res = []
    token = request.args.get('token')
    data = request.get_json()
    # Fix issue : data is empty with CORS in browser
    if data is None:
        data = request.form.to_dict()

    if isinstance(data, str):  # check if data is str
        data = json.loads(data)  # convert data to dict
    Salle = data['Salle']
    code = 500
    status = "fail"
    message = ""
    User = db.users.find_one({'token': token, 'administrator': True}, {'_id': 0});
    if User != None:
        try:
            check = db['Capteurs'].find({Salle: {"$exists": True}})
            Compteur = 0
            for rows in check:
                Compteur = Compteur + 1
            if Compteur == 0:
                message = "Any Salle with this name"
                code = 401
                status = "fail"

            else:
                res = db['Capteurs'].delete_one({Salle: {"$exists": True}})
                if res:
                    message = "Salle delete"
                    status = 'successful'
                    code = 200
                else:
                    message = "no modifications"
                    status = 'successful'
                    code = 204
        except Exception as ee:
            res = {"error": str(ee)}

    else:
        if token != None:
            message = "wrong token"
            status = 'fail'
            code = 401
        else:
            message = "any token"
            status = 'fail'
            code = 401
    return jsonify({"status": status, 'data': "Done", "message": message}), code


if __name__ == '__main__':
    app.run(host='aip-confort.milebits.com', port=3001, debug=True, ssl_context=('cert.pem', 'key.pem'))
