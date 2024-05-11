# Import necessary modules
from encodings import utf_8
from flask import Flask, make_response, url_for, redirect, request, render_template, current_app, g, send_file
import requests 
import json
from sqlalchemy import true
from libs import loadmap
import sqlite3

# Set the encoding
coding = utf_8
# -*- coding: utf-8 -*-

# Define the map name and database name
map_name = 'mapnew.json'
database_name = "_db.db"
table_sensors_name = "sensors"
table_users_name = "users"

# Connect to the SQLite database
con = sqlite3.connect(database_name, uri=true)

# Create tables for sensors and users if they don't exist
con.execute('CREATE TABLE IF NOT EXISTS ' + table_sensors_name + ' (id INTEGER PRIMARY KEY UNIQUE , lng TEXT , ltd TEXT , flood TEXT , status TEXT, road TEXT) ')
con.execute('CREATE TABLE IF NOT EXISTS ' + table_users_name + ' (id INTEGER PRIMARY KEY UNIQUE , name TEXT, phone TEXT , password TEXT) ')

# Load map points and add them to the sensors table if they don't already exist
map = json.load(open(map_name, encoding="utf8"))
for index, point in enumerate(map["points"]):
    # Create a cursor to execute SQL queries
    cur = con.cursor()

    # Check if the current point already exists in the sensors table
    cur.execute('SELECT * FROM ' + table_sensors_name + ' WHERE id = ? ', (point["id"],))
    records = cur.fetchall()

    # If the point doesn't exist in the sensors table, insert a new record
    if len(records) == 0:
        # Determine the flood and status values based on the point data
        flood_status = "closed" if point["flood"] == 1 else "open"
        sensor_status = "down" if "status" in point and point["status"] == 1 else "up"

        # Insert the new record into the sensors table
        con.execute('INSERT INTO ' + table_sensors_name + ' (id, lng, ltd, flood, status, road) VALUES (?,?,?,?,?,?);',
                    (point["id"], point["lng"], point["ltd"], flood_status, sensor_status, point["name"]))
        con.commit()

# Initialize the Flask application
app = Flask(__name__)

# Login route
@app.route("/", methods=["GET", "POST"])
def index():
    # Check if the request method is POST (i.e., a form submission)
    if request.method == 'POST':
        # Connect to the SQLite database
        con = sqlite3.connect(database_name, uri=true)
        cur = con.cursor()

        # Extract the phone and password from the form data
        phone = request.form['phone']
        password = request.form['password']

        # Execute a SQL query to check if the provided phone and password match a record in the users table
        cur.execute('SELECT phone,password FROM ' + table_users_name + ' WHERE phone = ? AND password = ? ', (phone, password))
        results = cur.fetchall()

        # Check if the query returned any results
        if len(results) == 0:
            # If no results, set an error message and render the login template
            errormsg = 'Sorry, Incorrect Credectials. Try Again!'
            return render_template("index.html", errormsg=errormsg)
        else:
            # If the query returned results, render the home template
            return render_template("home.html")

    # If the request method is GET (i.e., a regular page load), render the login template
    return render_template("index.html")
        
# Signup route
@app.route("/signup", methods=["GET", "POST"])
def signup():
    # Check if the request method is POST, indicating a form submission
    if request.method == 'POST':
        # Connect to the SQLite database
        con = sqlite3.connect(database_name, uri=True)
        cur = con.cursor()

        # Retrieve the form data
        name = request.form['name']
        phone = request.form['phone']
        password = request.form['password']

        # Check if the user already exists
        cur.execute('SELECT COUNT(*) FROM ' + table_users_name + ' WHERE phone = ?;', (phone,))
        result = cur.fetchone()
        if result[0] > 0:
            # If the user already exists, display an error message
            errormsg = "You already have an account!"
            return render_template("signup.html", errormsg=errormsg)

        # If the user doesn't exist, insert the new user data into the database
        cur.execute('INSERT INTO ' + table_users_name + ' (name, phone, password) VALUES (?, ?, ?);', (name, phone, password))
        con.commit()

        # Redirect the user to the home page after successful signup
        return render_template("home.html")

    # If the request method is GET, render the signup template
    return render_template("signup.html")
   
# Map route
@app.route("/map", methods=["GET"])
def map():
    # Initialize empty lists for map data
    buildings = []
    roads = []
    best_route = []
    points_map = []
    pSrcID = "-1"
    pDstID = "-1"

    # Load map data based on source and destination IDs provided in the request arguments
    if request.args.get("pSrcID") and request.args.get("pDstID"):
        # If source and destination IDs are provided, use them to load the map data
        pSrcID = request.args.get("pSrcID")
        pDstID = request.args.get("pDstID")
        buildings, roads, best_route, points_map, map_texts, best_route_string = loadmap(map_name, pSrcID, pDstID)
    else:
        # If no source and destination IDs are provided, load the default map data
        buildings, roads, best_route, points_map, map_texts, best_route_string = loadmap(map_name)

    # Render the map template with the loaded map data
    return render_template("map.html",
                           buildings=buildings,
                           roads=roads,
                           best_route=best_route,
                           points_map=points_map,
                           map_texts=map_texts,
                           pSrcID=pSrcID,
                           pDstID=pDstID,
                           best_route_string=best_route_string)

# Point clicked route
@app.route("/point_clicked", methods=["POST"])
def point_clicked():
    # Load the map data from the JSON file
    map = json.load(open(map_name, encoding="utf8"))

    # Toggle the flood status of the clicked point in the map JSON file
    for index, point in enumerate(map["points"]):
        # Check if the current point matches the clicked point
        if point["id"] == request.args.get("point_id"):
            # If the point has a 'flood' property, toggle its value
            if map["points"][index].get('flood'):
                map["points"][index]["flood"] = not map["points"][index]["flood"]
            # If the point doesn't have a 'flood' property, set it to True
            else:
                map["points"][index]["flood"] = True

    # Write the updated map data back to the JSON file
    out_file = open(map_name, "w")
    json.dump(map, out_file)
    out_file.close()

    # Return a success response
    return "0"

# Check path route
@app.route("/check_path", methods=["POST"])
def check_path():
    # Check if the necessary request arguments are provided
    if request.args.get("pSrcID") and request.args.get("pDstID") and request.args.get("best_route_string_return"):
        # Extract the values of the request arguments
        pSrcID = request.args.get("pSrcID")
        pDstID = request.args.get("pDstID")
        best_route_string_return = request.args.get("best_route_string_return")

        # Load the map data using the provided source and destination IDs
        buildings, roads, best_route, points_map, map_texts, best_route_string = loadmap(map_name, pSrcID, pDstID)

        # Check if the best_route_string_return matches the calculated best_route_string
        if best_route_string_return == best_route_string:
            # If the strings match, return "0" to indicate success
            return "0"
    # If the necessary request arguments are not provided or the strings don't match, return "-1" to indicate failure
    return "-1"

# Run the Flask application
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", use_reloader=False, port=5000)
