import cv2 
import numpy as np
import math
import json



def loadmap(map_name,pSrcID = "9",pDstID = "10"): 
    map = json.load(open(map_name, encoding="utf8"))   
    buildings = []
    roads = []
    best_route = []
    best_route_string = ""
    # flood_points = []
    points_map = []
    map_texts = []
    width = 800
    height = 600
    map_center = {"lng":21.477027745623726,"ltd": 39.25118148176732 } 
    blank_image = np.ones((height,width,3), np.uint8)
    scale = 380000

    widthf = 800.0
    heightf = 600.0
    font_size = 1


    # points
    for point in map["points"]:
        # if point.get('flood') == True:
        x1 = int( ( point["lng"] - map_center["lng"] ) * scale + width/2 )
        y1 = int( ( point["ltd"] - map_center["ltd"] ) * scale + height/2 )
        points_map.append([x1,y1,point.get('flood'),point["id"]])
     
    # print(points_map)

    # draw builings
    for building in map["buildings"]:
        x1 = int( (building["points"][0]["lng"] - map_center["lng"]) * scale + width/2 )
        y1 = int( (building["points"][0]["ltd"] - map_center["ltd"]) * scale + height/2 )
        x2 = int( (building["points"][1]["lng"] - map_center["lng"]) * scale + width/2 )
        y2 = int( (building["points"][1]["ltd"] - map_center["ltd"]) * scale + height/2 )
        x3 = int( (building["points"][2]["lng"] - map_center["lng"]) * scale + width/2 )
        y3 = int( (building["points"][2]["ltd"] - map_center["ltd"]) * scale + height/2 )
        x4 = int( (building["points"][3]["lng"] - map_center["lng"]) * scale + width/2 )
        y4 = int( (building["points"][3]["ltd"] - map_center["ltd"]) * scale + height/2 )
        building_poly = np.array([[x1,y1],[x2,y2],[x3,y3],[x4,y4]])
        buildings.append([x1,y1,x2,y2,x3,y3,x4,y4])
        cv2.fillPoly(blank_image, pts = [building_poly], color =(150,150,150))

    # draw roads + names
    for road in map["roads"]:
        count = 0
        for points_id in road["points_ids"]: 
            # print(points_id)
            if count > 0: 
                point1 = [x for x in map["points"] if x['id'] == road["points_ids"][count-1]]
                point2 = [x for x in map["points"] if x['id'] == road["points_ids"][count]]
                # print(point1)
                x1 = int( ( point1[0]["lng"] - map_center["lng"] ) * scale + width/2 )
                y1 = int( ( point1[0]["ltd"] - map_center["ltd"] ) * scale + height/2 )
                x2 = int( ( point2[0]["lng"] - map_center["lng"] ) * scale + width/2 )
                y2 = int( ( point2[0]["ltd"] - map_center["ltd"] ) * scale + height/2 )
                roads.append([x1,y1,x2,y2,int(road["width"] * scale)])
                cv2.line(blank_image, ( x1 , y1 ), ( x2 , y2 ), (220,220,220), int(road["width"] * scale ))      
                # print(x1,x2,y1,y2)
                # print(int((x1 + x2)/2) , int((y1 + y2)/2))
                linelength = np.sqrt( (x1-x2)**2 + (y1-y2)**2)
                showTimesOfStreetName = math.ceil( linelength * 6 / width  ) - 1
                if showTimesOfStreetName == 0: 
                    showTimesOfStreetName = 1
                
                if len( road["names"][0]["name"]) > 0:
                    for d in range(showTimesOfStreetName):
                        txt_img_width = font_size * 9 * len( road["names"][0]["name"] )
                        txt_img_height = font_size * 15
                        txt_img = np.zeros((txt_img_width , txt_img_width , 3) , np.uint8)    
                        cv2.putText(txt_img, road["names"][0]["name"],( font_size,int(font_size*7 + txt_img_width/2)  ), cv2.FONT_HERSHEY_PLAIN,font_size, (180,180,180) , 1)
                        if y2-y1 != 0:
                            angle_txt = math.degrees(math.atan((x2-x1)/(y2-y1)))+90
                            if angle_txt > 90:
                                angle_txt += 180
                        else:
                            angle_txt = 90
                        M = cv2.getRotationMatrix2D((txt_img_width/2,txt_img_width/2),angle_txt,1) 
                        rotate_30 = cv2.warpAffine(txt_img,M,(txt_img_width,txt_img_width)) 
                        txt_img_big = np.zeros((height,width,3), np.uint8) 
                        xt = int(x1 + (d+.5) * (x2-x1) / showTimesOfStreetName)
                        yt = int(y1 + 7 + (d+.5) * (y2-y1) / showTimesOfStreetName)  # 5 is the shift down
                        map_texts.append([xt,yt,360-angle_txt,road["names"][1]["name"]])
                        
                        if (xt+txt_img_width < width and yt+txt_img_width < height and xt-txt_img_width > 0 and yt-txt_img_width > 0):
                            txt_img_big[yt-int(txt_img_width/2):yt+int(txt_img_width/2),xt-int(txt_img_width/2):xt+int(txt_img_width/2)] = rotate_30[0:int(txt_img_width/2)*2,0:int(txt_img_width/2)*2]
                            # cv2_imshow(txt_img_big)
                            blank_image = blank_image - txt_img_big
                            # cv2.putText(blank_image, road["names"][0]["name"],( xt,yt  ), cv2.FONT_HERSHEY_PLAIN,font_size, (0,125,125) , 1)
            count += 1

    # cv2_imshow(txt_img)
    # cv2_imshow(rotate_30)
    # cv2_imshow(txt_img_big)

    # draw point
    count = 0
    for point in map["points"]:
        x1 = int( ( point["lng"] - map_center["lng"] ) * scale + width/2 )
        y1 = int( ( point["ltd"] - map_center["ltd"] ) * scale + height/2 )
        
        cv2.putText(blank_image, point["id"] ,( x1 , y1  ), cv2.FONT_HERSHEY_PLAIN,font_size, (100,100,255) , 2)
        count += 1

    # cv2.imshow("blank",blank_image)
    # cv2.waitKey()

    # find all routes



    possible_nexts = {}

    routes = []
    routes.append([pSrcID])

    blocked = False 
    steps_max = 20
    steps_count = 0

    while not blocked and steps_count < steps_max:
        blocked = True
        for r in range(10):
            s = len(routes)
            # print("s",s)
            for ss in range(s):  
                # print("ss",ss)
                # print("routes[ss]",routes[ss])
                # print("routes[ss][-1]",routes[ss][-1])
                possible_nexts = [point['id'] for point in map["points"] for next_id in point['nexts_drive'] if next_id == routes[ss][-1] and not point['id'] in routes[ss] and routes[ss][-1] != pDstID and point.get('flood') != True ]
                # print("possible_nexts",possible_nexts)
                for a in range(len(possible_nexts)):
                    blocked = False
                    steps_count +=1
                    if a==0:
                        routes[ss].append(possible_nexts[a])
                    else:
                        d = routes[ss][:-1]
                        d.append(possible_nexts[a])
                        routes.append( d )

        # print("routes",routes)
        # print("len routes",len(routes))

    good_routes = [route for route in routes if route[-1] == pDstID]
    good_routes_lenghts = []
    shortest_route_num = 0
    shortest_route_dist = 9999
    count2 = 0
    shortest_route = [] 
    for route in good_routes:
        count = 0
        distance = 0
        for points in route:
            if count > 0 :
                point1 = [x for x in map["points"] if x['id'] == route[count-1]]
                point2 = [x for x in map["points"] if x['id'] == route[count]]
                x1 = int( ( point1[0]["lng"] - map_center["lng"] ) * scale + width/2 )
                y1 = int( ( point1[0]["ltd"] - map_center["ltd"] ) * scale + height/2 )
                x2 = int( ( point2[0]["lng"] - map_center["lng"] ) * scale + width/2 )
                y2 = int( ( point2[0]["ltd"] - map_center["ltd"] ) * scale + height/2 )
                distance += math.sqrt( (x1-x2)**2 + (y1-y2)**2 )
            count += 1
        if distance < shortest_route_dist :
            shortest_route_dist = distance
            shortest_route_num = count2
            shortest_route = route
        good_routes_lenghts.append(distance)
        count2 += 1



    # print("good_routes",good_routes)
    # print("len(good_routes)",len(good_routes))

    # print("good_routes_lenghts",good_routes_lenghts)
    # print("len(good_routes_lenghts)",len(good_routes_lenghts))

    # print("shortest_route_num",shortest_route_num)
    # print("shortest_route_dist",shortest_route_dist)

    # draw route

    route_image = np.copy(blank_image)

    count = 0
    route_num = 0
    best_route_string=""
    if len(shortest_route)  > 0:
        best_route_string = shortest_route[0]
        for point in shortest_route : # good_routes[route_num] :
            # print("count",count,"point",point)
            if ( count > 0 ) :
                point1 = [x for x in map["points"] if x['id'] == shortest_route[count-1]] # good_routes[route_num][count-1]]
                point2 = [x for x in map["points"] if x['id'] == shortest_route[count]] # good_routes[route_num][count]]
                x1 = int( ( point1[0]["lng"] - map_center["lng"] ) * scale + width/2 )
                y1 = int( ( point1[0]["ltd"] - map_center["ltd"] ) * scale + height/2 )
                x2 = int( ( point2[0]["lng"] - map_center["lng"] ) * scale + width/2 )
                y2 = int( ( point2[0]["ltd"] - map_center["ltd"] ) * scale + height/2 )
                best_route.append([x1,y1,x2,y2]) 
                best_route_string += "_" + point2[0]['id']
                cv2.line(route_image, ( x1 , y1 ), ( x2 , y2 ), (220,100,100), int(road["width"] * scale ))      
            count += 1
   

    # cv2.imshow("route_image",route_image)
    # cv2.waitKey()
    # print(route)
    return buildings ,  roads ,  best_route , points_map ,map_texts ,best_route_string