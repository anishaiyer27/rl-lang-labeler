"""
    Labeling GUI to allow fluid scrubbing through frames and manual labeling of frames with natural language
    for downstream tasks.

    Framework to render GUI for mp4 input, frame extraction, and labeling editor.
    
    Anisha's Notes:
    Label Types:
        Low-level
        Compositional

    Prompting and specifications for what types of labels the user should input:
        Just verbs (low-level / compositional) or scene annotation?

    More efficient data storage if we work with observation arrays instead of MP4 files
        In Avalon: display_video(observation_array) -> MP4
        Serialize arrays of observation objects and upload those to GUI
        (either with intermediate local download or by swapping filepath st CWD is same
        as game play CWD)

        This also preserves frame_id information, and might make scrubbing through timeseries
        easier on display side.

        Output unfiltered csv with (start,end) times for each labeling instance.
        Transform to unfiltered csv with (start_frame_id, end_frame_id)

        Follow similar format from human scores datafile on Avalon repo

        Export data from rows to queriable JSONs to map labels to frame tuples over all files

    TODOs:
        Debug find_frame()
        Either add frame by frame image rendering to tkinter.Canvas or cv2.imshow() window
         for frame selection
         

"""

from tkinter import *
import tkinter.filedialog
import cv2
import ipywidgets as widget

import os
import csv
import subprocess as sp


class LabelerGUI:

    def __init__(self, root):

        self.window = root                    # main GUI context
        self.window.title("Avalon Labeler")   # title of window
        self.window.geometry("6000x3000")     # size of GUI window
        self.main_frame = Frame(root)       # main frame into which all the Gui components will be placed
        self.main_frame.pack()              # pack() basically sets up/inserts the element (turns it on)
        self.C = Canvas(self.window)
        self.C.pack()

        self.video_path = None
        self.output_path = None
        self.video = None

        self.video_file = None
        self.video_filename = None
        self.video_filepath = None

        self.audio_regions = []
        self.audio_frame_regions = None
        self.video_frames = []
        self.video_map = {}
        self.video_frame_regions = None

        self.load_video_button = Button(self.C,
                                        text="Load Video",
                                        command=self.load_video)

        self.play_video_button = Button(self.C,
                                        text="Play Video",
                                        command=self.play_video)
        
        self.label_video_button = Button(self.C,
                                        text="Label Video",
                                        command=self.label_video)
        
        self.clear_button = Button(self.C,
                                   text="Clear",
                                   command=self.clear)
        
        self.video_loaded_label = Label(self.C, text="video loaded", fg="blue")
        self.video_played_label = Label(self.C, text="frames extracted", fg="blue")
        
        self.instructions1 = Label(self.C, text="1. Load mp4 file", fg="navy")
        self.instructions2 = Label(self.C, text="2. Play video to extract frames", fg="navy")
        self.instructions3 = Label(self.C, text="3. Open labeler using Label button", fg="navy")
        self.instructions1.grid(row=4, column=1)
        self.instructions2.grid(row=5, column=1)
        self.instructions3.grid(row=6, column=1)
        
        self.load_video_button.grid(row=1, column=1)
        self.play_video_button.grid(row=2, column=1)
        self.label_video_button.grid(row=3, column=1)
        self.clear_button.grid(row=3, column=2)

        self.temp_audio_scrub_output = ""

    def load_video(self):
        self.video_file = tkinter.filedialog.askopenfilename()
        self.video_filename = os.path.split(self.video_file)[1]

        print("path split 0" + str(os.path.split(self.video_file)[0]))
        self.video_loaded_label.grid(row=1, column=2)
        
    def play_video(self):
        self.video=cv2.VideoCapture(self.video_file)
        last_ts=0.0
        while True:
            grabbed, frame=self.video.read()
            if not grabbed:
                print("End of video")
                self.video_played_label.grid(row=2, column=2)
                break
            if cv2.waitKey(28) & 0xFF == ord("q"):
                break
            #self.C.create_image(0,0,image=frame)
            self.video_frames.append(frame)
            this_ts = self.video.get(cv2.CAP_PROP_POS_MSEC)
            self.video_map[(last_ts,this_ts)] = frame
            last_ts = this_ts
            cv2.imshow("Video", frame)
        self.video.release()
        cv2.destroyAllWindows()
        
    def find_frame(self, ts):
        keys = list(self.video_map.keys())
        print(keys)
        index = self.find_frame_helper(len(keys)//2, keys, float(ts))
        return self.video_map[keys[index]]
                
    def find_frame_helper(self, i, keys, ts):
        if ts < keys[i][0]:
            return self.find_frame_helper(self, i-1, ts)
        elif ts > keys[i][1]:
            return self.find_frame_helper(self, i+1, ts)
        else:
            return i
    
    def nothing(self,x):
        pass
    
    def label_video(self):
        keys = list(self.video_map.keys())
        print(keys[0])
        start = keys[0][0]
        end = keys[-1][1]
        cv2.createTrackbar('time','Video',int(start),int(end),self.nothing)
        
        #w = Scale(self.C, from_=start, to=end, length=len(keys), tickinterval=0.5, orient=HORIZONTAL)
        #w.pack()
        #w.grid(row=9, column=1)
        t = cv2.getTrackbarPos('time','Video')
        #ts = w.get()
        while True:
            cv2.imshow("Video", self.find_frame(t))
        self.video.release()
        cv2.destroyAllWindows()
    
    def clear(self):
        # currently, the "clear" button leaves the mask
        # filepath in place rather than clearing it, so you
        # can reuse it for the next video you want to process

        self.video_file = None


        if self.video_loaded_label:
            self.video_loaded_label.grid_remove()

    """
    From an online resource: could be repurposed to segment frame regions.
    Kept as reference for useful methods and functionality.
    
    def scrub_video(self):

        between_statements = ""

        for index, region in enumerate(self.video_frame_regions):
            statement = "between(t,{},{})".format(region[0],region[1])
            if index == len(self.video_frame_regions) - 1:
                between_statements += statement
            else:
                between_statements += statement + "+"

        if not self.audio_frame_regions:
            command = ['ffmpeg',
                       '-i',
                       self.video_file,   # using original video
                       '-i',
                       self.mask_path,
                       '-filter_complex',
                       '\"[0:v][1:v] overlay=0:0:enable=\'{}\'\"'.format(between_statements),
                       '-pix_fmt',
                       'yuv420p',
                       '-c:a',
                       'copy',
                       self.output_path]
        else:
            command = ['ffmpeg',
                       '-i',
                       self.temp_audio_scrub_output,   # we're using the output from the audio scrub
                       '-i',
                       self.mask_path,
                       '-filter_complex',
                       '\"[0:v][1:v] overlay=0:0:enable=\'{}\'\"'.format(between_statements),
                       '-pix_fmt',
                       'yuv420p',
                       '-c:a',
                       'copy',
                       self.output_path]

        command_string = ""

        for element in command:
            command_string += " " + element

        print("command: " + command_string)

        pipe = sp.Popen(command_string, stdout=sp.PIPE, bufsize=10**8, shell=True)
        pipe.communicate()  # blocks until the subprocess is complete

        if not self.audio_frame_regions:
            return
        else:
            os.remove(self.temp_audio_scrub_output)

    def build_audio_comparison_commands(self):
        This takes the audio regions (in frame onset/offset format)
        and builds a compounded list of if statements that will be
        part of the command that is piped to ffmpeg. They will end
        up in the form:
            gt(t,a_onset)*lt(t,a_offset)+gt(t,b_onset)*lt(t,b_offset)+gt(t,c_onset)*lt(t,c_offset)
        :return: compounded if statement
        if_statments = ""

        for index, region in enumerate(self.audio_frame_regions):

            statement = "gt(t,{})*lt(t,{})".format(region[0],
                                                   region[1])
            if index == len(self.audio_frame_regions) - 1:
                if_statments += statement
            else:
                if_statments += statement + "+"

        print(if_statments)
        return if_statments


    def ms_to_s(self, timestamps):
        Converts a list of timestamps, originally in milliseconds,
        to their corresponding second values, The input list should
        be a list of lists, for example:
                [[1000, 2200], [3000, 5500], [8000, 14000]]
        :param timestamps: list of millisecond onset/offsets
        :return: converted timestamps
        results = []

        for region in timestamps:
            results.append([region[0]/1000, region[1]/1000])

        print("results: " + str(results))

        return results
    
    """

if __name__ == "__main__":

    root = Tk()
    app = LabelerGUI(root)
    root.mainloop()