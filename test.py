import matplotlib.pyplot as plt
from collections import deque

q = [0 for _ in range(10)]
q = deque(q)
print(q)
q.append(1)
print(q)
plt.plot(q)
plt.show()

