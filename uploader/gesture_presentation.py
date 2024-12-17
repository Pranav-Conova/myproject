import cv2
import os
import numpy as np
from cvzone.HandTrackingModule import HandDetector

def run_presentation(output_dir,sasi):
    gestureThreshold = 450
    folderPath = output_dir
    cap = cv2.VideoCapture(0)
    cap.set(3, 1280)
    cap.set(4, 720)

    detectorHand = HandDetector(detectionCon=0.8, maxHands=1)
    delay = 10
    buttonPressed = False
    counter = 0
    imgNumber = 0
    annotations = [[]]
    annotationNumber = -1
    annotationStart = False
    exitGestureStage = 0

    pathImages = sorted(os.listdir(folderPath), key=len)

    while True:
        success, img = cap.read()
        if not success:
            break

        img = cv2.flip(img, 1)
        pathFullImage = os.path.join(folderPath, pathImages[imgNumber])
        imgCurrent = cv2.imread(pathFullImage)

        screenHeight, screenWidth, _ = img.shape
        imgCurrent = cv2.resize(imgCurrent, (screenWidth, screenHeight))

        hands, _ = detectorHand.findHands(img)
        cv2.line(img, (0, gestureThreshold), (1280, gestureThreshold), (0, 255, 0), 10)

        if hands and not buttonPressed:
            hand = hands[0]
            cx, cy = hand["center"]
            lmList = hand["lmList"]
            fingers = detectorHand.fingersUp(hand)

            xVal = int(np.interp(lmList[8][0], [0, 1280], [0, screenWidth]))
            yVal = int(np.interp(lmList[8][1], [0, 720], [0, screenHeight]))
            indexFinger = xVal, yVal

            if cy <= gestureThreshold:
                if fingers == [1, 0, 0, 0, 0] and imgNumber > 0:
                    imgNumber -= 1
                    annotations = [[]]
                    annotationNumber = -1
                    buttonPressed = True

                if fingers == [0, 0, 0, 0, 1] and imgNumber < len(pathImages) - 1:
                    imgNumber += 1
                    annotations = [[]]
                    annotationNumber = -1
                    buttonPressed = True

                if exitGestureStage == 0 and fingers == [0, 1, 1, 1, 1]:
                    exitGestureStage = 1
                    buttonPressed = True

                if exitGestureStage == 1 and fingers == [1, 1, 1, 1, 1]:
                    break

            if fingers == [0, 1, 0, 0, 0]:
                if not annotationStart:
                    annotationStart = True
                    annotationNumber += 1
                    annotations.append([])
                annotations[annotationNumber].append(indexFinger)
                cv2.circle(imgCurrent, indexFinger, 12, (0, 0, 255), cv2.FILLED)

            else:
                annotationStart = False

            if fingers == [0, 1, 1, 1, 0] and annotations:
                annotations.pop(-1)
                annotationNumber -= 1
                buttonPressed = True

        if buttonPressed:
            counter += 1
            if counter > delay:
                counter = 0
                buttonPressed = False

        for annotation in annotations:
            for j in range(1, len(annotation)):
                cv2.line(imgCurrent, annotation[j - 1], annotation[j], (0, 0, 255), 12)

        # Add small camera frame to the top-right corner
        if sasi == 1:
            camera_small = cv2.resize(img, (200, 150))  # Small camera window size
            imgCurrent[10:160, screenWidth - 210:screenWidth - 10] = camera_small.copy()  # Use copy to avoid modifying the original frame

        ret, buffer = cv2.imencode('.jpg', imgCurrent)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    cap.release()
