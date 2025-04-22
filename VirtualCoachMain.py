import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
import math
import tkinter
import time
import datetime
import json
from io import BytesIO
from shutil import rmtree
from tkinter import filedialog
from cryptography.fernet import Fernet
from PIL import Image

import HumanPoseEstimation
import Reference
import UserTechnique
import feedbackArea

# List for holding current used ReferenceTechnique Object
referenceTechniques = []

# Current in-use Technique
usersTechnique = UserTechnique.UserTechnique([],[],None)

# List of pairs of feedbackArea objects and the average difference between userTechnique and ReferenceTechnique
feedbackList = []

# List of strings with the level of quality and the area with the percentage difference for output
provideFeedback = []

# reference comment for which part of the human pose estimation array equals which body part
# 0=head,1=neck,2=left shoulder,3=left elbow,4=left hand,5=right shoulder,6=right elbow,7=right hand,8=left hip,9=left knee,10=left foot,11=right hip,12=right knee,13=right foot,14=centre
# pointKey=["HEAD","NECK","LEFTSHOULDER","LEFTELBOW","LEFTHAND","RIGHTSHOULDER","RIGHTELBOW","RIGHTHAND","LEFTHIP","LEFTKNEE","LEFTFOOT","RIGHTHIP","RIGHTKNEE","RIGHTFOOT","CENTRE"]

# generates a unique encryption key for each download and adds to imageKey.key file
imageKey = Fernet.generate_key()
keyPath = (os.path.abspath('imageKey.key'))
if os.path.exists(keyPath) == False:
    with open((keyPath), 'wb') as keyFile:
        keyFile.write(imageKey)

# function for loading the reference images for the chosen technique
def loadImages(folderName):
    setOfImages = []
    for files in os.listdir("referenceTechniques\\"+folderName):
        im = cv2.imread(os.path.abspath("referenceTechniques\\"+folderName+"\\"+files))
        if im is not None:
            setOfImages.append(im)
    return setOfImages

# preprocess the reference images for chosen technique
def processRefImages(sport,exerciseName):
    processedImages = []
    fpath = "FeedbackAreas\\"+sport+"\\" + exerciseName + ".json"
    feedbackDict = {}
    with open(os.path.abspath(fpath)) as file:
        feedbackDict = json.load(file)
    setImages = loadImages(exerciseName)
    # for each reference image
    for im in setImages:
        # cv2 gets images in BGR colour and so requires conversion
        im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
        # crop to preprocessed size specified in the feedback areas json file
        cropArea = []
        try:
            cropArea = feedbackDict["referenceCrop"]
            im = im[cropArea[0]:cropArea[1],cropArea[2]:cropArea[3]]
        except:
            im = im
        processedImages.append(im)
    referenceTechnique = None
    # add to the referenceTechniques list
    referenceTechnique = Reference.Reference(exerciseName,processedImages,[],None)
    referenceTechniques.append(referenceTechnique)
    
    return referenceTechnique

# Allows a user to add their technique video from files
def inputVideo(technique):
    count=0
    # opens file explorer in tkinter window
    tkinter.Tk().withdraw()
    videoName = filedialog.askopenfilename()
    
    #opens file in video capture object
    videoLink = cv2.VideoCapture(videoName)
    #check file is real/open
    if not videoLink.isOpened():
        print("Error: could not open video file")
    else:

        # get total frames in file for own framerate
        numFrames = int(videoLink.get(cv2.CAP_PROP_FRAME_COUNT))
        # get the number of frames in referenceTechnique to check how many we need to split video by
        referShape = None
        for x in referenceTechniques:
                    if x.technique == technique:
                            referShape = x.frames[0]
                            break

        # loop through each frame in video link
        while videoLink.isOpened():
            #read frame and ret(confirms readable frame)
            ret, frame = videoLink.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                # shrinks or grows user's video to match height with reference video and proportionally change width
                height, width, channels = referShape.shape
                r = height / float(frame.shape[0])
                dim = (int(frame.shape[1] * r),height)
                frame = cv2.resize(frame, dim,interpolation=cv2.INTER_AREA)
                # append frame to usersTechnique frame list
                usersTechnique.frames.append(frame)
                # skips frames to only have double the reference frames by end. Most videos are in the 100s of frames and human pose estimation
                # on all of these frames is very slow. The number of frames are doubled to allow temporal analysis to syncronise the footages together
                count+=int(numFrames/((len(x.frames))*2))
                videoLink.set(cv2.CAP_PROP_POS_FRAMES, count)
            else:
                break
    videoLink.release()

# Crop the user's video
# Temporal analysis was affected by any extra space that affected the proportions between videos
# This uses human pose estimation to find the users highest head point and crops to just above this point
def cropVideo(technique):
    # get the shape of the reference image
    referShape = None
    for x in referenceTechniques:
                if x.technique == technique:
                        referShape = x.frames[0]

    # add the middle, three quarters, and last frame of the users technique to a list
    quickList = []
    quickList.append(usersTechnique.frames[int(len(usersTechnique.frames)/2)])
    quickList.append(usersTechnique.frames[int((len(usersTechnique.frames)/4))])
    quickList.append(usersTechnique.frames[int(len(usersTechnique.frames)-1)])
    # send to pose estimation function to find head point
    pointsArray, HPEdImages = HumanPoseEstimation.poseEstImages(quickList)
    # loop through to find highest point
    highest = 100000
    count = 0
    highestHead = 0
    for points in pointsArray:
        if points[0][1] < highest:
            highest = points[0][1]
            highestHead = count
        count += 1
    
    #crop all frames and change all length to reference length and width proportional to the length
    frameCropped = []
    height, width, channels = HPEdImages[0].shape
    for frame in usersTechnique.frames:
        cropped = frame[int(pointsArray[highestHead][0][1])-25:height,0:width]
        h, w, channels = referShape.shape
        r = h / float(cropped.shape[0])
        dim = (int(cropped.shape[1] * r),h)
        frame = cv2.resize(cropped, dim,interpolation=cv2.INTER_AREA)
        # append to list
        frameCropped.append(frame)
    usersTechnique.frames = frameCropped
    

# Allows the user to record video to be used in coaching
def recordVideo(technique,countdown,timing):
    #start countdown from user set number
    countdown = int(countdown)
    timing = int(timing)
    for i in range(countdown):
        time.sleep(1)
        print(countdown - i)

    #set camera capture
    cap = cv2.VideoCapture(0)
    #check camera is usable
    if not cap.isOpened():
        print("Cannot open camera")
        exit()
    
    #create file for video to be saved to
    recVideo = cv2.VideoWriter("userRecordedVideo.avi", cv2.VideoWriter_fourcc("M", "J", "P", "G"), 10, (int(cap.get(3)), int(cap.get(4))))

    #set length of recording time
    timingSet = time.time() + int(timing)

    # capture each frame for x time
    while time.time() < timingSet:
        # read frame and check if frame is read
        ret, frame = cap.read()
        if not ret:
            print("Can't receive frame (stream end?). Exiting ...")
            break
        
        #show frame to user
        cv2.imshow("frame",frame)
        #write to file
        recVideo.write(frame)
        #option to stop early
        if cv2.waitKey(1) == ord('q'):
            break
    
    # release capture, window and video file after time limit
    cap.release()
    cv2.destroyAllWindows()
    recVideo.release()

    #open video file
    videoLink = cv2.VideoCapture("userRecordedVideo.avi")
    #remove video for security
    os.remove("userRecordedVideo.avi")
    #check file is open
    if not videoLink.isOpened():
        print("Error: could not open video file")
    else:
        while videoLink.isOpened():
            # read each frame and check readable
            ret, frame = videoLink.read()
            if ret:
                #get reference frame shape
                for x in referenceTechniques:
                    if x.technique == technique:
                        referShape = x.frames[0]
                # change each frame to correct colour pattern and crop proportionally to reference length
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                height, width, channels = referShape.shape
                r = height / float(frame.shape[0])
                dim = (int(frame.shape[1] * r),height)
                frame = cv2.resize(frame, dim,interpolation=cv2.INTER_AREA)
                usersTechnique.frames.append(frame)    
            else:
                break
        videoLink.release()
        
        
# Function to match reference frames to their closest points in the user technique
# reduces number to equal to reference frames amount
def temporalAnalysis(technique):
    frameClosest = []
    pointsClosest = []

    # find used technique in reference
    for x in referenceTechniques:
        if x.technique == technique:
            #get each frame in reference points
            for frame in x.points:
                closest = 100000
                frameref = 0
                currentClosest = 0
                # for each user technique frame to find which has the closest head points
                for fr in usersTechnique.points:
                    if fr[0] != None and frame[0]!= None:
                        dis = calcDistance(fr[0],frame[0])
                        if dis < closest:
                            closest = dis
                            currentClosest = frameref
                    frameref+=1
                # add to closest point and frame
                pointsClosest.append(usersTechnique.points[currentClosest])
                frameClosest.append(usersTechnique.skeleton[currentClosest])
    # set final closest frames to skeleton and points array
    usersTechnique.skeleton = frameClosest
    usersTechnique.points = pointsClosest

# Calculate Distance
def calcDistance(pointA, pointB):
    try:
        # distance = square root (b1 - a1)^2 + (b2 - a2)^2
        distance = math.sqrt(((pointB[0] - pointA[0])**2) + ((pointB[1] - pointA[1])**2))
    except TypeError:
        # if human pose estimation cant find point it returns none for that coordinate, and so cannot be used in calculations
        distance = 0
    return distance

# Calculate Angle
def calcAngle(pointA, pointB, pointC):
    try:
        #angle = convert to degrees (instead of radians): arctan(c2-b2, c1-b1) - arctan(a2-b2,a1-b1)
        angle = math.degrees(math.atan2(pointC[1]-pointB[1], pointC[0]-pointB[0]) - math.atan2(pointA[1]-pointB[1], pointA[0]-pointB[0]))
        #convert to acute angle
        if angle >=180:
            angle = angle - 360
    except TypeError:
        # if human pose estimation cant find point it returns none for that coordinate, and so cannot be used in calculations
        angle = 0
    return abs(angle)

# Calculate Feedback from human pose estimation
def calculateFeedback(currentTechnique, pointsList, currentSport):
    #set feedback to none
    provideFeedback = []

    # hpe point reference guide
    # 0=head,1=neck,2=left shoulder,3=left elbow,4=left hand,5=right shoulder,6=right elbow,7=right hand,8=left hip,9=left knee,10=left foot,11=right hip,12=right knee,13=right foot,14=centre

    # get techique json file
    # technique json file contains the information on the technique and sport as well as an array of each tracking area for feedback with a name, type(angle or distance) and the points (refer to guide)
    fpath = "FeedbackAreas\\"+currentSport+"\\" + (currentTechnique.title()) + ".json"
    feedbackDict = {}
    # add to dictionary
    with open(os.path.abspath(fpath)) as file:
        feedbackDict = json.load(file)
    # convert each area to Feedback object and apend to list
    for area in feedbackDict["areas"]:
        provideFeedback.append(feedbackArea.Feedback(area['area'],area['points'],area['type'],[],[],[]))

    feedbackCount = 0
    framesCount = 0
    # generate feedback
    # go through each frame in reference and user technique
    for x in pointsList:
        feedbackCount = 0
        # for each feedback area in the technique dictionary
        for FeedbackArea in provideFeedback:
            # if the type of area is distance calculate the distance
            if FeedbackArea.type == "Distance":
                try:
                    #calculate the users distance between two points
                    if len(FeedbackArea.points) >= 2:
                        userDistance = calcDistance(pointsList[framesCount][FeedbackArea.points[0]], pointsList[framesCount][FeedbackArea.points[1]])
                except TypeError:
                    userAngle=0
                #find referenceTechnique
                for x in referenceTechniques:
                    if x.technique == currentTechnique:
                        try:
                            #calculate the reference distance between two points
                            if len(FeedbackArea.points) <= 2:
                                refDistance = calcDistance(x.points[framesCount][FeedbackArea.points[0]], x.points[framesCount][FeedbackArea.points[1]])
                        except TypeError:
                            # if human pose estimation cant find point it returns none for that coordinate, and so cannot be used in calculations
                            refDistance = 0
                # append the difference between the two points as well as the reference distance for percentage
                provideFeedback[feedbackCount].differencesList.append(abs(userDistance-refDistance))
                provideFeedback[feedbackCount].referenceList.append(refDistance)
                
            #if feedback area type is angle
            elif FeedbackArea.type == "Angle":
                try:
                    # if the provided area has 3 hpe points calculate the angle between the three for user
                    if len(FeedbackArea.points) < 3:
                        userAngle = calcAngle(pointsList[framesCount][FeedbackArea.points[0]], pointsList[framesCount][FeedbackArea.points[1]],(0,pointsList[framesCount][FeedbackArea.points[1]][1]))
                    elif len(FeedbackArea.points) >= 3:
                        # if not calculate the angle difference between the two points and a point on the same x axis as the middle point
                        userAngle = calcAngle(pointsList[framesCount][FeedbackArea.points[0]], pointsList[framesCount][FeedbackArea.points[1]], pointsList[framesCount][FeedbackArea.points[2]])

                except TypeError:
                    # if human pose estimation cant find point it returns none for that coordinate, and so cannot be used in calculations
                    userAngle=0
                #find reference technique
                for x in referenceTechniques:
                    if x.technique == currentTechnique:
                        try:
                            # if the provided area has 3 hpe points calculate the angle between the three for user
                            if len(FeedbackArea.points) < 3:
                                refAngle = calcAngle(x.points[framesCount][FeedbackArea.points[0]], x.points[framesCount][FeedbackArea.points[1]],(0,x.points[framesCount][FeedbackArea.points[1]][0]))
                            elif len(FeedbackArea.points) >= 3:
                                # if not calculate the angle difference between the two points and a point on the same x axis as the middle point
                                refAngle = calcAngle(x.points[framesCount][FeedbackArea.points[0]], x.points[framesCount][FeedbackArea.points[1]],x.points[framesCount][FeedbackArea.points[1]])
                        except TypeError:
                            # if human pose estimation cant find point it returns none for that coordinate, and so cannot be used in calculations
                            refAngle = 0
                #calculate the difference between the angle and append it and the reference angle
                provideFeedback[feedbackCount].differencesList.append(abs(userAngle-refAngle))
                provideFeedback[feedbackCount].referenceList.append(refAngle)
            feedbackCount +=1
        framesCount+=1

    differencesCount = 0
    #for each area in the differences
    for differences in provideFeedback:
        # calculate the average differences of each frame for differences and references
        difference = sum(provideFeedback[differencesCount].differencesList) / len(provideFeedback[differencesCount].differencesList)
        refAve = sum(provideFeedback[differencesCount].referenceList) / len(provideFeedback[differencesCount].referenceList)
        #convert to percentage difference
        percentDifference = difference/refAve
        percentDifference = percentDifference * 100
        # append the area object and percentage diff
        feedbackList.append((differences, percentDifference))
        differencesCount+=1

# Calcualte the feedback boundary and add to a list
def outputFeedback(differencesList):
    # add differences to different lists depending on percentage boundaries
    perfect = []
    good = []
    ok = []
    poor = []
    needImprovement = []
    for areaOfImpro in differencesList:
        if areaOfImpro[1] < 6:
            perfect.append(areaOfImpro)
        elif areaOfImpro[1] < 10:
            good.append(areaOfImpro)
        elif areaOfImpro[1] < 15:
            ok.append(areaOfImpro)
        elif areaOfImpro[1] < 20:
            poor.append(areaOfImpro)
        else:
            needImprovement.append(areaOfImpro)
    
    # append each string for providing feedback to user. Ordered in terms of priority from worst to best
    if(needImprovement!=[]):
        provideFeedback.append("Areas that need improvement:")
        for i in needImprovement:
            provideFeedback.append(("Area of Tracking: "+str(i[0].area) +", Percentage Difference: "+str(round(i[1],2))))

    if(poor!=[]):
        provideFeedback.append("Poor Areas:")
        for i in poor:
            provideFeedback.append(("Area of Tracking: "+str(i[0].area) +", Percentage Difference: "+str(round(i[1],2))))

    if(ok!=[]):
        provideFeedback.append("Ok Areas:")
        for i in ok:
            provideFeedback.append(("Area of Tracking: "+str(i[0].area) +", Percentage Difference: "+str(round(i[1],2))))
            
    if(good!=[]):
        provideFeedback.append("Good Areas:")
        for i in good:
            provideFeedback.append(("Area of Tracking: "+str(i[0].area) +", Percentage Difference: "+str(round(i[1],2))))

    if(perfect!=[]):
        provideFeedback.append("Perfect Areas:")
        for i in perfect:
            provideFeedback.append(("Area of Tracking: "+str(i[0].area) +", Percentage Difference: "+str(round(i[1],2))))
    feedbackList.clear()

# Add to history
def sendToHistory(currentTechnique):
    # store the current date time to prevent exact file names
    timeFile = (str(datetime.datetime.now())).replace(" ","_")
    # replace unusable characters in time
    timeFile = timeFile.replace(":","_")
    fname = "storedFeedback\\" + (currentTechnique.title()) + "-" + timeFile
    try:
        # get absolute path of intended folder
        fpath = os.path.abspath(fname)
        # create path
        os.makedirs(fpath)
    except FileExistsError:
        # if file does exist just get absolute path of folder
        fpath = os.path.abspath(fname)
    
    # create dictionary of just points
    jsonPoints = {
        "points": usersTechnique.points
    }
    # serialize points into a json object
    jsx = json.dumps(jsonPoints)
    # dump into json file
    with open(fpath+'\\pointsData.json', 'w') as file:
        json.dump(jsx, file)

    try:
        # make directory in folder for skeleton images
        fpath = os.path.abspath(fname)
        fpath = fpath + "\\skeletonsList"
        os.makedirs(fpath)
    except FileExistsError:
        # if file exists just create an absolute path
        fpath = os.path.abspath(fname)
    count = 0
    # write skeleton image to folder
    for skele in usersTechnique.skeleton:
        imagePath = fpath+'\\skeleton_'+ str(count) +'.jpg'
        # send file for encryption
        im = footageEncryption(cv2.cvtColor(usersTechnique.skeleton[count], cv2.COLOR_RGB2BGR),imagePath)
        count+=1

# encryption file for security and Data Protection Act 2018 coverage
def footageEncryption(im,imPath):
    # read the key file
    with open(keyPath, 'rb') as keyFile:
        key = keyFile.read()
    # change to key object
    fernetEncryptionKey = Fernet(key)
    # write file to filepath temporarily to change to normal image
    cv2.imwrite(imPath, im)
    # read written file
    with open(imPath, 'rb') as image:
        originalImage = image.read()
    # delete file for security
    os.remove(os.path.abspath(imPath))
    # encrypt file
    encryptedImage = fernetEncryptionKey.encrypt(originalImage)
    # write to folder
    with open(imPath, 'wb+') as image:
        image.write(encryptedImage)

    return encryptedImage

# Decryption function for history
def footageDecryption(imagePath):
    # open key file
    with open(keyPath, 'rb') as keyFile:
        imageKeyFile = keyFile.read()
    # change to key object
    fernetDecryptionKey = Fernet(imageKeyFile)
    # open encrypted image
    with open(imagePath, 'rb') as image:
        encryptedImage = image.read()
    # decrypt file
    decryptedImage = fernetDecryptionKey.decrypt(encryptedImage)
    # write to file temporarily for opencv library reading
    imagePath = imagePath.replace(".jpg","temp.jpg")
    with open(imagePath, 'wb+') as image:
        image.write(decryptedImage)
    im = cv2.imread(imagePath)
    # delete temporarily file
    os.remove(os.path.abspath(imagePath))
    return im

#startup function for getting the chosen technique
def startUp(sport,technique):
    # get and process the reference images for user's chosen technique
    refImages = processRefImages(sport,technique)
    # conduct hpe on reference videos
    pointsArray, HPEdImages = HumanPoseEstimation.poseEstImages(refImages.frames)
    # add points and skeleton images to reference Technique object
    for x in referenceTechniques:
        if x.technique == technique:
            x.skeleton = HPEdImages
            x.points = pointsArray
    

