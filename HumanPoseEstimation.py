import os
import cv2
import numpy as np
import matplotlib.pyplot as plt

from IPython.display import YouTubeVideo, display, Image

# Human Pose Estimation Files
protoFile   = os.path.join("model","pose_deploy_linevec_faster_4_stages.prototxt")
weightsFile = os.path.join("model", "pose_iter_160000.caffemodel")

# number of points
nPoints = 15
# poses that link to other poses (e.g. hand to arm, neck to head)
POSE_PAIRS = [
    [0, 1],
    [1, 2],
    [2, 3],
    [3, 4],
    [1, 5],
    [5, 6],
    [6, 7],
    [1, 14],
    [14, 8],
    [8, 9],
    [9, 10],
    [14, 11],
    [11, 12],
    [12, 13],
]

# load HPE files
net = cv2.dnn.readNetFromCaffe(protoFile, weightsFile)

#Calculate HPE
def poseEstImages(imageList):
    print("Calculating Pose Estimation")

    # set images and array to empty
    HPEdImages = []
    pointsArray = []
    # loop through all images in provided list
    for im in imageList:
        # get the width and height of images
        inWidth  = im.shape[1]
        inHeight = im.shape[0]
        #blob size
        netInputSize = (368, 368)
        # blob from image preprocesses the inputted image by creating a 4d blob, resizes and crops, subtracts mean values, scales values and swaps ble and red channels
        inpBlob = cv2.dnn.blobFromImage(im, 1.0 / 255, netInputSize, (0, 0, 0), swapRB=True, crop=False)
        # this is then input int othe neural network
        net.setInput(inpBlob)

        # Forward Pass to move through the network
        output = net.forward()

        # Display probability maps
        # loop through the number of points
        for i in range(nPoints):
            # probability map is a heatmap of the most likely location of a point in hpe
            probMap = output[0, i, :, :]
            # creates a display map with the images size
            displayMap = cv2.resize(probMap, (inWidth, inHeight), cv2.INTER_LINEAR)
        # X and Y Scale
        scaleX = inWidth  / output.shape[3]
        scaleY = inHeight / output.shape[2]

        # Empty list to store the detected keypoints
        points = []

        # Treshold - check if the probability is above this then add
        threshold = 0.1

        for i in range(nPoints):
            # Obtain probability map
            probMap = output[0, i, :, :]

            # Find global maxima of the probMap for the probability and point of the current point
            minVal, prob, minLoc, point = cv2.minMaxLoc(probMap)

            # Scale the point to fit on the original image
            x = scaleX * point[0]
            y = scaleY * point[1]

            if prob > threshold:
                # Add the point to the list if the probability is greater than the threshold
                points.append((int(x), int(y)))
            else:
                # if not then set to none so that it is not added to image
                points.append(None)
        # copys the images to different variables, one for points, one for skeleton
        imPoints = im.copy()
        imSkeleton = im.copy()
        # Draw points
        for i, p in enumerate(points):
            cv2.circle(imPoints, p, 2, (255, 255, 0), thickness=-1, lineType=cv2.FILLED)
            cv2.putText(imPoints, "{}".format(i), p, cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, lineType=cv2.LINE_AA)

        # Draw skeleton between the values in pose pairs
        for pair in POSE_PAIRS:
            partA = pair[0]
            partB = pair[1]
            # if neither are none values then draw
            if points[partA] and points[partB]:
                cv2.line(imSkeleton, points[partA], points[partB], (255, 255, 0), 2)
                cv2.circle(imSkeleton, points[partA], 8, (255, 0, 0), thickness=-1, lineType=cv2.FILLED)
        # add to the lists
        pointsArray.append(points)
        HPEdImages.append(imSkeleton)
    # return
    return(pointsArray, HPEdImages)
    
 