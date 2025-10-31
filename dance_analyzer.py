

import cv2
import mediapipe as mp
import numpy as np
from typing import Tuple, Optional, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DanceMovementAnalyzer:
   
    def __init__(self, 
                 min_detection_confidence: float = 0.5,
                 min_tracking_confidence: float = 0.5):
        
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
            model_complexity=2  # Use the most accurate model
        )
        
        self.keypoint_data = []
        
    def process_video(self, 
                     input_path: str, 
                     output_path: str,
                     draw_skeleton: bool = True) -> dict:
        
        logger.info(f"Processing video: {input_path}")
        
        # Open video file
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video file: {input_path}")
        
        # Get video properties
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        logger.info(f"Video properties - FPS: {fps}, Size: {width}x{height}, Frames: {total_frames}")
        
        # Initialize video writers for BOTH outputs
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out_overlay = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        # Create skeleton-only output path
        skeleton_only_path = output_path.replace('.mp4', '_skeleton_only.mp4')
        out_skeleton = cv2.VideoWriter(skeleton_only_path, fourcc, fps, (width, height))
        
        frame_count = 0
        detected_frames = 0
        self.keypoint_data = []
        
        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Convert BGR to RGB for MediaPipe
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Process ALL frames (continuous, no skipping)
                results = self.pose.process(rgb_frame)
                
                # Create skeleton-only frame (black background)
                skeleton_frame = np.zeros_like(frame)
                
                # Draw skeleton if pose detected
                if results and results.pose_landmarks:
                    detected_frames += 1
                    
                    if draw_skeleton:
                        # Draw pose landmarks on original frame (overlay)
                        self.mp_drawing.draw_landmarks(
                            frame,
                            results.pose_landmarks,
                            self.mp_pose.POSE_CONNECTIONS,
                            landmark_drawing_spec=self.mp_drawing_styles.get_default_pose_landmarks_style()
                        )
                        
                        # Draw pose landmarks on black background (skeleton only)
                        self.mp_drawing.draw_landmarks(
                            skeleton_frame,
                            results.pose_landmarks,
                            self.mp_pose.POSE_CONNECTIONS,
                            landmark_drawing_spec=self.mp_drawing_styles.get_default_pose_landmarks_style()
                        )
                    
                    # Store keypoint data for this frame
                    keypoints = self._extract_keypoints(results.pose_landmarks, frame_count)
                    self.keypoint_data.append(keypoints)
                
                # Write frames to BOTH output videos
                out_overlay.write(frame)
                out_skeleton.write(skeleton_frame)
                frame_count += 1
                
                if frame_count % 30 == 0:
                    logger.info(f"Processed {frame_count}/{total_frames} frames")
        
        finally:
            cap.release()
            out_overlay.release()
            out_skeleton.release()
        
        # Calculate analysis metrics
        detection_rate = (detected_frames / frame_count * 100) if frame_count > 0 else 0
        
        analysis_results = {
            'input_file': input_path,
            'output_file': output_path,
            'skeleton_only_file': skeleton_only_path,
            'total_frames': frame_count,
            'detected_frames': detected_frames,
            'detection_rate': detection_rate,
            'fps': fps,
            'resolution': (width, height),
            'keypoint_frames': len(self.keypoint_data)
        }
        
        logger.info(f"Processing complete - Detection rate: {detection_rate:.2f}%")
        logger.info(f"Output files: {output_path} and {skeleton_only_path}")
        return analysis_results
    
    def _extract_keypoints(self, pose_landmarks, frame_number: int) -> dict:
        
        keypoints = {
            'frame': frame_number,
            'landmarks': []
        }
        
        for idx, landmark in enumerate(pose_landmarks.landmark):
            keypoints['landmarks'].append({
                'id': idx,
                'name': self.mp_pose.PoseLandmark(idx).name,
                'x': landmark.x,
                'y': landmark.y,
                'z': landmark.z,
                'visibility': landmark.visibility
            })
        
        return keypoints
    
    def get_movement_statistics(self) -> dict:
      
        if not self.keypoint_data:
            return {'error': 'No keypoint data available'}
        
        # Calculate average visibility across all frames
        total_visibility = 0
        landmark_count = 0
        
        for frame_data in self.keypoint_data:
            for landmark in frame_data['landmarks']:
                total_visibility += landmark['visibility']
                landmark_count += 1
        
        avg_visibility = total_visibility / landmark_count if landmark_count > 0 else 0
        
        # Calculate movement range (simplified - based on hand movements)
        movement_stats = {
            'total_frames_analyzed': len(self.keypoint_data),
            'average_visibility': avg_visibility,
            'pose_detected': len(self.keypoint_data) > 0
        }
        
        return movement_stats
    
    def get_keypoint_data(self) -> List[dict]:
        """
        Get raw keypoint data from analysis
        
        Returns:
            List of keypoint dictionaries for each frame
        """
        return self.keypoint_data
    
    def cleanup(self):
        """Release resources"""
        self.pose.close()


def analyze_dance_video(input_path: str, 
                       output_path: str,
                       min_detection_confidence: float = 0.5,
                       min_tracking_confidence: float = 0.5) -> dict:
   
    analyzer = DanceMovementAnalyzer(
        min_detection_confidence=min_detection_confidence,
        min_tracking_confidence=min_tracking_confidence
    )
    
    try:
        results = analyzer.process_video(input_path, output_path)
        movement_stats = analyzer.get_movement_statistics()
        results['movement_statistics'] = movement_stats
        return results
    finally:
        analyzer.cleanup()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python dance_analyzer.py <input_video> <output_video>")
        sys.exit(1)
    
    input_video = sys.argv[1]
    output_video = sys.argv[2]
    
    results = analyze_dance_video(input_video, output_video)
    print("\n=== Analysis Results ===")
    for key, value in results.items():
        print(f"{key}: {value}")
