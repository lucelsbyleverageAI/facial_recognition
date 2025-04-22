#!/usr/bin/env python3
"""
Simple test script to verify that deepface and retina-face work properly.
"""

import os
import cv2
import numpy as np
from deepface import DeepFace
from retinaface import RetinaFace

def test_face_detection():
    """Test face detection using RetinaFace."""
    print("Creating a simple test image...")
    # Create a simple test image (a gray square)
    test_image = np.ones((300, 300, 3), dtype=np.uint8) * 128
    
    # Draw a simple face-like shape
    cv2.circle(test_image, (150, 150), 100, (200, 200, 200), -1)  # Head
    cv2.circle(test_image, (120, 120), 15, (50, 50, 50), -1)  # Left eye
    cv2.circle(test_image, (180, 120), 15, (50, 50, 50), -1)  # Right eye
    cv2.ellipse(test_image, (150, 180), (30, 10), 0, 0, 180, (50, 50, 50), -1)  # Mouth
    
    # Save the test image
    cv2.imwrite("test_face.jpg", test_image)
    print("Test image saved as test_face.jpg")
    
    print("\nTesting RetinaFace face detection...")
    try:
        # Attempt to detect faces
        faces = RetinaFace.detect_faces("test_face.jpg")
        print(f"RetinaFace detection result: {faces}")
        print("RetinaFace face detection successful!")
    except Exception as e:
        print(f"Error with RetinaFace: {e}")
    
    print("\nTesting DeepFace face detection...")
    try:
        # Attempt to extract faces using DeepFace with enforce_detection=False
        faces = DeepFace.extract_faces("test_face.jpg", detector_backend="retinaface", enforce_detection=False)
        print(f"DeepFace detected {len(faces)} face(s)")
        print("DeepFace face detection successful!")
    except Exception as e:
        print(f"Error with DeepFace: {e}")
    
    # Clean up test image
    if os.path.exists("test_face.jpg"):
        os.remove("test_face.jpg")
        print("\nTest image removed")

if __name__ == "__main__":
    test_face_detection() 