import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
import threading
import math
import tkinter
import time
import datetime
import json
import binascii
from io import BytesIO
from shutil import rmtree
from tkinter import filedialog
from cryptography.fernet import Fernet
from PIL import Image

import HumanPoseEstimation
import Reference
import UserTechnique
import feedbackArea
import VirtualCoachGUI

referenceTechniques = []

usersTechnique = UserTechnique.UserTechnique([],[],None)
feedbackList = []

provideFeedback = []
# 0=head,1=neck,2=left shoulder,3=left elbow,4=left hand,5=right shoulder,6=right elbow,7=right hand,8=left hip,9=left knee,10=left foot,11=right hip,12=right knee,13=right foot,14=centre
pointKey=["HEAD","NECK","LEFTSHOULDER","LEFTELBOW","LEFTHAND","RIGHTSHOULDER","RIGHTELBOW","RIGHTHAND","LEFTHIP","LEFTKNEE","LEFTFOOT","RIGHTHIP","RIGHTKNEE","RIGHTFOOT","CENTRE"]

imageKey = Fernet.generate_key()
keyPath = (os.path.abspath('imageKey.key'))
if os.path.exists(keyPath) == False:
    with open((keyPath), 'wb') as keyFile:
        keyFile.write(imageKey)

# load reference images
def loadImages(folderName):
    setOfImages = []
    for files in os.listdir("referenceTechniques\\"+folderName):
        im = cv2.imread(os.path.abspath("referenceTechniques\\"+folderName+"\\"+files))
        if im is not None:
            setOfImages.append(im)
    return setOfImages

# preprocossing reference images for useage
def processRefImages(sport,exerciseName):
    processedImages = []
    fpath = "FeedbackAreas\\"+sport+"\\" + exerciseName + ".json"
    feedbackDict = {}
    with open(os.path.abspath(fpath)) as file:
        feedbackDict = json.load(file)
    setImages = loadImages(exerciseName)
    for im in setImages:
        im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
        im = im[feedbackDict["referenceCrop"][0]:feedbackDict["referenceCrop"][1],feedbackDict["referenceCrop"][2]:feedbackDict["referenceCrop"][3]]
        processedImages.append(im)
    referenceTechnique = None
    referenceTechnique = Reference.Reference(exerciseName,processedImages,[],None)
    referenceTechniques.append(referenceTechnique)
    
    return referenceTechnique

# Select Sport
def selectSport():
    fname = "FeedbackAreas"
    sportList = os.listdir(os.path.abspath(fname))
    print("Select Sport:")
    count = 1
    for sport in sportList:
        print(str(count) + ": " + sport)
        count+=1
    print("0: Back")
    try:
        x = int(input())
        if x == 0:
            menu()
        elif x >= 1:
            return(sportList[x-1])
        else:
            print("error: incorrect input")
    except ValueError:
        print("Unusable value please try again")
        menu()

# Select Technique
def selectTechnique(sport):
    fname = "FeedbackAreas"
    techniqueList = os.listdir(os.path.abspath(fname+"\\"+sport))
    print("Select Technique:")
    count = 1
    for tech in techniqueList:
        print(str(count) + ": " + tech.replace(".json",""))
        count+=1
    print("0: Go Back")
    try:
        x = int(input())
        if x == 0:
            menu()
        elif x >= 1:
            return(techniqueList[x-1].replace(".json",""))
        else:
            print("error: incorrect input")
    except ValueError:
        print("Unusable value please try again")
        menu()
       
# Add Video
def addUserVideo(technique,sport):
    print("Select Video Input Method: 1 = Input Video from Files, 2 = Record Video, 3 = get technique information")
    try:
        x = int(input())
        if x == 1:
            inputVideo(technique)
        elif x == 2:
            recordVideo(technique)
        elif x == 3:
            fpath = "FeedbackAreas\\"+sport+"\\" + (technique.title()) + ".json"
            feedbackDict = {}
            with open(os.path.abspath(fpath)) as file:
                feedbackDict = json.load(file)
            print(feedbackDict["description"])
            addUserVideo(technique,sport)

    except ValueError:
        print("Invalid Value")
        menu()

# Input Video
def inputVideo(technique):
    count = 0
    videoName = print("Select Video")
    tkinter.Tk().withdraw()
    videoName = filedialog.askopenfilename()
    videoLink = cv2.VideoCapture(videoName)
    numFrames = int(videoLink.get(cv2.CAP_PROP_FRAME_COUNT))
    if not videoLink.isOpened():
        print("Error: could not open video file")
    else:
        referShape = None
        for x in referenceTechniques:
                    if x.technique == technique:
                            referShape = x.frames[0]
        while videoLink.isOpened():
            ret, frame = videoLink.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                height, width, channels = referShape.shape
                r = height / float(frame.shape[0])
                dim = (int(frame.shape[1] * r),height)
                frame = cv2.resize(frame, dim,interpolation=cv2.INTER_AREA)
                usersTechnique.frames.append(frame)
                count+=numFrames/15
                videoLink.set(cv2.CAP_PROP_POS_FRAMES, count)
            else:
                break
    videoLink.release()
    quickList = []
    quickList.append(usersTechnique.frames[int(len(usersTechnique.frames)/2)])
    quickList.append(usersTechnique.frames[int(len(usersTechnique.frames)/2)])
    pointsArray, HPEdImages = HumanPoseEstimation.poseEstImages(quickList)
    frameCropped = []
    height, width, channels = HPEdImages[0].shape
    for frame in usersTechnique.frames:
        print((pointsArray[0][0]))
        frameCropped.append(frame[int(pointsArray[0][0][0])-25:height,0:width])
    plt.imshow(frameCropped[0])
    plt.show()
    usersTechnique.frames = frameCropped
    

# Record Video
def recordVideo(technique,countdown,timing):

    countdown = int(countdown)
    timing = int(timing)
    for i in range(countdown):
        time.sleep(1)
        print(countdown - i)

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Cannot open camera")
        exit()
    
    recVideo = cv2.VideoWriter("userRecordedVideo.avi", cv2.VideoWriter_fourcc("M", "J", "P", "G"), 10, (int(cap.get(3)), int(cap.get(4))))

    timingSet = time.time() + int(timing)

    while time.time() < timingSet:
        # Capture frame-by-frame
        ret, frame = cap.read()
    
        # if frame is read correctly ret is True
        if not ret:
            print("Can't receive frame (stream end?). Exiting ...")
            break
        # Our operations on the frame come here
        # Display the resulting frame
        cv2.imshow("frame",frame)
        recVideo.write(frame)
        if cv2.waitKey(1) == ord('q'):
            break
    
    # When everything done, release the capture
    cap.release()
    cv2.destroyAllWindows()
    numFrames = int(recVideo.get(cv2.CAP_PROP_FRAME_COUNT))
    recVideo.release()
    count = 0
    videoLink = cv2.VideoCapture("userRecordedVideo.avi")
    numFrames = int(videoLink.get(cv2.CAP_PROP_FRAME_COUNT))
    if not videoLink.isOpened():
        print("Error: could not open video file")
    else:
        while videoLink.isOpened():
            ret, frame = videoLink.read()
            if ret:
                for x in referenceTechniques:
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    if x.technique == technique:
                        referShape = x.frames[0]
                    height, width, channels = referShape.shape
                    r = height / float(frame.shape[0])
                    dim = (int(frame.shape[1] * r),height)
                    frame = cv2.resize(frame, dim,interpolation=cv2.INTER_AREA)
                    usersTechnique.frames.append(frame)
                    # count+=numFrames/7
                    # videoLink.set(cv2.CAP_PROP_POS_FRAMES, count)
            else:
                break
        videoLink.release()
        os.remove("userRecordedVideo.avi")
        

def temporalAnalysis(technique):
    frameClosest = []
    pointsClosest = []
    for x in referenceTechniques:
        if x.technique == technique:
            for frame in x.points:
                closest = 100000
                frameref = 0
                currentClosest = 0
                for fr in usersTechnique.points:
                    if fr[14] != None and frame[14]!= None:
                        dis = calcDistance(fr[0],frame[0])
                        if dis < closest:
                            closest = dis
                            currentClosest = frameref
                    frameref+=1
                print(frameref)
                pointsClosest.append(usersTechnique.points[currentClosest])
                frameClosest.append(usersTechnique.skeleton[currentClosest])
    usersTechnique.skeleton = frameClosest
    usersTechnique.points = pointsClosest

# Calculate Distance
def calcDistance(pointA, pointB):
    try:
        distance = math.sqrt(((pointB[0] - pointA[0])**2) + ((pointB[1] - pointA[1])**2))
    except TypeError:
        distance = 0
    return distance

# Calculate Angle
def calcAngle(pointA, pointB, pointC):
    try:
        angle = math.degrees(math.atan2(pointC[1]-pointB[1], pointC[0]-pointB[0]) - math.atan2(pointA[1]-pointB[1], pointA[0]-pointB[0]))
        if angle >=180:
            angle = angle - 360
    except TypeError:
        angle = 0
    return abs(angle)

# Calculate Feedback
def calculateFeedback(currentTechnique, historyCheck, pointsList, currentSport):
    #for now compare deadlift and user technique
    print("Generating Feedback")
    provideFeedback = []

    # 0=head,1=neck,2=left shoulder,3=left elbow,4=left hand,5=right shoulder,6=right elbow,7=right hand,8=left hip,9=left knee,10=left foot,11=right hip,12=right knee,13=right foot,14=centre
    #deadlift
    #where could mistakes be made in technique
    # legs distance, angle of back, leg and hip distance, arms distance
    fpath = "FeedbackAreas\\"+currentSport+"\\" + (currentTechnique.title()) + ".json"
    feedbackDict = {}
    with open(os.path.abspath(fpath)) as file:
        feedbackDict = json.load(file)
    for area in feedbackDict["areas"]:
        provideFeedback.append(feedbackArea.Feedback(area['area'],area['points'],area['type'],[],[],[]))


    feedbackCount = 0
    framesCount = 0
    #compare the videos in these areas
    #check each frame
    for x in pointsList:
        feedbackCount = 0
        #calculate the angle or distance for each area
        for FeedbackArea in provideFeedback:
            if FeedbackArea.type == "Distance":
                try:
                    userDistance = calcDistance(pointsList[framesCount][FeedbackArea.points[0]], pointsList[framesCount][FeedbackArea.points[1]])
                except TypeError:
                    userAngle=0
                for x in referenceTechniques:
                    if x.technique == currentTechnique:
                        try:
                            refDistance = calcDistance(x.points[framesCount][FeedbackArea.points[0]], x.points[framesCount][FeedbackArea.points[1]])
                        except TypeError:
                            refDistance = 0
                #calculate the difference between the distance
                provideFeedback[feedbackCount].differencesList.append(abs(userDistance-refDistance))
                provideFeedback[feedbackCount].referenceList.append(refDistance)
                print(userDistance, "-d", refDistance ,"=",userDistance-refDistance)
            elif FeedbackArea.type == "Angle":
                try:
                    userAngle = calcAngle(pointsList[framesCount][FeedbackArea.points[0]], pointsList[framesCount][FeedbackArea.points[1]],(0,pointsList[framesCount][FeedbackArea.points[1]][1]))
                except TypeError:
                    userAngle=0
                for x in referenceTechniques:
                    if x.technique == currentTechnique:
                        try:
                            refAngle = calcAngle(x.points[framesCount][FeedbackArea.points[0]], x.points[framesCount][FeedbackArea.points[1]],(0,x.points[framesCount][FeedbackArea.points[1]][0]))
                        except TypeError:
                            refAngle = 0
                #calculate the difference between the angle
                provideFeedback[feedbackCount].differencesList.append(abs(userAngle-refAngle))
                provideFeedback[feedbackCount].referenceList.append(refAngle)
                print(userAngle, "-a", refAngle ,"=",userAngle-refAngle)

            feedbackCount +=1
        framesCount+=1

    #boundary checks to see how well they compare against the reference
    differencesCount = 0
    #for each area in the differences
    for differences in provideFeedback:
        #average difference of all frames
        difference = sum(provideFeedback[differencesCount].differencesList) / len(provideFeedback[differencesCount].differencesList)
        refAve = sum(provideFeedback[differencesCount].referenceList) / len(provideFeedback[differencesCount].referenceList)
        percentDifference = difference/refAve
        percentDifference = percentDifference * 100
        feedbackList.append((differences, percentDifference))
        differencesCount+=1

    print(feedbackList)

    #return areas for ouputting feedback
    # outputFeedback(feedbackList)
    # if(historyCheck == False):
    #     sendToHistory(currentTechnique)
    # else:
    #     menu()

# Output Feedback
def outputFeedback(differencesList):
    print("output feedback tbd")
    #priority - add to lists dependant on boundary output worst first to best last
    # 6,10,15,20,+
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

# View History
def viewHistory():
    print("view history tbd")
    fname = "storedFeedback"
    historyList = os.listdir(os.path.abspath(fname))
    count = 0
    for i in historyList:
        print(str(count+1)+": "+i)
    print("0: Back")
    print("99: For delete")
    print("")
    try:
        whichHist = int(input("Please input the number the wish to view: "))

        if whichHist <= len(historyList) and whichHist > 0:

            fpath = fname + "\\" + historyList[int(whichHist)-1] + "\\pointsData.json"

            with open(os.path.abspath(fpath)) as file:
                feedbackDict = json.loads(json.load(file))

            fpath = fname + "\\" + historyList[int(whichHist)-1] + "\\skeletonsList"
            skelList = os.listdir(os.path.abspath(fpath))

            inim = 1
            for x in skelList:
                skelImg = cv2.imread(os.path.abspath(fpath+ "\\" + x), 1)
                plt.subplot(4,3,inim)
                plt.axis("off")
                skelImg = cv2.cvtColor(skelImg, cv2.COLOR_RGB2BGR)
                plt.imshow(skelImg)
                inim+=1
            plt.show()

            calculateFeedback("Deadlift",True,feedbackDict["points"], "Powerlifting")
        elif whichHist == 0:
            menu()
        elif whichHist == 99:
            deleteHistory()
    except ValueError:
        print("Invalid Value")
        viewHistory()

# Add to history
def sendToHistory(currentTechnique):
    print("Do you wish to save the reference skeleton image and data for later use?")
    print("The image will be stored for later use. This can be deleted later")

    timeFile = (str(datetime.datetime.now())).replace(" ","_")
    timeFile = timeFile.replace(":","_")
    fname = "storedFeedback\\" + (currentTechnique.title()) + "-" + timeFile
    try:
        fpath = os.path.abspath(fname)
        os.makedirs(fpath)
    except FileExistsError:
        fpath = os.path.abspath(fname)
    
    jsonPoints = {
        "points": usersTechnique.points
    }
    jsx = json.dumps(jsonPoints)
    with open(fpath+'\\pointsData.json', 'w') as file:
        json.dump(jsx, file)

    try:
        fpath = os.path.abspath(fname)
        fpath = fpath + "\\skeletonsList"
        os.makedirs(fpath)
    except FileExistsError:
        fpath = os.path.abspath(fname)
    count = 0
    for skele in usersTechnique.skeleton:
        # im = footageEncryption(cv2.cvtColor(usersTechnique.skeleton[count], cv2.COLOR_RGB2BGR))
        # with open(fpath+'\\skeleton_'+ str(count) +'.jpg',"wb+") as image:
        #     image.write(im)
        cv2.imwrite(fpath+'\\skeleton_'+ str(count) +'.jpg', (cv2.cvtColor(usersTechnique.skeleton[count], cv2.COLOR_RGB2BGR)))
        count+=1
    # im = footageDecryption(fpath+'\\skeleton_'+ str(4) +'.jpg')
    print("Successfully written to folder " + fpath)


# Delete History
def deleteHistory():
    print("delete history tbd")
    fname = "storedFeedback"
    historyList = os.listdir(os.path.abspath(fname))
    count = 0
    for i in historyList:
        print(str(count+1)+": "+i)
    print("0: Back")
    print("")
    try:
        whichHist = int(input("Please input the number to delete: "))

        if whichHist <= len(historyList) and whichHist > 0:
            fpath = fname + "\\" + historyList[int(whichHist)-1]
            rmtree(fpath)
            print("Successfully deleted")
            menu()
        elif whichHist == 0:
            menu()
        else: 
            print("incorrect input")
            viewHistory()
    except ValueError:
        print("Invalid Value")
        menu()


# Encryption
def footageEncryption(image):
    print("encryption tbd")
    with open(keyPath, 'rb') as keyFile:
        key = keyFile.read()
    image = Image.fromarray(image)
    encryptKey = Fernet(key) 
    byteImage = image.tobytes()
    encryptedImage = encryptKey.encrypt(byteImage)

    return encryptedImage

# Decryption
def footageDecryption(imagePath):
    print("decryption tbd")
    with open(keyPath, 'rb') as keyFile:
        imageKeyFile = keyFile.read()
        
    decryptKey = Fernet(imageKeyFile)

    with open(imagePath, 'r') as img:
        encryptedImage = img.read()
        
    decryptedImage = decryptKey.decrypt(encryptedImage)
    decryptedImage = BytesIO(decryptedImage)
    file_bytes = np.asarray(decryptedImage, dtype=np.uint8)
    im = cv2.imdecode(file_bytes,cv2.IMREAD_COLOR)
    imagePath = imagePath.replace(".jpg","temp.jpg")
    with open(imagePath, 'w') as image:
        image.write(im)
    im = cv2.imread(imagePath)
    return im

# Manage Techniques
def manageTechniques():
    # show sports and their techniques
    print("tbd")
    # select sport

        # add technique

        # delete sport

    # or add sport


def menu():
    print("Choose option")
    print("1: Track Technique")
    print("2: Track History")
    print("3: Manage Tecnhiques")
    try:
        x = int(input())
        if(x == 1):
            chosenSport = selectSport()
            chosenTechnique = selectTechnique(chosenSport)
            addUserVideo(chosenTechnique,chosenSport)
            #conduct hpe on added video

            pointsArray, HPEdImages = HumanPoseEstimation.poseEstImages(usersTechnique.frames)
            usersTechnique.skeleton = HPEdImages
            usersTechnique.points = pointsArray
            #calculate feedback
            calculateFeedback(chosenTechnique,False,usersTechnique.points,chosenSport)
        elif(x == 2):
            viewHistory()
        elif(x == 3):
            manageTechniques()
        else:
            print("Invalid option")
    except ValueError:
        print("invalid input")

#main function for easability
def main():
    #start processing reference images
    refImages = processRefImages("Powerlifting","Deadlift")
    #conduct hpe on reference videos
    pointsArray, HPEdImages = HumanPoseEstimation.poseEstImages(refImages.frames)
    for x in referenceTechniques:
        if x.technique == "Deadlift":
            x.skeleton = HPEdImages
            x.points = pointsArray
    #thread to start adding user video
    

