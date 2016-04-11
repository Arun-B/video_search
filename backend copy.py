# read about monkey patch in the references folder in gevent.txt
from gevent import monkey; monkey.patch_all()
import json, io, chardet, unicodedata, os
from bottle import Bottle, template, static_file, run, request, route, redirect
import preprocessor
from nltk.tokenize import word_tokenize

app = Bottle()
list_of_shows = ['DD', 'BCS']
DIR_PLOTS = {'DD': '/Users/arun/Movies/Daredevil/DD_PLOTS', 'BCS':'/Users/arun/Movies/BetterCallSaul/BCS_PLOTS'}
DIR_STAMPS = {'DD': '/Users/arun/Movies/Daredevil/DD_STAMPS', 'BCS':'/Users/arun/Movies/BetterCallSaul/BCS_STAMPS'}
DIR_SUBS = {'DD': '/Users/arun/Movies/Daredevil/DD_SUBS', 'BCS':'/Users/arun/Movies/BetterCallSaul/BCS_SUBS'}
DIR_VIDS = {'DD': '/Users/arun/Movies/Daredevil', 'BCS':'/Users/arun/Movies/BetterCallSaul'}
DIR_PLTSUB = {'DD': '/Users/arun/Movies/Daredevil/DD_PLTSUB', 'BCS':'/Users/arun/Movies/BetterCallSaul/BCS_PLTSUB'}
DIR_SUBSHOT = {'DD': '/Users/arun/Movies/Daredevil/DD_SUBSHOT', 'BCS':'/Users/arun/Movies/BetterCallSaul/BCS_SUBSHOT'}
DIR_PLOTSHOT = {'DD': '/Users/arun/Movies/Daredevil/DD_PLOTSHOT', 'BCS':'/Users/arun/Movies/BetterCallSaul/BCS_PLOTSHOT'}
DIR_TRANSC = {'DD': '/Users/arun/Movies/Daredevil/DD_TRANSCRIPTS', 'BCS':'/Users/arun/Movies/BetterCallSaul/BCS_TRANSCRIPTS'}
file_names = {'DD': ['DDS1E01', 'DDS1E02', 'DDS1E03', 'DDS1E04'], 'BCS': ["BCS1E01", "BCS1E02", "BCS1E03", "BCS1E04", "BCS1E05", "BCS1E06", "BCS1E07", "BCS1E08", "BCS1E09", "BCS1E10"]} # to ignore the DS file in mac

# for example no_episodes can contain {'DD': 4, 'BCS': 10}
no_episodes = {}
for show in list_of_shows:
    no_episodes[show] = len(file_names[show])

# the names of the video files on disk
# can this be replaced by automatic listdir at the directory?
video_file_names = {'DD': ['DDS1E01', 'DDS1E02', 'DDS1E03', 'DDS1E04'], 'BCS': ["Better.Call.Saul.S01E01.HDTV.x264-KILLERS", "better.call.saul.102.hdtv-lol", "better.call.saul.103.hdtv-lol", "better.call.saul.104.hdtv-lol", "better.call.saul.105.hdtv-lol", "BCS1E06", "better.call.saul.S01E07", "BCS1E08", "BCS1E09", "better.call.saul.110.hdtv-lol"]}

# storing time and scene stamps for multiple shows
# each show will
time_stamps, scene_stamps = {}, {}
for show in list_of_shows:
    time_stamps[show], scene_stamps[show] = [], []

# time and scene stamps are actually lists
for show in list_of_shows:
    for vid_file_name in video_file_names[show]:
        time_stamps_path = DIR_STAMPS[show]+'/'+vid_file_name+'_proc_ts.json'
        scene_stamps_path = DIR_STAMPS[show]+'/'+vid_file_name+'_proc_ss.json'
        try:
            with open(time_stamps_path, 'r') as fp1, open(scene_stamps_path, 'r') as fp2:
                time_stamps[show].append(json.load(fp1))
                scene_stamps[show].append(json.load(fp2))
        except IOError:
            with open(time_stamps_path, 'w') as fp1, open(scene_stamps_path, 'w') as fp2:
                t1, t2 = preprocessor.get_scene_stamps(DIR_VIDS[show]+"/"+vid_file_name+".mp4")
                time_stamps[show].append(t1)
                scene_stamps[show].append(t2)
                json.dump(time_stamps[show][-1], fp1)
                json.dump(scene_stamps[show][-1], fp2)

# process and store the plot on the drive
plot_sentences = {}
for show in list_of_shows:
    plot_sentences[show] = []

for show in list_of_shows:
    for plot in file_names[show]:
    # storing the processed part in json
        file_path = DIR_PLOTS[show]+"/"+plot+"_proc_plot.json"
        try:
            with open(file_path, 'r') as fp:
                plot_sentences[show].append(json.load(fp))
        except IOError:
            with open(file_path, 'w') as fp:
                plot_sentences[show].append(preprocessor.fetch_plot_data(DIR_PLOTS[show]+"/"+plot+"_plot.txt"))
                json.dump(plot_sentences[show][-1], fp)

# should run only the first time!
# preprocess the srt files and convert them to utf-8
# is destructive
for show in list_of_shows:
    for f in file_names[show]:
        file_path = DIR_SUBS[show]+'/'+f+'.srt'
        if chardet.detect(file_path)['encoding'] not in ['utf-8', 'ascii']:
            data = open(file_path).read()
            with open(file_path, 'w') as fp:
                fp.write(data.decode('Windows-1252').encode('utf-8'))
                fp.write(data.decode(char.detect(file_path)['encoding']).encode('utf-8'))
# alternatively for the last line -> instead of windows use detected value

sub_stamps, sub_text, untouched_sub_text = {}, {}, {}
for show in list_of_shows:
    sub_stamps[show], sub_text[show], untouched_sub_text[show] = [], [], []

for show in list_of_shows:
    for sub_file in file_names[show]:
        # storing the processed part in json
        sub_stamps_path = DIR_SUBS[show]+'/'+sub_file+'_proc_sub_st.json'
        sub_text_path = DIR_SUBS[show]+'/'+sub_file+'_proc_sub_tx.json'
        sub_unttext_path = DIR_SUBS[show]+'/'+sub_file+'_proc_sub_untx.json'
        temp_path = DIR_SUBS[show]+'/'+'temp.srt'
        try:
            with open(sub_stamps_path, 'r') as fp1, open(sub_text_path, 'r') as fp2, open(sub_unttext_path, 'r') as fp3:
                sub_stamps[show].append(json.load(fp1))
                sub_text[show].append(json.load(fp2))
                untouched_sub_text[show].append(json.load(fp3))
        except IOError:
            with open(sub_stamps_path, 'w') as fp1, open(sub_text_path, 'w') as fp2, open(sub_unttext_path, 'w') as fp3:
                with io.open(DIR_SUBS[show]+'/'+sub_file+'.srt', 'r', encoding='utf-8') as sub,  open(temp_path, 'w') as temp_fp:
                    # temporary file containing semi preprocessed subtitle
                    # don't use if doing preprocessing?
                    temp_fp.write(unicodedata.normalize('NFKD', sub.read()).encode('ascii', 'ignore'))  # replace unicode chars with closest equivalents
                t1, t2, t3 = preprocessor.fetch_subtitle_data(temp_path)
                sub_stamps[show].append(t1)
                sub_text[show].append(t2)
                untouched_sub_text[show].append(t3)
                json.dump(sub_stamps[show][-1], fp1)
                json.dump(sub_text[show][-1], fp2)
                json.dump(untouched_sub_text[show][-1], fp3)

# for plot to subtitle mapping in a variable
plot_to_sub, idf, tf_idf = {}, {}, {}
for show in list_of_shows:
    plot_to_sub[show] = [None for i in range(no_episodes[show])]
    idf[show] = [None for i in range(no_episodes[show])]
    tf_idf[show] = [None for i in range(no_episodes[show])]

for show in list_of_shows:
    for index, vid_file in enumerate(file_names[show]):
        plot_to_sub_path = DIR_PLTSUB[show]+'/'+vid_file+'_proc_pltsub.json'
        idf_path = DIR_PLTSUB[show]+'/'+vid_file+'_idf.json'
        tf_idf_path = DIR_PLTSUB[show]+'/'+vid_file+'_tf_idf.json'
        try:
            with open(plot_to_sub_path, 'r') as fp1, open(idf_path, 'r') as fp2, open(tf_idf_path, 'r') as fp3:
                plot_to_sub[show][index] = json.load(fp1)
                idf[show][index] = json.load(fp2)
                tf_idf[show][index] = {int(k):v for k,v in json.load(fp3).items()}
        except IOError:
            with open(plot_to_sub_path, 'w') as fp1, open(idf_path, 'w') as fp2, open(tf_idf_path, 'w') as fp3:
                t1, t2, t3 = preprocessor.plot_sub_assigner(plot_sentences[show][index], sub_text[show][index])
                plot_to_sub[show][index], idf[show][index], tf_idf[show][index] = t1, t2, t3
                json.dump(plot_to_sub[show][index], fp1)
                json.dump(idf[show][index], fp2)
                json.dump(tf_idf[show][index], fp3)

# subtitle to shot mapping
sub_to_shot = {}
for show in list_of_shows:
    sub_to_shot[show] = [None for i in range(no_episodes[show])]

for show in list_of_shows:
    for index, vid_file in enumerate(file_names[show]):
        # storing the processed part in json
        sub_to_shot_path = DIR_SUBSHOT[show]+'/'+vid_file+'_proc_subshot.json'
        try:
            with open(sub_to_shot_path, 'r') as fp1:
                sub_to_shot[show][index] = json.load(fp1)
        except IOError:
            with open(sub_to_shot_path, 'w') as fp1:
                sub_to_shot[show][index] = preprocessor.sub_shot_assigner(sub_stamps[show][index], scene_stamps[show][index])
                json.dump(sub_to_shot[show][index], fp1)

# plot to shot mapping
plot_to_shot = {}
for show in list_of_shows:
    plot_to_shot[show] = [None for i in range(no_episodes[show])]

for show in list_of_shows:
    for index, vid_file in enumerate(file_names[show]):
        # storing the processed part in json
        plot_to_shot_path = DIR_PLOTSHOT[show]+'/'+vid_file+'_proc_plotshot.json'
        try:
            with open(plot_to_shot_path, 'r') as fp1:
                plot_to_shot[show][index] = json.load(fp1)
        except IOError:
            with open(plot_to_shot_path, 'w') as fp1:
                plot_to_shot[show][index] = preprocessor.plot_shot_assigner(plot_to_sub[show][index], sub_to_shot[show][index])
                json.dump(plot_to_shot[show][index], fp1)

# fetch transcripts
# fetching transcripts depends on the availability of one...
action_stamps = {}
for show in list_of_shows:
    action_stamps[show] = {}

# get list of directory files
for show in list_of_shows:
    # check whether transcripts exist?
    dir_entries = [i[:-4] for i in os.listdir(DIR_TRANSC[show]) if i.endswith('.txt')]
    for f in dir_entries:  # got rid of txt suffix
        # storing the processed part in json
        file_path = DIR_TRANSC[show]+'/'+f+'_ac.json' # action stamps
        try:
            with open(file_path, 'r') as fp:
                action_stamps[show][f[:-7]] = json.load(fp)
        except IOError:
            # for the first time
            transc_text = preprocessor.get_transcript_data(DIR_TRANSC[show]+'/'+f+'.txt')
            # preprocessing for transcripts
            utx = [None for i in range(len(untouched_sub_text[show][file_names[show].index(f[:-7])]))]
            for i, j in enumerate(untouched_sub_text[show][file_names[show].index(f[:-7])]):
                temp_i = word_tokenize(j.lower())
                temp_i = [k for k in temp_i if k not in ["...", "''",  ".", "!", "?", ",", "``", "--", "[", "]", "<", ">", "/", "(", ")", "-"]]
                utx[i] = temp_i
            transc_stamps = preprocessor.get_transcript_stamps(utx, transc_text, sub_stamps[show][file_names[show].index(f[:-7])])
            action_stamps[show][f[:-7]] = preprocessor.get_action_stamps(transc_text, transc_stamps)
            with open(file_path, 'w') as fp:
                json.dump(action_stamps[show][f[:-7]], fp)

# video_description contains the description of the links in html (subtitle text)
# for now for links in the episode list
with open('metadata/video_description.json') as fp1:
    video_description = json.load(fp1)
shot_timestamps, video_descr, shots_list = None, None, None

@app.route('/')
def index_page():
    redirect('/index')

@app.route('/index')
def index_page():
    return template('index')

@app.route('/login')  # get method here...
def login():
    return template('login')

# login logic
@app.route('/login', method='POST')
def login():
    username = request.forms.get('userid')
    password = request.forms.get('passid')
    list_ids = {'chinmay123': '123456'}
    if (username in list_ids and password == list_ids[username]):
        print 'hello', username
        redirect('/show_select')
    else:
        return '<p style="text-align: center">Login failed.</p>'

@app.route('/show_select')
def show_selection():
    return template('list_of_shows')

@app.route('/show_episodes/<show_name>')
def show_selection(show_name):
    return template("episode_list", show_name=show_name, video_description=video_description[show_name])

@app.route('/view_episode/<show_name>/<episode_num:int>')
def show_episode(show_name, episode_num):
    print "display episode"
    return template("episode_display", video_path=DIR_VIDS[show_name]+'/'+video_file_names[show_name][episode_num]+'.mp4', show_name=show_name)

@app.route('/search/<show_name>/<episode_num:int>')
def search(show_name, episode_num):
    return template('search_page', show_name=show_name)

@app.route('/search/<show_name>/<episode_num:int>', method='POST')  # get method here...
def search_routine(show_name, episode_num):
    query = request.forms.get('searcher')
    print 'You searched for :', query
    redirect('/search/'+show_name+'/'+str(episode_num)+'/'+query)

@app.route('/search/<show_name>/<episode_num:int>/<query>')
def query_parse(show_name, episode_num, query): # arbitrary name
    # caching of 3 queries for faster retrieval can be done here...
    global shot_timestamps, video_descr, shots_list
    print "Searching through episode number :", episode_num
    shot_timestamps, video_descr, shots_list, m = preprocessor.similarity_fn1(time_stamps[show_name][episode_num], sub_to_shot[show_name][episode_num], idf[show_name][episode_num], tf_idf[show_name][episode_num], plot_sentences[show_name][episode_num], plot_to_sub[show_name][episode_num], sub_text[show_name][episode_num], untouched_sub_text[show_name][episode_num], plot_to_shot[show_name][episode_num], query)
    max_sim, max_sim_sentence = preprocessor.similarity_fn2(action_stamps[show_name][file_names[show_name][episode_num]], query)
    u = action_stamps[show_name][file_names[show_name][episode_num]][max_sim_sentence]
    a_shot_timestamp, a_video_descr = u[1][0], ' '.join(u[0])
    try:# or if no results
        if max_sim >= m:
            shot_timestamps[0] = a_shot_timestamp
            video_descr[0] = a_video_descr
            print 'replace hua!', max_sim
    except:
        print 'No replace'
    print "The values are", shot_timestamps, video_descr
    if ((shot_timestamps, video_descr) == (-1, -1)):
        redirect('/search/'+show_name+'/'+str(episode_num)+'/query/NaQ')
    if (len(shot_timestamps) >= 3):
        redirect('/search/'+show_name+'/'+str(episode_num)+'/query/0')
    elif (len(shot_timestamps) != 0):  # lies between 0 and 3
        redirect('/search/'+show_name+'/'+str(episode_num)+'/query/single')
    elif (len(shot_timestamps) == 0):  # replace with else
        redirect('/search/'+show_name+'/'+str(episode_num)+'/query/NaQ')

@app.route('/search/<show_name>/<episode_num:int>/query/<res_number:int>')
def top_result(show_name, episode_num, res_number):
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
    return template("results_page", link_to=links, show_name=show_name, shot_timestamp=shot_timestamps[res_number], sub_fin=temp2, ts_ind=temp1, ep_name=file_names[show_name][episode_num], ep_num=str(episode_num), video_path=DIR_VIDS[show_name]+'/'+video_file_names[show_name][episode_num]+'.mp4')

# search specific assets
@app.route('/search/<show_name>/<episode_num:int>/query/single')
def single_result(show_name, episode_num):
    print "display only result"
    return template("results_page_single", shot_timestamp=shot_timestamps[0], show_name=show_name, video_path=DIR_VIDS[show_name]+"/"+video_file_names[show_name][episode_num]+".mp4", ep_num=str(episode_num))

@app.route('/search/<show_name>/<episode_num:int>/query/NaQ')
def no_result(show_name, episode_num):
    print 'No results to display'
    return template('no_results', show_name=show_name, episode_num=str(episode_num))

# for assets specific to the index page -> missing 404?
@app.route('/main_assets/<foldername>/<filename>')
def static_server(foldername, filename):
    return static_file(filename, root='main_assets/'+foldername)

@app.route('/main_assets/css/theme-color/<filename>')
def static_server(filename):
    return static_file(filename, root="main_assets/css/theme-color")

@app.route('/main_assets/<filename>')
def static_server(filename):
    return static_file(filename, root="main_assets")

# login page specific assets -> reduce length in the future (wildcard)
@app.route('/login_assets/<foldername>/<filename>')
def static_server(foldername, filename):
    return static_file(filename, root='login_assets/'+foldername)

# for show select specific assets
@app.route('/list_shows_assets/<foldername>/<filename>')
def static_server(foldername, filename):
    return static_file(filename, root='list_shows_assets/'+foldername)

@app.route('/list_shows_assets/<folder1>/<folder2>/<filename>')
def static_server(folder1, folder2, filename):
    return static_file(filename, root='list_shows_assets/'+folder1+'/'+folder2)

# list of episodes specific assets
@app.route('/Users/arun/Movies/<show_name>/<filename>')
def static_server(show_name, filename):
    return static_file(filename, root='/Users/arun/Movies/'+show_name)

@app.route('/episode_list_assets/<foldername>/<filename>')
def static_server(foldername, filename):
    return static_file(filename, root='episode_list_assets/'+foldername)

@app.route('/episode_list_assets/<folder1>/<folder2>/<filename>')
def static_server(folder1, folder2, filename):
    return static_file(filename, root='episode_list_assets/'+folder1+'/'+folder2)

# display episode
@app.route('/results_assets/<folder>/<filename>')
def static_server(folder, filename):
    return static_file(filename, root='results_assets/'+folder)

# search page specific assets
@app.route('/search_assets/css/<filename>')
def static_server(filename):
    return static_file(filename, root="search_assets/css")

# get request for thumbnails
# @app.route('/Users/arun/Movies/BetterCallSaul/thumbnails/<ep_name>/<filename>')
# def static_server(ep_name, filename):
#     return static_file(filename, root="/Users/arun/Movies/BetterCallSaul/thumbnails/"+ep_name)


run(app, host='127.0.0.1', port=8080, server='gevent')
