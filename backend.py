# read about monkey patch in the references folder in gevent.txt
from gevent import monkey; monkey.patch_all()
import json, io, chardet, unicodedata
from bottle import Bottle, template, static_file, run, request, route, redirect
from preprocessor import fetch_plot_data, get_scene_stamps, fetch_subtitle_data, plot_sub_assigner, sub_shot_assigner, plot_shot_assigner, similarity_fn1
# from preprocessor import get_scene_stamps, fetch_subtitle_data, sub_to_char, sub_shot_assigner, shot_to_speakers, fetch_plot_data, plot_to_char, plot_to_shot, query_processor_sim2
app = Bottle()
# time_stamps, scene_stamps = get_scene_stamps("test-mentalist.avi")
# sub_stamps, sub_text = fetch_subtitle_data("video_meta/mentalist_sub.srt")
# sub_to_speaker = sub_to_char("video_meta/mentalist_transc.txt", sub_text)
# sub_to_shot = sub_shot_assigner(sub_stamps, scene_stamps)
# shot_to_speaker = shot_to_speakers(sub_to_shot, sub_to_speaker, len(time_stamps))
# plot_sentences = fetch_plot_data("video_meta/mentalist_plot.txt")
# speakers_in_plt_sent = plot_to_char(plot_sentences)
# for i in speakers_in_plt_sent:
#     speakers_in_plt_sent[i] = [item.upper() for item in speakers_in_plt_sent[i]]
# plt_to_shot = plot_to_shot(speakers_in_plt_sent, shot_to_speaker)
# change this to the path of your Videos and subtitles
import json, io, chardet, unicodedata
from preprocessor import fetch_plot_data, fetch_subtitle_data, get_scene_stamps, plot_sub_assigner, sub_shot_assigner, plot_shot_assigner, similarity_fn1
DIR_PLOTS = '/Users/arun/Movies/BetterCallSaul/BCS_PLOTS'
DIR_STAMPS = '/Users/arun/Movies/BetterCallSaul/BCS_STAMPS'
DIR_SUBS = '/Users/arun/Movies/BetterCallSaul/BCS_SUBS'
DIR_VIDS = '/Users/arun/Movies/BetterCallSaul'
DIR_PLTSUB = '/Users/arun/Movies/BetterCallSaul/BCS_PLTSUB'
DIR_SUBSHOT = '/Users/arun/Movies/BetterCallSaul/BCS_SUBSHOT'
DIR_PLOTSHOT = '/Users/arun/Movies/BetterCallSaul/BCS_PLOTSHOT'
file_names = ["BCS1E01", "BCS1E02", "BCS1E03", "BCS1E04", "BCS1E05", "BCS1E06", "BCS1E07", "BCS1E08", "BCS1E09", "BCS1E10"] # to ignore the DS file in mac
no_episodes = len(file_names)

video_file_names = ["Better.Call.Saul.S01E01.HDTV.x264-KILLERS", "better.call.saul.102.hdtv-lol", "better.call.saul.103.hdtv-lol", "better.call.saul.104.hdtv-lol", "better.call.saul.105.hdtv-lol", "BCS1E06", "better.call.saul.S01E07", "BCS1E08", "BCS1E09", "better.call.saul.110.hdtv-lol"]

# for multi episode processing
time_stamps, scene_stamps = [], []
for vid_file in video_file_names:
    time_stamps_path = DIR_STAMPS+"/"+vid_file+"_proc_ts.json"
    scene_stamps_path = DIR_STAMPS+"/"+vid_file+"_proc_ss.json"
    try:
        with open(time_stamps_path, 'r') as fp1, open(scene_stamps_path, 'r') as fp2:
            time_stamps.append(json.load(fp1))
            scene_stamps.append(json.load(fp2))
    except IOError:
        with open(time_stamps_path, 'w') as fp1, open(scene_stamps_path, 'w') as fp2:
            t1, t2 = get_scene_stamps(DIR_VIDS+"/"+vid_file+".mp4")
            time_stamps.append(t1)
            scene_stamps.append(t2)
            json.dump(time_stamps[-1], fp1)
            json.dump(scene_stamps[-1], fp2)

plot_sentences = []
for plot in file_names:
    # storing the processed part in json
    file_path = DIR_PLOTS+"/"+plot+"_proc_plot.json"
    try:
        with open(file_path, 'r') as fp:
            plot_sentences.append(json.load(fp))
    except IOError:
        with open(file_path, 'w') as fp:
            plot_sentences.append(fetch_plot_data(DIR_PLOTS+"/"+plot+"_plot.txt"))
            json.dump(plot_sentences[-1], fp)

# should run only the first time!
# preprocess the srt files and convert them to utf-8
# supposed to be non destructive (but f that)
# for f in file_names:
#     file_path = DIR_SUBS+"/"+f+".srt"
#     if chardet.detect("file_path")["encoding"] != "utf-8"
#         data = open(file_path).read()
#         with open(file_path, "w") as fp:
#             fp.write(data.decode('Windows-1252').encode('utf-8'))
#             fp.write(data.decode(char.detect("file_path")["encoding"]).encode("utf-8"))
# alternatively for the last line -> instead of windows use detected value

sub_stamps, sub_text, untouched_sub_text = [], [], []
for sub_file in file_names:
    # storing the processed part in json
    sub_stamps_path = DIR_SUBS+"/"+sub_file+"_proc_sub_st.json"
    sub_text_path = DIR_SUBS+"/"+sub_file+"_proc_sub_tx.json"
    sub_unttext_path = DIR_SUBS+"/"+sub_file+"_proc_sub_untx.json"
    temp_path = DIR_SUBS+"/"+"temp.srt"
    try:
        with open(sub_stamps_path, 'r') as fp1, open(sub_text_path, 'r') as fp2, open(sub_unttext_path, 'r') as fp3:
            sub_stamps.append(json.load(fp1))
            sub_text.append(json.load(fp2))
            untouched_sub_text.append(json.load(fp3))
    except IOError:
        with open(sub_stamps_path, 'w') as fp1, open(sub_text_path, 'w') as fp2, open(sub_unttext_path, 'w') as fp3:
            with io.open(DIR_SUBS+"/"+sub_file+".srt", "r", encoding="utf-8") as sub,  open(temp_path, 'w') as temp_fp:
                # temporary file containing semi preprocessed subtitle
                temp_fp.write(unicodedata.normalize("NFKD", sub.read()).encode("ascii", "ignore"))  # replace unicode chars with closest equivalents
            t1, t2, t3 = fetch_subtitle_data(temp_path)
            sub_stamps.append(t1)
            sub_text.append(t2)
            untouched_sub_text.append(t3)
            json.dump(sub_stamps[-1], fp1)
            json.dump(sub_text[-1], fp2)
            json.dump(untouched_sub_text[-1], fp3)

# for plot to subtitle and subtitle to shot
plot_to_sub = [None for i in range(no_episodes)]
idf = [None for i in range(no_episodes)]
tf_idf = [None for i in range(no_episodes)]
for index, vid_file in enumerate(file_names):
    plot_to_sub_path = DIR_PLTSUB+"/"+vid_file+"_proc_pltsub.json"
    idf_path = DIR_PLTSUB+"/"+vid_file+"_idf.json"
    tf_idf_path = DIR_PLTSUB+"/"+vid_file+"_tf_idf.json"
    try:
        with open(plot_to_sub_path, 'r') as fp1, open(idf_path, 'r') as fp2, open(tf_idf_path, 'r') as fp3:
            plot_to_sub[index] = json.load(fp1)
            idf[index] = json.load(fp2)
            tf_idf[index] = {int(k):v for k,v in json.load(fp3).items()}
    except IOError:
        with open(plot_to_sub_path, 'w') as fp1, open(idf_path, 'w') as fp2, open(tf_idf_path, 'w') as fp3:
            t1, t2, t3 = plot_sub_assigner(plot_sentences[index], sub_text[index])
            plot_to_sub[index], idf[index], tf_idf[index] = t1, t2, t3
            json.dump(plot_to_sub[index], fp1)
            json.dump(idf[index], fp2)
            json.dump(tf_idf[index], fp3)

sub_to_shot = [None for i in range(no_episodes)]
for index, vid_file in enumerate(file_names):
    # storing the processed part in json
    sub_to_shot_path = DIR_SUBSHOT+"/"+vid_file+"_proc_subshot.json"
    try:
        with open(sub_to_shot_path, 'r') as fp1:
            sub_to_shot[index] = json.load(fp1)
    except IOError:
        with open(sub_to_shot_path, 'w') as fp1:
            sub_to_shot[index] = sub_shot_assigner(sub_stamps[index], scene_stamps[index])
            json.dump(sub_to_shot[index], fp1)

plot_to_shot = [None for i in range(no_episodes)]
for index, vid_file in enumerate(file_names):
    # storing the processed part in json
    plot_to_shot_path = DIR_PLOTSHOT+"/"+vid_file+"_proc_plotshot.json"
    try:
        with open(plot_to_shot_path, 'r') as fp1:
            plot_to_shot[index] = json.load(fp1)
    except IOError:
        with open(plot_to_shot_path, 'w') as fp1:
            plot_to_shot[index] = plot_shot_assigner(plot_to_sub[index], sub_to_shot[index])
            json.dump(plot_to_shot[index], fp1)

# video_descr contains the description of the links in html (subtitle text)
shot_timestamps, video_descr, shots_list = None, None, None

@app.route('/')
def first_page():
    redirect("/index")

@app.route('/index')
def index_page():
    return template("index")

@app.route('/login')  # get method here...
def login():
    return template("login")

@app.route('/show_select')
def search():
    return template("list_of_shows")

@app.route('/show_episodes')
def search():
    return template("episode_list")

@app.route('/view_episode/<episode_num:int>')
def show_episode(episode_num):
    print "display episode"
    return template("episode_display", video_path=DIR_VIDS+"/"+video_file_names[episode_num-1]+".mp4")

@app.route('/search/<episode_num:int>')
def search(episode_num):
    return template("search_page")

@app.route('/search/<episode_num:int>', method='POST')  # get method here...
def search_routine(episode_num):
    query = request.forms.get('searcher')
    print "You searched for :", query
    redirect("/search/"+str(episode_num)+"/"+query)

@app.route('/search/<episode_num:int>/<query>')
def query_parse(episode_num, query): # arbitrary name
    # caching of 3 queries for faster retrieval can be done here...
    global shot_timestamps, video_descr, shots_list
    print "searching through episode number :", episode_num
    shot_timestamps, video_descr, shots_list = similarity_fn1(time_stamps[episode_num-1], sub_to_shot[episode_num-1], idf[episode_num-1], tf_idf[episode_num-1], plot_sentences[episode_num-1], plot_to_sub[episode_num-1], sub_text[episode_num-1], untouched_sub_text[episode_num-1], plot_to_shot[episode_num-1], query)
    # shot_timestamps, video_descr, shots_list = query_processor_sim2(plot_sentences, plt_to_shot, time_stamps, query)
    print "The values are", shot_timestamps, video_descr
    if ((shot_timestamps, video_descr) == (-1, -1)):
        redirect("/search/"+str(episode_num)+"/query/NaQ")
    if (len(shot_timestamps) >= 3):
        redirect("/search/"+str(episode_num)+"/query/0")
    elif (len(shot_timestamps) != 0):  # lies between 0 and 3
        redirect("/search/"+str(episode_num)+"/query/single")
    elif (len(shot_timestamps) == 0):  # replace with else
        redirect("/search/"+str(episode_num)+"/query/NaQ")

@app.route('/search/<episode_num:int>/query/<res_number:int>')
def top_result(episode_num, res_number):
    print "displaying result"
    temp1, temp2, links = [], [], None
    if res_number == 0:
        links = [1, 2]
        temp1.extend([shots_list[1], shots_list[2]])
        temp2.extend([video_descr[1], video_descr[2]])
    elif res_number == 1:
        links = [0, 2]
        temp1.extend([shots_list[0], shots_list[2]])
        temp2.extend([video_descr[0], video_descr[2]])
    elif res_number == 2:              # or replace with else
        links = [0, 1]
        temp1.extend([shots_list[0], shots_list[1]])
        temp2.extend([video_descr[0], video_descr[1]])
    return template("results_page", link_to=links, shot_timestamp=shot_timestamps[res_number], sub_fin=temp2, ts_ind=temp1, ep_name=file_names[episode_num-1], ep_num=str(episode_num), video_path=DIR_VIDS+"/"+video_file_names[episode_num-1]+".mp4")

@app.route('/search/<episode_num:int>/query/single')
def single_result(episode_num):
    print "display only result"
    return template("results_page_single", shot_timestamp=shot_timestamps[0], video_path=DIR_VIDS+"/"+video_file_names[episode_num-1]+".mp4", ep_num=str(episode_num))

@app.route('/search/<episode_num:int>/query/NaQ')
def no_result(episode_num):
    print "no results to display"
    return template("no_results", ep_num=str(episode_num))

# get request for thumbnails
# @app.route('/search/<episode_num:int>/query/thumbnails/BCS1E06/<filename>')
# def static_server(episode_num, filename):
#     return static_file(filename, root="thumbnails/BCS1E06")

# display episode
@app.route('/view_episode/results_assets/css/<filename>')
def static_server(filename):
    return static_file(filename, root="results_assets/css")

# @app.route('/results_assets/images/<filename>')
# def static_server(filename):
#     return static_file(filename, root="results_assets/images")

# @app.route('/BCS/<filename>')
# def static_server(filename):
#     return static_file(filename, root="BCS")

# results page specific assets -> reduce length in the future (wildcard)
@app.route('/search/<episode_num:int>/query/results_assets/css/<filename>')
def static_server(episode_num, filename):
    return static_file(filename, root="results_assets/css")

@app.route('/search/<episode_num:int>/query/results_assets/images/<filename>')
def static_server(episode_num, filename):
    return static_file(filename, root="results_assets/images")

@app.route('/Users/arun/Movies/BetterCallSaul/thumbnails/<ep_name>/<filename>')
def static_server(ep_name, filename):
    return static_file(filename, root="/Users/arun/Movies/BetterCallSaul/thumbnails/"+ep_name)
# @app.route('/search/query/<filename>')
# def static_server(filename):
#     return static_file(filename, root="")
#
# @app.route('/search/query/BCS/<filename>')
# def static_server(filename):
#     return static_file(filename, root="BCS")
#
# @app.route('/search/results_assets/css/<filename>')
# def static_server(filename):
#     return static_file(filename, root="results_assets/css")

# for show select specific assets
@app.route('/list_shows_assets/sass/<filename>')
def static_server(filename):
    return static_file(filename, root="list_shows_assets/sass")

@app.route('/list_shows_assets/fonts/<filename>')
def static_server(filename):
    return static_file(filename, root="list_shows_assets/fonts")

@app.route('/list_shows_assets/img/<filename>')
def static_server(filename):
    return static_file(filename, root="list_shows_assets/img")

@app.route('/list_shows_assets/css/<filename>')
def static_server(filename):
    return static_file(filename, root="list_shows_assets/css")

@app.route('/list_shows_assets/js/<filename>')
def static_server(filename):
    return static_file(filename, root="list_shows_assets/js")

@app.route('/list_shows_assets/js/vendor/<filename>')
def static_server(filename):
    return static_file(filename, root="list_shows_assets/js/vendor")

@app.route('/list_shows_assets/js/min/<filename>')
def static_server(filename):
    return static_file(filename, root="list_shows_assets/js/min")

# list of episodes specific assets
@app.route('/Users/arun/Movies/BetterCallSaul/<filename>')
def static_server(filename):
    return static_file(filename, root="/Users/arun/Movies/BetterCallSaul")

@app.route('/episode_list_assets/sass/<filename>')
def static_server(filename):
    return static_file(filename, root="episode_list_assets/sass")

@app.route('/episode_list_assets/sass/base/<filename>')
def static_server(filename):
    return static_file(filename, root="episode_list_assets/sass/base")

@app.route('/episode_list_assets/sass/components/<filename>')
def static_server(filename):
    return static_file(filename, root="episode_list_assets/sass/components")

@app.route('/episode_list_assets/sass/layout/<filename>')
def static_server(filename):
    return static_file(filename, root="episode_list_assets/sass/layout")

@app.route('/episode_list_assets/sass/libs/<filename>')
def static_server(filename):
    return static_file(filename, root="episode_list_assets/sass/libs")

@app.route('/episode_list_assets/fonts/<filename>')
def static_server(filename):
    return static_file(filename, root="episode_list_assets/fonts")

@app.route('/episode_list_assets/images/<filename>')
def static_server(filename):
    return static_file(filename, root="episode_list_assets/images")

@app.route('/episode_list_assets/css/<filename>')
def static_server(filename):
    return static_file(filename, root="episode_list_assets/css")

@app.route('/episode_list_assets/js/<filename>')
def static_server(filename):
    return static_file(filename, root="episode_list_assets/js")

@app.route('/episode_list_assets/js/ie/<filename>')
def static_server(filename):
    return static_file(filename, root="episode_list_assets/js/ie")

# search page specific assets -> reduce length in the future (wildcard)
@app.route('/search/search_assets/css/<filename>')
def static_server(filename):
    return static_file(filename, root="search_assets/css")

# login page specific assets -> reduce length in the future (wildcard)
@app.route('/login_assets/css/<filename>')
def static_server(filename):
    return static_file(filename, root="login_assets/css")

@app.route('/login_assets/fonts/<filename>')
def static_server(filename):
    return static_file(filename, root="login_assets/fonts")

@app.route('/login_assets/images/<filename>')
def static_server(filename):
    return static_file(filename, root="login_assets/images")

# for assets specific to the index page -> missing 404?
@app.route('/main_assets/css/<filename>')
def static_server(filename):
    return static_file(filename, root="main_assets/css")

@app.route('/main_assets/js/<filename>')
def static_server(filename):
    return static_file(filename, root="main_assets/js")

@app.route('/main_assets/<filename>')
def static_server(filename):
    return static_file(filename, root="main_assets")

@app.route('/main_assets/css/theme-color/<filename>')
def static_server(filename):
    return static_file(filename, root="main_assets/css/theme-color")

@app.route('/main_assets/fonts/<filename>')
def static_server(filename):
    return static_file(filename, root="main_assets/fonts")

@app.route('/main_assets/images/<filename>')
def static_server(filename):
    return static_file(filename, root="main_assets/images")

# login logic
@app.route('/login', method='POST')
def do_login():
    username = request.forms.get('userid')
    password = request.forms.get('passid')
    list_ids = {"chinmay123": "123456", "sanuski":"abcd1234"}
    if (username in list_ids and password == list_ids[username]):
        print "hello", username
        redirect('/show_select')
        #redirect('/search')
    else:
        return "<p>Login failed.</p>"

run(app, host="127.0.0.1", port=8080, server="gevent")
