#!/usr/bin/env python
# coding: utf-8

# In[59]:


#pour exécuter le code, il faut le mettre dans le même dossier avec les dossiers "diverse" et "thème"
#Une fois que toutes les cellues sont exécutées, il faudra exécuter les deux dernières cellules pour générer une nouvelle question.
#Nous continuons d'ajouter des ressources et d'élargir les thèmes de question.*


# In[15]:


import sys
import json
from SPARQLWrapper import SPARQLWrapper, JSON #librairie pour effectuer des reuquêtes SPARQL en Python
import random
endpoint_url = "https://query.wikidata.org/sparql"


# In[16]:


#exécution de requêtes SPARQL
def get_results(endpoint_url,query):
    user_agent = "WDQS-example Python/%s.%s" % (sys.version_info[0], sys.version_info[1])
    # TODO adjust user agent; see https://w.wiki/CX6
    sparql = SPARQLWrapper(endpoint_url, agent=user_agent)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    return sparql.query().convert()
#rangement des resultats
def get_resultat(query):
    rel = [ ]
    results = get_results(endpoint_url,query)
    for result in results["results"]["bindings"]:
        rel.append(result['itemLabel']["value"])
    return rel


# In[17]:


def ouvrir_json(chemin):
    f = open(chemin, encoding="utf−8") 
    toto = json.load(f)
    f.close()
    return toto
def ecrire_json(dataset,chemin):
    donnee = json.dumps(dataset, indent =2,ensure_ascii=False) 
    w = open(chemin, "w",encoding = "utf-8")
    w.write(donnee)
    w.close()
    print("Jeu de données stocké dans %s"%chemin)


# In[18]:


#gestion du type de donnée temps
m_liste = ouvrir_json("diverse/m_liste.json")
def get_siecle(s,lan):
    s_label = " "
    if lan =="zh":
        s_label = s+"世纪"
    if lan =="fr":
        if s == "1":
            s_label = s+"er" + " siècle"
        else:
            s_label = s+"e" + " siècle"
    if lan =="en":
        if s == "1":
            s_label = s+"st" + " century"
        if s == "2":
            s_label = s+"nd" + " century"
        if s == "3":
            s_label = s+"rd" + " century"
        else:
            s_label = s+"th" + " century"
    return s_label

def get_date(d,lan):
    data = { }
    av = "False"
    if d[0] == "-":
        av = "True"
        d = d[1:11]
    y = d[0:4]
    m = d[5:7]
    j = d[8:10]
    s = str(int(int(y)/100)+1)
    #s_label = get_siecle(s,lan)
    #print(y)
    #print(m)
    #print(j)
    date_label = " "
    m_label = m_liste[m][lan]
    #print(m_label)
    if y[0]== "0":
        y = y[1:4]    
    if m == "01" and j == "01":
        if y[-2:] =="01":
            date_label = get_siecle(s,lan)
        else:
            if lan in ["fr","en"]:
                date_label = y
            else:
                date_label = y+"年"
    else:        
        if lan in ["fr","en"]:
            date_label = m_label +" "+y 
        else:
            date_label = y+"年"+m+"月"
  
    
    if av == "True":
        date = int("-"+y+m+j)
        if lan == "fr":
            date_label = date_label +" av.j.c."
        if lan == "en":
            date_label = date_label +"BC"
        if lan =="zh":
            date_label = "公元前"+date_label
    else:
        date =int(y+m+j)
    data["date"]=date  #date absolue
    data["label"] = date_label # label de date
    return data


# In[19]:


#nettoyage de Triplet : suppression des triplets dont la similarité entre l'objet et le sujet est trop grande
#nettoyage des entités qui n'ont pas de lable
from difflib import SequenceMatcher 

def similarity(a, b):    
    return SequenceMatcher(None, a, b).ratio() 

def gestion_objet(sujet,objet):
    objet_1 = [ ]
    for ele in objet: 
        if ele[0] not in ["t", "Q"] and similarity(sujet, ele) <= 0.65 :
            objet_1.append(ele)
    return objet_1
        


# In[20]:


#obtention de paires candidates qui permettront la verbalisation de question
def get_paires_candidates(donnee,id_entite,predicat_id,lan_de_q):
    paires_candidates = { }
    liste_objet = [ ]
    all_id = id_entite
    while len(paires_candidates)<4: #4 paires à générer
        sujet_id = random.choice(all_id )
        sujet = donnee["libelle"][sujet_id][lan_de_q] #label de sujet
        query = " SELECT ?item ?itemLabel ?pic WHERE { wd:%s  wdt:%s ?item SERVICE wikibase:label { bd:serviceParam wikibase:language '%s '}} " %(sujet_id,predicat_id,lan_de_q)
        reponse =  get_resultat(query) #obtention d'objet
        all_id.remove(sujet_id)
        if len(reponse) != 0 and len(gestion_objet(sujet,reponse)) != 0: #nettoyage de triplet
            paires_candidates[sujet] = gestion_objet(sujet,reponse)
    return paires_candidates


# In[21]:


#analyse sur les tripets pour obtenir les types de questions disponibles sur ces triplets
liste_comparable = ["temps","hauteur","longueur","superficie","quantité","taux"]
def trouver_q_type(candidat,type_predicat,predicat_id):
    q_type = [1,2]
    if donnee_predicat[predicat_id]["verbal"] != "": #si le prédicat a des alias verbaux
        q_type.append(3)
    
    if type_predicat in liste_comparable: #si le prédicat est comparable
        q_type.append(4)
        if donnee_predicat[predicat_id]["verbal"] != "":
            q_type.append(5) # et qu'il a des alias verbaux
    else:    
        dic_nb = { }
        liste_nb = [ ]
    #list_T_F = [ ]
        for k,v in candidat.items( ):    #analyse sur les nombres d'élément dans l'objet pour déterminer les types de questions 
            liste_nb.append(len(v))
            if len(v)>=3 and 6 not in q_type:
                q_type.append(6)
                q_type.append(7)
        liste_nb.sort( )
        if liste_nb [2] != liste_nb[3]:
            q_type.append(8)
        if liste_nb [0] != liste_nb[1]:
            q_type.append(9)
        if len(set(liste_nb)) >=3:
            q_type.append(10)
        
    return q_type


# In[22]:


# retourne de nouvelles paires candidates(qui ne sont pas pour la comparaison) 
#où il y a une correspondance biuvonique entre le sujet et l'objet
#ajout d'unité
def gestion_candidat (candidat, type_P,lan_de_q):
    candidat_1 = { }
    liste_objet = [ ]
    for k,v in candidat.items( ):
        objet = random.choice(v)
        while objet not in liste_objet: #on garantit que les 4 objets sont différents et qu'il ne fait pas partie d'objets des autres sujets
            liste_objet.append(objet)
            if type_P == "temps": #gestion du type de donnée temps
                candidat_1[k] = get_date(objet,lan_de_q)["label"]
            else: #ajout d'unité 
                if type_P in ["hauteur","longueur"] :
                    candidat_1[k] = objet + " m"
                elif type_P == "superficie" :
                    candidat_1[k] = objet + " km2 "
                elif type_P == "taux":
                    candidat_1[k] = objet +" %"
                else :
                    candidat_1[k] = objet
    return candidat_1


# In[23]:


# retourne de nouvelles paires candidates(pour la comparaison) où il y a une correspondance biuvonique entre le sujet et l'objet
#pas d'ajout d'unité
def gestion_candidat_compa (candidat,type_P):
    candidat_1 = { }
    liste_objet = [ ]
    for k,v in candidat.items( ):
        objet = random.choice(v)
        while objet not in liste_objet: #on garantit que les 4 objets sont différents et qu'il ne fait pas partie d'objets des autres sujets
            liste_objet.append(objet)
            if type_P == "temps":
                candidat_1[k] = get_date(objet,lan_de_q)["date"]# pour le temps, on obtiens la date absolue pour la comparaison
            else:
                candidat_1[k] = float(objet) #transforme le string en float pour la comparaison
    return candidat_1


# In[24]:


#obtient le nombre d'élément dans l'objet
def get_objet_nombre (candidat):
    candidat_1 = { }
    for k,v in candidat.items( ):
        candidat_1[k] = len(v)
    return candidat_1


# In[25]:


liste_interro_nv = ouvrir_json("diverse/lexique_interro_nv.json") #liste de lexique interrogatif pour la question non verbale
def generation_question_spo(predicat_id,lan_de_q,candidat): #génération de question sujet-prédicat-objet non verbale
    predicat = random.choice(donnee_predicat[predicat_id]["alias"][lan_de_q]) #verbalisation de predicat
    type_predicat = donnee_predicat[predicat_id]["type"]
    lex_interro = liste_interro_nv[type_predicat][lan_de_q] #obtention de lexique interrogatif
    candidat_1 = gestion_candidat(candidat,type_predicat,lan_de_q) #gestion de paires candidates(gestion de date, ajout d'unité etc.)
    Q_A = { }
    liste_reponse = [ ]
    liste_entite = [ ]
    
    for k,v in candidat_1.items():
        liste_reponse.append(v) #réponses candidates
        liste_entite.append(k)
    sujet = random.choice(liste_entite) #choix de paire visé (aléatoire) verbalisation de sujet
    reponse = candidat_1[sujet] #réponse correcte
  
    liste_patron = {   #liste de patron pour ce type de questions
     "fr": [
           " %s est  %s de  %s ? "%(lex_interro, predicat,sujet),
           " Le(la) %s de  %s est ...?"%(predicat,sujet),
           " Quelle réponse suivante est  %s de  %s ?"%(predicat,sujet),
          " Quelle réponse suivante correspond à %s de %s ?" %(predicat,sujet)
           ],
     "en": [
          " %s is the %s of  %s ? "%(lex_interro,predicat,sujet),
          " The %s of  %s is ...? "%(predicat,sujet),
         " Which following answer corresponds to the  %s of  %s ? "%(predicat,sujet)
           ],
      "zh": [
          "下列哪一个答案是%s的%s? "%(sujet,predicat),
          "下列哪一个选项是%s的%s? "%(sujet,predicat),
          "%s的%s是...?"%(sujet,predicat)
       ]
    }
    patron = random.choice(liste_patron[lan_de_q]) #choix aléatoire de patron selon la langue de question
    #print(patron)
    
   
          
    Q_A["question"]=patron #verbalisation de question
    Q_A["responses"]= liste_reponse #réponses candidates
    Q_A["reponse correcte"] = reponse #réponse correcte
    #print(question)
    #print(liste_reponse)
    return Q_A


# In[26]:


def generation_question_spo_inverse(predicat_id,lan_de_q,candidat): #génération de question sujet-prédicat-objet non verbale
    predicat = random.choice(donnee_predicat[predicat_id]["alias"][lan_de_q])#verbalisation de predicat
    type_predicat = donnee_predicat[predicat_id]["type"]
    label_theme = random.choice(donnee_entite["appelation"][lan_de_q]) #verbalisation du thème
    candidat_1 = gestion_candidat(candidat,type_predicat,lan_de_q) #gestion de paires candidates
    candidat_inverse = {v:k for k,v in candidat_1.items()} #inversement de sujet et objet
                                                          #ensuite, le processus de génération de question est pareil que le type
                                                          #sujet-prédicat-objet
    Q_A = { }
    liste_reponse = [ ]
    liste_entite = [ ]
    
    for k,v in candidat_inverse.items():
        liste_reponse.append(v)
        liste_entite.append(k)
    sujet = random.choice(liste_entite)
    reponse = candidat_inverse[sujet]
   
    liste_patron = {
     "fr": [
           " %s est  %s de ... ? " % (sujet, predicat),
           " %s est  %s de quel(le) %s%s? " % (sujet, predicat, label_theme,random.choice([""," suivant(e)"])),
           " Quel(le) %s%s a %s comme %s ? " % (label_theme,random.choice([""," suivant(e)"]), sujet, predicat),
           " %s correspond à %s de quel(le) %s%s?" %(sujet,predicat, label_theme,random.choice([""," suivant(e)"]))
           ],
     "en": [
          " %s is the %s of ... ? "%(sujet, predicat),
          " %s is the %s of which following %s ? "%(sujet, predicat, label_theme),
          " Which following %s has %s as its %s ? "%(label_theme, sujet, predicat),
          " %s matchs the %s of which following %s ? "% (sujet,predicat, label_theme)
           ],
      "zh": [
          "%s是...的%s"%(sujet,predicat),
          "%s是下面哪个%s的%s"%(sujet,label_theme,predicat),
          "下列哪个%s的%s是%s"%(label_theme,predicat,sujet)
       ]
    }
    patron = random.choice(liste_patron[lan_de_q])
   
    
    
          
    Q_A["question"]=patron #verbalisation de question
    Q_A["responses"]= liste_reponse #réponses candidates
    Q_A["reponse correcte"] = reponse #réponse correcte
    
    return Q_A


# In[27]:


liste_interro = ouvrir_json("diverse/lexique_interrogatif.json") #liste de lexique interrogatif pour la question verbale
liste_prep = ouvrir_json("diverse/liste_prep.json") #liste de préposition
def generation_question_spo_vb(predicat_id,lan_de_q,candidat):  #génération de question sujet-prédicat-objet verbale
    predicat = random.choice(donnee_predicat[predicat_id]["verbal"][lan_de_q])#verbalisation de predicat
    type_p = donnee_predicat[predicat_id]["type"]
    
    candidat_1 = gestion_candidat(candidat,type_p,lan_de_q) #gestion de paires candidates
    Q_A = { }
    liste_reponse = [ ]
    liste_entite = [ ]
   
    for k,v in candidat_1.items():
        liste_reponse.append(v) #réponses candidates
        liste_entite.append(k)
    sujet = random.choice(liste_entite)  #choix de paire visé (aléatoire) et verbalisation de sujet
    reponse = candidat_1[sujet] #reponse correcte
   
    
    if type_p != "normal": #liste de patron pour ce type de question
        lex_interro = liste_interro[type_p][lan_de_q]
        prep = liste_prep[type_p][lan_de_q]
        liste_patron = {
                "fr": [
                    " %s %s %s ? "%(lex_interro, predicat,sujet),
                    " %s %s %s ... ?" %(sujet, predicat, prep)
                      ],
                "en": [
                    "%s %s %s ?"% (lex_interro, predicat,sujet),
                    "%s %s %s ... ?" %(sujet, predicat, prep)
                      ],
                "zh": [
                    "%s%s...?"%(sujet,predicat),
                    "%s%s%s ?"%(sujet,predicat,lex_interro)
                     ]
                   }
    else: #pas de lexique interrogatif pour des prédicat du type "normal"
        liste_patron = {
            "fr" : ["%s %s..." %(sujet, predicat)],
            "en" : ["%s %s..." %(sujet, predicat)],
            "zh" : ["%s%s..." %(sujet, predicat)],
        }
    
    patron = random.choice(liste_patron[lan_de_q])
        
    Q_A["question"]=patron #verbalisation de question
    Q_A["responses"]= liste_reponse #réponses candidates
    Q_A["reponse correcte"] = reponse #réponse correcte
   
    return Q_A


# In[28]:


lexique_compa = ouvrir_json("diverse/lexique_compa.json") #liste de lexiques pour comparaison
def generation_question_comparaison(predicat_id,lan_de_q,candidat): #génération de question du type comparaison sur la valeur numérique
    predicat = random.choice(donnee_predicat[predicat_id]["alias"][lan_de_q]) #verbalisation du prédicat
    type_p = donnee_predicat[predicat_id]["type"]
    label_theme = random.choice(donnee_entite["appelation"][lan_de_q]) #verbalisation du thème 
    candidat_1 = gestion_candidat_compa(candidat,type_p) #gestion de paires candidates pour la COMPARAISON 
    Q_A = { }
    liste_reponse = [ ]
    liste_entite = [ ]
    for k, v in candidat_1.items( ):
        liste_entite.append(v)
        liste_reponse.append(k) #liste de réponses
    para = random.choice (["max","min"]) # choix de "plus grande valeur "  ou "plus petite valeur"
    adj_liste = lexique_compa[type_p][lan_de_q][para]
    adj_compa =random.choice(adj_liste) #choix de lexique comparatif
    if para == "max":
        reponse = max(candidat_1,key = candidat_1.get)  #choix de réponse correcte selon "la plus grande valeur " ou "la plus petite valeur"
    else:
        reponse = min(candidat_1,key = candidat_1.get)
    
    #liste de patrons pour ce type de question
    liste_patron = {
     "fr": [
           " Quel(le) %s a %s %s ? " % (label_theme,adj_compa,predicat),
           " Le(a) %s qui a %s %s est...? " % (label_theme,adj_compa,predicat),
           " Le(a) %s dont le(a) %s est %s est...? " % (label_theme, predicat, adj_compa),
           " Parmi toutes les réponses suivantes, laquelle a %s %s ?"%(adj_compa, predicat)
     
        ],
     "en": [
           " Which %s has %s %s ?" % (label_theme,adj_compa,predicat),
           " The %s %s has %s %s is ... ? " % (label_theme,random.choice(["which", "that"]), adj_compa,predicat ),
           "Among the following answers, which one has the %s %s ?" %(adj_compa,predicat)
         
     ] ,  
     "zh": [
           "下列哪一个%s的%s%s?"%(label_theme,predicat,adj_compa),
           "下列选项中, 拥有%s的%s的%s是...?"%(adj_compa,predicat,label_theme),
           "在下列%s中, 哪一个有%s的%s?"%(label_theme,adj_compa, predicat)
     ]   
    
     
    }
    patron = random.choice(liste_patron[lan_de_q])
    question =  patron      
    Q_A["question"]=patron #verbalisation de question
    Q_A["responses"]= liste_reponse #réponses candidates
    Q_A["reponse correcte"] = reponse #réponse correcte
    return Q_A


# In[29]:


lexique_compa_adv = ouvrir_json("diverse/lexique_compa_adv.json") #liste de lexiques pour comparaison
def generation_question_comparaison_verbal(predicat_id,lan_de_q,candidat): #génération de question verbale du type comparaison sur la valeur numérique
    predicat = random.choice(donnee_predicat[predicat_id]["verbal"][lan_de_q]) #verbalisation du prédicat
    type_p = donnee_predicat[predicat_id]["type"]
    label_theme = random.choice(donnee_entite["appelation"][lan_de_q]) #verbalisation du thème 
    candidat_1 = gestion_candidat_compa(candidat,type_p) #gestion de paires candidates pour la COMPARAISON 
    Q_A = { }
    liste_reponse = [ ]
    liste_entite = [ ]
    for k, v in candidat_1.items( ):
        liste_entite.append(v)
        liste_reponse.append(k) #liste de réponses
    para = random.choice (["max","min"]) # choix de "plus grande valeur "  ou "plus petite valeur"
    adv_liste = lexique_compa_adv[type_p][lan_de_q][para]
    adv_compa =random.choice(adj_liste) #choix de lexique comparatif
    if para == "max":
        reponse = max(candidat_1,key = candidat_1.get)  #choix de réponse correcte selon "la plus grande valeur " ou "la plus petite valeur"
    else:
        reponse = min(candidat_1,key = candidat_1.get)
    
    #liste de patrons pour ce type de question
    liste_patron = {
     "fr": [
           " Quel(le) %s %s %s ? " % (label_theme,predicat, adv_compa),
           " Le(a) %s qui %s %s est...? " % (label_theme,predicat, adv_compa),
           " Parmi toutes les réponses suivantes, laquelle a %s %s ?"%(predicat, adv_compa)
     
        ],
     "en": [
           " Which %s %s %s ?" % (label_theme, predicat, adv_compa),
           " The %s %s %s %s is ... ? " % (label_theme,random.choice(["which", "that"]),predicat,adv_compa),
           "Among the following answers, which one %s %s ?" %(predicat,adj_compa)
         
     ] ,  
     "zh": [
           "下列哪一个%s的%s%s?"%(label_theme,predicat,adv_compa),
           "下列选项中, 拥有%s的%s的%s是...?"%(adj_compa,predicat,label_theme),
           "在下列%s中, 哪一个的%s%s?"%(label_theme,predicat,adv_compa)
     ]   
    
     
    }
    patron = random.choice(liste_patron[lan_de_q])
    question =  patron      
    Q_A["question"]=patron #verbalisation de question
    Q_A["responses"]= liste_reponse #réponses candidates
    Q_A["reponse correcte"] = reponse #réponse correcte
    return Q_A


# In[30]:


#retourne dans un ensembre de paires candidates, les paires dont le nombre d'élément dans l'objet est >= 3, et on choisit 3 éléments dans l'objet 
#pour former de nouvelles paires
def get_objet_3(candidat):
    candidat_new = { }
    for k,v in candidat.items():
        if len(v)>= 3:
            candidat_new[k] = random.sample(v,3)
    return candidat_new


# In[31]:


def generation_question_objet_non(predicat_id,lan_de_q,candidat):#génération de question du type : trouver un élément qui ne fait pas partie de
                                                                 #élements dans l'objet
        
    predicat = random.choice(donnee_predicat[predicat_id]["alias"][lan_de_q]) #verbalisation de prédicat
    label_theme = random.choice(donnee_entite["appelation"][lan_de_q]) #verbalisation de thème 
    liste_objet = [ ]
    candidat_1 = get_objet_3(candidat) #retourne dans l'ensembre de paires candidates, les paires dont le nombre d'élément dans l'objet est >= 3
    Q_A = { }
    
    sujet = random.choice(list(candidat_1))#paire(sujet) visée
    liste_reponse = candidat_1[sujet]
    for k,v in candidat.items():
        for ele in v:
            if ele not in candidat[sujet]:
                liste_objet.append(ele) #on garantit que les réponses corretes candidates ne sont pas dans l'objet de la paire visée
    
    reponse = random.choice(list(set(liste_objet).difference(set(liste_reponse)))) #choix d'une réponse candidate
    liste_reponse.append(reponse) #liste_reponse
    
    #liste de patron
    liste_patron = {
     "fr": [
           " Quelle réponse suivante ne fait pas partie de %s de %s ? " % (predicat, sujet),
           " La réponse qui n'est pas %s de %s est ...?"%(predicat,sujet)
           
        ],
     "en": [
              "Which following answer is not the %s of %s ?"%(predicat,sujet),
              "The answer which doesn't belong to the %s of %s is ...?"%(predicat,sujet)
     ] ,  
     "zh": [
             "下列哪一个%s不%s%s的%s"%(random.choice(["答案","选项"]),random.choice(["属于","是"]),sujet,predicat)
     ]   
    
     
    }
    patron = random.choice(liste_patron[lan_de_q])
    Q_A["question"]=patron #verbalisation de question
    Q_A["responses"]= liste_reponse #réponses candidates
    Q_A["reponse correcte"] = reponse #réponse correcte
    return Q_A


# In[32]:


def generation_question_objet_oui(predicat_id,lan_de_q,candidat):#génération de question du type : trouver un élément qui fait partie de
                                                                 #élements dans l'objet
    predicat = random.choice(donnee_predicat[predicat_id]["alias"][lan_de_q]) #verbalisation de prédicat
    liste_objet = [ ]
    Q_A = { }
    
    
    
    for k,v in candidat.items():
        for ele in v:
            liste_objet.append(ele) #liste de tous les éléments dans l'objet
            
    sujet = random.choice(list(candidat)) #choix de paire visée, verbalisation de sujet
    reponse = random.choice(candidat[sujet]) #une réponse correcte 
    
    liste_reponse = random.sample(list(set(liste_objet).difference(set(candidat[sujet]))),3) #choix de 3 réponses incorrecte(ceux qui ne sont
                                                                                            # pas dans l'objet de la paire visée)
    liste_reponse.append(reponse)
    
    #liste de patron
    liste_patron = {
     "fr": [
           " Quelle réponse suivante fait partie de %s de %s ? " % (predicat, sujet),
           " La réponse qui est %s de %s est ...?"%(predicat,sujet)
           
        ],
     "en": [
              "Which following answer is the %s of %s ?"%(predicat,sujet),
              "The answer which belongs to the %s of %s is ...?"%(predicat,sujet)
     ] ,  
     "zh": [
             "下列哪一个%s%s%s的%s"%(random.choice(["答案","选项"]),random.choice(["属于","是"]),sujet,predicat)
     ]   
    
     
    }
    patron = random.choice(liste_patron[lan_de_q])
    Q_A["question"]=patron #verbalisation de question
    Q_A["responses"]= liste_reponse #réponses candidates
    Q_A["reponse correcte"] = reponse #réponse correcte
    return Q_A


# In[33]:


liste_lexique_compa = {"max" : { "fr" : "plus de",
                 "en" : "more",
                 "zh" : "最多"
               },
       "min" :{ "fr" : "moins de",
                 "en" : "less",
                 "zh" : "最少"
               }
       } #lexique pour la comparaison sur le nombre 
def generation_question_objet_compa(predicat_id,lan_de_q,candidat,para):#génération du type de question : trouver le sujet qui a 
                                                            #plus(para =max)/moins(para = min) d'entité dans l'objet
    Q_A = { }
    predicat = random.choice(donnee_predicat[predicat_id]["alias"][lan_de_q]) #verbalisation de prédicat
    label_theme = random.choice(donnee_entite["appelation"][lan_de_q]) #verbalisation de thème
    lex_compa = liste_lexique_compa[para][lan_de_q] #verbalisation de lexique comparatif
    candidat_1 = get_objet_nombre(candidat) #obtient le nombre d'élément dans l'objet
    liste_reponse = list(candidat_1) #reponses candidates
    ranking = sorted(candidat_1.items(), key=lambda x: x[1], reverse=True) #ordre descendant selon le nombre d'élément dans l'objet
    if para == "max": #choix de réponse correcte selon le "para" 
        reponse = ranking[0][0] #le plus nombreux
        lex_compa = liste_lexique_compa[para][lan_de_q]
    else:
        reponse = ranking[3][0] #le moins nombreux
     
    #liste de patrons
    liste_patron = {
     "fr": [
           " Quel(le) %s %s %s %s que les autres ? " % (label_theme,random.choice(["a", "possède"]), lex_compa,predicat),
           " Le(a) %s qui %s %s %s que les autres est.. ? "%(label_theme,random.choice(["a", "possède"]), lex_compa,predicat),
           " Quel(le) est le(la) %s qui %s %s %s ?"%(label_theme,random.choice(["a", "possède"]), lex_compa,predicat)
           
        ],
     "en": [
              "Which following %s %s %s %s than the others ?"%(random.choice([label_theme,"answer"]), random.choice(["has", "owns"]),lex_compa,predicat),
              "The %s which %s %s %s than the others is ... ? "%(random.choice([label_theme,"answer"]), random.choice(["has", "owns"]),lex_compa,predicat),
              "Which is the %s that %s %s %s ?" %(random.choice([label_theme,"answer"]), random.choice(["has", "owns"]),lex_compa,predicat)
     
     ],
      "zh" : ["下列哪一个%s有%s的%s ?"%(random.choice([label_theme,"选项"]),lex_compa,predicat),
              "下列哪一个%s的%s%s ?" % (random.choice([label_theme,"选项"]),predicat,lex_compa)
            
          
      ]
    
    }
        
    patron = random.choice(liste_patron[lan_de_q])
    Q_A["question"]=patron #verbalisation de question
    Q_A["responses"]= liste_reponse #réponses candidates
    Q_A["reponse correcte"] = reponse #réponse correcte
    return Q_A
                                                     


# In[34]:


def generation_question_objet_nb(predicat_id,lan_de_q,candidat):#génération du type de question : trouver le nomhre d'élément dans l'objet pour une entité
    Q_A = { }
    predicat = random.choice(donnee_predicat[predicat_id]["alias"][lan_de_q]) #verbalisation de prédicat
    
    candidat_1 = get_objet_nombre(candidat) #obtient le nombre d'éléments dans l'objet
    sujet = random.choice(list(candidat_1)) #verbalisation de sujet, choix de paire visée
    reponse =  candidat_1[sujet] #réponse correcte
    liste_reponse = [reponse] #liste de réponses candidates
    
    for k,v in candidat_1.items( ):
        if k != sujet:
            if v not in liste_reponse:
                liste_reponse.append(v) #on ajoute le nombre d'éléments dans les autres ojets dans la liste de réponse candidates
            else:
                liste_reponse.append(v+1) # on incrémente le nombre de 1 en cas de deux nombres identiques
    #liste de patrons
    liste_patron = {
     "fr": [
           "Quel est le nombre de %s pour %s ?"%(predicat,sujet),
           "Combien de %s %s %s ? " %(predicat,random.choice(["a","possède"]),sujet)
           
        ],
     "en": [ "Which is the number of %s for %s ?"%(predicat,sujet),
             "How many %s does %s %s ?" %(predicat, sujet, random.choice(["own","have"]))
              
     ],
      "zh" : [
             "%s的%s的数量是...? "%(sujet,predicat), 
             "%s有几个%s? "%(sujet,predicat)
      ]
    
    }
     
    patron = random.choice(liste_patron[lan_de_q])
    Q_A["question"]=patron #verbalisation de question
    Q_A["responses"]= liste_reponse #réponses candidates
    Q_A["reponse correcte"] = reponse #réponse correcte
    return Q_A


# In[35]:


# dans les cellules suivantes sont présentées des fonctions pour générer des phrases affirmatives, comparatives et négatives (correctes ou incorrectes)


def get_deux_paire(id_target,liste_id_entite,liste_id_predicat,donnee_predicat,lan_de_q): #génération de deux paires 'sujet:objet'
                                                                                        #avec le même prédicat, qui seront utilisées pour la génération de phrases
    sujet = donnee_entite["libelle"][id_target][lan_de_q] #choix d'entité visée
    paire = { }
    response = [ ]
    id_predi = liste_id_predicat
    while len(paire)< 1: #génération de la première paire avec l'entité visée
                         #la boucle permet de gérer la situation où l'on ne trouve pas de réponse avec un certain prédicat
        predicat_id = random.choice(id_predi) #choix de prédicat
        predicat = random.choice(donnee_predicat[predicat_id]["alias"][lan_de_q])
        query = " SELECT ?item ?itemLabel ?pic WHERE { wd:%s  wdt:%s ?item SERVICE wikibase:label { bd:serviceParam wikibase:language '%s '}} " %(id_target,predicat_id,lan_de_q)
        reponse =  get_resultat(query) #obtention de résultat
        if len(reponse) != 0 and len(gestion_objet(sujet,reponse)) != 0: #gestion de l'objet
            paire[sujet]  = gestion_objet(sujet,reponse) 
    while len(paire) <2 : #génération de la première paire avec l'autre entité, et le même prédicat
                           #la boucle permet de gérer la situation où l'on ne trouve pas de réponse avec une certaine entité
        id_entite_2 = random.choice(list(set(liste_id_entite).difference(set([id_target]))))
        sujet_2 = donnee_entite["libelle"][id_entite_2][lan_de_q]
        query = " SELECT ?item ?itemLabel ?pic WHERE { wd:%s  wdt:%s ?item SERVICE wikibase:label { bd:serviceParam wikibase:language '%s '}} " %(id_entite_2,predicat_id,lan_de_q)
        reponse =  get_resultat(query)
        if len(reponse) != 0 and len(gestion_objet(sujet,reponse)) != 0:
            paire[sujet_2]  = gestion_objet(sujet,reponse) #gestion de l'objet
    type_p = donnee_predicat[predicat_id]["type"] #type de prédicat
    
    paire_1 = gestion_candidat (paire, type_p,lan_de_q) #gestion de paires(type de donnée temps, ajout d'unité),
                                                        #pour générer des phrases non comparables
    paire_1["predicat_id"] = predicat_id #on ajoute l'information de prédicat pour la génération de phrase
    paire_2 = { } 
    if type_p in liste_comparable:
        paire_2 = gestion_candidat_compa (paire, type_p)
        paire_2["predicat_id"] = predicat_id #on génère le deuxième ensemble de deux paires qui seront utilisés pour la génération de phrase
                                            #comparative, quand le type de prédicat est comparable, sinon, le deuxière ensemble est vide
    p = { }
    p["p1"] = paire_1
    p["p2"] =paire_2 #on obtient deux ensembre de deux paires
    return p
#exemple : 
#  {'p1': {'Chennai': '1639', 'Istanbul': '666BC', 'predicat_id': 'P571'},
 #  'p2': {'Chennai': 16390101, 'Istanbul': -6660101, 'predicat_id': 'P571'}}
#avec le prédicat date de création
#p1 permet : La date de fondation de Chennai n'est pas 666BC
#P2 permet : Chennai a été fondé plus tard que Istanbul


# In[36]:


def generation_phr_correct_affirm(deux_triplet,donnee_predicat,lan_de_q): #génération d'une phrase correcte affirmative sur une entité
    
    sujet = list(deux_triplet)[0] #verbalisation de sujet (p1):
    objet = deux_triplet[sujet] #verbalisation d'objet(p&)
    prep = ""
    #determination de type de phrase selon le caractéristique de prédicat
    predicat_id = deux_triplet["predicat_id"]
    type_predicat = donnee_predicat[predicat_id]["type"]
    type_phr = ["spo","spo_inverse"] 
    if donnee_predicat[predicat_id]["verbal"] != "":
        type_phr.append("spo_vb")#la phrase pourrait être verbale si le prédicat a des alias verbaux 
    type_p = random.choice(type_phr) #choix aléatoire de type de phrase
    
    #génération de phrase avec des patron
    if type_p == "spo_vb":
        predicat = random.choice(donnee_predicat[predicat_id]["verbal"][lan_de_q])
        prep = liste_prep[type_predicat][lan_de_q]
    else:
        predicat = random.choice(donnee_predicat[predicat_id]["alias"][lan_de_q])
    liste_patron ={
                   "spo"  : {
                             "fr" : "Le(a) %s de %s est %s."%(predicat,sujet,objet), #ex. La capitale de France est Paris.
                             "en" : "The %s of %s is %s."%(predicat,sujet,objet),
                             "zh" : "%s的%s是%s."%(sujet,predicat,objet)
                           },
                    "spo_inverse" : {
                          "fr" : "%s est %s de %s. " %(objet,predicat,sujet), #Paris est capitale de France
                          "en" : "%s is the %s of %s."%(objet,predicat,sujet),
                          "zh" : "%s是%s的%s"%(objet,sujet,predicat)
                    },
                    "spo_vb" : {
                          "fr" : "%s %s %s %s. " %(sujet,predicat,prep,objet), #Paris se situe en France
                          "en" : "%s %s %s %s. " %(sujet,predicat,prep,objet),
                          "zh" :"%s %s %s." %(sujet,predicat,objet)
                    
                    }
                        
                    
                    
      }
    phrase = liste_patron[type_p][lan_de_q] #génération d'une phrase
    return phrase


# In[37]:


def generation_phr_correct_neg(deux_triplet,donnee_predicat,lan_de_q):#génération d'une phrase correcte négative sur une entité
    sujet_1 = list(deux_triplet)[0] #verbalisation de sujet(p1)
    objet_1 = deux_triplet[sujet_1]
    
    sujet_2 = list(deux_triplet)[1]
    objet_2 = deux_triplet[sujet_2] #verbalisation d'objet(p2)
    
    predicat_id = deux_triplet["predicat_id"]
    predicat = random.choice(donnee_predicat[predicat_id]["alias"][lan_de_q]) #verbalisation de prédicat
    
    

    
    type_phr = ["spo","spo_inverse"]
    type_p = random.choice(type_phr) #choix de type de phrase
    
    #liste de patrons pour des phrases négatives
    liste_patron ={
                   "spo"  : {
                             "fr" : "Le(a) %s de %s n'est pas %s."%(predicat,sujet_1,objet_2), #La capitale de France n'est pas Pékin.
                             "en" : "The %s of %s is not %s."%(predicat,sujet_1,objet_2),
                             "zh" : "%s的%s不是%s."%(sujet_1,predicat,objet_2)
                           },
                    "spo_inverse" : {
                          "fr" : "%s n'est pas %s de %s. " %(objet_2,predicat,sujet_1), #Pélin n'est pas capitale de France
                          "en" : "%s is not the %s of %s."%(objet_2,predicat,sujet_1),
                          "zh" : "%s不是%s的%s"%(objet_2,sujet_1,predicat)
                    }
           
                    
      }
     
    phrase = liste_patron[type_p][lan_de_q] #génération d'une phrase
    return phrase


# In[38]:


liste_lex_compa = {
  "temps" : {"fr" : {"max" : [ "plus récent(e)", "moins ancien(ne)"],
                    "min" : [ "plus ancien(ne)", "moins récent(e)"]
                    },
			"en" : {"max" : [ "more recent"],
                     "min" : [ "earlier"]
                    },
			"zh" : {"max" : [ "更晚"],
                     "min" : [ "更早"]
                    }
			
			},

 "hauteur" : {"fr" : {"max" : [ "plus haut(e)", "plus élevé(e)", "moins bas(se)"],
                      "min" : [ "plus bas(se)", "moins élevé(e)", "moins haut(e)"]
                    },
			"en" : {"max" : [ "higher"],
                    "min" : [ "lower"]
                    },
			"zh" : {"max" : [ "更高"],
                     "min" : [ "更低","更矮"]
                    }
			
			 },

  "superficie" : {"fr" : {"max" : [ "plus grand(e)", "moins petit(e)"],
                          "min" : [ "plus petit(e)", "moins grand(e)"]
                    },
			      "en" : {"max" : [ "bigger"],
                          "min" : [ "smaller"]
                    },
			      "zh" : {"max" : [ "更大"],
                         "min" : [ "更小"]
                         }
			
			 },
	"quantité" : {"fr" : {"max" : [ "plus nombreux(se)"],
                          "min" : [ "moins nombreux(se)"]
                    },
			      "en" : {"max" : [ "more numerous"],
                          "min" : [ "less numerous"]
                    },
			      "zh" : {"max" : [ "更多"],
                         "min" : [ "更少"]
                         }
                 },
	"longueur" : {"fr" : {"max" : [ "plus long(ue)"],
                          "min" : [ "plus court(e)","moins court(e)"]
                    },
			      "en" : {"max" : [ "longer"],
                          "min" : [ "shorter"]
                    },
			      "zh" : {"max" : [ "更长"],
                         "min" : [ "更短"]
                         }
					
                 },
    "taux" : {"fr" : {"max" : [ "plus élevé"],
                          "min" : [ "plus bas"]
                    },
			      "en" : {"max" : [ "higher"],
                          "min" : [ "lower"]
                    },
			      "zh" : {"max" : [ "更高"],
                         "min" : [ "更低"]
                         }
					
                 },
			 

} #lexique comparatif pour générer une phrase selon le type de prédicat





def generation_phr_correct_compa(deux_triplet,donnee_predicat,lan_de_q): #génération d'une phrase comparative correcte
   
    sujet_1 = list(deux_triplet)[0] #verbalisation de sujet_1(p1)
    objet_1 = deux_triplet[sujet_1] #valeur numérique pour l'objet 1
    
    sujet_2 = list(deux_triplet)[1] #verbalisation de sujet_1(p2)
    objet_2 = deux_triplet[sujet_2] #valeur numérique pour l'objet 2
    
    predicat_id = deux_triplet["predicat_id"]
    predicat = random.choice(donnee_predicat[predicat_id]["alias"][lan_de_q]) #verbalisation de prédicat
    
    type_predicat = donnee_predicat[predicat_id]["type"]
    type_phr = ["spo","spo_inverse"]   
   
    type_p = random.choice(type_phr) #choix de type de phrase
    if type_p == "spo":
        if objet_1>objet_2 :
            lex_compa =  random.choice(liste_lex_compa[type_predicat][lan_de_q]["max"]) #choix de lexique comparatif selon la comparaison
                                                                  #entre les deux objets et le type de prédicat
        else:
            lex_compa = random.choice(liste_lex_compa[type_predicat][lan_de_q]["min"])
            
    if type_p == "spo_inverse":
        if objet_1>objet_2 :
            lex_compa =  random.choice(liste_lex_compa[type_predicat][lan_de_q]["min"])
        else:
            lex_compa = random.choice(liste_lex_compa[type_predicat][lan_de_q]["max"])
    liste_patron ={
                   "spo"  : {
                             "fr" : "Le(a) %s de %s est %s que %s."%(predicat,sujet_1,lex_compa,sujet_2),
                                      # La population de France est moins nombreuse que la Chine.  (lex_compa : min)
                             "en" : "The %s of %s is %s than %s."%(predicat,sujet_1,lex_compa,sujet_2),
                             "zh" : "%s的%s比%s%s."%(sujet_1,predicat,sujet_2, lex_compa)
                           },
                    "spo_inverse" : {
                          "fr" : "Le(a) %s de %s est %s que %s."%(predicat,sujet_2,lex_compa,sujet_1),
                                # La population de Chine est plus nombreuse que la France.  (lex_compa : max)
                          "en" : "The %s of %s is %s than %s."%(predicat,sujet_2,lex_compa,sujet_1),
                          "zh" : "%s的%s比%s%s."%(sujet_2,predicat,sujet_1, lex_compa)
                   
                    }
                    
      }
     
    phrase = liste_patron[type_p][lan_de_q] #génération d'une phrase
    return phrase


# In[39]:


def generation_phr_incorrect_affirm(deux_triplet,donnee_predicat,lan_de_q): #génération d'une phrase incorrecte affirmative
   
    sujet_1 = list(deux_triplet)[0]
    objet_1 = deux_triplet[sujet_1]
    
    sujet_2 = list(deux_triplet)[1]
    objet_2 = deux_triplet[sujet_2] #comparé avec le processus pour générer une phrase affirmative incorrecte, on utilise l'objet de la p2
                                   # pour la génération de phrase. Le reste est le même. 
    
    predicat_id = deux_triplet["predicat_id"]
    type_predicat = donnee_predicat[predicat_id]["type"]
    type_phr = ["spo","spo_inverse"]   
    prep = ""
    
    if donnee_predicat[predicat_id]["verbal"] != "":
        type_phr.append("spo_vb")
    type_p = random.choice(type_phr)
    if type_p == "spo_vb":
        predicat = random.choice(donnee_predicat[predicat_id]["verbal"][lan_de_q])
        prep = liste_prep[type_predicat][lan_de_q]
    else:
        predicat = random.choice(donnee_predicat[predicat_id]["alias"][lan_de_q])
    liste_patron ={
                   "spo"  : {
                             "fr" : "Le(a) %s de %s est %s."%(predicat,sujet_1,objet_2), #La capitale de France est Pékin.
                             "en" : "The %s of %s is %s."%(predicat,sujet_1,objet_2),
                             "zh" : "%s的%s是%s."%(sujet_1,predicat,objet_2)
                           },
                    "spo_inverse" : {
                          "fr" : "%s est %s de %s. " %(objet_2,predicat,sujet_1), #Pékin est capitale de France.
                          "en" : "%s is the %s of %s."%(objet_2,predicat,sujet_1),
                          "zh" : "%s是%s的%s"%(objet_2,sujet_1,predicat)
                    },
                    "spo_vb" : {
                          "fr" : "%s %s %s %s. " %(sujet_1,predicat,prep,objet_2),
                          "en" : "%s %s %s %s. " %(sujet_1,predicat,prep,objet_2),
                          "zh" :"%s%s%s." %(sujet_1,predicat,objet_2)
                    
                    }
                        
                    
                    
      }
     
    phrase = liste_patron[type_p][lan_de_q]
    return phrase


# In[40]:


def generation_phr_incorrect_neg(deux_triplet,donnee_predicat,lan_de_q):#génération de phrase négative incorrecte
    #ici, on utilise le sujet et l'objet de la p1 pour générer une phrase négative
    sujet = list(deux_triplet)[0]
    objet = deux_triplet[sujet]
   
    predicat_id = deux_triplet["predicat_id"]
    predicat = random.choice(donnee_predicat[predicat_id]["alias"][lan_de_q])
    type_phr = ["spo","spo_inverse"]
    type_p = random.choice(type_phr)
 
    liste_patron ={
                   "spo"  : {
                             "fr" : "Le(a) %s de %s n'est pas %s."%(predicat,sujet,objet), #La capitale de France n'est Paris.
                             "en" : "The %s of %s is not %s."%(predicat,sujet,objet),
                             "zh" : "%s的%s不是%s."%(sujet,predicat,objet)
                           },
                    "spo_inverse" : {
                          "fr" : "%s n'est pas %s de %s. " %(objet,predicat,sujet), #Paris n'est pas capitale de France.
                          "en" : "%s is not the %s of %s."%(objet,predicat,sujet),
                          "zh" : "%s不是%s的%s"%(objet,sujet,predicat)
                    }
      
                  
                    
      }
    phrase = liste_patron[type_p][lan_de_q]
    return phrase


# In[41]:


def generation_phr_incorrect_compa(deux_triplet,donnee_predicat,lan_de_q): #génération d'une phrase comparative incorrecte 
   
    sujet_1 = list(deux_triplet)[0]
    objet_1 = deux_triplet[sujet_1]
    
    sujet_2 = list(deux_triplet)[1]
    objet_2 = deux_triplet[sujet_2]
    
    predicat_id = deux_triplet["predicat_id"]
    predicat = random.choice(donnee_predicat[predicat_id]["alias"][lan_de_q])
    
    type_predicat = donnee_predicat[predicat_id]["type"]
    type_phr = ["spo","spo_inverse"]   
   
    type_p = random.choice(type_phr)
    if type_p == "spo": 
        if objet_1>objet_2 : #comparé avec le processus pour la génération d'une phrase comparative correcte, ici on choisit le mauvais 
                            #lexique comparatif. Le reste est le même.
            lex_compa =  random.choice(liste_lex_compa[type_predicat][lan_de_q]["min"])
        else:
            lex_compa = random.choice(liste_lex_compa[type_predicat][lan_de_q]["max"])
            
    if type_p == "spo_inverse":
        if objet_1>objet_2 :
            lex_compa =  random.choice(liste_lex_compa[type_predicat][lan_de_q]["max"])
        else:
            lex_compa = random.choice(liste_lex_compa[type_predicat][lan_de_q]["min"])
    liste_patron ={
                   "spo"  : {
                             "fr" : "Le(a) %s de %s est %s que %s."%(predicat,sujet_1,lex_compa,sujet_2),
                                #La population de France est plus nombreuse que Chine. (objet_1<objet_2, lex_compa : max )
                             "en" : "The %s of %s is %s than %s."%(predicat,sujet_1,lex_compa,sujet_2),
                             "zh" : "%s的%s比%s%s."%(sujet_1,predicat,sujet_2, lex_compa)
                           },
                    "spo_inverse" : {
                          "fr" : "Le(a) %s de %s est %s que %s."%(predicat,sujet_2,lex_compa,sujet_1),
                             #La population de Chine est moins nombreuse que France. (objet_1>objet_2, lex_compa : min )
                          "en" : "The %s of %s is %s than %s."%(predicat,sujet_2,lex_compa,sujet_1),
                          "zh" : "%s的%s比%s%s."%(sujet_2,predicat,sujet_1, lex_compa)
                   
                    }
                    
      }
     
    phrase = liste_patron[type_p][lan_de_q]
    return phrase


# In[42]:


def generation_phrase_correct_entite(id_entite,liste_id_entite,liste_id_predicat,donnee_predicat,lan_de_q):#génération d'une phrase correcte sur une entité
    deux_triplet = get_deux_paire(id_entite,liste_id_entite,liste_id_predicat,donnee_predicat,lan_de_q)#génération de p1 p2
    predicat_id = deux_triplet["p1"]["predicat_id"]
    type_predicat = donnee_predicat[predicat_id]["type"]#type de prédicat
    liste_phrase_type = [1,2]
    
    if len (deux_triplet["p2"]) != 0: #si p2 n'est pas vide, c'est à dire une phrase comparative pourrait être générée
        liste_phrase_type.append(3)
    phr_type = random.choice(liste_phrase_type) #choix de type de phrase
    if phr_type == 1: 
        deux_triplet = deux_triplet["p1"]
        phrase = generation_phr_correct_affirm(deux_triplet,donnee_predicat,lan_de_q) #phrase affirmative correcte
    if phr_type == 2:
        deux_triplet = deux_triplet["p1"]
        phrase = generation_phr_correct_neg(deux_triplet,donnee_predicat,lan_de_q)#phrase négative correcte
    if phr_type == 3:
        deux_triplet = deux_triplet["p2"]
        phrase = generation_phr_correct_compa(deux_triplet,donnee_predicat,lan_de_q) # phrase comparative correcte
    return phrase #returne la phrase


# In[43]:


def generation_phrase_incorrect_entite(id_entite,liste_id_entite,liste_id_predicat,donnee_predicat,lan_de_q):#génération d'une phrase incorrecte sur une entité
    deux_triplet = get_deux_paire(id_entite,liste_id_entite,liste_id_predicat,donnee_predicat,lan_de_q)#génération de p1 p2
    predicat_id = deux_triplet["p1"]["predicat_id"]
    type_predicat = donnee_predicat[predicat_id]["type"]
    liste_phrase_type = [1,2]
    
    if len (deux_triplet["p2"]) != 0:#si p2 n'est pas vide, c'est à dire une phrase comparative pourrait être générée
        liste_phrase_type.append(3)
    phr_type = random.choice(liste_phrase_type)#choix de type de phrase
    if phr_type == 1:
        deux_triplet = deux_triplet["p1"]
        phrase = generation_phr_incorrect_affirm(deux_triplet,donnee_predicat,lan_de_q)#phrase affirmative correcte
    if phr_type == 2:
        deux_triplet = deux_triplet["p1"]
        phrase = generation_phr_incorrect_neg(deux_triplet,donnee_predicat,lan_de_q)#phrase négative correcte
    if phr_type == 3:
        deux_triplet = deux_triplet["p2"]
        phrase = generation_phr_incorrect_compa(deux_triplet,donnee_predicat,lan_de_q)# phrase comparative correcte
    liste_id_predicat.remove(predicat_id)
    return phrase#returne la phrase


# In[44]:


#génération de question du type trouver une phrase correcte / incorrecte sur une entité
def generation_question_sur_entite(liste_id_entite,liste_id_predicat,donnee_predicat,lan_de_q):
    Q_A = { }
    id_entite = random.choice(liste_id_entite)
    sujet = donnee_entite["libelle"][id_entite][lan_de_q] #verbalisation de sujet
    type_q = random.choice(["choix_correct","choix_incorrect"])
    if type_q == "choix_correct": #trouver une phrase correcte : génération de 3 phrases incorrectes, 1 phrase correcte
        phr_1 =  generation_phrase_incorrect_entite(id_entite,liste_id_entite,id_predicat,donnee_predicat,lan_de_q)
        phr_2 =  generation_phrase_incorrect_entite(id_entite,liste_id_entite,id_predicat,donnee_predicat,lan_de_q)
        phr_3 = generation_phrase_incorrect_entite(id_entite,liste_id_entite,id_predicat,donnee_predicat,lan_de_q)
        phr_4 = generation_phrase_correct_entite(id_entite,liste_id_entite,id_predicat,donnee_predicat,lan_de_q)
    else:#trouver une phrase correcte : génération de 3 phrases correctes, 1 phrase incorrecte
        phr_1 =  generation_phrase_correct_entite(id_entite,liste_id_entite,id_predicat,donnee_predicat,lan_de_q)
        phr_2 =  generation_phrase_correct_entite(id_entite,liste_id_entite,id_predicat,donnee_predicat,lan_de_q)
        phr_3 = generation_phrase_correct_entite(id_entite,liste_id_entite,id_predicat,donnee_predicat,lan_de_q)
        phr_4 = generation_phrase_incorrect_entite(id_entite,liste_id_entite,id_predicat,donnee_predicat,lan_de_q)
    
    #liste de patron
    liste_patron = {
                     "choix_correct" : {
                         "fr" : [ "Quelle %s suivante sur %s est correcte  ?"%(random.choice(["phrase","affirmation","information"]),sujet),
                                  "Parmis toutes les %s sur %s, laquelle est correcte?"%(random.choice(["phrases","affirmations","informations"]),sujet)
                                 
                                ],
                         "en" :["Which following %s about %s is correct ?"%(random.choice(["phrase","statement","information"]),sujet),
                                "Among all the %s about %s, which one is correct ?"%(random.choice(["phrases","statements","informations"]),
                                                                                     sujet)],
                                    
                         "zh" : ["下列关于%s的说法中,哪一个正确?"%(sujet),
                                 "下列哪一个关于%s的说法正确?"%(sujet),
                                 "下列关于%s的说法中, 正确的是...?"%(sujet)
                                ]
                         
                     },
        
        
                    "choix_incorrect" :{
                        "fr" :[ "Quelle %s suivante sur %s est incorrecte  ?"%(random.choice(["phrase","affirmation","information"]),sujet),
                                "Parmi toutes les %s sur %s, laquelle est incorrecte?"%(random.choice(["phrases","affirmations","informations"]),sujet),
                                 "Quelle %s suivante sur %s n'est pas correcte  ?"%(random.choice(["phrase","affirmation","information"]),sujet),
                                "Parmi toutes les %s sur %s, laquelle n'est pas correcte?"%(random.choice(["phrases","affirmations","informations"]),sujet)
                                ],
                        "en" :["Which following %s about %s is not correct ?"%(random.choice(["phrase","statement","information"]),sujet),
                               "Among all the %s about %s, which one is not correct ?"%(random.choice(["phrases","statements","informations"]),sujet),
                               "Which following %s about %s is incorrect ?"%(random.choice(["phrase","statement","information"]),sujet),
                                "Among all the %s about %s, which one is incorrect ?"%(random.choice(["phrases","statements","informations"]),
                                                                                       sujet)
                              ],
                         "zh" : ["下列关于%s的说法中,哪一个%s?"%(sujet,random.choice(["不正确","是错误的"])),
                                 "下列哪一个关于%s的说法%s?"%(sujet,random.choice(["不正确","是错误的"])),
                                 "下列关于%s的说法中, %s的是...?"%(sujet,random.choice(["不正确","错误"]))
                                ]
                         
                        
                        
                    }
        }
    
    patron = random.choice(liste_patron[type_q][lan_de_q]) #choix de patron
  
 
    
    liste_reponse = [phr_1,phr_2,phr_3,phr_4] #liste de phrases
    random.shuffle(liste_reponse) # on change l'ordre de 4 phrases générés
   
    Q_A["question"]=patron #verbalisation de question
    Q_A["responses"]= liste_reponse #réponses candidates
    Q_A["reponse correcte"] = phr_4 #réponse correcte    
        
    return Q_A
    
        
        
        
        
        


# In[45]:


#génération de question du type trouver une phrase correcte / incorrecte sur un thème
def generation_question_sur_theme(liste_id_entite,liste_id_predicat,donnee_predicat,lan_de_q):
    Q_A = { }
    id_entite = random.choice(liste_id_entite)
    label_theme = random.choice(donnee_entite["appelation"][lan_de_q])
    type_q = random.choice(["choix_correct","choix_incorrect"])
    if type_q == "choix_correct": #une entité différente pour chaque phrase. Le reste est pareil que la gérération question du type trouver une phrase correcte / incorrecte sur une entité
        id_entite = random.choice(liste_id_entite)
        phr_1 =  generation_phrase_incorrect_entite(id_entite,liste_id_entite,id_predicat,donnee_predicat,lan_de_q)
        id_entite = random.choice(liste_id_entite)
        phr_2 =  generation_phrase_incorrect_entite(id_entite,liste_id_entite,id_predicat,donnee_predicat,lan_de_q)
        id_entite = random.choice(liste_id_entite)
        phr_3 = generation_phrase_incorrect_entite(id_entite,liste_id_entite,id_predicat,donnee_predicat,lan_de_q)
        id_entite = random.choice(liste_id_entite)
        phr_4 = generation_phrase_correct_entite(id_entite,liste_id_entite,id_predicat,donnee_predicat,lan_de_q)
    else:#une entité différente pour chaque phrase
        id_entite = random.choice(liste_id_entite)
        phr_1 =  generation_phrase_correct_entite(id_entite,liste_id_entite,id_predicat,donnee_predicat,lan_de_q)
        id_entite = random.choice(liste_id_entite)
        phr_2 =  generation_phrase_correct_entite(id_entite,liste_id_entite,id_predicat,donnee_predicat,lan_de_q)
        id_entite = random.choice(liste_id_entite)
        phr_3 = generation_phrase_correct_entite(id_entite,liste_id_entite,id_predicat,donnee_predicat,lan_de_q)
        id_entite = random.choice(liste_id_entite)
        phr_4 = generation_phrase_incorrect_entite(id_entite,liste_id_entite,id_predicat,donnee_predicat,lan_de_q)
        
    liste_patron = {
                     "choix_correct" : {
                         "fr" : [ "Quelle %s suivante sur les %s est correcte  ?"%(random.choice(["phrase","affirmation","information"]),label_theme),
                                  "Parmi toutes les %s sur les %s, laquelle est correcte?"%(random.choice(["phrases","affirmations","informations"]),label_theme)
                                 
                                ],
                         "en" :["Which following %s about the %s is correct ?"%(random.choice(["phrase","statement","information"]),label_theme),
                                "Among all the %s about the %s, which one is correct ?"%(random.choice(["phrases","statements","informations"]),
                                                                                     label_theme)],
                                    
                         "zh" : ["下列关于%s的说法中,哪一个正确?"%(label_theme),
                                 "下列哪一个关于%s的说法正确?"%(label_theme),
                                 "下列关于%s的说法中, 正确的是...?"%(label_theme)
                                ]
                         
                     },
        
        
                    "choix_incorrect" :{
                        "fr" :[ "Quelle %s suivante sur les %s est incorrecte  ?"%(random.choice(["phrase","affirmation","information"]),label_theme),
                                "Parmi toutes les %s sur les %s, laquelle est incorrecte?"%(random.choice(["phrases","affirmations","informations"]),label_theme),
                                 "Quelle %s suivante sur les %s n'est pas correcte  ?"%(random.choice(["phrase","affirmation","information"]),label_theme),
                                "Parmi toutes les %s sur les %s, laquelle n'est pas correcte?"%(random.choice(["phrases","affirmations","informations"]),label_theme)
                                ],
                        "en" :["Which following %s about the %s is not correct ?"%(random.choice(["phrase","statement","information"]),label_theme),
                               "Among all the %s about the %s, which one is not correct ?"%(random.choice(["phrases","statements","informations"]),label_theme),
                               "Which following %s about the %s is incorrect ?"%(random.choice(["phrase","statement","information"]),label_theme),
                                "Among all the %s about the %s, which one is incorrect ?"%(random.choice(["phrases","statements","informations"]),
                                                                                       label_theme)
                              ],
                         "zh" : ["下列关于%s的说法中,哪一个%s?"%(label_theme,random.choice(["不正确","是错误的"])),
                                 "下列哪一个关于%s的说法%s?"%(label_theme,random.choice(["不正确","是错误的"])),
                                 "下列关于%s的说法中, %s的是...?"%(label_theme,random.choice(["不正确","错误"]))
                                ]
                         
                        
                        
                    }
        }
    
    patron = random.choice(liste_patron[type_q][lan_de_q])
  
  
    
    liste_reponse = [phr_1,phr_2,phr_3,phr_4]
    random.shuffle(liste_reponse)
    Q_A["question"]=patron #verbalisation de question
    Q_A["responses"]= liste_reponse #réponses candidates
    Q_A["reponse correcte"] = phr_4 #réponse correcte    
        
        
    return Q_A   


# In[46]:


liste_theme = {"géographie":["capitale en europe"]}
lan_liste = ["zh","fr","en"]
lan_de_q = random.choice(lan_liste)
theme = "géographie"
dif = random.choice(["facile","moyen","difficile"])
#class_choise = random.choice(liste_theme[theme]) 
#chemin = "thème\%s\%s"%(theme,class_choise)
#chemin_entite = chemin+"\donnee_entite.json"
#chemin_predicat = chemin+"\donnee_predicat.json"
#donnee_predicat = ouvrir_json(chemin_predicat)
#donnee_entite = ouvrir_json(chemin_entite)
#label_theme = random.choice(donnee_entite["appelation"][lan_de_q])


# In[47]:


from time import *


# In[57]:


liste_theme = {"géographie":["capitale en europe","les plus grandes villes dans le monde","les plus grandes villes en Asie",
                            "les plus grandes villes en Chine","les plus grandes villes en Europe","les plus grandes villes en France",
                             "10 millions d'habitants","pays africains","Pays d'Amérique du nord","Pays d'Amérique du sud","pays d'océanie",
                             "pays en asie","pays europeens","rivières"
                            
                            
                            ]} 
lan_liste = ["fr","zh","en"]
lan_de_q = random.choice(lan_liste)#choix de difficulté (ici c'est aléatoire mais on peut tout à fait le fixer selons nos besoins)
theme = "géographie"
dif = random.choice(["difficile","facile","moyen"]) #choix de difficulté (ici c'est aléatoire mais on peut tout à fait le fixer selons nos besoins)
begin_time = time()
class_choise = random.choice(liste_theme[theme])  #choix de thème (ici c'est aléatoire mais on peut tout à fait le fixer selons nos besoins)
#class_choise = "10 millions d'habitants"
chemin = "thème\%s\%s"%(theme,class_choise) #ouvrir les fichiers contenant les informations des entités et prédicats selon le thème choisi
chemin_entite = chemin+"\donnee_entite.json"
chemin_predicat = chemin+"\donnee_predicat.json"
donnee_predicat = ouvrir_json(chemin_predicat)
donnee_entite = ouvrir_json(chemin_entite)
label_theme = random.choice(donnee_entite["appelation"][lan_de_q])#label de thème

if dif == "facile":    #combinaison de liste d'entités et liste de prédicat dans ce thème, les types de questions selon la difficulté 
    type_q = [1,2,3]
    id_entite = donnee_entite["dif"]["populaires"]
    id_predicat = donnee_predicat["populaires"]
if dif == "moyen" :
    type_q = [1,2,3,4,5,6,7,8,9,10]
    cas = random.choice([1,2])
    if cas == 1 :
        id_entite = donnee_entite["dif"]["populaires"]
        id_predicat = donnee_predicat["rares"]
    else:
        id_entite = donnee_entite["dif"]["rares"]
        id_predicat = donnee_predicat["populaires"]
if dif == "difficile":
    cas = random.choice([1,2])
    if cas == 1 :
        cas_ = random.choice([1,2])
        if cas_ == 1:
            id_entite = donnee_entite["dif"]["populaires"]
            id_predicat = donnee_predicat["rares"]
            type_q = [11,12]
        if cas == 2 :
            id_entite = donnee_entite["dif"]["rares"]
            id_predicat = donnee_predicat["populaires"]
            type_q = [11,12]
    elif cas == 2 :
        id_entite = donnee_entite["dif"]["rares"]
        id_predicat = donnee_predicat["rares"]
        type_q = [1,2,3,4,5,6,7,8,9,10]
if type_q == [11,12]: # le cas particulier, quand la difficulté choisie est "difficile", les prédicats et les entités ont des popularités diffiérentes
    quiz_type = random.choice(type_q) #on génère directement le quiz, pas besoin de passer aux étapes suivantes
    if quiz_type == 11: #choix de phrase correcte/incorrecte sur une entité
        quiz = generation_question_sur_entite(id_entite,id_predicat,donnee_predicat,lan_de_q)
    else:#choix de phrase correcte/incorrecte sur un thème
        quiz = generation_question_sur_theme(id_entite,id_predicat,donnee_predicat,lan_de_q)
else: #selon, dans les autres cas 
    predicat_id = random.choice(id_predicat) # choix de prédicat 
    predicat_type = predicat_type = donnee_predicat[predicat_id]["type"] #type de prédicat
    paires_candidates = get_paires_candidates(donnee_entite,id_entite,predicat_id,lan_de_q) # génération de 4 paires candidates
    q_type_pc = trouver_q_type(paires_candidates,predicat_type,predicat_id) # analyse de types de questions disponibles sur ces paires
    q_type_def = list(set(q_type_pc).intersection(set(type_q))) # intersection avec les types exigés par la difficulté des questions
    quiz_type = random.choice(q_type_def) # choix de type de question 
    if quiz_type == 1:# différent fonction sera appliquée, selon le type de question, pour générer une question
        quiz =generation_question_spo(predicat_id,lan_de_q,paires_candidates)
    if quiz_type == 2:
        quiz =generation_question_spo_inverse(predicat_id,lan_de_q,paires_candidates)
    if quiz_type ==3:
        quiz =generation_question_spo_vb(predicat_id,lan_de_q,paires_candidates)
    if quiz_type == 4:
        quiz = generation_question_comparaison(predicat_id,lan_de_q,paires_candidates)
    if quiz_type == 6:
        quiz = generation_question_objet_non(predicat_id,lan_de_q,paires_candidates)
    if quiz_type ==7:
        quiz = generation_question_objet_oui(predicat_id,lan_de_q,paires_candidates)
    if quiz_type ==8:
        quiz = generation_question_objet_compa(predicat_id,lan_de_q,paires_candidates,"max")
    if quiz_type ==9:
        quiz = generation_question_objet_compa(predicat_id,lan_de_q,paires_candidates,"min")  
    if quiz_type ==10:
        quiz = generation_question_objet_nb(predicat_id,lan_de_q,paires_candidates) 
end_time = time()
run_time = end_time-begin_time
print("thème : ", class_choise)
print("difficulté :", dif)
print("question : ", quiz["question"])
print("réponses : ",  quiz["responses"])

print("temps utilisé :", run_time)


# In[58]:


print("réponse correcte : ", quiz["reponse correcte"])


# In[ ]:




