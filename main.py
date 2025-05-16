import video_finder_class 
import video_processor_class

def main():
    user_input_directory = input("Enter a directory to a video")
    user_input_output_directory = input("Enter an ouput directory. Enter Nothing for default. Default: frames_completed")
    if user_input_output_directory is None:
        user_input_output_directory = "frames_completed"


    videos = []
    video_finder = video_finder_class.videoFinder()
    videos = video_finder.find_videos(user_input_directory)

    video_processor = video_processor_class.VideoProcessor()

    video_processor.get_user_selected_video_extension()

    video_processor.get_user_selected_audio_extension()

    output_dir = 'frames_completed'
    
    for video_path in videos:
        existing_parts = video_processor.split_video(video_path) 

    for part in existing_parts:
        video_processor.process_video(part, output_dir, analyze_xth_frame=1)

if __name__ == "__main__":
    main()