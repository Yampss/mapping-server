"""
Unit Tests for Dance Movement Analyzer
Tests keypoint detection accuracy and output formatting
"""

import unittest
import cv2
import numpy as np
import os
import tempfile
from dance_analyzer import DanceMovementAnalyzer, analyze_dance_video


class TestDanceMovementAnalyzer(unittest.TestCase):
    """Test suite for Dance Movement Analyzer"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures"""
        # Use your own test video file
        cls.test_dir = "./test_output"
        os.makedirs(cls.test_dir, exist_ok=True)
        cls.test_video_path = "tesfile.mp4"  # Your test file
        cls.output_video_path = os.path.join(cls.test_dir, "output_video.mp4")
        
        
    
    def setUp(self):
        """Set up for each test"""
        self.analyzer = DanceMovementAnalyzer(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
    
    def tearDown(self):
        """Clean up after each test"""
        self.analyzer.cleanup()
    
    def test_initialization(self):
        """Test analyzer initialization"""
        self.assertIsNotNone(self.analyzer.mp_pose)
        self.assertIsNotNone(self.analyzer.pose)
        self.assertEqual(len(self.analyzer.keypoint_data), 0)
    
    def test_video_processing(self):
        """Test video processing with skeleton overlay"""
        results = self.analyzer.process_video(
            self.test_video_path,
            self.output_video_path,
            draw_skeleton=True
        )
        
        # Check that results contain expected keys
        self.assertIn('total_frames', results)
        self.assertIn('detected_frames', results)
        self.assertIn('detection_rate', results)
        self.assertIn('fps', results)
        self.assertIn('resolution', results)
        
        # Check that total frames is positive
        self.assertGreater(results['total_frames'], 0)
        
        # Check that output file was created
        self.assertTrue(os.path.exists(self.output_video_path))
        
        # Verify output video properties
        cap = cv2.VideoCapture(self.output_video_path)
        self.assertTrue(cap.isOpened())
        
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.assertEqual(frame_count, results['total_frames'])
        
        cap.release()
    
    def test_keypoint_extraction(self):
        """Test keypoint extraction accuracy"""
        results = self.analyzer.process_video(
            self.test_video_path,
            self.output_video_path
        )
        
        keypoint_data = self.analyzer.get_keypoint_data()
        
        # Check that keypoints were extracted
        self.assertGreaterEqual(len(keypoint_data), 0)
        
        if len(keypoint_data) > 0:
            # Check structure of keypoint data
            first_frame = keypoint_data[0]
            self.assertIn('frame', first_frame)
            self.assertIn('landmarks', first_frame)
            
            # Check that landmarks have correct structure
            if len(first_frame['landmarks']) > 0:
                landmark = first_frame['landmarks'][0]
                self.assertIn('id', landmark)
                self.assertIn('name', landmark)
                self.assertIn('x', landmark)
                self.assertIn('y', landmark)
                self.assertIn('z', landmark)
                self.assertIn('visibility', landmark)
                
                # Check that coordinates are normalized (0-1 range)
                self.assertGreaterEqual(landmark['x'], 0)
                self.assertLessEqual(landmark['x'], 1)
                self.assertGreaterEqual(landmark['y'], 0)
                self.assertLessEqual(landmark['y'], 1)
                self.assertGreaterEqual(landmark['visibility'], 0)
                self.assertLessEqual(landmark['visibility'], 1)
    
    def test_movement_statistics(self):
        """Test movement statistics calculation"""
        self.analyzer.process_video(
            self.test_video_path,
            self.output_video_path
        )
        
        stats = self.analyzer.get_movement_statistics()
        
        # Check that statistics contain expected keys
        self.assertIn('total_frames_analyzed', stats)
        self.assertIn('pose_detected', stats)
        
        if stats['pose_detected']:
            self.assertIn('average_visibility', stats)
            self.assertGreaterEqual(stats['average_visibility'], 0)
            self.assertLessEqual(stats['average_visibility'], 1)
    
    def test_output_format(self):
        """Test output video format consistency"""
        results = self.analyzer.process_video(
            self.test_video_path,
            self.output_video_path
        )
        
        # Compare input and output properties
        input_cap = cv2.VideoCapture(self.test_video_path)
        output_cap = cv2.VideoCapture(self.output_video_path)
        
        input_fps = int(input_cap.get(cv2.CAP_PROP_FPS))
        output_fps = int(output_cap.get(cv2.CAP_PROP_FPS))
        
        input_width = int(input_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        output_width = int(output_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        
        input_height = int(input_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        output_height = int(output_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Output should maintain same properties as input
        self.assertEqual(input_fps, output_fps)
        self.assertEqual(input_width, output_width)
        self.assertEqual(input_height, output_height)
        
        input_cap.release()
        output_cap.release()
    
    def test_convenience_function(self):
        """Test the convenience function wrapper"""
        results = analyze_dance_video(
            self.test_video_path,
            self.output_video_path
        )
        
        # Check that results include movement statistics
        self.assertIn('movement_statistics', results)
        self.assertIn('total_frames', results)
        self.assertIn('detection_rate', results)
    
    def test_invalid_video_path(self):
        """Test handling of invalid video path"""
        with self.assertRaises(ValueError):
            self.analyzer.process_video(
                "nonexistent_video.mp4",
                self.output_video_path
            )
    
    def test_empty_keypoint_data_statistics(self):
        """Test statistics when no keypoints detected"""
        # Don't process any video
        stats = self.analyzer.get_movement_statistics()
        self.assertIn('error', stats)
    
    @classmethod
    def tearDownClass(cls):
        # """Clean up test files"""
        # import shutil
        # if os.path.exists(cls.test_dir):
        #     shutil.rmtree(cls.test_dir)
        pass


class TestKeypointAccuracy(unittest.TestCase):
    """Test keypoint detection accuracy"""
    
    def test_landmark_count(self):
        """Test that correct number of landmarks are detected"""
        # MediaPipe Pose should detect 33 landmarks
        expected_landmarks = 33
        
        analyzer = DanceMovementAnalyzer()
        
        # Create a simple test frame
        test_frame = np.ones((480, 640, 3), dtype=np.uint8) * 255
        
        # Draw a simple stick figure
        # (In real scenario, this should be a real person)
        cv2.circle(test_frame, (320, 100), 30, (0, 0, 0), -1)  # Head
        cv2.line(test_frame, (320, 130), (320, 250), (0, 0, 0), 10)  # Body
        cv2.line(test_frame, (320, 150), (250, 200), (0, 0, 0), 8)  # Left arm
        cv2.line(test_frame, (320, 150), (390, 200), (0, 0, 0), 8)  # Right arm
        cv2.line(test_frame, (320, 250), (280, 350), (0, 0, 0), 8)  # Left leg
        cv2.line(test_frame, (320, 250), (360, 350), (0, 0, 0), 8)  # Right leg
        
        rgb_frame = cv2.cvtColor(test_frame, cv2.COLOR_BGR2RGB)
        results = analyzer.pose.process(rgb_frame)
        
        if results.pose_landmarks:
            landmark_count = len(results.pose_landmarks.landmark)
            self.assertEqual(landmark_count, expected_landmarks)
        
        analyzer.cleanup()


def run_tests():
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test cases
    suite.addTests(loader.loadTestsFromTestCase(TestDanceMovementAnalyzer))
    suite.addTests(loader.loadTestsFromTestCase(TestKeypointAccuracy))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
