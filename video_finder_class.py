import os

class videoFinder:

    # initalize data
    def __init__(self):
        self.__results = ''
        self.__root_folder = "" # directory the user passes to recursively look for videos ]
        self.__video_extensions = ["webm", "mkv", "flv", "vob", "ogv", "ogg", "rrc", "gifv", "mng", "mov", "avi", "qt", "wmv", "yuv", "rm", "asf", "amv", "mp4", "m4p", "m4v", "mpg", "mp2", "mpeg", "mpe", "mpv", "m4v", "svi", "3gp", "3g2", "mxf", "roq", "nsv", "flv", "f4v", "f4p", "f4a", "f4b", "mod"]
        self.__video_paths = []
        self.__input_directory = ''
    # end def __init__

    # recursively find videos in a directory
    # return list of all videos found
    def find_videos(self, input_directory):
        self.__input_directory = input_directory
        for root, dirs, files in os.walk(self.__input_directory):
            for file in files:
                if file.endswith(tuple(self.__video_extensions)):
                    self.__video_paths.append( os.path.join(root, file))

        return self.__video_paths