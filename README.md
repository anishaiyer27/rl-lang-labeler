# rl-lang-labeler

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