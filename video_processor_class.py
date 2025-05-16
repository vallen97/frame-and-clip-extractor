from concurrent.futures import ThreadPoolExecutor
import cv2
import ffmpeg
import json
import mediapipe as mp
import numpy as np
import os
from pathlib import Path
from PIL import Image as PILImage, ImageCms
import subprocess
from tqdm import tqdm
import torch
from ultralytics import YOLO
import frame_image_saver_class
import video_encoder_class


class VideoProcessor:
    def __init__(self,):
        "Process video frame by frame, look for items in frame image here"
        return