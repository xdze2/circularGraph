#/usr/bin/env python
# -*- coding:utf-8 -*-

from flask import Flask, request, jsonify
from flask import render_template

from copy import deepcopy
from math import sqrt

import requests
import json

url = "http://kodexlab.com/cnrtl/graph/verb/api/play"

app = Flask(__name__)



# ==============================

@app.route('/')
def accueil():

   return render_template('layout_circular.html', query='tourner' )

@app.route('/<query>/')
def queryPage(query):
   #tagList = sorted(  tagsCounts.iteritems() , key=lambda x : x[1], reverse=True )[:100]
   # nEnfant, enfantList = enfants( 'racine', nbre=30 )
    return render_template('layout_circular.html', query=query )

@app.route('/square/<query>/')
def querySquarePage(query):

    if len( query )<1:
        query = 'tourner'
    return render_template('layout_square.html', query=query )

@app.route('/tournesol/<query>/')
def queryTournesol(query):

    if len( query )<1:
        query = 'tourner'

    return render_template('layout_tournesol.html', query=query )

# -------------------------------------------------------
@app.route('/data/<query>/')
def graphdata(query):
    query = str(query)

    print query

    if len( query ) > 1:
        request = { "query":query }
    else: request = { "query":'tourner' }

    res = requests.get(url, data=json.dumps(request), headers={"content-type":"application/json"})
    data = res.json()

    if not data["results"]:
        return "no result"
    # ### Formatage pour le graph circulaire


    # In[8]:

    myData = {}

    myData['links'] = data['results']['graph']['es']
    myData['nodes'] = data['results']['graph']['vs']


    # In[28]:

    # Dico de correspondance:  id local vertex -> id du cluster
    clusters_id = {}
    for id_cluster , c in enumerate( data['results']['clusters']['clusters'] ):
        for i, vertex_id in enumerate( c['vids'] ):
            clusters_id[vertex_id] = id_cluster 
            
    #print clusters_id
    myData['clusters_id'] = clusters_id


    # In[29]:

    # Enregistre le cluster_id pour chaque  node
    #  et créer un dico idLoc -> idGraph 

    loc2graph = {}

    for i, node in enumerate( myData['nodes'] ):
        myData['nodes'][i]['cluster_id'] = clusters_id[ node['id'] ]
        loc2graph[ node['id'] ]  = node['gid']


    # In[30]:

    # Enregistre les Graph_id dans les dico "liens"
    for i, link in enumerate( myData['links'] ):
        myData['links'][i]['gid_s'] =  loc2graph[ link['s'] ]
        myData['links'][i]['gid_t'] =  loc2graph[ link['t'] ]
        
        a = [ loc2graph[ link['s'] ], loc2graph[ link['t'] ]]
        myData['links'][i]['id'] =  str( min(a) )+ str( max(a) )  #astuce pour créer un identifiant unique de chaque lien


    # In[31]:

    # Retrouve et Enregistre la requête
    myData['query'] = None
    q = data['results']['query']
    for n in myData['nodes']:
        if n['lemme'] == q:
            myData['query'] = n
            print n['lemme']
            
    print myData['query']

    # --- retrouve l'id du cluster de la requete ---
    id_cluster_query = myData['clusters_id'][ myData['query']['id'] ]
    print ' id cluster de la requete: ', id_cluster_query


    # In[33]:

    # créer une liste ordonnées des Noeux, en inserrant les espaces vide entre les clusters
    # donne l'angle  : theta = iDelta * delta   en fonction de l'id du noeud
    # dico{ key= vertex id   , value= iDelta  }
    # Place la requete à un bout,    avec son cluster

    # on place le cluster de la requete au debut :
    c_list = data["results"]['clusters']['clusters']
    c_list.insert( 0, c_list.pop( id_cluster_query ) ) 

    # on place la requete en haut de son cluster ...
    c_list[0]['vids'].append(  c_list[0]['vids'].pop( c_list[0]['vids'].index(myData['query']['id']) ) )


    # In[34]:

    print c_list[0]['vids']


    # In[36]:

    iDelta = {}
    i = 0

    for c in  c_list :
        for vId in c['vids']:
            #if vId == myData['query']['id']:
            #    continue
            iDelta[ vId ] = i
            i = i + 1
        i = i + 1 # espace vide entre cluster
        
    nNodes = i - 1
    print nNodes

    myData['iDelta'] = iDelta
    myData['nNodes'] = nNodes


    # In[39]:

    # Enregistre les iDelta dans le dico Nodes
    for v in myData['nodes']:
        v['iDelta'] = iDelta[  v['id'] ]
        
    print myData['nodes'][:2]

    # Enregistre les iDelta dans le dico Links
    for i, link in enumerate( myData['links'] ):
        myData['links'][i]['iDelta_s'] =  iDelta[ link['s'] ]
        myData['links'][i]['iDelta_t'] =  iDelta[ link['t'] ]
        
    print myData['links'][:2]


    # In[32]:

    # --- Manage les types de liens ---
    for i, edge in enumerate( myData['links'] ):
        if edge['s']==myData['query']['id'] or edge['t']==myData['query']['id']:
            myData['links'][i]['type'] = 'query'
        elif clusters_id[ edge['s'] ] == clusters_id[ edge['t'] ]:
            myData['links'][i]['type'] = 'intra'
        else:
            myData['links'][i]['type'] = 'inter'

    #print myData['links']


    # In[33]:

    # --- Compte les liens sur le graph 'local' ---
    degreeDic = {}
    for link in myData['links']:
        
        degreeDic[ link['s'] ] = degreeDic.get( link['s'], 0 ) + 1
        degreeDic[ link['t'] ] = degreeDic.get( link['t'], 0 ) + 1

    print degreeDic

    # enregistre les valeurs dans le dico Nodes
    for v in myData['nodes']:
        v['deg_loc'] = degreeDic[  v['id'] ]


    return jsonify(**myData)
    


# -------------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True)


