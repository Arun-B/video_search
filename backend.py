# read about monkey patch in the references folder in gevent.txt
from gevent import monkey; monkey.patch_all()
from bottle import Bottle, template, static_file, run, request, route, redirect
from preprocessor import plot_tokenizer, get_scene_stamp, get_subtitle_stamp, plot_sub_assigner, sub_shot_assigner, query_processor
app = Bottle()
plot_sentences = plot_tokenizer()
time_stamps, scene_stamps = get_scene_stamp()
sub_stamps, sub_text = get_subtitle_stamp()
# now sub_text and plot_sentences contain processed subtitles and plot sentences
plot_to_sub, idf, tf_idf = plot_sub_assigner(plot_sentences, sub_text)
sub_to_shot = sub_shot_assigner(sub_stamps, scene_stamps)
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
    return template("portfolio_two")

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
    shot_timestamps, video_descr, shots_list = query_processor(time_stamps, sub_to_shot, idf, tf_idf, plot_sentences, plot_to_sub, sub_text, query)
    print "the values are", shot_timestamps, video_descr
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
    return template("results_page", link_to=links, shot_timestamp=shot_timestamps[res_number], sub_fin=temp2, ts_ind=temp1)

@app.route('/search/query/single')
def single_result():
    print "display only result"
    return template("results_page_single", shot_timestamp=shot_timestamps[0])

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
@app.route('/search/query/thumbnails/<filename>')
def static_server(filename):
    return static_file(filename, root="thumbnails")

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

@app.route('/search/results_assets/css/<filename>')
def static_server(filename):
    return static_file(filename, root="results_assets/css")

# for show select specific assets
@app.route('/show_assets/images/<filename>')
def static_server(filename):
    return static_file(filename, root="show_assets/images")

@app.route('/show_assets/images/portfolio_two/<filename>')
def static_server(filename):
    return static_file(filename, root="show_assets/images/portfolio_two")

@app.route('/show_assets/css/<filename>')
def static_server(filename):
    return static_file(filename, root="show_assets/css")

@app.route('/show_assets/js/<filename>')
def static_server(filename):
    return static_file(filename, root="show_assets/js")

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
