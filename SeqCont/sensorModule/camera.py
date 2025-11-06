#
# camera_module.py
#
import cv2
import base64
import time
import util

#logger = util.logging.getLogger("MyApp.camera") 

class cameraModule:
    """
    카메라 모듈 클래스
    OpenCV를 사용하여 카메라에서 이미지를 캡처하고 base64로 인코딩합니다.
    """
    gstreamer_pipeline = (
    "nvarguscamerasrc ! "
    "nvvidconv ! "
    "video/x-raw(memory:NVMM), format=NV12 ! "
    "nvvidconv ! "
    "video/x-raw(format=BGRx, width=640, height=480) ! "
    "videoconvert ! "
    "appsink"
    )


    def __init__(self, camera_index=0):
        """
        카메라 초기화.
        :param camera_index: 카메라 장치 인덱스 (일반적으로 0)
        """
        self.camera_index = camera_index
        
    def init_camera(self):
        self.cap = cv2.VideoCapture(self.gstreamer_pipeline, cv2.CAP_GSTREAMER)
        if not self.cap.isOpened():
            print(f"Error: 카메라 장치({self.camera_index})를 열 수 없습니다.")
        else:
            print(f"카메라 장치({self.camera_index})가 성공적으로 열렸습니다.")

    def get_camera_idx(self):
        return self.camera_index
    def capture_images(self, num_images=1):
        """
        지정된 수의 이미지를 캡처하고 파일로 저장하며,
        base64 문자열 리스트로 반환합니다.
        
        :param num_images: 캡처할 이미지 수
        :return: base64 인코딩된 이미지 문자열 리스트
        """
        if not self.cap.isOpened():
            print("카메라가 준비되지 않았습니다.")
            return False
        ret, frame = self.cap.read()
        encoded_string = None
        if ret:               
            # 2. 이미지를 Base64로 인코딩하여 리스트에 추가
            is_success, buffer = cv2.imencode(".jpg", frame)
            if is_success:
                encoded_string = base64.b64encode(buffer).decode("utf-8")
                # print(f"  - {i+1}번째 이미지 인코딩 완료.")
        # 연속 촬영 시 약간의 딜레이 추가
        time.sleep(0.5)

        return encoded_string

    def release_camera(self):
        """
        카메라 장치 리소스 해제
        """
        if self.cap.isOpened():
            self.cap.release()
            print("카메라 리소스가 해제되었습니다.")