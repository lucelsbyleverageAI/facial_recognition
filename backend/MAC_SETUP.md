# Facial Recognition Backend Setup for macOS on Apple Silicon (M1/M2/M3)

This guide explains how to set up the facial recognition backend on macOS with Apple Silicon processors (M1, M2, M3).

## Prerequisites

- macOS running on Apple Silicon (M1, M2, or M3)
- Python 3.10 (installed via pyenv or homebrew)
- Git

## Step 1: Create a Virtual Environment

```bash
# Create a Python 3.10 virtual environment
python3.10 -m venv .venv

# Activate the virtual environment
source .venv/bin/activate

# Verify the Python version
python --version  # Should output Python 3.10.x
```

## Step 2: Build tensorflow-io-gcs-filesystem from Source

Since tensorflow-io-gcs-filesystem doesn't have official wheels for Apple Silicon, we need to build it from source:

```bash
# Install wheel package
pip install wheel

# Clone the tensorflow-io repository
cd /tmp
git clone https://github.com/tensorflow/io.git tensorflow-io
cd tensorflow-io

# Build the tensorflow-io-gcs-filesystem wheel
python setup.py -q bdist_wheel --project tensorflow_io_gcs_filesystem

# Install the wheel
cd dist
pip install $(ls tensorflow_io_gcs_filesystem-*.whl) --force-reinstall

# Go back to your project directory
cd /path/to/your/project
```

## Step 3: Install TensorFlow and Related Packages

```bash
# Install TensorFlow with Metal acceleration
pip install tensorflow==2.19.0 tensorflow-metal

# Install other dependencies
pip install numpy opencv-python pillow deepface retina-face matplotlib pandas psutil watchdog
pip install gql fastapi uvicorn pytest pytest-asyncio requests-toolbelt aiohttp python-dotenv asyncpg boto3 httpx jinja2
```

## Step 4: Verify Installation

Create a simple test script to verify that the facial recognition packages are working:

```python
import cv2
import numpy as np
from deepface import DeepFace
from retinaface import RetinaFace

# Create a test image and save it
test_image = np.ones((300, 300, 3), dtype=np.uint8) * 128
cv2.imwrite("test_face.jpg", test_image)

# Test RetinaFace
faces = RetinaFace.detect_faces("test_face.jpg")
print(f"RetinaFace detection result: {faces}")

# Test DeepFace
faces = DeepFace.extract_faces("test_face.jpg", detector_backend="retinaface", enforce_detection=False)
print(f"DeepFace detected {len(faces)} face(s)")
```

## Known Issues and Solutions

1. **Issue**: `tensorflow-io-gcs-filesystem` lacks official wheels for Apple Silicon.
   **Solution**: Build from source as described in Step 2.

2. **Issue**: DeepFace face detection might fail with real-world images.
   **Solution**: Use `enforce_detection=False` parameter when calling DeepFace functions.

3. **Issue**: Some TensorFlow versions might not be compatible with macOS.
   **Solution**: We recommend using TensorFlow 2.19.0 with tensorflow-metal for optimal performance on Apple Silicon.

## Running the Test Script

To verify that the facial recognition backend is working correctly, run the test script:

```bash
python test_recognition.py
```

The test script should look like this:

```python
import cv2
from deepface import DeepFace
from retinaface import RetinaFace

# Test image path
image_path = "test_image.jpg"  # Replace with your test image

# Load image
img = cv2.imread(image_path)
if img is None:
    print(f"Failed to load image: {image_path}")
    exit(1)

print("Testing RetinaFace detection...")
# RetinaFace detection
faces = RetinaFace.detect_faces(image_path)
print(f"RetinaFace detected {len(faces)} face(s)")
for face_key in faces:
    face = faces[face_key]
    facial_area = face["facial_area"]
    landmarks = face["landmarks"]
    print(f"Face {face_key} - Score: {face['score']:.4f}")
    print(f"  Bounding box: {facial_area}")
    print(f"  Landmarks: {landmarks}")

print("\nTesting DeepFace analysis...")
# DeepFace analysis
try:
    results = DeepFace.analyze(
        img_path=image_path, 
        actions=['age', 'gender', 'emotion', 'race'],
        enforce_detection=False
    )
    
    if isinstance(results, list):
        for i, result in enumerate(results):
            print(f"Face {i+1} analysis:")
            print(f"  Age: {result['age']}")
            print(f"  Gender: {result['gender']}")
            print(f"  Dominant emotion: {result['dominant_emotion']}")
            print(f"  Dominant race: {result['dominant_race']}")
    else:
        print("Face analysis:")
        print(f"  Age: {results['age']}")
        print(f"  Gender: {results['gender']}")
        print(f"  Dominant emotion: {results['dominant_emotion']}")
        print(f"  Dominant race: {results['dominant_race']}")
except Exception as e:
    print(f"DeepFace analysis failed: {e}")

print("\nFacial recognition backend test complete!")
```

Note: The test script will fail to connect to the GraphQL database without proper credentials, but it confirms that the facial recognition components (RetinaFace and DeepFace) are working correctly. 