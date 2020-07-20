import stats_processing
import numpy as np

stats_processing.hello()
i = 0
for i in range(1,10):
    print(np.random.poisson(lam=5,size=1))
