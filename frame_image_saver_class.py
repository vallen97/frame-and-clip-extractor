import cv2
import imagehash
import numpy as np
import os
from pathlib import Path
from PIL import Image as PILImage, ImageCms
from tqdm import tqdm
import torch
from ultralytics import YOLO

class FrameImageSaver:
    def __init__(self, icc_profile_path="AdobeRGB1998.icc"):
        # Set the AdobeRGB1998 ICC profile path
        self.adobe_rgb_icc_path = icc_profile_path
        self.__iamge_extensions = [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".tif", ".ppm", ".pgm", ".pbm", ".pnm", ".webp", ".ico", ".icns", ".msp", ".pcx", ".blp", ".dds", ".eps", ".sgi", ".tga", ".xbm", ".cur", ".dcx", ".fits", ".fli", ".flc", ".fpx", ".gbr", ".gd", ".imt", ".iptc", ".mcidas", ".mic", ".mpo", ".pcd", ".pixar", ".psd", ".qoi", ".sun", ".wal", ".wmf", ".emf"]
        self.__selected_image_extension = ''
        self.__is_upscale_denoise = False
        self.__is_image_folder_zipped = False
        self.__image_hash = []
        self.__image_hash_threshold = 2

    def denoise_and_upscale(self, frame):
        if self.__is_upscale_denoise:
            frame = cv2.fastNlMeansDenoisingColored(frame, None, 10, 10, 7, 21)
            height, width = frame.shape[:2]
            frame = cv2.resize(frame, (width * 2, height * 2), interpolation=cv2.INTER_CUBIC)  # 2x upscale
        return frame

    def save_frame_as_image(self, frame, frames_folder, frame_num, item_str):
        
        image_filename = os.path.join(frames_folder, f"frame_{frame_num}_{item_str}{self.__selected_image_extension}")
        
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = PILImage.fromarray(frame_rgb)

        start_frame, end_frame = self.is_similar_image(pil_image, frame_num)


        if(start_frame !=0 and end_frame != 0):
            try:
                profile = ImageCms.getOpenProfile(self.adobe_rgb_icc_path)
                pil_image = ImageCms.profileToProfile(pil_image, profile, profile, outputMode='RGB')
                pil_image.save(image_filename, format=self.__selected_image_extension[1:].upper(), quality=90, icc_profile=profile.tobytes())
                print(f"Saved frame {frame_num} with {item_str} as JPEG with AdobeRGB1998 profile.")
            except Exception as e:
                pil_image.save(image_filename, format=self.__selected_image_extension[1:].upper(), quality=90)
                print(f"Saved frame {frame_num} with {item_str} as JPEG without ICC profile. Error: {e}")
            return [start_frame, end_frame]
        
        return [0,0]

    def compress_to_zip(self, output_dir, clip_name):
        if self.__is_image_folder_zipped:

            zip_filename = os.path.join(output_dir, f"{clip_name}.zip")
            with ZipFile(zip_filename, 'w') as zipf:
                for folder in [os.path.join(output_dir, clip_name, "frames"), os.path.join(output_dir, clip_name, "clips")]:
                    for root, dirs, files in os.walk(folder):
                        for file in files:
                            zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), output_dir))

    def compute_image_hash(image_path):
        """Compute a hash for the image for similarity comparison."""
        try:
            with PILImage.open(image_path) as img:
                img_hash = imagehash.average_hash(img)
                return img_hash
        except Exception as e:
            print(f"Error computing hash for {image_path}: {e}")
            return None
        
    def is_similar_image(self, frame, frame_num ):
        
        original_hash = imagehash.average_hash(frame)
        
        hash_as_str = imagehash.hex_to_hash(str(original_hash))

        ''' Default values that should be overwritten to get where the clip should be'''
        end_frame_time = 0
        start_frame_time = 108000 # 30 minutes in seconds * 60 frames per second, Assuming this is the largest amount of frames in a video
        
        
        for i_h in self.__image_hash:
            existing_hash = str(i_h['hash'])
            existing_hash = imagehash.hex_to_hash(existing_hash)

            # print(existing_hash, i_h['frame_start'])
            if int(i_h['frame_start']) < start_frame_time:
                start_frame_time = int(i_h['frame_start'])
            elif int(i_h['frame_start']) > end_frame_time:
                end_frame_time = int(i_h['frame_start'])
                

            
            if(existing_hash - hash_as_str <= self.__image_hash_threshold):
                print("images are the same")
                
            else:
                if not any(d['hash'] == hash_as_str for d in self.__image_hash):
                    # print("IN HERE")
                    self.__image_hash = []
                    thisdict = {
                        "hash": hash_as_str,
                        "frame_start": frame_num,
                    }
                    self.__image_hash.append(thisdict)
                    start_frame_time = int(frame_num)
                    break

        # Set the first frame
        if len(self.__image_hash) == 0:
            thisdict = {
            "hash": hash_as_str,
            "frame_start": frame_num,
            }
            self.__image_hash.append(thisdict)

        if end_frame_time != 0 and start_frame_time != 108000 and end_frame_time < start_frame_time:
            return [end_frame_time, start_frame_time]


        return [0, 0]    

    
    # ask the user what image type to save as, if they want to upscale and denoise
    def set_values(self):
        ''' TESTING comment below and remove return to get user inputted'''
        self.__selected_image_extension = ".jpeg"
        self.__is_upscale_denoise = False
        self.__is_image_folder_zipped = False

        return


        for i in range(len(self.__iamge_extensions)):
            print(f'{i+1}) {self.__iamge_extensions[i]}')

        select_image_type = int(input("Enter a number to select the image to be saved as: "))-1
        if select_image_type > len(self.__iamge_extensions):
            select_image_type = len(self.__iamge_extensions) -1
        
        self.__selected_image_extension = self.__iamge_extensions[select_image_type]


        user_upscaleAndDenoise = input("Do you want to upscale 2X and denoise: (Yes/No)").lower()
        if user_upscaleAndDenoise == "yes" or user_upscaleAndDenoise == "y":
            self.__is_upscale_denoise = True


        user_zipfolder = input("Do you want to make a zip file of all of the frames: (Yes/No)").lower()
        if user_zipfolder == "yes" or user_zipfolder == "y":
            self.__is_image_folder_zipped  = True
        
    def get_upscale_denoise(self):
        return self.__is_upscale_denoise



