
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
from random import randint
import numpy as np

fig, ax = plt.subplots(figsize=(10, 8))
plt.subplots_adjust(bottom=0.2)  # Make room for slider

# Initial values
n_init = 3
iterations = 1000
pointX = [0, 1, 0.5]  # Initial triangle points
pointY = [0, 0, 1]
points = [plt.plot(pointX[i], pointY[i], 'go', picker=5)[0] for i in range(n_init)]

# Create sliders
ax_slider_points = plt.axes((0.2, 0.1, 0.6, 0.03))
ax_slider_iter = plt.axes((0.2, 0.05, 0.6, 0.03))
n_slider = Slider(ax_slider_points, 'Points', 3, 10, valinit=n_init, valstep=1)
iter_slider = Slider(ax_slider_iter, 'Iterations', 100, 5000, valinit=iterations, valstep=100)

pointsX = [0]  # Starting point
pointsY = [0]

def update_points(val):
    n = int(n_slider.val)
    # Update number of points
    while len(points) < n:
        new_x = np.random.random()
        new_y = np.random.random()
        new_point = plt.plot(new_x, new_y, 'go', picker=5)[0]
        new_point.set_picker(True)
        points.append(new_point)
        pointX.append(new_x)
        pointY.append(new_y)
    
    while len(points) > n:
        points[-1].remove()
        points.pop()
        pointX.pop()
        pointY.pop()
    
    generate_chaos_game()
    fig.canvas.draw_idle()

def on_pick(event):
    if event.artist in points:
        point_index = points.index(event.artist)
        ax.set_picker(draggable_point_handler(point_index))

def draggable_point_handler(point_index):
    def on_mouse_move(event):
        if event.inaxes:
            points[point_index].set_data([event.xdata], [event.ydata])
            pointX[point_index] = event.xdata
            pointY[point_index] = event.ydata
            generate_chaos_game()
            fig.canvas.draw_idle()
    
    def on_button_release(event):
        ax.figure.canvas.mpl_disconnect(move_callback)
        ax.figure.canvas.mpl_disconnect(release_callback)
    
    move_callback = ax.figure.canvas.mpl_connect('motion_notify_event', on_mouse_move)
    release_callback = ax.figure.canvas.mpl_connect('button_release_event', on_button_release)
    return True

def generate_chaos_game():
    # Clear previous points
    for line in ax.lines[len(points):]:
        line.remove()
    
    # Generate new chaos game points
    current_x = pointsX[0]
    current_y = pointsY[0]
    new_pointsX = [current_x]
    new_pointsY = [current_y]
    
    for _ in range(int(iter_slider.val)):
        m = randint(0, len(pointX)-1)
        current_x = (current_x + pointX[m]) / 2
        current_y = (current_y + pointY[m]) / 2
        new_pointsX.append(current_x)
        new_pointsY.append(current_y)
    
    ax.plot(new_pointsX, new_pointsY, '.', color='blue', markersize=1, alpha=0.5)

n_slider.on_changed(update_points)
iter_slider.on_changed(lambda val: generate_chaos_game())
fig.canvas.mpl_connect('pick_event', on_pick)

# Generate initial chaos game
generate_chaos_game()

plt.show()
