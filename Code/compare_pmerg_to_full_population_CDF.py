'''
~~~
The input to this code is a distribution of probability values (from a given merger classification) when applied to the full SDSS sample.
It then calculates the CDF for this distribution, allowing you to:
1) Calculate the cdf value for a given p_merg value, or
2) Define their own distribution cutoffs (i.e., what is the p_merg value associated with the 10% point of the full SDSS distribution)

Using #1 you can interpret the p_merg value for an individual or list of galaxies in the context of the full sample. 
For instance, if your galaxy has a p_merg value of 0.016 and you would like to know how it stacks up to other p_merg values, you can run it through, returning a value of , which means that XXXX% of the full sample has a p_merg value less than 0.016. The interpretation here is that XXXXX.

Using #2 you can instead find the p_merg values that correspond to certain CDF values. This is useful if you want to define cutoffs for which X% of the population falls above or below a value.
~~~
'''

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os
import scipy
import scipy.stats

# Input the merger classification name
merger_type = 'minor_merger'
# Prefix where the LDA and probability tables are saved 
prefix = '/Users/rebeccanevin/Documents/CfA_Code/MergerMonger/Tables/'


# Step 1: import the probability values for these galaxies
df_LDA = pd.io.parsers.read_csv(prefix+'LDA_out_all_SDSS_predictors_'+str(merger_type)+'.txt', sep='\t')

# Extract the probability values from this table
p_vals = df_LDA['p_merg'].values



# Define a histogram with spacing defined
spacing = len(p_vals)#100000 # this will be the histogram binning but also how finely sampled the CDF is
hist = np.histogram(p_vals, bins=spacing)

# Put this in continuous distribution form in order to calculate the CDF
hist_dist = scipy.stats.rv_histogram(hist)

# Find individual cdf values corresponding to a p_merg value
p_list = [0.016, 0.997]
cdf_list = []
for p in p_list:
    cdf_list.append(hist_dist.cdf(p))
    print('CDF value is ', hist_dist.cdf(p),' when p_merg = ', p)

# In order to back out the p_merg values that correspond to a given point on the CDF curve,
# it is necessary to make a non-linear transformation of the xs, or p_merg values:
# This is because you're moving faster along the CDF distribution when you're at very high or very low
# p values

X_lin = np.linspace(-100,100,10000)
X = [1/(1+np.exp(-x)) for x in X_lin]# transform into logit space

# Get all cdf values
cdf_val = [hist_dist.cdf(x) for x in X]

# Find the x point at which the cdf value is 10% and 90% - 0.1 and 0.9 (can replace this with your own thresholds)
def find_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return idx, array[idx]

idx_non, val_non = find_nearest(np.array(cdf_val), 0.1)
X_non = X[idx_non]

idx_merg, val_merg = find_nearest(np.array(cdf_val),0.9)
X_merg =X[idx_merg]

print('p_merg value is ', X_non, 'when ',val_non,' of the full population has a lower p_merg value')
print('p_merg value is ', X_merg, 'when ',1-val_merg,' of the full population has a higher p_merg value')


# Visualize this relationship:
plt.scatter(X, cdf_val, s=0.1)
plt.xlabel('p_merg')
plt.ylabel('CDF')
plt.show()




# Put this into a loop to find a bunch of p_merg values that correspond to different cdf points:
cdf_percent = np.linspace(0.01, 0.99, 100)

cdf_percent = [0.01,0.05,0.1,0.25, 0.5, 0.75, 0.9,0.95,0.99]
for percent in cdf_percent:
    idx, val = find_nearest(np.array(cdf_val),percent)
    X_val = X[idx]
    print('cdf point', percent, 'pmerg value', X_val, 'when ', val,' of the full pop has a lower pmerg value')

# Plot the p_merg values and the CDF for this distribution:

plt.clf()
plt.title("p_merg distribution and CDF")
plt.hist(p_vals, bins=100)# Here its nice to bin up a little more
plt.plot(X, hist_dist.pdf(X), label='PDF')
# scale the cdf by the number of galaxies so you can see it on the same plot
#plt.plot(X, hist_dist.cdf(X)*len(p_vals)/2, label='CDF')
plt.legend()
#plt.axvline(x=X_non, color='red') # vertical line for thresholds
#plt.axvline(x=X_merg, color='red')
#plt.annotate('p = '+str(round(X_non,4)), xy=(X_non+0.01, 10), xycoords='data', color='red')
#plt.annotate('p = '+str(round(X_merg,4)), xy=(X_merg+0.01, 10), xycoords='data', color='red')


#plt.scatter(p_list, cdf_list, color='red', zorder=100)
#for i in range(len(p_list)):

#    plt.annotate('cdf = '+str(round(cdf_list[i],4)), xy=(p_list[i],cdf_list[i]+0.15), xycoords='data', color='red')
plt.legend()
plt.show()

