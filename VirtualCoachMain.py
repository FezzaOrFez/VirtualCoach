import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
import threading
import math

from IPython.display import YouTubeVideo, display, Image

import HumanPoseEstimation
import Reference
import UserTechnique

referenceDeadliftTechnique = Reference.Deadlift([],[],None)
referenceBenchPressTechnique = Reference.BenchPress([],[],None)
referenceSquatTechnique = Reference.Squat([],[],None)
usersTechnique = UserTechnique.UserTechnique([],[],None)

# 0=head,1=neck,2=left shoulder,3=left elbow,4=left hand,5=right shoulder,6=right elbow,7=right hand,8=left hip,9=left knee,10=left foot,11=right hip,12=right knee,13=right foot,14=centre
pointKey=["HEAD","NECK","LEFTSHOULDER","LEFTELBOW","LEFTHAND","RIGHTSHOULDER","RIGHTELBOW","RIGHTHAND","LEFTHIP","LEFTKNEE","LEFTFOOT","RIGHTHIP","RIGHTKNEE","RIGHTFOOT","CENTRE"]


# load reference images
def loadImages(folderName):
    setOfImages = []
    for files in os.listdir(folderName):
        im = cv2.imread(os.path.join(folderName,files))
        if im is not None:
            setOfImages.append(im)
    return setOfImages

# preprocossing reference images for useage
def processRefImages(exerciseName):
    processedImages = []

    setImages = loadImages(exerciseName.lower())
    for im in setImages:
        if exerciseName.lower() == "deadlift":
            im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
            im = im[0:400,175:500]
            processedImages.append(im)
        if exerciseName.lower() == "bench_press":
            im = cv2.resize(im, (480,360))
            im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
            im = im[75:400,75:400]
            im = cv2.rotate(im, cv2.ROTATE_90_COUNTERCLOCKWISE)
            processedImages.append(im)
        if exerciseName.lower() == "squat":
            im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
            im = im[0:400,0:180]
            processedImages.append(im)
    referenceTechnique = None
    if exerciseName.lower() == "deadlift":
        referenceDeadliftTechnique.frames = processedImages
        referenceTechnique = referenceDeadliftTechnique
    elif exerciseName.lower() == "bench_press":
        referenceBenchPressTechnique.frames = processedImages
        referenceTechnique = referenceBenchPressTechnique
    elif exerciseName.lower() == "squat":
        referenceSquatTechnique.frames = processedImages
        referenceTechnique = referenceSquatTechnique
    
    return referenceTechnique

       
# Add Video
def addUserVideo(technique):
    print("Select Video Input Method: 1 = Input Video from Files, 2 = Record Video")
    x = input()
    if x == "1":
        inputVideo(technique)
    elif x == "2":
        recordVideo()
    else:
        print("error: incorrect input")


# Input Video
def inputVideo(technique):
    count = 0
    videoName = input("Type Video Name: ")
    videoLink = cv2.VideoCapture(videoName)
    numFrames = int(videoLink.get(cv2.CAP_PROP_FRAME_COUNT))
    if not videoLink.isOpened():
        print("Error: could not open video file")
    else:
        while videoLink.isOpened():
            ret, frame = videoLink.read()
            if ret:
                if technique == "deadlift":
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    referShape = referenceDeadliftTechnique.frames[0]
                    height, width, channels = referShape.shape
                    frame = cv2.resize(frame, (height,width))
                    usersTechnique.frames.append(frame)
                    count+=numFrames/7
                    videoLink.set(cv2.CAP_PROP_POS_FRAMES, count)
                    plt.imshow(frame)
                    plt.show()
                elif technique == "bench_press":
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    referShape = referenceBenchPressTechnique.frames[0]
                    height, width, channels = referShape.shape
                    frame = cv2.resize(frame, (height,width))
                    usersTechnique.frames.append(frame)
                    count+=numFrames/7
                    videoLink.set(cv2.CAP_PROP_POS_FRAMES, count)
                    plt.imshow(frame)
                    plt.show()
                elif technique == "squat":
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    referShape = referenceSquatTechnique.frames[0]
                    height, width, channels = referShape.shape
                    frame = cv2.resize(frame, (height,width))
                    usersTechnique.frames.append(frame)
                    count+=numFrames/7
                    videoLink.set(cv2.CAP_PROP_POS_FRAMES, count)
                    plt.imshow(frame)
                    plt.show()
            else:
                break
    videoLink.release()

# def joinPoints(imageSet):
#     iterate=0
#     frameIte=0
#     while frameIte != len(imageSet.frames):
#         pointTuple = []
#         for point in imageSet.points[frameIte]:
#             pointTuple.append((pointKey[iterate],point))
#             iterate+=1
#         imageSet.frameSet.append(pointTuple)
#         frameIte+=1

# Calculate Distance
def calcDistance(pointA, pointB):
    distance = pointA

# Calculate Angle
def calcAngle(pointA, pointB, pointC):
    print("tbd")

# Calculate Feedback
def calculateFeedback():
    print("tbd")
    #for now compare deadlift and user technique
    frame = usersTechnique.points[4]
    print(calcDistance(frame[0],frame[1]))


# Output Feedback
def outputFeedback():
    print("output feedback tbd")

# Select Sport
def selectSport():
    print("select sport tbd")

# Select Technique
def selectTechnique():
    print("select technique tbd")

# Record Video
def recordVideo():
    print("record video tbd")

# View History
def viewHistory():
    print("view history tbd")

# Delete History
def deleteHistory():
    print("delete history tbd")

# Encryption
def footageEncryption():
    print("encryption tbd")

# Decryption
def footageDecryption():
    print("decryption tbd")

#main function for easability
def main():
    #start processing reference images
    refImages = processRefImages("deadlift")
    # inim=1
    # for im in refImages.frames:
    #     plt.subplot(4,3,inim)
    #     plt.imshow(im)
    #     plt.axis('off')
    #     inim += 1

    #thread to start adding user video
    StartThread = threading.Thread(target=addUserVideo,args=("deadlift",))
    StartThread.start()
    #conduct hpe on reference videos
    pointsArray, HPEdImages = HumanPoseEstimation.poseEstImages(refImages.frames)
    referenceDeadliftTechnique.skeleton = HPEdImages
    referenceDeadliftTechnique.points = pointsArray
    StartThread.join()
    #conduct hpe on added video
    pointsArray, HPEdImages = HumanPoseEstimation.poseEstImages(usersTechnique.frames)
    usersTechnique.skeleton = HPEdImages
    usersTechnique.points = pointsArray

    #calculate feedback
    calculateFeedback()
    
main()
