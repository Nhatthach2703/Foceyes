from tkinter import *
from datetime import datetime
from tkinter import Label, Frame, Canvas
import tkinter as tk
import PIL.Image, PIL.ImageTk
import time
from datetime import datetime
import detection
import calendar
import cv2 as cv
from tkinter import messagebox as mb
###def show_result(class_name):



window = tk.Tk()
window.title('TESTING SYSTEM')

window.geometry('1000x750')
canvas = Canvas(window, width=1000, height=750)
canvas.pack(anchor="center")

start_time = datetime.now().time().strftime('%H:%M:%S')
start_text = f'ONLINE: ' + start_time

start_date = datetime.now().date()
start_date_text =f'{start_date.year}/{start_date.month}/{start_date.day} ' + start_time

running = 1
def xoa_cua_so():
    global running
    detection.cur.execute("DELETE FROM SessionNum WHERE Id IN (SELECT Id FROM SessionNum ORDER BY Id DESC LIMIT -1 OFFSET 2)")
    sqlsyn = "INSERT INTO SessionNum (TableName, SessionDate) VALUES ('" + detection.current_session + "', '" + start_date_text + "')"
    cur.execute(sqlsyn)
    conn.commit()

    if detection.video_name!="":
        detection.writer.release()
        if detection.video_name[len(detection.video_name) - 5] != str(detection.TOTAL_DISTRACT) and review==0:
            detection.os.remove(detection.video_name)
    detection.changeNearestSession()
    detection.cv.destroyAllWindows()
    detection.camera.release()
    running = 0
    
    

def update_datetime():
    global current_date_text
    global time_label_text
    current_date = datetime.now().date()
    current_date_text =f'{current_date.year} {calendar.month_name[current_date.month]} {current_date.day}'.upper()

    window.after(1000, update_datetime)

selected_table = ''
def reviewMode():
    if selected_table =='':
        return
    else:
        camrow = conn.execute('SELECT VideoPath FROM '+ selected_table).fetchall()
        timerow = conn.execute('SELECT Time FROM '+ selected_table).fetchall()
        reviewPanelOpen(camrow, timerow)

def reviewPanelOpen(camrow, timerow):
    i = 0
    
    for widget in review_frame.winfo_children():
        widget.destroy()
    
    
    for vPath in camrow:
    
        thumb = cv.VideoCapture(vPath[0])
        r, thumbnail = thumb.read()
        Timg = PIL.Image.fromarray(cv.cvtColor(thumbnail, cv.COLOR_BGR2RGB)).resize((120,86))
        Tphoto = PIL.ImageTk.PhotoImage(image=Timg)
        lb = Button(review_frame, text = vPath[0], command=lambda: reviewStart(lb.cget('text')))
        lb.image=Tphoto
        lb.config(image=Tphoto)
        lb.grid(row=0, column=i)

        i=i+1
    i = 0

    for timeS in timerow:
        lb2= Label(review_frame, text = timeS[0])
        lb2.grid(row=1, column=i)
        i+=1



tempTotalDistract = 0
review = 0
def reviewStart(link):
    global review
    global tempTotalDistract
    if review == 1:
        mb.showerror("Alert", "You are in review mode!")
        return

    tempTotalDistract = detection.TOTAL_DISTRACT
    review = 1
    detection.reviewMode(link)
    
    
def exitReviewMode():
    global review
    
    review = 0
    detection.exitReviewMode(tempTotalDistract)
    

# starting time here 
time_label_text = ""
start_time = time.time()
update_datetime()

#Navbar
mbar = Menu(window)
mfile = Menu(mbar)
mfile.add_separator()
mbar.add_cascade(label='Files', menu = mfile)
mbar.add_cascade(label='Customize', menu = mfile)
mbar.add_cascade(label='Help', menu = mfile)
mbar.add_cascade(label='User', menu = mfile)
window.config(menu = mbar)

#Camera holder
camera_frame = Frame(canvas)
camera_frame.place(x=50, y=45)

#Review Holder
outer_frame = Frame(canvas, height= 160, width= 600)
outer_frame.place(x=50, y=500)

sc_canvas = Canvas(outer_frame)
review_frame = Frame(sc_canvas)

scrollbar = Scrollbar(outer_frame, orient='horizontal', command=sc_canvas.xview)
sc_canvas.configure(xscrollcommand=scrollbar.set)

scrollbar.pack(side='bottom', fill='x')
sc_canvas.pack(side='left')
sc_canvas.create_window((0,0),window=review_frame,anchor='nw')
def myfunc(event):
    sc_canvas.configure(scrollregion=sc_canvas.bbox("all"), height= 160, width= 600)
review_frame.bind("<Configure>", myfunc)


#
date_time_frame = Frame(canvas)
date_time_frame.place(x=700, y=45)
date_label = Label(date_time_frame, fg='black', font=('Myriad Pro Bold Condensed', 20))
date_label.grid(row=0, column=0, sticky='w')
start_time_label = Label(date_time_frame, fg='black', font=('Myriad Pro Bold Condensed', 13))
start_time_label.grid(row=1, column=0, sticky='w')
time_label = Label(date_time_frame, fg='black', font=('Myriad Pro Bold Condensed', 13))
time_label.grid(row=2, column=0, sticky='w')

distraction_frame = Frame(canvas)
distraction_frame.place(x=700, y=150)
distraction_label = Label(distraction_frame, fg='black', font=('Myriad Pro Bold Condensed', 13))
distraction_label.grid(row=0, column=0, sticky='w')
ratio_label = Label(distraction_frame, fg='black', font=('Myriad Pro Bold Condensed', 10))
ratio_label.grid(row=1, column=0, sticky='w')
direction_label = Label(distraction_frame, fg='black', font=('Myriad Pro Bold Condensed', 10))
direction_label.grid(row=2, column=0, sticky='w')
total_distraction_label = Label(distraction_frame, fg='black', font=('Myriad Pro Bold Condensed', 10))
total_distraction_label.grid(row=3, column=0, sticky='w')
timer_label = Label(distraction_frame, fg='black', font=('Myriad Pro Bold Condensed', 10))
timer_label.grid(row=4, column=0, sticky='w')

distance_frame = Frame(canvas)
distance_frame.place(x=700, y=280)
distance_label = Label(distance_frame, fg='black', font=('Myriad Pro Bold Condensed', 13))
distance_label.grid(row=0, column=0, sticky='w')
safe_label = Label(distance_frame, fg='black', font=('Myriad Pro Bold Condensed', 10))
safe_label.grid(row=1, column=0, sticky='w')

#History and Report
hr_frame = Frame(canvas)
hr_frame.place(x=700, y=400)
hr_label = Label(hr_frame, fg='black', font=('Myriad Pro Bold Condensed', 16))
hr_label.grid(row=0, column=0, sticky='w')
hr_lb = Listbox(hr_frame, width=40, height=4, selectbackground = 'green')
hr_lb.bind('<FocusOut>', lambda e: hr_lb.selection_clear(0, END))

hr_lb.grid(row=1, column=0, pady=10, sticky='w')
conn = detection.conn
cur = detection.cur
row=conn.execute('''SELECT SessionDate from SessionNum LIMIT 0,10''')
i=0 # row value inside the loop 

for sessionFolder in row: 
    hr_lb.insert(i, sessionFolder)
    i=i+1

def select():
    selection = hr_lb.curselection()
    if selection:
        selection = hr_lb.curselection()[0]
        selrow=conn.execute('''SELECT Id FROM SessionNum ''').fetchall()[0][0]
        selection = selection + selrow
        selrow = conn.execute('SELECT TableName FROM SessionNum WHERE Id='+str(selection)).fetchall()[0][0]
        return selrow
    else:
        return ''

reviewButton = Button(hr_frame, text ="REVIEW THIS", command = reviewMode, font=('Myriad Pro Bold Condensed', 10))
reviewButton.grid(row=2, column=0, pady=20, sticky='e')


window.protocol("WM_DELETE_WINDOW", xoa_cua_so)
while running == 1:

    if detection.detectionLoop() == 0:
        if review==1:
            top = Toplevel(window)
            top.geometry("300x40")
            top.title('Alert')
    
            Message(top, text='Exiting review mode, returning to current session...', pady=20, anchor='center',width=300).pack()
            top.geometry("+%d+%d" %(500,375))
    
            window.after(2000, top.destroy)
            exitReviewMode()
            top.update_idletasks()
            top.update()
            continue
        else:
            continue
    frame = detection.frame

    img = PIL.Image.fromarray(cv.cvtColor(frame, cv.COLOR_BGR2RGB)).resize((600,430))
    photo = PIL.ImageTk.PhotoImage(image=img)
    camera_frame_label = Label(camera_frame, image=photo)
    camera_frame_label.grid(row=0, column=0)

    camera_frame_label.config(highlightbackground="green", highlightthickness=4)
    if (detection.distracted > 0):
        camera_frame_label.config(highlightbackground="red", highlightthickness=4)
    date_label.config(text=current_date_text)
    start_time_label.config(text=start_text)
    time_label.config(text=detection.timer_text)
    
    distraction_title = f'Distraction'.upper()
    distraction_label.config(text=distraction_title)
    ratio_label.config(text=detection.ratio_text)
    direction_label.config(text=detection.direction_text)
    total_distraction_label.config(text=detection.total_distraction_text)
    timer_label.config(text=detection.endtimer_text)

    safe_text="Appropriate distance"
    safe_label.config(fg='green')
    if (detection.distance_to_camera) < 50:
        safe_text="Please stay further from the screen"
        safe_label.config(fg='red')
    
    if (detection.distance_to_camera) > 90:
        safe_text="Please stay closer to the screen"
        safe_label.config(fg='red')

    safe_label.config(text=safe_text)
    distance_title = f'Distance: {detection.distance_text}' .upper()
    distance_label.config(text=distance_title)

    

    #History and Report
    hr_title = f'History'.upper()
    hr_label.config(text=hr_title)
    selected_table = select()

    if (running == 0):
        break
    window.update_idletasks()
    window.update()
 
window.destroy()
   
    
