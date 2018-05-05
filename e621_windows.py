# -*- coding: utf-8 -*- 
import os
import time
import requests
import sys
import argparse
import glob
import urllib

import json

from tkinter import *
from tkinter import filedialog
from tkinter import messagebox
from tkinter.ttk import Progressbar
from tkinter import scrolledtext
import tkinter as tk

from PIL import ImageTk, Image

import math

from xml.etree import ElementTree

APP_PHP_INDEX = "e621.net/post/index.xml"
APP_NAME = "e621"
API_URL = 'http://' + APP_PHP_INDEX + '?page=dapi&s=post&q=index&limit=100&tags={0:s}&page={1:d}'

SETTINGS_DIR = os.getenv('APPDATA') + "/e621-dl/"
SETTINGS_FLE = ".settings"

print( SETTINGS_DIR )

SAVE_FOLDER = ""
PAGE_LIMIT = 50
CURRENTLY_DOWNLOADING = False
CANCEL_DOWNLOADING = False

def printProgressBar(iteration, total, prefix='', suffix='', decimals=1, length=100, fill='■'):

    percent = 100 * (iteration / float(total))
    progress_bar( percent )
    if iteration >= total:
        print()


def safe_filename(string):
    set = 'abcdefghijklmnopqrstuvwxyz_-'
    string = string.replace(' ', '-')
    string = string.replace('--', '-')
    s = ''
    for c in string:
        if set.find(c) != -1:
            s = s + c

    return s


def downloadFile(url, directory):
    with open(directory, 'wb') as f:
        start = time.clock()
        r = requests.get(url, stream=True)
        total_length = r.headers.get('content-length')
        dl = 0
        if total_length is None:
            f.write(r.content)
        else:
            for chunk in r.iter_content(20480):
                dl += len(chunk)
                f.write(chunk)
                set_file_size( dl, total_length )
                printProgressBar(dl, int(total_length), prefix='Progress:', suffix='Complete', length=50)

    finish_time = round(time.clock() - start, 1)
    log_output("\nFile saved. '" + directory + "'\n")
    log_output('Took ' + str(finish_time) + 's')
    return finish_time


def get_posts(dir, tags):
    
    global CANCEL_DOWNLOADING

    page = 1
    posts = []
    while True:

        if CANCEL_DOWNLOADING:
            CANCEL_DOWNLOADING = False
            log_output( "Download canceled." )
            break

        if len( posts ) >= int( PAGE_LIMIT ):
            return posts

        post_url = API_URL.format(tags.replace(' ', '+'), page)

        log_output('Getting info from page ' + str(page) )
        log_output('URL: ' + post_url)

        headers = {
            'User-Agent': 'Skys E621 Downloaer. V0.15'
        }

        req = requests.get(post_url, headers=headers)
        html = req.text
        
        xmltree = ElementTree.fromstring( html )
        xml_data = xmltree.findall('post')
        
        for post in xml_data:

            if len( posts ) >= int( PAGE_LIMIT ):
                return posts

            posts.append( post )

        if len(xml_data) < 100:
            break
        page += 1

    return posts


def save_posts(dir, tags):

    dir = dir + "/"

    global CURRENTLY_DOWNLOADING
    global CANCEL_DOWNLOADING
    global image_e

    CURRENTLY_DOWNLOADING = True

    posts = get_posts(dir, tags)
    posts_count = len(posts)
    log_output('Found ' + str(posts_count) + ' posts.')
    
    currentPostNumber = 0
    maxPosts = len( posts )
    
    for post in posts:
        
        if CANCEL_DOWNLOADING:
            CANCEL_DOWNLOADING = False
            log_output( "Download canceled." )
            break

        currentPostNumber = currentPostNumber + 1
        
        log_output( "Post Number: " + str( currentPostNumber ) + "/" + str( maxPosts ) )

        perc = ( currentPostNumber / maxPosts ) * 100

        progress_bar_total( perc )

        post_url = post.find('file_url').text
        post_tags = post.find('tags' ).text
        post_id = post.find('id').text
        post_status = post.find('status').text
        real_file_name, post_ext = os.path.splitext(post_url)
        file_name = post_id + "-" + safe_filename(post_tags)[:128] + post_ext

        current_file( str( currentPostNumber ) + "/" + str( maxPosts ) + " ID: " +  post_id )

        if len( glob.glob( dir + post_id + '-*' ) ) > 0:
            log_output( post_id + ' already exists. Post ID: "' + post_id + '"', error=True )
            continue
            
        log_output('Downloading post ' + str(post_id) + '...')
        fullpath = os.path.join(dir, file_name)
        downloadFile(post_url, fullpath)

        try:
            preview_image( fullpath, post_ext )
        except:
            log_output( "Error previewing image!" )

    button_state( 1 )

    current_file( "Done!" )

    set_file_size( 0, 0, True )

    progress_bar( 1 )
    progress_bar_total( 1 )

    log_output('\n\nFinished! All files downloaded successfully!')

    messagebox.showinfo('Finished!', str( currentPostNumber ) + ' files downloaded successfully!')

    CURRENTLY_DOWNLOADING = False

    preview_image( "", "" )

    open_dir( True )

def preview_image( dir, ext ):

    global image_e

    if ext == ".png" or ext == ".jpg" or ext == ".gif":
        img2 = Image.open( dir )
        img2 = img2.resize( ( 375, 375 ), Image.ANTIALIAS ) #The (250, 250) is (height, width)
        img2 = ImageTk.PhotoImage( img2 )
        image_e.configure( image=img2 )
        image_e.image = img2
    else:
        log_output( "File not png, jpg, or gif. Skipping preview." )
        image_e.configure( image="" )

def button_state( s ):
    
    global cancel
    global page_btn
    global tag_box
    global dir_box
    global go_btn
    global btn

    if s:
        page_btn.configure( state="normal" )
        tag_box.configure( state="normal" )
        dir_box.configure( state="normal" )
        tk_state( cancel, 0 )
    else:
        tk_state( cancel, 1 )
        page_btn.configure( state="readonly" )
        tag_box.configure( state="readonly" )
        dir_box.configure( state="readonly" )

    tk_state( go_btn, s )
    tk_state( btn, s )

    window.update()

def log_output( s, main=True, error=False ):
    
    print( s )

    if main:

        color = 'green'

        if error:
            color = 'red'

        output_txt.configure(state='normal')
        output_txt.insert(tk.END, s + '\n', 'name' )
        output_txt.tag_config('name', background='black',foreground=color)
        output_txt.configure(state='disabled')
        output_txt.yview(tk.END)

    window.update()

def progress_bar( p ):

    prog_bar['value'] = p
    window.update()

def progress_bar_total( p ):

    prog2_bar['value'] = p

def current_file( f ):
    prog_txt.configure( text=f )

def set_file_size( c, m, clear=False ):

    c = math.floor( int( c ) / 1024 )
    m = math.floor( int( m ) / 1024 )

    txt = str( c ) + "kb/" + str( m ) + "kb"

    if clear:
        txt = ""

    file_size.configure( text=txt )

def msg( t, s ):
    messagebox.showinfo( t, s )

def warning( t, s ):
    messagebox.showerror( t, s )

def tk_state( e, i ):

    global window

    if i == True:
        e.configure( state="active" )
    else:
        e.configure( state="disabled" )

def get_tags():
    return tag_box.get()

def set_pages():

    global PAGE_LIMIT

    PAGE_LIMIT = page_btn.get()

    log_output( "Max Pages set to: " + str( PAGE_LIMIT ), 0 )

def open_dir( o=False ):
    global SAVE_FOLDER

    if o:
        if messagebox.askyesno( 'Open Folder?','Would you like to open the folder now?' ):
            os.startfile( SAVE_FOLDER )
    else:
        os.startfile( SAVE_FOLDER )

def ask_dir( ask=True ):

    global SAVE_FOLDER

    if ask:
        SAVE_FOLDER = filedialog.askdirectory()

    if os.path.isdir( SAVE_FOLDER ):
        dir_box.delete(0, 'end')
        dir_box.insert( 0, SAVE_FOLDER )
        tk_state( go_btn, 1 )
    else:
        if messagebox.askyesno( 'Create Directoy?','That directory doesn\'t exist!\nCreate one?' ):
            os.makedirs( SAVE_FOLDER )
            tk_state( go_btn, 1 )
        else:
            warning( "Uh oh!", "Please enter a valid directoy!" )
            tk_state( go_btn, 0 )
            return False

def cancel_download():
    
    global CANCEL_DOWNLOADING

    if messagebox.askyesno( "Cancel", "You sure you want to cancel current downloads?" ):
        CANCEL_DOWNLOADING = True

def on_closing():
    if CURRENTLY_DOWNLOADING == True:
        if messagebox.askyesno("Quit", "Files are still downloading!\nDo you want to quit?"):
            window.destroy()
    else:
        window.destroy()

def start_download():
    
    global CANCEL_DOWNLOADING
    global SAVE_FOLDER

    SAVE_FOLDER = dir_box.get()

    if ask_dir( False ) == False:
        return

    CANCEL_DOWNLOADING = False

    tags = get_tags()

    button_state( 0 )

    save_settings()

    save_posts( SAVE_FOLDER, tags )


title = "Sky's " + APP_NAME + " Downloader! Powered By Python 3"

print('##############################################')
print(title)
print('##############################################')

def load_settings():

    global SETTINGS_DIR
    global SETTINGS_FLE
    global SAVE_FOLDER
    global PAGE_LIMIT
    global tag_box
    global page_btn

    file = SETTINGS_DIR + SETTINGS_FLE

    if os.path.isfile( file ):

        settings_file = open( file, "r" )
        settings_json = settings_file.read()

        settings = json.loads( settings_json )

        log_output( settings[ 0 ], False )

        dir = settings[ 0 ]
        tags = settings[ 1 ]
        pg = settings[ 2 ]

        SAVE_FOLDER = dir
        ask_dir( False )

        PAGE_LIMIT = pg
        
        page_btn.delete(0,"end")
        page_btn.insert(0,PAGE_LIMIT)

        set_pages()

        tag_box.insert( 0, tags )

        log_output( "Last settings loaded from file." )

    else:
        log_output( "Settings file not foumd. Creating one.", False )
        save_settings()

def save_settings():

    global SETTINGS_DIR
    global SETTINGS_FLE
    global SAVE_FOLDER
    global PAGE_LIMIT

    file = SETTINGS_DIR + SETTINGS_FLE

    data = [ SAVE_FOLDER, get_tags(), PAGE_LIMIT ]

    if os.path.isdir( SETTINGS_DIR ):
        log_output( "Settings found.", False )
    else:
        os.makedirs( SETTINGS_DIR )


    with open( file,'w') as f:
        log_output( "Writing settings to file.", False )
        
        f.write( json.dumps( data ) )

window = Tk()
window.title( "Sky's E621 Downloader" )
window.minsize(width=800, height=400)
window.maxsize(width=800, height=400)

# Directory btn and text entry

dir_txt = Label( window, text="Directory: " )
dir_txt.place(relx=.01, rely=.002 )

dir_box = Entry( window, width=62 )
dir_box.place(relx=.01, rely=.06 )

btn = Button(window, text="...", command=ask_dir )
btn.place(relx=.49  , rely=.05 )

############################

# Tags input box and label

tag_txt = Label( window, text="Enter Tags (separated by spaces): " )
tag_txt.place(relx=.01, rely=.14 )

tag_box = Entry( window, width=66 )
tag_box.place(relx=.01, rely=.2 )

bleh = Label( window, text="Posts: " )
bleh.place(relx=.38, rely=.305 )
page_btn = Spinbox(window, from_=1, to=10000, width=5, command=set_pages )
page_btn.place(relx=.455, rely=.305 )

page_btn.delete(0,"end")
page_btn.insert(0,PAGE_LIMIT)

set_pages()

go_btn = Button(window, text="Download", command=start_download )
go_btn.place(relx=.01, rely=.3 )
go_btn.configure( state="disabled" )

cancel = Button(window, text="Cancel", command=cancel_download )
cancel.place(relx=.095, rely=.3 )
cancel.configure( state="disabled" )

open_f = Button(window, text="Open Folder", command=open_dir )
open_f.place(relx=.16, rely=.3 )

image_e = Label( window, image = "" )
image_e.place(relx=0.52, rely=.049 )

#############################

# Progress bar

prog_txt = Label( window, text="File: " )
prog_txt.place(relx=.001, rely=.39 )
file_size = Label( window, text=" ", anchor="e" )
file_size.place(relx=.39, rely=.39 )
prog_bar = Progressbar( window, length=400, style='green.Horizontal.TProgressbar')
prog_bar.place(relx=.01, rely=.46 )

prog2_bar = Progressbar( window, length=400, style='green.Horizontal.TProgressbar')
prog2_bar.place(relx=.01, rely=.525 )


##########################

output_txt = scrolledtext.ScrolledText(window,width=47,height=10)
output_txt.place(relx=.01, rely=.59 )
output_txt.configure( state="disabled" )
L = [ 83,67,82,73,80,84,69,68,32,66,89,58,32,83,75,89,76,69,82,32,77,69,87,83 ]
log_output( "\n\n\n\n\n\n\n\n\n\n\n\n" + ''.join(map(chr,L)) )

load_settings()

window.protocol("WM_DELETE_WINDOW", on_closing )
window.mainloop()
