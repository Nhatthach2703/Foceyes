import cv2 as cv
import mediapipe as mp
import time
import utils, math
import numpy as np
import sqlite3
import os
import datetime

# variables 
frame_counter =0
video_name = ""
CEF_COUNTER =0
TOTAL_BLINKS =0
DISTRACT_COUNTER =0
TOTAL_DISTRACT=0
# constants
CLOSED_EYES_FRAME =3
FONTS =cv.FONT_HERSHEY_COMPLEX

# face bounder indices 
FACE_OVAL=[ 10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136, 172, 58, 132, 93, 234, 127, 162, 21, 54, 103,67, 109]

# lips indices for Landmarks
LIPS=[ 61, 146, 91, 181, 84, 17, 314, 405, 321, 375,291, 308, 324, 318, 402, 317, 14, 87, 178, 88, 95,185, 40, 39, 37,0 ,267 ,269 ,270 ,409, 415, 310, 311, 312, 13, 82, 81, 42, 183, 78 ]
LOWER_LIPS =[61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 308, 324, 318, 402, 317, 14, 87, 178, 88, 95]
UPPER_LIPS=[ 185, 40, 39, 37,0 ,267 ,269 ,270 ,409, 415, 310, 311, 312, 13, 82, 81, 42, 183, 78] 
# Left eyes indices 
LEFT_EYE =[ 362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385,384, 398 ]
LEFT_EYEBROW =[ 336, 296, 334, 293, 300, 276, 283, 282, 295, 285 ]

# right eyes indices
RIGHT_EYE=[ 33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161 , 246 ]  
RIGHT_EYEBROW=[ 70, 63, 105, 66, 107, 55, 65, 52, 53, 46 ]

# iris indices
LEFT_IRIS = [474, 475, 476, 477]
RIGHT_IRIS = [469, 470, 471, 472]
KNOWN_INTEROCULAR_DISTANCE = 6.5  # In centimeters
ASSUMED_FOCAL_LENGTH = 1000       # In pixels (adjust as needed)

map_face_mesh = mp.solutions.face_mesh

# database connection
def findNearestSession():
    with open("data/SessionCount.txt", 'r') as f:
        line = f.read()
        return line

def changeNearestSession():
    with open("data/SessionCount.txt", 'r') as f:
        line = int(f.read())
    with open("data/SessionCount.txt", 'w') as f:
        if line == 4:
            f.write("1")
        else:
            f.write(str(line+1))
database_name = "data/SessionDb.db"
conn = sqlite3.connect(database_name)
cur = conn.cursor()
current_session = ""
def database_work():
    global current_video_dir
    global current_session
    current_video_dir = 'data/Session' + findNearestSession()
    current_session = "SessionTrack" + findNearestSession()
    current_table_drop = "DROP TABLE IF EXISTS " + current_session
    current_table_creat = "CREATE TABLE " + current_session + "(Id INTEGER PRIMARY KEY AUTOINCREMENT, Time TEXT, VideoPath TEXT)"
    for f in os.listdir(current_video_dir):
        os.remove(os.path.join(current_video_dir, f))

    cur.execute(current_table_drop)
    cur.execute(current_table_creat)
    
database_work()
conn.commit()
# camera object 
camera = cv.VideoCapture(0)
# landmark detection function 
def landmarksDetection(img, results, draw=False):
    img_height, img_width= img.shape[:2]
    # list[(x,y), (x,y)....]
    mesh_coord = [(int(point.x * img_width), int(point.y * img_height)) for point in results.multi_face_landmarks[0].landmark]
    if draw :
        [cv.circle(img, p, 2, (0,255,0), -1) for p in mesh_coord]

    # returning the list of tuples for each landmarks 
    return mesh_coord

# Euclaidean distance 
def euclaideanDistance(point, point1):
    x, y = point
    x1, y1 = point1
    distance = math.sqrt((x1 - x)**2 + (y1 - y)**2)
    return distance

# Blinking Ratio
def blinkRatio(img, landmarks, right_indices, left_indices):
    # Right eyes 
    # horizontal line 
    rh_right = landmarks[right_indices[0]]
    rh_left = landmarks[right_indices[8]]
    # vertical line 
    rv_top = landmarks[right_indices[12]]
    rv_bottom = landmarks[right_indices[4]]
    

    # LEFT_EYE 
    # horizontal line 
    lh_right = landmarks[left_indices[0]]
    lh_left = landmarks[left_indices[8]]
    # vertical line 
    lv_top = landmarks[left_indices[12]]
    lv_bottom = landmarks[left_indices[4]]
    
    rhDistance = euclaideanDistance(rh_right, rh_left) + 0.1
    rvDistance = euclaideanDistance(rv_top, rv_bottom) + 0.1

    lvDistance = euclaideanDistance(lv_top, lv_bottom) + 0.1
    lhDistance = euclaideanDistance(lh_right, lh_left) + 0.1

    reRatio = rhDistance/rvDistance
    leRatio = lhDistance/lvDistance

    ratio = (reRatio+leRatio)/2
    return reRatio, leRatio, ratio

# Function to calculate distance from interocular distance
def calculate_distance(interocular_distance):
    distance = (KNOWN_INTEROCULAR_DISTANCE * ASSUMED_FOCAL_LENGTH) / interocular_distance
    return distance

# Eyes Extrctor function,
def eyesExtractor(img, right_eye_coords, left_eye_coords):
    # converting color image to  scale image 
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    
    # getting the dimension of image 
    dim = gray.shape

    # creating mask from gray scale dim
    mask = np.zeros(dim, dtype=np.uint8)

    # drawing Eyes Shape on mask with white color 
    cv.fillPoly(mask, [np.array(right_eye_coords, dtype=np.int32)], 255)
    cv.fillPoly(mask, [np.array(left_eye_coords, dtype=np.int32)], 255)

    # showing the mask 
    # cv.imshow('mask', mask)
    
    # draw eyes image on mask, where white shape is 
    eyes = cv.bitwise_and(gray, gray, mask=mask)
    # change black color to gray other than eys 
    # cv.imshow('eyes draw', eyes)
    eyes[mask==0]=155
    
    # getting minium and maximum x and y  for right and left eyes 
    # For Right Eye 
    r_max_x = (max(right_eye_coords, key=lambda item: item[0]))[0]
    r_min_x = (min(right_eye_coords, key=lambda item: item[0]))[0]
    r_max_y = (max(right_eye_coords, key=lambda item : item[1]))[1]
    r_min_y = (min(right_eye_coords, key=lambda item: item[1]))[1]

    # For LEFT Eye
    l_max_x = (max(left_eye_coords, key=lambda item: item[0]))[0]
    l_min_x = (min(left_eye_coords, key=lambda item: item[0]))[0]
    l_max_y = (max(left_eye_coords, key=lambda item : item[1]))[1]
    l_min_y = (min(left_eye_coords, key=lambda item: item[1]))[1]

    # croping the eyes from mask 
    cropped_right = eyes[r_min_y: r_max_y, r_min_x: r_max_x]
    cropped_left = eyes[l_min_y: l_max_y, l_min_x: l_max_x]
    
    if cropped_right.shape[0] == 0 or cropped_right.shape[1] == 0 or cropped_left.shape[0] == 0 or cropped_left.shape[1] == 0:
        return None, None

    # returning the cropped eyes 
    return cropped_right, cropped_left

# Eyes Postion Estimator 
def positionEstimator(cropped_eye):
    if cropped_eye is None:
        return "Not Found", [utils.GRAY, utils.YELLOW]
    # getting height and width of eye 
    h, w =cropped_eye.shape
    
    # remove the noise from images // có thể bỏ đc 
    gaussain_blur = cv.GaussianBlur(cropped_eye, (9,9),0)
    median_blur = cv.medianBlur(gaussain_blur, 3)


    # applying thrsholding to convert binary_image
    ret, threshed_eye = cv.threshold(median_blur, 130, 255, cv.THRESH_BINARY)
    # ret, threshed_eye = cv.threshold(cropped_eye, 130, 255, cv.THRESH_BINARY)

    # create fixd part for eye with 
    piece = int(w/3) 

    # slicing the eyes into three parts 
    right_piece = threshed_eye[0:h, 0:piece]
    center_piece = threshed_eye[0:h, piece: piece+piece]
    left_piece = threshed_eye[0:h, piece +piece:w]
    
    # calling pixel counter function
    eye_position, color = pixelCounter(right_piece, center_piece, left_piece)

    return eye_position, color 

# creating pixel counter function 
def pixelCounter(first_piece, second_piece, third_piece):
    # counting black pixel in each part 
    right_part = np.sum(first_piece == 0)
    center_part = np.sum(second_piece == 0)
    left_part = np.sum(third_piece == 0)
    
    eye_parts = [right_part, center_part, left_part]

    # getting the index of max values in the list 
    max_index = eye_parts.index(max(eye_parts))
    pos_eye = '' 
    if max_index == 0:
        pos_eye = "RIGHT"
        color = [utils.BLACK, utils.GREEN]
    elif max_index == 1:
        pos_eye = 'CENTER'
        color = [utils.YELLOW, utils.PINK]
    elif max_index == 2:
        pos_eye = 'LEFT'
        color = [utils.GRAY, utils.YELLOW]
    else:
        pos_eye = "Closed"
        color = [utils.GRAY, utils.YELLOW]
        
    return pos_eye, color

# Starting time here
start_time = time.time()

# Variable to store the previous interocular distance
previous_interocular_distance = None

distracted = 0
endtimer_text=""
timer_text=""
ratio_text=""
direction_text=""
total_distraction_text=""
distance_text=""
fps_text=""
distance_to_camera = 0
ret, frame = camera.read()
review = 0

def reviewMode(review_link):
    global camera
    global review
    global TOTAL_DISTRACT
    TOTAL_DISTRACT = 0
    review = 1
    camera = cv.VideoCapture(review_link)

def exitReviewMode(temp):
    global camera
    global review
    global TOTAL_DISTRACT
    TOTAL_DISTRACT = temp
    review = 0
    camera = cv.VideoCapture(0)

def detectionLoop():
    global frame, ret
    global timer_text, endtimer_text
    global ratio_text
    global direction_text
    global total_distraction_text
    global distance_text
    global fps_text
    global frame_counter 
    global video_name 
    global CEF_COUNTER
    global TOTAL_BLINKS 
    global DISTRACT_COUNTER 
    global TOTAL_DISTRACT
    global CLOSED_EYES_FRAME
    global writer
    global timer, distracted, distance_to_camera
    with map_face_mesh.FaceMesh(
    max_num_faces = 1, 
    refine_landmarks=True,
    min_detection_confidence = 0.5,
    min_tracking_confidence = 0.5
) as face_mesh:
        frame_counter = frame_counter + 1 # frame counter
        ret, frame = camera.read() # getting frame from camera 
        if not ret: 
            return 0# no more frames break
        #  resizing frame
        
        frame = cv.resize(frame, None, fx=1.5, fy=1.5, interpolation=cv.INTER_CUBIC)
        frame_height, frame_width= frame.shape[:2]
        rgb_frame = cv.cvtColor(frame, cv.COLOR_RGB2BGR)
        results  = face_mesh.process(rgb_frame)
        
        img_h, img_w = frame.shape[:2]
        
        if results.multi_face_landmarks:
            mesh_coords = landmarksDetection(frame, results, False)
            reRatio, leRatio, ratio = blinkRatio(frame, mesh_coords, RIGHT_EYE, LEFT_EYE)
            
            mesh_points=np.array([np.multiply([p.x, p.y], [img_w, img_h]).astype(int) for p in results.multi_face_landmarks[0].landmark])
            (l_cx, l_cy),l_radius = cv.minEnclosingCircle(mesh_points[LEFT_IRIS])
            (r_cx, r_cy),r_radius = cv.minEnclosingCircle(mesh_points[RIGHT_IRIS])
            center_left = np.array([l_cx, l_cy], dtype=np.int32)
            center_right = np.array([r_cx, r_cy], dtype=np.int32)
            
            # cv.putText(frame, f'ratio {ratio}', (100, 100), FONTS, 1.0, utils.GREEN, 2)
            ratio_text = f'Ratio : {round(ratio,2)}'
            
            # Measure the interocular distance
            left_eye_center = np.array(mesh_coords[LEFT_EYE[8]])
            right_eye_center = np.array(mesh_coords[RIGHT_EYE[8]])
            interocular_distance = np.linalg.norm(left_eye_center - right_eye_center)

            # Calculate the distance to the camera
            distance_to_camera = calculate_distance(interocular_distance)

            # Display the distance on the frame
            distance_text = f'{round(distance_to_camera, 2)} cm'
            
            # Eye Direction Estimation
            right_coords = [mesh_coords[p] for p in RIGHT_EYE]
            left_coords = [mesh_coords[p] for p in LEFT_EYE]
            crop_right, crop_left = eyesExtractor(frame, right_coords, left_coords)
            eye_position, color = positionEstimator(crop_right)
            direction_text = f'Direction: {eye_position}'
            # eye_position_left, color = positionEstimator(crop_left)
            # utils.colorBackgroundText(frame, f'L: {eye_position_left}', FONTS, 1.0, (40, 350), 2, color[0], color[1], 8, 8)
            
            if (reRatio > 5.5 and leRatio > 5.5) or eye_position!='CENTER':
                if reRatio > 5.5 and leRatio > 5.5:
                    CEF_COUNTER +=1
                    # cv.putText(frame, 'Blink', (200, 50), FONTS, 1.3, utils.PINK, 2)
                #start timer + video start
                DISTRACT_COUNTER+=1
                if DISTRACT_COUNTER == 1:
                    timer = time.time()
                    if review == 0:
                        video_name = current_video_dir + "/Distraction_Track" + "_" + str(TOTAL_DISTRACT + 1) + ".mp4"
                        writer= cv.VideoWriter(video_name, cv.VideoWriter_fourcc(*'DIVX'), 20, (frame_width,frame_height))
                if review == 0:
                    writer.write(frame)
                
                
                #distraction cases
                endtimer = int(time.time()-timer)
                endtimer_text = f'Closing: {int(endtimer//60)} minutes, {int(endtimer%60)} seconds'
                if (endtimer < 2):
                    distracted = 0
                if (endtimer >= 2):
                    
                    if endtimer == 2:
                        distracted +=1
                    if distracted == 1: #write to database
                        TOTAL_DISTRACT +=1
                        if review == 0:
                            sqlsyn = "INSERT INTO " + current_session + "(Time, VideoPath) VALUES ('" + str(datetime.datetime.now()) +"', '" + video_name +"')"
                            cur.execute(sqlsyn)
                            conn.commit()

            else:
                DISTRACT_COUNTER =0
                distracted =0
                if CEF_COUNTER>CLOSED_EYES_FRAME:
                    TOTAL_BLINKS +=1
                    CEF_COUNTER =0
            # cv.putText(frame, f'Total Blinks: {TOTAL_BLINKS}', (100, 150), FONTS, 0.6, utils.GREEN, 2)
            total_distraction_text = f'Total Distract: {TOTAL_DISTRACT}'
            
            cv.circle(frame, center_left, int(l_radius), (255, 0, 255), 1, cv.LINE_AA)
            cv.circle(frame, center_right, int(r_radius), (255, 0, 255), 1, cv.LINE_AA )
            cv.polylines(frame,  [np.array([mesh_coords[p] for p in LEFT_EYE ], dtype=np.int32)], True, utils.GREEN, 1, cv.LINE_AA)
            cv.polylines(frame,  [np.array([mesh_coords[p] for p in RIGHT_EYE ], dtype=np.int32)], True, utils.GREEN, 1, cv.LINE_AA)

        # Timer
        end_time = time.time()-start_time
        end_minutes = int(end_time // 60)
        end_seconds = int(end_time % 60)
        
        # Calculating  frame per seconds FPS
        fps = frame_counter/end_time
        
        # Display timer on the frame
        timer_text = f'Timer: {end_minutes} minutes, {end_seconds} seconds'
        
        fps_text = f'FPS: {round(fps,1)}'
        
        #cv.imshow('Test5', frame)
        

    # starting Video loop here.
