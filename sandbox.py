import numpy as np
import matplotlib.pyplot as plt

def press(event):
    print('press', event.key)
    if event.key == 'enter':
        cnt.append(1)
    if event.key == 'a':
        result = sum(cnt)
        print(result, cnt)

cnt=[]
fig, ax = plt.subplots()
fig.canvas.mpl_connect('key_press_event', press)
ax.plot(np.random.rand(12), np.random.rand(12), 'go')
plt.show()