import cv2
import mediapipe as mp
import numpy as np

class FaceHandTracker:
    def __init__(self):
        # Initialize MediaPipe solutions
        self.mp_holistic = mp.solutions.holistic
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        # Initialize the holistic model
        self.holistic = self.mp_holistic.Holistic(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5)

    def process_frame(self, frame):
        # Convert BGR to RGB
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process the image and detect landmarks
        results = self.holistic.process(image)
        
        # Convert back to BGR for displaying
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        
        # Draw face landmarks
        if results.face_landmarks:
            self.mp_drawing.draw_landmarks(
                image,
                results.face_landmarks,
                self.mp_holistic.FACEMESH_CONTOURS,
                landmark_drawing_spec=None,
                connection_drawing_spec=self.mp_drawing_styles.get_default_face_mesh_contours_style())

        # Draw pose landmarks (arms)
        if results.pose_landmarks:
            self.mp_drawing.draw_landmarks(
                image,
                results.pose_landmarks,
                self.mp_holistic.POSE_CONNECTIONS,
                landmark_drawing_spec=self.mp_drawing_styles.get_default_pose_landmarks_style())

        # Draw hand landmarks
        for hand_landmarks in [results.left_hand_landmarks, results.right_hand_landmarks]:
            if hand_landmarks:
                self.mp_drawing.draw_landmarks(
                    image,
                    hand_landmarks,
                    self.mp_holistic.HAND_CONNECTIONS,
                    landmark_drawing_spec=self.mp_drawing_styles.get_default_hand_landmarks_style(),
                    connection_drawing_spec=self.mp_drawing_styles.get_default_hand_connections_style())
        
        return image

    def run(self):
        # Initialize webcam
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("Error: Could not access the webcam.")
            print("Please make sure:")
            print("1. Your webcam is properly connected")
            print("2. You have granted camera permissions to the application")
            print("3. No other application is currently using the webcam")
            return

        print("Successfully opened webcam. Starting tracking...")
        print("Press 'q' to quit the application")

        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                print("Failed to read from webcam")
                break

            # Process the frame
            processed_frame = self.process_frame(frame)
            
            # Display the frame
            cv2.imshow('Face and Hand Tracking', processed_frame)
            
            # Break the loop if 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        # Clean up
        cap.release()
        cv2.destroyAllWindows()
        self.holistic.close()

if __name__ == "__main__":
    tracker = FaceHandTracker()
    tracker.run()
