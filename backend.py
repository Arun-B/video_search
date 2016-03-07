# read about monkey patch in the references folder in gevent.txt
from gevent import monkey; monkey.patch_all()
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
# working only on the episode 6 of BCS
video_file_path = "BCS/BCS1E06.mp4"
plot_sentences = fetch_plot_data("video_meta/BCS/BCS1E06_plot.txt")
time_stamps, scene_stamps = get_scene_stamps(video_file_path)
sub_stamps, sub_text, untouched_sub_text = fetch_subtitle_data("video_meta/BCS/BCS1E06.srt")
# now sub_text and plot_sentences contain processed subtitles and plot sentences
plot_to_sub, idf, tf_idf = plot_sub_assigner(plot_sentences, sub_text)
sub_to_shot = sub_shot_assigner(sub_stamps, scene_stamps)
plot_to_shot = plot_shot_assigner(plot_to_sub, sub_to_shot)
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

@app.route('/show_episodes')
def search():
    return template("episode_list")

@app.route('/show_select')
def search():
    return template("list_of_shows")

@app.route('/view_episode')
def show_episode():
    print "display episode"
    return template("episode_display", video_path=video_file_path)

@app.route('/search')
def search():
    return template("search_page")

@app.route('/search', method='POST')  # get method here...
def search_routine():
    query = request.forms.get('searcher')
    print "You searched for :", query
    redirect("/search/"+query)

@app.route('/search/<query>')
def query_parse(query): # arbitrary name
    global shot_timestamps, video_descr, shots_list
    shot_timestamps, video_descr, shots_list = similarity_fn1(time_stamps, sub_to_shot, idf, tf_idf, plot_sentences, plot_to_sub, sub_text, untouched_sub_text, plot_to_shot, query)
    # shot_timestamps, video_descr, shots_list = query_processor_sim2(plot_sentences, plt_to_shot, time_stamps, query)
    print "The values are", shot_timestamps, video_descr
    if ((shot_timestamps, video_descr) == (-1, -1)):
        redirect("/search/query/404")
    if (len(shot_timestamps) >= 3):
        redirect("/search/query/0")
    elif (len(shot_timestamps) != 0):  # lies between 0 and 3
        redirect("/search/query/single")
    elif (len(shot_timestamps) == 0):  # replace with else
        redirect("/search/query/404")

@app.route('/search/query/<res_number:int>')
def top_result(res_number):
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
    return template("results_page", link_to=links, shot_timestamp=shot_timestamps[res_number], sub_fin=temp2, ts_ind=temp1, video_path=video_file_path)

@app.route('/search/query/single')
def single_result():
    print "display only result"
    return template("results_page_single", shot_timestamp=shot_timestamps[0], video_path=video_file_path)

@app.route('/search/query/404')
def no_result():
    print "no results to display"
    return '''<head>
                <link href="results_assets/css/style.css" rel="stylesheet" type="text/css" media="all" />
              </head>
              <body>
                <h2><center>There seems to be no scene matching your query</h2>
                <div class="page-nav">
                  <ul>
                    <li><a href="/search" >Go Back to Search</a></li>
                  </ul>
                </div>
              </body>'''

# get request for thumbnails
@app.route('/search/query/thumbnails/BCS1E06/<filename>')
def static_server(filename):
    return static_file(filename, root="thumbnails/BCS1E06")

# display episode
@app.route('/results_assets/css/<filename>')
def static_server(filename):
    return static_file(filename, root="results_assets/css")

@app.route('/results_assets/images/<filename>')
def static_server(filename):
    return static_file(filename, root="results_assets/images")

@app.route('/BCS/<filename>')
def static_server(filename):
    return static_file(filename, root="BCS")

# results page specific assets -> reduce length in the future (wildcard)
@app.route('/search/query/results_assets/css/<filename>')
def static_server(filename):
    return static_file(filename, root="results_assets/css")

@app.route('/search/query/results_assets/images/<filename>')
def static_server(filename):
    return static_file(filename, root="results_assets/images")

@app.route('/search/query/<filename>')
def static_server(filename):
    return static_file(filename, root="")

@app.route('/search/query/BCS/<filename>')
def static_server(filename):
    return static_file(filename, root="BCS")

@app.route('/search/results_assets/css/<filename>')
def static_server(filename):
    return static_file(filename, root="results_assets/css")

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
@app.route('/search_assets/css/<filename>')
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
