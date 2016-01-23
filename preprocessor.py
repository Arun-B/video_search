# -*- coding: utf-8 -*-
# above line required to make non ascii characters work
# ffmpeg -i test.mp4 -vf select='gt(scene\,0.4)' -vsync vfr thumb%04d.png
# use above to get thumbnail output
import os, re
from cos_sim import termFrequency, inverseDocumentFrequency, tfIdf, sim
# plot sentences are split and mapped to subtitles
from nltk.tokenize import sent_tokenize, word_tokenize    # nltk sentence tokenizer, nltk word tokenizer
from nltk.stem import WordNetLemmatizer                   # for lemmatization
wordnet_lemmatizer = WordNetLemmatizer()                  # initialization of the lemmatizer
from nltk.corpus import stopwords                         # initialization for stop word removal
stop = stopwords.words('english')

# preprocessing of the plot sentences
def plot_tokenizer(plot_txt="video_meta/test_plot.txt"):
    plt_sent = []    # lemmatize + rid of punctuation & stopwords for each plot sentence & append to plt_sent
    for sentence in sent_tokenize(open(plot_txt, "r").read()):
        temp_sent = word_tokenize(sentence.lower())
        temp_sent = [i for i in temp_sent if i not in ["...", ".", "!", "?", ",", "``", "--", "[", "]", "<", ">", "♪", "/i", "/", "-", ":"]]
        temp_sent = [str(wordnet_lemmatizer.lemmatize(i)) for i in temp_sent]
        temp_sent = [i for i in temp_sent if i not in stop]
        plt_sent.append(temp_sent)
    return plt_sent

# preprocessing to get the scenes detected in the video
# split time stamps by reading from file and append to scene_stamps
# scene stamps contain the scene boundaries
def get_scene_stamp(movie_name="test.mp4"):
    # stores its output in the output.txt for further processing
    if (os.stat("video_meta/output.txt").st_size == 0):
        func_str = 'ffprobe -show_frames -of compact=p=0 -f lavfi "movie=' + movie_name + ',select=gt(scene\,0.4)" > video_meta/output.txt'
        os.system(func_str)    # call to the os to process above command
    time_stamps, scene_stamps = [0], []
    for line in open("video_meta/output.txt").readlines():
        fields = line.split('|')
        time_stamps.append(float(fields[4].split('=')[1]))
    for i in range(len(time_stamps)-1):
        scene_stamps.append((time_stamps[i], time_stamps[i+1]))
    return time_stamps, scene_stamps

def get_subtitle_stamp(sub_file="video_meta/test_sub.srt"):
    # to get subtitle stamps
    sub_stamps, sub_text, buf = [], [], []
    subs = open(sub_file).readlines()
    for index, line in enumerate(subs):
        l = line.strip()
        if l:
            buf.append(l)
        if (not l or index == len(subs)-1):
            # first process the time stamps
            temp = re.split(" --> ", buf[1])
            temp_1 = temp[0].split(":")
            temp_2 = temp[1].split(":")
            # convert the time stamp into seconds only...
            temp_1 = float(temp_1[1])*60 + float("".join(temp_1[2].split(",")))/1000.0
            temp_2 = float(temp_2[1])*60 + float("".join(temp_2[2].split(",")))/1000.0
            sub_stamps.append((temp_1, temp_2))
            # process the text to remove punctuation, stop words etc.
            temp = word_tokenize(" ".join(buf[2:]).lower())
            temp = [x for x in temp if x not in ["...", ".", "!", "?", ",", "``", "--", "[", "]", "<", ">", "♪", "/i", "/", "-", ":"]]
            temp = [str(wordnet_lemmatizer.lemmatize(x)) for x in temp]
            temp = [x for x in temp if x not in stop]
            sub_text.append(temp)
            buf = []
    return sub_stamps, sub_text

def plot_shot_assigner(plt_sent, sub_text):
    # plot assignment to shots
    plot_to_shot = [[] for i in range(len(plt_sent))]
    tf = {}
    # find term frequency for all plot sentences
    for index, plot_sentence in enumerate(plt_sent):
        tf[index] = termFrequency(plot_sentence)
    idf = inverseDocumentFrequency(plt_sent)
    tf_idf = tfIdf(tf, idf)
    for index, sub_sent in enumerate(sub_text):
    # which plot sentence most similar with subtitle?
        ret_val = sim(sub_sent, idf, tf_idf, len(plt_sent))
        if ret_val == (-1, -1) or ret_val == (0, 'None'):    # query mein jhol hain
            continue
        else:
            plot_to_shot[ret_val[1]].append((index, ret_val[0]))
    return plot_to_shot, idf, tf_idf

def sub_shot_assigner(sub_stamps, scene_stamps):
    # first part assigns shot numbers to each part of a subtitle
    # optimizations can be done here
    sub_to_shot = [[0, 0] for i in range(len(sub_stamps))]
    for sub_index, sub in enumerate(sub_stamps):
        for scene_index, scene in enumerate(scene_stamps):
            if (sub[0] < scene[1]):
                sub_to_shot[sub_index][0] = scene_index
                break
    for sub_index, sub in enumerate(sub_stamps):
        for scene_index, scene in enumerate(scene_stamps):
            if (sub[1] < scene[1]):
                sub_to_shot[sub_index][1] = scene_index
                break
    # second part assigns the subtitles properly to shots based on above information
    fin_sub_to_shot = [None]*len(sub_to_shot)
    for index, tup in enumerate(sub_to_shot):
        if (tup[0] == tup[1]):    # subtitle start and end in the same shot
            fin_sub_to_shot[index] = tup[0]
        else:    # tup[1] - tup[0] >= 1
            diff = tup[1] - tup[0]    # (scene gap between the subtitle start and end) + 1
            for i in range(1, diff):    # if difference is 1 it won't work
                fin_sub_to_shot[index+i] = tup[0] + i
            if ((scene_stamps[tup[0]][1]-sub_stamps[index][0])/float(scene_stamps[tup[0]][1]-scene_stamps[tup[0]][0])) > ((sub_stamps[index][1]-scene_stamps[tup[1]][0])/float(scene_stamps[tup[1]][1]-scene_stamps[tup[1]][0])):
                fin_sub_to_shot[index] = tup[0]
            else:
                fin_sub_to_shot[index] = tup[1]
    return fin_sub_to_shot

def query_processor(time_stamps, fin_sub_to_shot, idf, tf_idf, plt_sent, plot_to_shot, sub_text, q="mike"):
    temp_q = word_tokenize(q.lower())
    temp_q = [x for x in temp_q if x not in ["...", ".", "!", "?", ",", "``", "--", "[", "]", "<", ">", "♪", "/i", "/", "-"]]
    temp_q = [str(wordnet_lemmatizer.lemmatize(x)) for x in temp_q]
    temp_q = [x for x in temp_q if x not in stop]
    max_sim, max_plt = sim(temp_q, idf, tf_idf, len(plt_sent))
    if max_plt == "None":
        print "Your query does not match any scene in the video"
        return (-1, -1, -1)
    print "For query", temp_q, "the highest sim. is with", plt_sent[max_plt], "with sim.", max_sim
    shots, shots_final, subs, subs_final, ts_indices, ts_final = [], [], [], [], [], []
    # plot_to_shot gives the matching list of subtitle sentences -> [(35, 0.2656571164563915), (604, 0.2658152134299805), (619, 0.26629063540377135), (624, 0.44261725639867383), (687, 0.3904935983047358)]
    # for sorting with respect to second element of tuple
    # check here
    for i in sorted(plot_to_shot[max_plt], key = lambda x: x[1]):        # assign final shot based on subtitle
        subs.append(sub_text[i[0]])                                      # append subtitle number
        ts_indices.append(fin_sub_to_shot[i[0]])                         # contains the shot numbers (1-135)
        shots.append(int(time_stamps[fin_sub_to_shot[i[0]]]))  # knowing that time stamps has the start time of scenes
    # get the unique items in shots as there may be overlapping shots
    for item in shots:
        if item not in shots_final:
            shots_final.append(item)
            subs_final.append(" ".join(subs[shots.index(item)]))
    for item in ts_indices:
        if item not in ts_final:
            ts_final.append(item)
    print "The highest matching subtitle for above query :", sub_text[(sorted(plot_to_shot[max_plt], key = lambda x: x[1])[0][0])]
    print "The matching shot numbers :", ts_final
    return shots_final, subs_final, ts_final
