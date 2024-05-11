from encodings import utf_8
from flask import Flask, make_response, url_for, redirect, request, render_template, current_app, g, send_file
import requests    # pip install requests
import json
from sqlalchemy import true
from libs import loadmap
import sqlite3

coding = utf_8
# -*- coding: utf-8 -*-

# map_name = 'map.json'
map_name = 'mapnew.json'

database_name = "_db.db"
table_sensors_name = "sensors"
table_admins_name = "admins"
table_users_name = "users"

con = sqlite3.connect(database_name,uri=true)
con.execute('CREATE TABLE IF NOT EXISTS ' + table_sensors_name + ' (id INTEGER PRIMARY KEY UNIQUE , lng TEXT , ltd TEXT , flood TEXT , status TEXT, road TEXT) ')
con.execute('CREATE TABLE IF NOT EXISTS ' + table_admins_name + ' (id INTEGER PRIMARY KEY UNIQUE , email TEXT , password TEXT) ')
con.execute('CREATE TABLE IF NOT EXISTS ' + table_users_name + ' (id INTEGER PRIMARY KEY UNIQUE , phone TEXT , password TEXT, username TEXT) ')

# add the default admins
cur = con.cursor()
cur.execute('INSERT INTO ' + table_admins_name + ' (email,password) VALUES (?,?);',("dana@gmail.com","1234",))
cur.execute('INSERT INTO ' + table_admins_name + ' (email,password) VALUES (?,?);',("asrar@gmail.com","4321",))
cur.execute('INSERT INTO ' + table_admins_name + ' (email,password) VALUES (?,?);',("lama@gmail.com","1234",))
cur.execute('INSERT INTO ' + table_admins_name + ' (email,password) VALUES (?,?);',("lina@gmail.com","4321",))
con.commit()


# add map points to sensors table
map = json.load(open(map_name, encoding="utf8"))
for index,point in enumerate(map["points"]):
    cur = con.cursor()
    cur.execute('SELECT * FROM ' + table_sensors_name + ' WHERE id = ? ', (point["id"],) )
    records = cur.fetchall()
    if len(records) == 0:
        # status is not on the json file
        con.execute('INSERT INTO ' + table_sensors_name + ' (id, lng, ltd, flood, status, road) VALUES (?,?,?,?,?,?);',
            (point["id"], point["lng"], point["ltd"],
             "closed" if point["flood"] == 1 else "open",
            #  chaeck if the sensor was removed
             "down" if "status" in point and point["status"] == 1 else "up",point["name"],))

        con.commit()   

con.close()


app = Flask(__name__)

@app.route("/changeFlood", methods=["POST"])
def changeFlood():
    point_id = request.args["pointid"]
    point_flood = request.args["point_flood"]
    new_point_flood = "open" if point_flood == "closed" else "closed"
    con = sqlite3.connect(database_name,uri=true)
    con.execute('UPDATE ' + table_sensors_name + ' SET flood = ? WHERE id = ? ', (new_point_flood,point_id,) )
    con.commit() 
    con.close()
    return "0"

@app.route("/changeSensor", methods=["POST"])
def changeSensor():
    point_id = request.args["pointid"]
    point_sensor = request.args["point_sensor"]
    new_point_sensor = "up" if point_sensor == "down" else "down"
    con = sqlite3.connect(database_name,uri=true)
    con.execute('UPDATE ' + table_sensors_name + ' SET status = ? WHERE id = ? ', (new_point_sensor,point_id,) )
    con.commit() 
    con.close()
    return "0"

@app.route("/removeSensor", methods=["POST"])
def removeSensor():
    point_id = request.args["pointid"]
    con = sqlite3.connect(database_name, uri=True)
    con.execute('DELETE FROM ' + table_sensors_name + ' WHERE id = ?', (point_id,))
    con.commit()
    con.close()
    return "0"

@app.route("/addSensor", methods=["POST"])
def addSensor():
    intersection_name = request.args["intersection_name"]
    con = sqlite3.connect(database_name, uri=True)
    con.execute('INSERT INTO ' + table_sensors_name + ' ( flood, status, road) VALUES (?,?,?);',
            ("open","pending" ,intersection_name,))

    con.commit()    
    con.close()
    return "0"

@app.route("/manageSensor", methods=["GET"])
def manageSensor():
    sensors_data = []
    con = sqlite3.connect(database_name,uri=true)
    cur = con.cursor()
    cur.execute('SELECT * FROM ' + table_sensors_name)
    records = cur.fetchall()
    for record in records:
        sensors_data.append([record[0],record[3],record[4],record[5]])
    con.close()
    
    return render_template("manageSensor.html",sensors_data = sensors_data)



@app.route("/",methods=["GET", "POST"])
def index():
    if request.method == 'POST':
        con = sqlite3.connect(database_name,uri=true)
        cur = con.cursor()
        email = request.form['email']
        password = request.form['password']

        cur.execute('SELECT email,password FROM ' + table_admins_name + ' WHERE email = ? AND password = ? ', (email, password) )
        results = cur.fetchall()

        if len(results) == 0:
            errormsg = 'Sorry, Incorrect Credectials. Try Again!'
            return render_template("index.html", errormsg=errormsg)
        else:
            return render_template("dashboard.html")
    return render_template("index.html")
        
    

@app.route("/dashboard", methods=["GET"])
def dashboard():
    return render_template("dashboard.html")


@app.route("/map",methods=["GET"])
def map():
    buildings = []
    roads = []
    best_route = []
    points_map = []  
    pSrcID = "-1"
    pDstID = "-1"
    if request.args.get("pSrcID") and request.args.get("pDstID"):
        pSrcID = request.args.get("pSrcID")
        pDstID = request.args.get("pDstID")
        buildings,roads,best_route,points_map,map_texts,best_route_string = loadmap(map_name,pSrcID,pDstID) 
    else:
        buildings,roads,best_route,points_map,map_texts,best_route_string = loadmap(map_name) 

    return render_template("map.html",buildings=buildings,roads=roads,best_route=best_route,points_map=points_map,map_texts=map_texts,pSrcID = pSrcID,pDstID = pDstID , best_route_string =best_route_string)

@app.route("/point_clicked",methods=["POST"])
def point_clicked():
    point_id = request.args["point_id"]
    
    map = json.load(open(map_name, encoding="utf8"))   
    for index,point in enumerate(map["points"]):
        if point["id"] == point_id:
            if map["points"][index].get('flood'):
                map["points"][index]["flood"] = not map["points"][index]["flood"]
            else:
                map["points"][index]["flood"] = True
            new_point_flood = "open" if map["points"][index]["flood"] == False else "closed"
            con = sqlite3.connect(database_name,uri=true)
            con.execute('UPDATE ' + table_sensors_name + ' SET flood = ? WHERE id = ? ', (new_point_flood,point_id,) )
            con.commit()
            con.close()
    out_file = open(map_name, "w")
    json.dump(map , out_file)
    out_file.close()
    
    return "0"

@app.route("/check_path",methods=["POST"])
def check_path():
    if request.args.get("pSrcID") and request.args.get("pDstID") and request.args.get("best_route_string_return"):
        pSrcID = request.args.get("pSrcID")
        pDstID = request.args.get("pDstID")
        best_route_string_return = request.args.get("best_route_string_return")
        buildings,roads,best_route,points_map,map_texts,best_route_string = loadmap(map_name,pSrcID,pDstID)
        if (best_route_string_return == best_route_string):
            return "0"
    return "-1"

if __name__ == "__main__":
    app.run(debug=True,host="0.0.0.0",use_reloader=False,port=5000)
