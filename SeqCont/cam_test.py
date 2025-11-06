#
# camera_module.py
#
import cv2
import base64
import time
import util
# GSTREAMER_PIPELINE = (
#     "nvarguscamerasrc sensor-id=0 ! "
#     "video/x-raw(memory:NVMM), width=640, height=480, format=NV12, framerate=30/1 ! "
#     "nvvidconv ! "
#     "video/x-raw(memory:system), format=BGRx ! "
#     "videoconvert ! "
#     "video/x-raw, format=BGR ! "
#     "appsink drop=true max-buffers=1"
# )
GSTREAMER_PIPELINE = (
"nvarguscamerasrc ! "
"nvvidconv ! "
"video/x-raw(memory:NVMM), format=NV12 ! "
"nvvidconv ! "
"video/x-raw(format=BGRx, width=640, height=480) ! "
"videoconvert ! "
"videoflip method=clockwise !"
"video/x-raw, format=BGR ! "
"appsink"
)

capture = cv2.VideoCapture(GSTREAMER_PIPELINE, cv2.CAP_GSTREAMER)

if not capture.isOpened():
    print("Error: Failed to open camera. Check pipeline and camera status.")
    exit() # Exit immediately if camera isn't open

while True:
    # 33ms마다 반복문을 실행 (approx 30 FPS)
    ret, frame = capture.read() 
    
    if not ret or frame is None:
        print("Error: Failed to capture frame.")
        break # Exit loop on capture failure

    cv2.imshow("VideoFrame", frame)
    
    # Check for 'q' key press to exit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break 

capture.release()
cv2.destroyAllWindows()
