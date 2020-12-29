import json
import re

from app.projects.service import ProjectService
from app.user.service import UserService
from app.utils.grew_utils import grew_request
from flask import Response, abort, current_app, request
from flask_login import current_user
from flask_restx import Namespace, Resource, reqparse

api = Namespace(
    "Lexicon", description="Endpoints for dealing with samples of project"
)  # noqa


@api.route("/<string:project_name>/lexicon")
class LexiconResource(Resource):
    "Lexicon"

    def post(self, project_name: str):
        parser = reqparse.RequestParser()
        parser.add_argument(name="samplenames", type=str, action="append")
        parser.add_argument(name="treeSelection", type=str)
        args = parser.parse_args()

        sample_names = args.get("samplenames")
        treeSelection = args.get("treeSelection")
        print(sample_names, treeSelection)
        reply = grew_request(
            "getLexicon",
            data={"project_id": project_name, "sample_ids": json.dumps(sample_names)},
        )
        for i in reply["data"]:
            x = {"key": i["form"] + i["lemma"] + i["POS"] + i["features"] + i["gloss"]}
            i.update(x)
        resp = {"status_code": 200, "lexicon": reply["data"], "message": "hello"}
        return resp


@api.route("/<string:project_name>/export/json")
class LexiconExportJson(Resource):
    def post(self, project_name: str):
        parser = reqparse.RequestParser()
        parser.add_argument(name="data", type=dict, action="append")
        args = parser.parse_args()

        lexicon = args.get("data")
        for element in lexicon:
            del element["key"]
        line = json.dumps(lexicon, separators=(",", ":"), indent=4)
        resp = Response(line, status=200)
        return resp


@api.route("/<string:project_name>/export/tsv")
class LexiconExportTsv(Resource):
    def post(self, project_name: str):
        parser = reqparse.RequestParser()
        parser.add_argument(name="data", type=dict, action="append")
        args = parser.parse_args()
        lexicon = args.get("data")
        features = ["form", "lemma", "POS", "features", "gloss", "frequency"]
        line = ""
        for i in lexicon:
            for f in features:
                try:
                    line += i[f] + "\t"
                except TypeError:
                    line += str(i[f])
            line += "\n"

        resp = Response(line, status=200)
        return resp


@api.route("/<project_name>/transformationgrew")
class TransformationGrewResource(Resource):
    def post(self, project_name: str):
        parser = reqparse.RequestParser()
        parser.add_argument(name="data", type=dict, action="append")
        args = parser.parse_args()
        lexicon = args.get("data")
        comp = 0
        patterns = []
        commands = []
        without = ""
        dic = {
            0: "form",
            1 : "lemma",
            2 : "upos",
            3 :"Gloss",
            4 : "trait"
            }
        for i in lexicon['data'] :
            rule_grew = "pattern {"
            #print(i['info2Change'])
            line1 = i['currentInfo'].split(' ')
            line2 = i['info2Change'].split(' ')
            #print(line2)
            comp+=1
            patterns.append(transform_grew_get_pattern(line1, dic, comp))
            rule_grew += patterns[comp-1]+'}'
            resultat = transform_grew_verif(line1, line2)
            co, without_traits = (transform_grew_get_commands(resultat,line1, line2, dic, comp))
            commands.append(co)
            if without_traits != '' : 
                if without != "" :
                    without += ", "
                without = without + without_traits
                rule_grew += " without{ "+without_traits+"}"
            rule_grew += " command{ " + commands[comp-1]+"}"
        patterns[0] = '% click the button \'Correct lexicon\' to update the queries\n\npattern { ' + patterns[0][0:]
        commands[0] = 'commands { '+ commands[0][0:]
        patterns[len(lexicon['data'])-1] += ' }'
        commands.append('}')
        if len(without) != 0 :
            without = '\nwithout { ' + without + '}'
        patterns_output = ','.join(patterns)
        commands_output = ''.join(commands)
        resp = {
            "patterns": patterns_output,
            "commands": commands_output,
            "without": without,
        }
        # print("patterns :", ','.join(patterns), "\ncommands :", ''.join(commands))
        resp["status_code"] = 200
        return resp


# TODO : It seems that this function is not finished. Ask Lila what should be done -> finished function
@api.route("/<project_name>/upload/validator", methods=["POST", "OPTIONS"])
class LexiconUploadValidatorResource(Resource):
    def post(self, project_name):
        fichier = request.files["files"]
        f = fichier.read()
        resp = {"validator": f, "message": "hello"}
        resp["status_code"] = 200
        return resp


@api.route("/<project_name>/addvalidator")
class LexiconAddValidatorResource(Resource):
    def post(self, project_name: str):
        parser = reqparse.RequestParser()
        parser.add_argument(name="data", type=dict, action="append")
        parser.add_argument(name="validator", type=dict, action="append")
        args = parser.parse_args()
        lexicon = args.get("data")

        
        lexicon = args.get("data")
        validator = args.get("validator")
        list_validator = []
        line=[]
        A = []
        B = []
        AB_Ok=[]
        AB_Diff=[]
        list_types = {
            "In the two dictionaries with the same information" : AB_Ok,
            "Identical form in both dictionaries with different information" : AB_Diff,
            "Only in the old dictionary" : A,
            "Only in the imported dictionary" : B}

        for i in validator['validator'].split('\n'):
            a = i.split("\t")
            if a[-1] == '': 
                a.pop()
            if a != []: 
                a[-1] = a[0] + a[1] + a[2] + a[3] + a[4]
                newjson = {
                    "form":a[0],
                    "lemma":a[1],
                    "POS":a[2],
                    "features":a[3],
                    "gloss":a[4],
                    "key":a[-1],
                    }
                list_validator.append(newjson)
        # print("lexicon = \n", list_lexicon, "\n\nval = \n", list_validator)

        
        for x in lexicon['data']:
            if 'frequency' in x: 
                del x['frequency']
            for y in list_validator:
                # le token existe dans les deux dicts avec les mêmes feats
                if x['key'] == y['key'] and x not in AB_Ok and x not in AB_Diff: 
                    x['toChange'] = "_"
                    AB_Ok.append(x)
                # le terme existe dans les deux dictionnaires mais avec de différents feats
                elif x['key'] != y['key'] and x['form'] == y['form'] and x not in AB_Ok and x not in AB_Diff and y not in AB_Ok and y not in AB_Diff: 
                    x['toChange'] = y['form'] + ' ' + y['lemma'] + ' ' + y['POS'] + ' ' + y['gloss'] + ' ' + y['features']
                    AB_Diff.extend((x,y))

        # le token n'existe pas dans le dict A
        for x in lexicon['data']:
            if x not in AB_Ok and x not in AB_Diff and x not in A:
                x['toChange'] = "_"
                A.append(x)

        # le token n'existe pas dans le dict B
        for y in list_validator:
            if y not in AB_Ok and y not in AB_Diff and x not in B: 
                y['toChange'] = "_"
                B.append(y)

        # print("AAAAAAA ",A,"\n\nBBBBBBBB ",B, "\n\nAB OK", AB_Ok, "\n\nAB Diff", AB_Diff)
        
        for i in list_types:
            for s in list_types[i]:
                s['type'] = i
                line.append(s)
        # print(line)
        resp = {"dics": line, "message": "hello"}
        resp["status_code"] = 200
        return resp


################################################################################
##################                                        #######################
##################           Helpers functions            #######################
##################                                        #######################
################################################################################


def transform_grew_verif(ligne1, ligne2): #Voir différences entre deux lignes
	liste=[]
	if len(ligne1) > len(ligne2): 
		maximum = len(ligne1)
	else: 
		maximum = len(ligne2)
	for i in range(maximum):
		try:
			if ligne1[i] != ligne2[i]:
				liste.append(i)
		except IndexError:
			liste.append(i)
	#print("transform_grew_verif",liste)
	return liste

def transform_grew_get_pattern(ligne, dic, comp): 
	pattern = "X" + str(comp) + '[form=\"' + ligne[0] + '\"'
	for element in range(1,len(ligne)):
		if element == len(ligne)-1:
			# print(element, ligne[element], dic[element])
			if ligne[element] != "_" and '=' in ligne[element]: #features
				mot = ligne[element].split("|") #Number=Sing, PronType=Dem
				pattern = pattern + ", " + ", ".join(mot)
		elif element == 2: # upos = PRON
			pattern = pattern + ", " + dic[element] + "=" + ligne[element]
		else:
			pattern = pattern + ", " + dic[element] + '=\"' + ligne[element] + '\"' # forme=\"dat\", lemma=\"dat\"
	pattern = pattern + "]"
	return pattern


def transform_grew_get_without(l, l2, comp):
	mot = l.split("|")
	mot2 = l2.split("|")
	les_traits = []
	liste_traits = []
	feats_str = ""
	# for i in mot :
	# 	if i not in mot2 and i !="_": # suppression de traits 1 non existant dans traits2
	# 		les_traits = les_traits+"del_feat X"+str(comp)+"."+i.split("=")[0]+';'
	for i in mot2:
		if i not in mot and i != "_": # ajout traits2 non existant dans traits1
			liste_traits.append(i)
	# print(les_traits, liste_traits)
	# print (without, liste_traits, len(liste_traits))
	if len(liste_traits) == 0:
		feats_str = False
	if liste_traits:
		les_traits.append("X" + str(comp) + "[" + ",".join(liste_traits) + "]")
		for feat in liste_traits:
			feats_str += "X" + str(comp) + "." + feat + "; "
	return les_traits, feats_str

# def transform_grew_get_features(l2, comp):
# 	les_traits=""
# 	mot2 = l2.split("|")
# 	without = "without { X["
# 	liste_traits = []
# 	for i in mot2 :
# 		les_traits = les_traits+" X"+str(comp)+"."+i+";"
# 		liste_traits.append(i)
# 	without=without+", ".join(liste_traits)+"]}\n"
# 	#print (without, liste_traits, len(liste_traits))
# 	if len(liste_traits)==0 :
# 		without = False
# 	return les_traits, without

def transform_grew_traits_corriges(l, l2, comp): # différence entre deux feats
	traits = ''
	mot1 = l.split("|")
	print(mot1, l,l2)
	if l2 == "_":
		for i in mot1:
			traits = traits + "del_feat X" + str(comp) + "." + i.split("=")[0] + '; '
	else:
		mot2 = l2.split("|")
		print(mot2)
		for i in mot1:  # suppression des traits 1
			if i not in mot2:
				traits = traits + "del_feat X" + str(comp) + "." + i.split("=")[0] + '; '
	return traits

def transform_grew_get_commands(resultat, ligne1, ligne2, dic, comp):
	correction = ""
	commands = ""
	# without_traits = ""
	list_traits2 = []
	temp_var = ""
	for e in resultat:
		if e == 4: #si traits sont différents
			# try :
			#print(len(ligne1[e].split("|")), len(ligne2[e].split("|")))
			if ligne2[e] != "_" and len(ligne1[e].split("|")) < len(ligne2[e].split("|")) or ligne1[e] == "_":
				if ligne2[e] != "": #insertion des traits
					list_traits2, feats_str = transform_grew_get_without(ligne1[e], ligne2[e], comp)
					temp_var = ",".join(list_traits2)
					#print(temp_var,"123123", list_traits2)
					commands = commands + feats_str
					#print(without_traits,"1112222333", list_traits2)
			else: #si on doit supprimer les traits de ligne1 :
				#print("transform_grew_get_commands vers traits_a_supprimer", ligne1[e],ligne2[e], comp)
				traits_a_supprimer = transform_grew_traits_corriges(ligne1[e], ligne2[e], comp)
				commands = commands + traits_a_supprimer
		else: # si la différence n'est pas trait
			#print(e, dic, comp, ligne1, ligne2)
			commands = commands + "X" + str(comp) + "." + dic[e] + '=\"' + ligne2[e] + '\"; '
	correction = correction + commands
	#print(correction, "------", commands)
	return correction, temp_var