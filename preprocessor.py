# -*- coding: utf-8 -*-
# above line required to make non ascii characters work
# ffmpeg -i test.mp4 -vf select='gt(scene\,0.4)' -vsync vfr thumb%04d.png
# use above to get thumbnail output
import os, re
from cos_sim import termFrequency, inverseDocumentFrequency, tfIdf, sim
from nltk.tokenize import sent_tokenize, word_tokenize    # nltk sentence and word tokenizers
from nltk.stem import WordNetLemmatizer                   # for lemmatization
wordnet_lemmatizer = WordNetLemmatizer()                  # initialization of the lemmatizer
from nltk.corpus import stopwords                         # initialization for stop word removal
stop = stopwords.words('english')
from nltk import pos_tag, ne_chunk

# tokenizer functionality common to all
def tokenizer(to_tokenize):  # assumes that object to tokenize is a list
    temp = []
    for token in to_tokenize:
        temp_i = word_tokenize(token)
        temp_i = word_tokenize(token.lower())  # needs to be commented for similarity function 2
        temp_i = [j for j in temp_i if j not in ["...", ".", "!", "?", ",", "``", "--", "[", "]", "<", ">", "♪", "/i", "/", "(", ")", "-", ":"]]
        temp_i = [str(wordnet_lemmatizer.lemmatize(j)) for j in temp_i]
        temp_i = [j for j in temp_i if j not in stop]
        temp.append(temp_i)
    return temp    # return a pointer to the list

# preprocessing of the plot sentences
def fetch_plot_data(plot_txt_path="video_meta/test_plot.txt"):
    plot_sentences = tokenizer(sent_tokenize(open(plot_txt_path, "r").read()))
    return plot_sentences

# preprocessing to get the scenes detected in the video
# split time stamps by reading from file and append to scene_stamps
# scene stamps contain the scene boundaries
def get_scene_stamps(video_file_path="test.mp4"):
    # stores its output in the output.txt for further processing
    if (os.stat("video_meta/BCS/output6.txt").st_size == 0):
        func_str = 'ffprobe -show_frames -of compact=p=0 -f lavfi "movie=BCS/BCS1E06.mp4,select=gt(scene\,0.4)" > video_meta/BCS/output6.txt'
        os.system(func_str)    # call to the os to process above command
    time_stamps, scene_stamps = [0], []
    for line in open("video_meta/BCS/output6.txt").readlines():
        fields = line.split('|')
        time_stamps.append(float(fields[4].split('=')[1]))
        scene_stamps.append((time_stamps[-2], time_stamps[-1]))
    return time_stamps, scene_stamps

def fetch_subtitle_data(sub_file_path="video_meta/test_sub.srt"):
    # to get subtitle stamps
    sub_stamps, sub_text, buf = [], [], []
    subs = open(sub_file_path).readlines()
    for index, line in enumerate(subs):
        l = line.strip()
        if l:
            buf.append(l)
        if (not l or index == len(subs)-1):
            # first process the time stamps
            temp = re.split(" --> ", buf[1])
            temp_1, temp_2 = temp[0].split(":"), temp[1].split(":")
            # convert the time stamp into seconds only...
            temp_1 = float(temp_1[1])*60 + float("".join(temp_1[2].split(",")))/1000.0
            temp_2 = float(temp_2[1])*60 + float("".join(temp_2[2].split(",")))/1000.0
            sub_stamps.append((temp_1, temp_2))
            sub_text.append(" ".join(buf[2:]))
            buf = []
    untouched_sub_text = sub_text
    sub_text = tokenizer(sub_text)  # perform tokenization after appending all subtitles in sub_text
    return sub_stamps, sub_text, untouched_sub_text

def plot_sub_assigner(plot_sentences, sub_text):  # used by sim. function 1
    # plot assignment to shots
    plot_to_sub = [[] for i in range(len(plot_sentences))]
    tf = {}
    # find term frequency for all plot sentences
    for index, plot_sentence in enumerate(plot_sentences):
        tf[index] = termFrequency(plot_sentence)
    idf = inverseDocumentFrequency(plot_sentences)
    tf_idf = tfIdf(tf, idf)
    for index, sub_sentence in enumerate(sub_text):
    # which plot sentence most similar with subtitle?
        similarity = sim(sub_sentence, idf, tf_idf, len(plot_sentences))
        if similarity == (-1, -1) or similarity == (0, 'None'):    # query has a problem
            continue
        else:
            plot_to_sub[similarity[1]].append((index, similarity[0]))
    # sort plot_to_sub before return
    for i in range(len(plot_to_sub)):
        plot_to_sub[i] = sorted(plot_to_sub[i], key = lambda x: x[1])
    return plot_to_sub, idf, tf_idf

def sub_shot_assigner(sub_stamps, scene_stamps):
    # first part assigns shot numbers to each part of a subtitle
    # optimizations can be done here
    temp_sub_shot = [[0, 0] for i in range(len(sub_stamps))]
    for sub_index, sub in enumerate(sub_stamps):
        for scene_index, scene in enumerate(scene_stamps):
            if (sub[0] < scene[1]):
                temp_sub_shot[sub_index][0] = scene_index
                break
    for sub_index, sub in enumerate(sub_stamps):
        for scene_index, scene in enumerate(scene_stamps):
            if (sub[1] < scene[1]):
                temp_sub_shot[sub_index][1] = scene_index
                break
    # second part assigns the subtitles properly to shots based on above information
    sub_to_shot = [None]*len(temp_sub_shot)
    for index, tup in enumerate(temp_sub_shot):
        if (tup[0] == tup[1]):    # subtitle start and end in the same shot
            sub_to_shot[index] = tup[0]
        else:    # tup[1] - tup[0] >= 1
            diff = tup[1] - tup[0]    # (scene gap between the subtitle start and end) + 1
            for i in range(1, diff):    # if difference is 1 it won't work
                sub_to_shot[index+i] = tup[0] + i
            if ((scene_stamps[tup[0]][1]-sub_stamps[index][0])/float(scene_stamps[tup[0]][1]-scene_stamps[tup[0]][0])) > ((sub_stamps[index][1]-scene_stamps[tup[1]][0])/float(scene_stamps[tup[1]][1]-scene_stamps[tup[1]][0])):
                sub_to_shot[index] = tup[0]
            else:
                sub_to_shot[index] = tup[1]
    return sub_to_shot

def plot_shot_assigner(plot_to_sub, sub_to_shot):
    # plot_to_sub[i] gives the matching list of subtitle sentences -> [(35, 0.2656571164563915), (604, 0.2658152134299805), (619, 0.26629063540377135), (624, 0.44261725639867383), (687, 0.3904935983047358)]
    temp, plot_to_shot = [[] for i in range(len(plot_to_sub))], [[] for i in range(len(plot_to_sub))]  # as many as the number of plot sentences
    for i in range(len(plot_to_sub)):
        temp[i] = [sub_to_shot[j[0]] for j in plot_to_sub[i]]
    # use this method instead of list(set())
    for i in range(len(plot_to_sub)):
        for item in temp[i]:
            if item not in plot_to_shot[i]:
                plot_to_shot[i].append(item)
    # now plot_to_shot has the sorted list of shots
    return plot_to_shot

def plot_to_char(plot_sentences):
    speakers_in_plt_sent = {}
    for i in range(len(plot_sentences)):
        speakers_in_plt_sent[i] = []
    for index, sentence in enumerate(plot_sentences):  # hacked away
        pos_tags = pos_tag(sentence)
        temp = ne_chunk(pos_tags).pos()
        for words in temp:
            if words[1] == "PERSON":
                speakers_in_plt_sent[index].append(words[0][0])
    return speakers_in_plt_sent

def sub_to_char(transc_path, sub_text):
    transc, speakers, dialogs = [], [], []
    t = open(transc_path, "r").readlines()
    #remove lines without ':' so that actions, narrations are removed
    for line in t:
        if ':' in line:                       # transc contains lines without actions/narrations
            transc.append(line.strip().split(":"))  # strip to get rid of the newline characters
            if len(transc[-1]) > 10:
                transc.remove(transc[-1])           # get rid of the last element if char. name > 10
    for item in transc:                             # make seperate lists of items and transcripts
        speakers.append(item[0])
        dialogs.append(item[1])
    dialogs, sub_to_speaker = tokenizer(dialogs), {}

    sub_to_speaker = [0]*len(sub_text)
    for sub_index, sub in enumerate(sub_text):
        for dialog_index, dialog in enumerate(dialogs):
            cnt = 0
            for word in sub:
                if word in dialog:  # like trigram comparison
                    cnt += 1
                    if sub_to_speaker[sub_index] == 0:
                        if cnt >= 3 or cnt == len(sub):   # len(sub) because a subtitle may be 2/1 words
                            sub_to_speaker[sub_index] = speakers[dialog_index]
                        else:
                            sub_to_speaker[sub_index] = 0
                else:
                    cnt = 0
    return sub_to_speaker

def shot_to_speakers(sub_to_shot, sub_to_speaker, len_time_stamps):
    shot_to_speaker = {}
    for i in range(len_time_stamps):
        shot_to_speaker[i] = []
    for index, character in enumerate(sub_to_speaker):
        shot_to_speaker[sub_to_shot[index]].append(character)
    for i in range(len(shot_to_speaker)):
        shot_to_speaker[i] = list(set([item for item in shot_to_speaker[i] if item != 0]))
    return shot_to_speaker

def plot_to_shot_2(speakers_in_plt_sent, shot_to_speaker):                 # used by similarity 2
    # count = 1
    plt_shot = {}
    for i in range(len(speakers_in_plt_sent)):
        plt_shot[i] = []
    # for i in shot_to_speaker:
    #     for j in speakers_in_plt_sent: #sorted(speakers_in_plt_sent.keys(), reverse=True):
    #         if len(set(shot_to_speaker[i])&set(speakers_in_plt_sent[j])) >= count:
    #             count += 1
    #             plt_shot[j].append(i)
    #     count = 1
    shots_per_plot = int(round(len(shot_to_speaker)/float(len(speakers_in_plt_sent))))
    for i in range(len(shot_to_speaker)/shots_per_plot):
        score, final_scores = [0]*shots_per_plot, []
        for j in range(shots_per_plot*i, i*shots_per_plot+shots_per_plot):
            score[j%shots_per_plot] = len(set(shot_to_speaker[j])&set(speakers_in_plt_sent[i]))
            if (len(set(shot_to_speaker[j])) == score[j%shots_per_plot]):
                score[j%shots_per_plot] += 1
            final_scores.append((j, score[j%shots_per_plot]))
        final_scores = sorted(final_scores, key = lambda x: x[1], reverse=True)
        #print final_scores
        plt_shot[i].extend([final_scores[0][0], final_scores[1][0], final_scores[2][0]])
    return plt_shot

def similarity_fn1(time_stamps, sub_to_shot, idf, tf_idf, plot_sentences, plot_to_sub, sub_text, untouched_sub_text, plot_to_shot, query="mike"):
    temp_q = tokenizer([query])[0]  # tokenizer accepts a list
    max_sim, max_sim_sentence = sim(temp_q, idf, tf_idf, len(plot_sentences))
    if max_sim_sentence == "None":
        print "Your query does not match any scene in the video"
        return (-1, -1, -1)
    print "For query", temp_q, "the highest sim. is with", plot_sentences[max_sim_sentence], "with sim.", max_sim
    shots_list = plot_to_shot[max_sim_sentence]
    #print "Matching shots are :", shots_list
    video_descr = [untouched_sub_text[sub_to_shot.index(shot)] for shot in shots_list]
    shot_timestamps = [time_stamps[shot] for shot in shots_list]
    print "The highest matching subtitle for query :", sub_text[plot_to_sub[max_sim_sentence][0][0]]
    print "The matching shot numbers :", plot_to_shot[max_sim_sentence]
    return shot_timestamps, video_descr, shots_list

def query_processor_sim2(plot_sentences, plt_to_shot, time_stamps, query="Jane"):
    temp_q = tokenizer([query])[0]  # tokenizer accepts a list
    tf = {}
    # find term frequency for all plot sentences
    for index, plot_sentence in enumerate(plot_sentences):
        tf[index] = termFrequency(plot_sentence)
    idf = inverseDocumentFrequency(plot_sentences)
    tf_idf = tfIdf(tf, idf)
    max_sim, max_sim_sentence = sim(temp_q, idf, tf_idf, len(plot_sentences))
    if max_sim_sentence == "None":
        print "Your query does not match any scene in the video"
        return (-1, -1, -1)
    print "For query", temp_q, "the highest sim. is with", plot_sentences[max_sim_sentence], "with sim.", max_sim
    shot_timestamps = [time_stamps[shot] for shot in plt_to_shot[max_sim_sentence]]
    print "The matching shot numbers :", plt_to_shot[max_sim_sentence]
    return shot_timestamps, ["blah", "balh", "blah"], plt_to_shot[max_sim_sentence]
