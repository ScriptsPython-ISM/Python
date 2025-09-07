import numpy as np
import matplotlib.pyplot as plt
from pynput.keyboard import Listener, Key
import pygame

def get_input_line():
    pygame.init()
    screen = pygame.display.set_mode((600, 600))
    pygame.display.set_caption("Draw Line")
    clock = pygame.time.Clock()

    line = []
    connected = False
    drawing = True

    x, y = -1000, -1000
    line.append((x, y, connected))

    while drawing:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                drawing = False

            elif event.type == pygame.MOUSEMOTION:
                mx, my = event.pos
                if mx > x:
                    if connected:
                        pygame.draw.line(screen, (255, 255, 255), (x, y), (mx, my), 2)
                    x, y = mx, my
                    line.append(((x - 300)/300, (y - 300)/300, connected))

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    connected = True
                    x, y = mx, my
                if event.key == pygame.K_RETURN:
                    drawing = False

        pygame.display.flip()
        clock.tick(1000)

    pygame.quit()
    pygame.display.quit()
    return line

from typing import List, Tuple, Callable, Optional

def piecewise_linear(points: List[Tuple[float, float, bool]]) -> Callable[[float], Optional[float]]:
    """
    Create a piecewise linear function from points with connectivity info.
    
    Args:
        points: A list of (x, y, connected) where
                - x, y: coordinates of the point
                - connected: True if this point should be connected to the previous one

    Returns:
        A function f(x) that returns the interpolated y-value if x lies within
        a connected segment, otherwise None.
    """
    segments = []
    for (x1, y1, c), (x2, y2, _) in zip(points, points[1:]):
        if c:
            if x1 == x2:
                continue
            m = (y2 - y1) / (x2 - x1)
            b = y1 - m * x1
            segments.append((x1, x2, m, b))

    def f(x: float) -> Optional[float]:
        for x1, x2, m, b in segments:
            if x1 <= x <= x2 or x2 <= x <= x1:
                return m * x + b
        return None

    return f

def fourier_approx(f: Callable[[float], float], depth: int, samples: int = 1000):
    xs = np.linspace(0, 2*np.pi, samples, endpoint=False)
    ys = np.array([f(600 * x / (2*np.pi)) for x in xs])

    a0 = (1 / np.pi) * np.trapezoid(ys, xs) / 2
    an = []
    bn = []
    for n in range(1, depth+1):
        an.append((1/np.pi) * np.trapezoid(ys * np.cos(n*xs), xs))
        bn.append((1/np.pi) * np.trapezoid(ys * np.sin(n*xs), xs))

    def approx(x: float):
        theta = 2*np.pi * x / 600
        total = a0
        for n in range(1, depth+1):
            total += an[n-1]*np.cos(n*theta) + bn[n-1]*np.sin(n*theta)
        return total

    return approx

input_line = get_input_line()
f = piecewise_linear(input_line)
def safe_f(x):
    val = f(x)
    if val is None:
        return safe_f.last
    safe_f.last = val
    return val
safe_f.last = 0

plt.ion()
fig, ax = plt.subplots()
x = np.linspace(-1, 1, 1000)
y = [safe_f(xi) for xi in x]
ax.plot(x, y, color='black')

depth = 1
F = fourier_approx(safe_f, depth)
Y = [F(xi * 2 * np.pi) for xi in x]
ax.plot(x, Y, color='red')

def on_press(event):
    global depth, F, Y
    if event.key == 'up':
        depth += 1
    elif event.key == 'down' and depth > 1:
        depth -= 1
    elif event.key == 'escape':
        plt.close()
        return

    F = fourier_approx(safe_f, depth)
    Y = [F(xi * 2 * np.pi / 1) for xi in x]

    ax.clear()
    ax.plot(x, y, color='black')
    ax.plot(x, Y, color='red')
    plt.draw()
    print(f"Depth: {depth}")

fig.canvas.mpl_connect('key_press_event', on_press)

plt.show(block = True)