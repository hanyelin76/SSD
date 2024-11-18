import cv2
import numpy as np
import random
import pyttsx3
from asyncua import Client, ua
import asyncio
import PySimpleGUI as sg
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import mysql.connector
from mysql.connector import Error
from datetime import datetime  # Import datetime module to get the current date


async def write_data(segment, color, retry_count=5):
    url = "opc.tcp://192.168.0.26:4840/"  # OPCUA Server address & port no.
    for attempt in range(retry_count):
        try:
            async with Client(url=url, timeout=10) as client:  # Increased timeout to 10 seconds
                light_segment = client.get_node("ns=4;s=MAIN.lightSegment")  # NodeID
                workpiece_color = client.get_node("ns=4;s=MAIN.workpieceColor")  # NodeID
                dv_segment = ua.DataValue(ua.Variant(segment, ua.VariantType.Int16))  # Data type
                dv_color = ua.DataValue(ua.Variant(color, ua.VariantType.Int16))  # Data type
                await workpiece_color.set_value(dv_color)
                await light_segment.set_value(dv_segment)
                return
        except (ConnectionResetError, TimeoutError) as e:
            print(f"Attempt {attempt + 1} failed with error: {e}")
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
    print(f"Failed to write data after {retry_count} attempts.")

def connect():
    try:
        # connect to database
        conn = mysql.connector.connect(
            host="localhost",
            database="mini_project_11",
            user="me2631",
            password="me2631P2337838*"
        )
        return conn
    except(Exception, Error) as error:
        print(error)

# Initialize the database
def initialize_database():
    try:
        conn = connect()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM mini_table_11;")
        count = cursor.fetchone()[0]
        if count == 0:
            cursor.execute("INSERT INTO mini_table_11 (date, blue, red, yellow, green, orange) VALUES (%s, 0, 0, 0, 0, 0);", (datetime.now().strftime('%Y-%m-%d'),))
            conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error initializing database: {e}")

# get total number of records
def get_records_count(cursor):
    # execute the command
    cursor.execute('''SELECT * FROM mini_table_11;''')
    return len(cursor.fetchall())

def update_color_count(color_counts):
    try:
        conn = connect()
        cursor = conn.cursor()
        current_date = datetime.now().strftime('%Y-%m-%d')
        cursor.execute("SELECT COUNT(*) FROM mini_table_11 WHERE date = %s;", (current_date,))
        count = cursor.fetchone()[0]
        if count == 0:
            cursor.execute("INSERT INTO mini_table_11 (date, blue, red, yellow, green, orange) VALUES (%s, 0, 0, 0, 0, 0);", (current_date,))
        
        for color_name, count in color_counts.items():
            cursor.execute(f"UPDATE mini_table_11 SET {color_name} = {color_name} + %s WHERE date = %s", (count, current_date))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error updating color count: {e}")

def get_random_color_ranges():
    # Define color ranges in HSV space and BGR values for different colors
    colors = ['blue', 'red', 'yellow', 'green', 'orange']
    color_name = random.choice(colors)
    if color_name == 'blue':
        lower = np.array([95, 50, 50])
        upper = np.array([130, 255, 255])
        color_bgr = (255, 0, 0)
        n = 4
    elif color_name == 'red':
        lower = np.array([0, 100, 100])
        upper = np.array([10, 255, 255])
        color_bgr = (0, 0, 255)
        n = 2
    elif color_name == 'yellow':
        lower = np.array([20, 100, 100])
        upper = np.array([30, 255, 255])
        color_bgr = (0, 255, 255)
        n = 3
    elif color_name == 'green':
        lower = np.array([35, 100, 100])
        upper = np.array([85, 255, 255])
        color_bgr = (0, 255, 0)
        n = 1
    elif color_name == 'orange':
        lower = np.array([10, 100, 100])
        upper = np.array([20, 255, 255])
        color_bgr = (0, 165, 255)
        n = 5
    else:
        raise ValueError("Unsupported color name")
    return color_name, lower, upper, color_bgr, n

def draw_contours(frame, mask, color_name, color_bgr):
    # Find contours in the mask and draw the largest one if its area is above a threshold
    contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    largest_area = 0
    detected_contour = None
    for contour in contours:
        area = cv2.contourArea(contour)  # Calculate area of the contour
        if area > largest_area:
            largest_area = area
            detected_contour = contour  # Update the largest contour
    
    detected = False
    if largest_area > 4000:  # Check if the detected contour area is significant
        detected = True
        x, y, w, h = cv2.boundingRect(detected_contour)  # Get bounding box of the contour
        frame = cv2.rectangle(frame, (x, y), (x + w, y + h), color_bgr, 2)  # Draw rectangle around the detected contour
        cv2.putText(frame, color_name, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1.0, color_bgr, 2)  # Label the detected color
    return frame, detected, largest_area

def sorting_process(colors, engine, cap, window, color_counts):
    # Manage the sorting process, detecting colors, and updating the GUI
    color_names = [color[0] for color in colors]
    lower_colors = [color[1] for color in colors]
    upper_colors = [color[2] for color in colors]
    color_bgrs = [color[3] for color in colors]
    color_ns = [color[4] for color in colors]
    current_target = 0  # Index of the current target color
    detected_flags = [False] * 5  # Flags to indicate detection of each color
    next_workpiece = False
    processing_active = True
    asyncio.run(write_data(0, 0))
    print("Sorting Process Started")

    window['Start Sorting Process'].update(disabled=True)
    window['Stop Sorting Process'].update(disabled=False)
    window['Next Workpiece Check'].update(disabled=False)

    while processing_active:
        event, values = window.read(timeout=20)
        if event == sg.WIN_CLOSED or event == 'Stop Sorting Process':
            asyncio.run(write_data(0, 0))
            processing_active = False
            print("Sorting Process Stop\n")
            break
            
        elif event == 'Next Workpiece Check':
            next_workpiece = True  # Trigger next workpiece check
        elif event == 'Show Workpiece Processed':
            show_graph(window)  # Show processed workpieces graph

        ret, frame = cap.read()
        if not ret:
            continue

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)  # Convert frame to HSV color space

        largest_area = 0
        detected_color_name = None
        detected_color_bgr = None
        for i in range(5):
            segment = current_target + 1
            color_mask = cv2.inRange(hsv, lower_colors[i], upper_colors[i])  # Create mask for the current color range
            temp_frame, detected, area = draw_contours(frame.copy(), color_mask, f"{color_names[i].capitalize()} Colour", color_bgrs[i])

            if detected and area > largest_area:
                largest_area = area
                detected_color_name = color_names[i]
                detected_color_bgr = color_bgrs[i]
                frame = temp_frame  # Update the frame with the current highest area contour

        for i in range(5):
            center_x = 50 + i * 100
            if detected_flags[i]:
                cv2.circle(frame, (center_x, 50), 30, color_bgrs[i], -1)  # Filled circle if detected
            else:
                cv2.circle(frame, (center_x, 50), 30, color_bgrs[i], 2)  # Empty circle if not detected

        cv2.putText(frame, 'Press Esc to EXIT', (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2, cv2.LINE_4)  # Exit instructions

        if detected_color_name and next_workpiece:
            if detected_color_name == color_names[current_target]:
                asyncio.run(write_data(segment, color_ns[current_target]))
                detected_flags[current_target] = True
                print(f"{detected_color_name.capitalize()} colour match, transferred to Smart Beacon\n")
                engine.say(f"{detected_color_name.capitalize()} colour match, transferred to Smart Beacon")
                color_counts[detected_color_name] += 1  # Increment the count for the detected color
                current_target += 1
            else:
                engine.say(f"{detected_color_name.capitalize()} colour does not match, reject the workpiece")
                print(f"{detected_color_name.capitalize()} colour does not match, reject the workpiece\n")
            engine.runAndWait()

            largest_area = 0
            next_workpiece = False

            if all(detected_flags):
                detected_flags[current_target - 1] = True  # Ensure the last bubble is filled
                asyncio.run(write_data(6, 1))
                print("Sorting process complete\n")
                engine.say("Sorting process complete")
                engine.runAndWait()
                update_color_count(color_counts)  # Update the color count in the database
                current_target = 0
                #return  # Exit the function to allow the main loop to regenerate colors

        imgbytes = cv2.imencode('.png', frame)[1].tobytes()  # Encode the frame as a PNG image
        window['image'].update(data=imgbytes)  # Update the image in the GUI

        if cv2.waitKey(5) & 0xFF == 27:  # Exit if 'Esc' key is pressed
            break

    #cap.release()
    cv2.destroyAllWindows()

def create_gui():
    # Set up the GUI layout
    layout = [
        [
            sg.Column([
                [sg.Text('Sorting Process Control')],
                [sg.Button('Start Sorting Process'), sg.Button('Stop Sorting Process')],
                [sg.Button('Next Workpiece Check')],
                [sg.Button('Show Workpiece Processed')],
                [sg.Button('Blink Stop')],
                [sg.Button('Exit')]
            ]),
            sg.VSeparator(),
            sg.Column([
                [sg.Image(filename='', key='image')]  # Image display area
            ]),
            sg.VSeparator(),
            sg.Column([
                [sg.Canvas(key='canvas', size=(400, 300))]  # Canvas for matplotlib graph
            ])
        ]
    ]
    window = sg.Window('Sorting Process', layout, finalize=True)  # Create the window with the layout
    engine = pyttsx3.init()  # Initialize the text-to-speech engine
    return window, engine

def draw_figure(canvas, figure):
    # Draw a matplotlib figure on a Tkinter canvas
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
    return figure_canvas_agg

def show_graph(window):
    # Fetch color counts from the database and display a bar graph of workpieces processed
    color_counts = fetch_color_counts_from_db()

    colors = list(color_counts.keys())
    counts = list(color_counts.values())
    
    # Define color mappings
    color_map = {
        'blue': '#0000FF',
        'red': '#FF0000',
        'yellow': '#FFFF00',
        'green': '#00FF00',
        'orange': '#FFA500'
    }
    
    # Map counts to colors
    bar_colors = [color_map[color] for color in colors]
    
    fig, ax = plt.subplots()
    ax.bar(colors, counts, color=bar_colors)  # Create the bar chart
    ax.set_title('Workpieces Processed')
    ax.set_xlabel('Colors')
    ax.set_ylabel('Count')

    canvas_elem = window['canvas']
    canvas = canvas_elem.TKCanvas

    # Destroy any existing children widgets of the canvas
    for child in canvas.winfo_children():
        child.destroy()

    draw_figure(canvas, fig)  # Draw the figure on the canvas

def fetch_color_counts_from_db():
    try:
        conn = connect()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM mini_table_11 WHERE date = %s", (datetime.now().strftime('%Y-%m-%d'),))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        if result:
            # Convert the fetched result to the required format
            color_counts = {key: result[key] for key in ['blue', 'red', 'yellow', 'green', 'orange']}
            return color_counts
        else:
            return {color: 0 for color in ['blue', 'red', 'yellow', 'green', 'orange']}
    except Exception as e:
        print(f"Error fetching color counts: {e}")
        return {color: 0 for color in ['blue', 'red', 'yellow', 'green', 'orange']}

def main():
    # Main function to run the sorting GUI and process
    initialize_database()  # Initialize the database before starting the GUI
    window, engine = create_gui()
    cap = cv2.VideoCapture(1)  # Open the default camera
    
    color_counts = {color: 0 for color in ['blue', 'red', 'yellow', 'green', 'orange']}  # Initialize color counts

    sorting_active = False  # Flag to check if sorting is active

    while True:
        event, values = window.read(timeout=20)
        if event == sg.WIN_CLOSED:
            break

        ret, frame = cap.read()
        if not sorting_active:
            window['Start Sorting Process'].update(disabled=False)
            window['Stop Sorting Process'].update(disabled=True)
            window['Next Workpiece Check'].update(disabled=True)

        if ret:
            imgbytes = cv2.imencode('.png', frame)[1].tobytes()  # Encode the frame as a PNG image
            window['image'].update(data=imgbytes)  # Update the image in the GUI

        if event == 'Start Sorting Process' and not sorting_active:
            sorting_active = True
            colors = [get_random_color_ranges() for _ in range(5)]  # Regenerate colors
            sorting_process(colors, engine, cap, window, color_counts)
            sorting_active = False
            #cap.release()  # Release the capture to reset it
            #cap = cv2.VideoCapture(0)  # Reinitialize the capture

        if event == 'Stop Sorting Process':
            print("Sorting Process Stop")
            asyncio.run(write_data(0, 0))
            sorting_active = False
            #cap.release()  # Release the capture to reset it
            #cap = cv2.VideoCapture(0)  # Reinitialize the capture

        if event == 'Blink Stop':
            asyncio.run(write_data(7, 0))

        if event == 'Show Workpiece Processed':
            show_graph(window)  # Show the graph of workpieces processed

        if event == sg.WIN_CLOSED or event == 'Exit':
            break

    cap.release()
    window.close()

if __name__ == "__main__":
    main()



