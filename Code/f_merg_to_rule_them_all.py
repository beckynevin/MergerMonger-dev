#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This is to test if changing the bins changes the result
# of the trends of f_merg with redshift and mass

# This is combo'ed with Mendel,
# so is restricted to the cross-over between these 
# two samples
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import glob
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import summary_table
from matplotlib.patches import Rectangle



# path
dir = '/Users/rebeccanevin/Documents/CfA_Code/MergerMonger-dev/Tables/'


# This is to load up the mass complete table:
ack = False # option whether to use ackermann cross-matches
mass = 'log_stellar_mass_from_color'
red = 'z'
spacing_z = 0.02
complete = True
completeness = 95
nbins_mass = 15
suffix = str(spacing_z)+'_'+str(red)+'_'+str(mass)+'_completeness_'+str(completeness)


# Check if this table ^ even exists:
if os.path.exists(dir+'all_mass_color_complete_'+str(suffix)+'.txt'):
    print('it exists! you can run the f_merg analysis')
else:
    print('missing mass table to run this analysis')


# Now import the stuff to get your LDA and predictor table
# so you can have various properties of each galaxy
type_marginalized = '_flags_cut_segmap'
type_gal = 'predictors'
run = 'minor_merger_postc_include_coal_1.0'
# set this if you want to do a limited subset
num = None
savefigs = False
# set this if you want to save the result
save_df = True
JK_anyway = False

s_n_cut = False
s_n_cut_low = 50
s_n_cut_high = 50000

b_t_cut = False
b_t_cut_low = 0.2
b_t_cut_high = 0.3

if ack:
    table_name = dir + 'f_merg_'+str(run)+'_'+str(suffix)+'_mass_bins_'+str(nbins_mass)+'_ack_flags.csv'
else:
    if complete:
        table_name = dir + 'f_merg_'+str(run)+'_'+str(suffix)+'_mass_bins_'+str(nbins_mass)+'_flags.csv'
    else:
        table_name = dir + 'f_merg_'+str(run)+'_'+str(suffix)+'_incomplete_mass_bins_'+str(nbins_mass)+'_flags.csv'
    
if os.path.exists(table_name) and save_df:
    print('table already exists do you want to oversave?')

    




df_LDA = pd.io.parsers.read_csv(filepath_or_buffer=dir+'LDA_out_all_SDSS_'+type_gal+'_'+run+'_flags.txt',header=[0],sep='\t')

# Because the df_LDA doesn't have the final flag, use the predictor table to instead clean via merging

# Run OLS with predictor values and z and stellar mass and p_merg:
df_predictors = pd.io.parsers.read_csv(filepath_or_buffer=dir+'SDSS_predictors_all_flags_plus_segmap.txt',header=[0],sep='\t')

if len(df_LDA) != len(df_predictors):
    print('these have different lengths cannot use one to flag')
    STOP

# First clean this so that there's no segmap flags
df_predictors_clean = df_predictors[(df_predictors['low S/N'] ==0) & (df_predictors['outlier predictor']==0) & (df_predictors['segmap']==0)]

if s_n_cut:
    df_predictors_clean = df_predictors_clean[(df_predictors_clean['S/N'] > s_n_cut_low) & (df_predictors_clean['S/N'] < s_n_cut_high)]
    print('length after s_n_cut', len(df_predictors_clean))

clean_LDA = df_LDA[df_LDA['ID'].isin(df_predictors_clean['ID'].values)]

if complete:
    masstable = pd.io.parsers.read_csv(filepath_or_buffer=dir+'all_mass_color_complete_'+str(suffix)+'.txt',header=[0],sep='\t')
else:
    masstable = pd.io.parsers.read_csv(filepath_or_buffer=dir+'all_mass_'+str(suffix)+'.txt',header=[0],sep='\t')



if red == 'z_spec':
    masstable = masstable[masstable['logBD'] < 13]
    masstable = masstable[masstable['dBD'] < 1]
    masstable['B/T'] = 10**masstable['logMb']/(10**masstable['logMb']+10**masstable['logMd'])
    masstable = masstable[['objID',
    'z_x','z_spec',
    'logBD','log_stellar_mass_from_color','B/T']]
else:
    masstable = masstable[masstable['log_stellar_mass_from_color'] < 13]
    masstable = masstable[['objID',
    'z','log_stellar_mass_from_color']]

if b_t_cut:
    masstable = masstable[(masstable['B/T'] > b_t_cut_low) & (masstable['B/T'] < b_t_cut_high)]
    print('length after b_t_cut', len(masstable))
    #STOP



# Now merge this with LDA
#merged_1 = masstable_m.merge(clean_LDA, left_on='objID', right_on='ID')#[0:1000]# Now merging on dr8

merged_1 = masstable.merge(clean_LDA,left_on='objID', right_on='ID',# left_index=True, right_index=True,
                  suffixes=('', '_y'))
if red == 'z_spec':
    merged_1 = merged_1[['ID','z_x','z_spec','logBD','log_stellar_mass_from_color',
        'p_merg','B/T']]
else:
    merged_1 = merged_1[['ID','z','log_stellar_mass_from_color',
        'p_merg']]


#merged_1.drop(merged_1.filter(regex='_y$').columns, axis=1, inplace=True)

final_merged = merged_1.merge(df_predictors_clean, on='ID')
if red == 'z_spec':
    final_merged = final_merged[['ID','z_x','z_spec','logBD','log_stellar_mass_from_color',
        'p_merg','S/N','B/T']]
else:
    final_merged = final_merged[['ID','z','log_stellar_mass_from_color',
        'p_merg','S/N']]
print('len merged with mendel', len(final_merged))





# Load in the bins in z unless its the incomplete version (suffix == 'color'), 
# in that case define your own spacing
bins_z = np.load(dir+'all_mass_color_complete_'+str(suffix)+'_bins.npy')




# This is for dropping some stuff if you need it to run fast
if num:
    final_merged = final_merged.dropna()[0:num]
else:
    final_merged = final_merged.dropna()
print('length after dropping Nans', len(final_merged))



if ack:
    # Next import the ackermann sample and get it into 
    #cols = ['dr7objid','z','logMt','b_logMt','B_logMt','logMb','b_logMb','B_logMb','logMd','b_logMd','B_logMd','zmin','zmax','PpS','type','dBD']
    ack_table = pd.io.parsers.read_csv(filepath_or_buffer=dir+'ackermann_2018.csv')#, delim_whitespace=True)
    # Delte all rows that have Nans
    ack_table = ack_table.dropna()

    crossmatch = pd.io.parsers.read_csv(filepath_or_buffer=dir+'crossmatch_dr8_dr7_beckynevin.csv',sep=',', header=[0])
    # columns are: 'objID', 'dr7objid'


    merged_ack = ack_table.merge(crossmatch, left_on = 'objid', right_on='dr7objid')[['objID','p_merger_0','p_merger_1','p_merger_2','p_merger_3']]
    merged_ack['p_merger_avg'] = merged_ack[['p_merger_0', 'p_merger_1','p_merger_2','p_merger_3']].mean(axis=1)
    #np.nanmean([merged_ack['p_merger_0'],merged_ack['p_merger_1'],merged_ack['p_merger_2'],merged_ack['p_merger_3']])
    
    final_merged = final_merged.merge(merged_ack, left_on = 'ID', right_on='objID')
    print('len merged ours ack', len(final_merged))
    try:
        final_merged['z'] = final_merged['z_x']
    except KeyError:
        print(final_merged.columns)
    








# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Run OLS with predictor values and z and stellar mass and p_merg:
# Now merge these two and run an OLS:



#cats, bins



cats_mass, bins_mass = pd.qcut(final_merged[mass], q=nbins_mass, retbins=True, precision = 1)
#df['mass_bin'] = cats_mass

centers_z = [(bins_z[x+1] - bins_z[x])/2 + bins_z[x] for x in range(len(bins_z)-1)]
centers_mass = [(bins_mass[x+1] - bins_mass[x])/2 + bins_mass[x] for x in range(len(bins_mass)-1)]
 


# Before you do any analysis, it's necessary to drop certain parts of the table that are not
# complete
# Is this possible to do after you save?
# What kind of criteria do I want to use to do this?
# One way could be to drop bins that have a weird distribution of masses?
# Likewise, a weird distribution of redshifts
# Maybe the mean in one of these is significantly off





if save_df:
    # make a massive plot
    plt.clf()
    currentAxis = plt.gca()
    plt.scatter(final_merged[red], final_merged[mass], color='grey', s=0.1)
    plt.ylabel('log stellar mass')
    plt.xlabel(r'$z$')
    
    
    # first go through and load up all of prior files
    list_of_prior_files = glob.glob(dir + 'change_prior/LDA_out_all_SDSS_predictors_'+str(run)+'_0.*'+str(type_marginalized)+'.txt')
    print('length of prior files', len(list_of_prior_files))
    if len(list_of_prior_files) ==0:
        print('there are no priors prepared')
        name_single = dir + 'LDA_out_all_SDSS_predictors_'+str(run)+'_flags.txt'
        table = pd.io.parsers.read_csv(filepath_or_buffer=name_single,header=[0],sep='\t')[['ID','p_merg']]
    else:
        table_list = []
        for p in range(len(list_of_prior_files)):
            print('p prior', p)
            prior_file = pd.io.parsers.read_csv(filepath_or_buffer=list_of_prior_files[p],header=[0],sep='\t')
            # cut it way down
            if p == 0:
                table = prior_file[['ID','p_merg']]

            else:
                table_p = prior_file[['p_merg']] # just take p_merg if not the last one
                table_p.columns = ['p_merg_'+str(p)]
                # Now stack all of these tables
                table = table.join(table_p)
        
        

    # Now that these are all joined together, identify which ones have IDs that match mergers
    
    count = {}
    flag = {}
    S_N = {}
    if red == 'z_spec':
        B_T = {}
    f_merg = {}
    f_merg_avg = {}
    f_merg_std = {}
    for i in range(len(bins_z)-1):
        bin_start_z = bins_z[i]
        bin_end_z = bins_z[i+1]
        bin_center_z = (bin_end_z - bin_start_z)/2 + bin_start_z
        print('start z ', bin_start_z, 'stop z ', bin_end_z, 'center', bin_center_z)
        for j in range(len(bins_mass)-1):
            bin_start_mass = bins_mass[j]
            bin_end_mass = bins_mass[j+1]
            bin_center_mass = (bin_end_mass - bin_start_mass)/2 + bin_start_mass
            print('start mass ', bin_start_mass, 'stop mass ', bin_end_mass, 'center', bin_center_mass)
            # build dataset
            df_select = final_merged[(final_merged[red] > bin_start_z) 
                    & (final_merged[red] < bin_end_z) 
                    & (final_merged[mass] > bin_start_mass) 
                    & (final_merged[mass] < bin_end_mass)]
            
            # Now figure out where the means are 
            
            med_x = np.median(df_select[red].values)
            med_y = np.median(df_select[mass].values)
            std_x = np.std(df_select[red].values)
            std_y = np.std(df_select[mass].values)
            
            
            if (((med_x - std_x) > bin_center_z) & ((med_x + std_x) > bin_center_z)) | (((med_x - std_x) < bin_center_z) & ((med_x + std_x) < bin_center_z)) | (std_x > (bin_end_z - bin_start_z)/2):
                off_in_z = True
            else:
                off_in_z = False
                
            if (((med_y - std_y) > bin_center_mass) & ((med_y + std_y) > bin_center_mass)) | (((med_y - std_y) < bin_center_mass) & ((med_y + std_y) < bin_center_mass)) | (std_y > (bin_end_mass - bin_start_mass)/2):
                off_in_mass = True
            else:
                off_in_mass = False
                
            
            
            
            
            
            # so basically, if the medians of the distribution
            # are significantly different than the zcen and masscen,
            # then throw a flag because probably incomplete
            if off_in_mass or off_in_z:
                flag[centers_z[i],centers_mass[j]] = 1
            else:
                flag[centers_z[i],centers_mass[j]] = 0
                
                if len(df_select) > 1000:
                    # Rectangle is expanded from lower left corner
                    #
                    plt.scatter(df_select[red], df_select[mass], color='#52DEE5', s=0.1)
                    currentAxis.add_patch(
                        Rectangle((bin_start_z, bin_start_mass), 
                                bin_end_z - bin_start_z, bin_end_mass - bin_start_mass, facecolor='None', 
                                edgecolor='black')
                        )
                    plt.annotate(f'{round(len(df_select)/1000,1)}', 
                                 xy = (bin_start_z+0.005, bin_start_mass+0.005), 
                                 xycoords='data', size=5)
                    
                

                
         
            
            S_N[centers_z[i],centers_mass[j]] = np.mean(df_select['S/N'].values)
            if red == 'z_spec':
                B_T[centers_z[i],centers_mass[j]] = np.mean(df_select['B/T'].values)
               
            
            count[centers_z[i],centers_mass[j]] = len(df_select)
            
            # if the selection is > 0 then plot:
            plot_red = False
            if len(df_select) > 0 and plot_red:
                plt.clf()
                plt.scatter(final_merged[red].values, final_merged[mass].values, color='grey', s=0.1)
                plt.scatter(df_select[red].values, df_select[mass].values, color='red', s=0.1)
                plt.scatter(bin_center_z, bin_center_mass, color='black', s=1)
                plt.scatter(np.median(df_select[red].values), np.median(df_select[mass].values), color='orange', s=1)
            
                
                plt.errorbar(med_x, med_y, 
                         xerr = std_x,
                         yerr = std_y,
                         color='orange')
                
                if off_in_mass:
                    plt.annotate('off in mass', xy=(0.03,0.93), xycoords='axes fraction')
                if off_in_z:
                    plt.annotate('off in z', xy=(0.03,0.97), xycoords='axes fraction')
                
                
                if off_in_mass or off_in_z:
                    plt.title('flagging')
                    
                plt.show()
                
            print(ack)
            if ack:
                if len(df_select) <100:#== 0:
                    f_merg_avg[centers_z[i],centers_mass[j]] = np.nan
                    f_merg_std[centers_z[i],centers_mass[j]] = np.nan
                else:
                    f_merg_std[centers_z[i],centers_mass[j]] = 0
                    f_merg_avg[centers_z[i],centers_mass[j]] = len(df_select[df_select['p_merger_avg'] > 0.95])/len(df_select)

            else:
                df_select = df_select[['ID']] # just take this because you don't need the other deets
            

                merged = table.merge(df_select, on = 'ID')#left_on='ID', right_on='objID')
                # for each column of p_merg, calculate the the f_merg and then find the median
            

                gt = (merged > 0.5).apply(np.count_nonzero)
                
            

                #fmerg_here = len(np.where(merged['p_merg_x'] > 0.5)[0])/len(merged)
                
                #f_merg[centers_z[i]].append(fmerg_here)
                f_merg_avg[centers_z[i],centers_mass[j]] = np.median(gt.values[1:]/len(merged))
                f_merg_std[centers_z[i],centers_mass[j]] = np.std(gt.values[1:]/len(merged))
    plt.show()
    


    # find a way to put this into df format
    mass_val = []
    z_val = []
    f_merg_val = []
    f_merg_e_val = []
    count_val = []
    s_n_val = []
    flag_val = []
    if red == 'z_spec':
        b_t_val = []
    for i in range(len(bins_z)-1):
        for j in range(len(bins_mass)-1):
            f_merg_val.append(f_merg_avg[centers_z[i],centers_mass[j]])
            f_merg_e_val.append(f_merg_std[centers_z[i],centers_mass[j]])
            flag_val.append(flag[centers_z[i],centers_mass[j]])
            z_val.append(centers_z[i])
            mass_val.append(centers_mass[j])
            count_val.append(count[centers_z[i],centers_mass[j]])
            s_n_val.append(S_N[centers_z[i],centers_mass[j]])
            if red == 'z_spec':
                b_t_val.append(B_T[centers_z[i],centers_mass[j]])
    # Now make a df out of these lists
    if red == 'z_spec':
        df_fmerg = pd.DataFrame(list(zip(flag_val, mass_val, z_val, f_merg_val, f_merg_e_val, count_val, s_n_val, b_t_val)),
                             columns =['flag', 'mass', 'z', 'fmerg', 'fmerg_std', 'count', 'S/N', 'B/T'])
    else:
        df_fmerg = pd.DataFrame(list(zip(flag_val, mass_val, z_val, f_merg_val, f_merg_e_val, count_val, s_n_val)),columns =['flag', 'mass', 'z', 'fmerg', 'fmerg_std', 'count', 'S/N'])
    #except:
    #		df_fmerg = pd.DataFrame(list(zip(mass_val, z_val, f_merg_val, f_merg_e_val, count_val, s_n_val, b_t_val)),
    #           columns =['mass', 'z_x', 'fmerg', 'fmerg_std', 'count', 'S/N', 'B/T'])
    df_fmerg.to_csv(table_name, sep='\t')
else:
    df_fmerg = pd.read_csv(table_name, sep = '\t')

# OMG drop the flags
df_fmerg = df_fmerg[df_fmerg['flag']==0]
df_fmerg = df_fmerg.dropna()
print(df_fmerg)

ind = 'S/N'

# Do a 2D regression first with just mass and z:
X = df_fmerg[[ind]] 

y = df_fmerg['fmerg']
## fit a OLS model with intercept on mass and z
X = sm.add_constant(X)
est = sm.OLS(y, X).fit()
print(est.summary())

# First, regress z and S/N:
X = df_fmerg[['z']] 
y = df_fmerg[ind]
X = sm.add_constant(X)
est = sm.OLS(y, X).fit()
print(est.summary())

# First, regress z and S/N:
X = df_fmerg[['mass']] 
y = df_fmerg[ind]
X = sm.add_constant(X)
est = sm.OLS(y, X).fit()
print(est.summary())




# Do a 2D regression first with just mass and z:
if red == 'z_spec':
    X = df_fmerg[['mass', 'z']] 
else:
    X = df_fmerg[['mass', 'z']] 

y = df_fmerg[ind]
## fit a OLS model with intercept on mass and z
X = sm.add_constant(X)
est = sm.OLS(y, X).fit()
print(est.summary())

# Do a 2D regression:
X = df_fmerg[['mass', 'z', 'S/N']] 

y = df_fmerg['fmerg']
## fit a OLS model with intercept on mass and z
X = sm.add_constant(X)
est = sm.OLS(y, X).fit()
print(est.summary())

# Do a 2D regression:
X = df_fmerg[['mass', 'z', ind]] 

y = df_fmerg['fmerg']
## fit a OLS model with intercept on mass and z
X = sm.add_constant(X)
est = sm.OLS(y, X).fit()
print(est.summary())




# same thing but standardized
X = df_fmerg[['mass', 'z', ind]] 

from sklearn import preprocessing
# l1, l2, max don't really make much of a difference
# still getting super small #s when normalized
# Used to be Normalizer
normalizer = preprocessing.StandardScaler()#norm='l1')
normalized_train_X = normalizer.fit_transform(X)


X_std = normalizer.transform(X)

## fit a OLS model with intercept on mass and z
X = sm.add_constant(X_std)
est = sm.OLS(y, X).fit()
print(est.summary())




count = df_fmerg['count'].values

max_count = max(count)
print('also max?', max_count)



plt.clf()

# there should be 8 different redshifts
colors = ['#493843','#61988E','#A0B2A6','#CBBFBB','#EABDA8','#FF9000','#DE639A','#D33E43']
colors = ['#C5979D','#E7BBE3','#78C0E0','#449DD1','#3943B7','#150578','#0E0E52','black']
colors = ['#7D7C7A','#DEA47E','#AD2831','#800E13','#640D14','#38040E','#250902','black',
    '#7D7C7A','#DEA47E','#AD2831','#800E13','#640D14','#38040E','#250902','black',
    '#7D7C7A','#DEA47E','#AD2831','#800E13','#640D14','#38040E','#250902','black']

print('centers of mass', centers_mass)
print('centers of zs', centers_z)

fit = []
xs = []
ys = []
errors = []



for zcen in centers_z:
    
    # Grab everything with a z value from the df
    df_select = df_fmerg[df_fmerg['z'] == zcen].dropna().reset_index()
    if len(df_select)==0:
        continue
    # should already be sorted by mass
    #massall = df_select['mass'].values
    count = df_select['count'].values#[(massall > centers_mass[0]) & (massall < centers_mass[-1])]
    masscen = df_select['mass'].values#[(massall > centers_mass[0]) & (massall < centers_mass[-1])]
    

    
    # to do a linear regression, I'm going to need to define X and y
    #masscen_masked = np.ma.masked_where(count < 1000, masscen)
    x = masscen.reshape(-1,1)
    x = x[count > 1000]
    #x = np.ma.masked_where(count < 1000, x)
    try:
        X = sm.add_constant(x)
    except ValueError:
        continue
    y = df_select['fmerg']#[(massall > centers_mass[0]) & (massall < centers_mass[-1])]

    # mask y where count is less than 1000
    
    y = y[count > 1000].reset_index(drop=True)
    #np.ma.masked_where(count < 1000, y)

    error = df_select['fmerg_std']#[(massall > centers_mass[0]) & (massall < centers_mass[-1])]
    
    xs.append(masscen[count > 1000])
    ys.append(y)
    errors.append(error[count > 1000])
    

    # If there are no errors because this didn't have a bunch of different priors,
    # 
    if np.all(error) == 0.0 or JK_anyway:
        # This means you should jacknife because we don't have errors

        res = sm.OLS(y, X, missing='drop').fit()
        try:
            slope = res.params[1]
        except IndexError:
            fit.append(0)
            continue
        st, data, ss2 = summary_table(res, alpha=0.05)
        fittedvalues = data[:,2]
        predict_mean_se  = data[:,3]
        predict_mean_ci_low, predict_mean_ci_upp = data[:,4:6].T
        predict_ci_low, predict_ci_upp = data[:,6:8].T

        fit.append(fittedvalues)

        plt.plot(x, fittedvalues, color='#3D3B8E')#, label='OLS')
        plt.scatter(x, y, color='#E072A4', label='data', zorder=100)

        plt.plot(x, predict_ci_low, color='#6883BA', lw=2)
        plt.plot(x, predict_ci_upp, color='#6883BA', lw=2)
        plt.plot(x, predict_mean_ci_low, color='#6883BA', lw=2)
        plt.plot(x, predict_mean_ci_upp, color='#6883BA', lw=2)

        slopes = []
        # What about bootstrapping, iteratively dropping each of the points and re-fitting the line?
        for i in range(len(y)):
            '''
            xcrop= np.delete(masscen,i).reshape(-1,1)#.pop(i)
            #print(np.shape(x))
            Xcrop = sm.add_constant(xcrop)
            '''

            xcrop = np.delete(x,i)
            Xcrop = sm.add_constant(xcrop)
            
            #X_crop = X.crop(i).reset_index()
            ycrop = y.drop(i).reset_index(drop=True)

            

        
            res = sm.OLS(ycrop, Xcrop, missing='drop').fit()
            try:
                slope = res.params[1]
            except IndexError:
                
                continue
            st, data, ss2 = summary_table(res, alpha=0.05)
            fittedvalues = data[:,2]
            plt.plot(xcrop, fittedvalues, color='#B0E298', alpha=0.5)#, label='OLS')
            slopes.append(slope)

        
        plt.xlabel('Mass bins')
        plt.ylabel('fmerg')
        plt.title('$z = $'+str(zcen))
        #plt.legend()
        plt.annotate(f'{round(slope,3)} JK {round(np.mean(slopes),3)} pm {round(np.std(slopes),3)}', 
            xy=(0.01,0.9), xycoords='axes fraction', color='#3D3B8E')
        plt.show()

        
    
    else:
        # This is if you want to MCMC

        res_bb = sm.OLS(y, X, missing = 'drop').fit()#, missing = 'drop'
        try:
            _, data_bb, _ = summary_table(res_bb, alpha=0.05)
        except TypeError:
            fit.append(0)
            continue
        big_boy_fit = data_bb[:,2]
        
        fit.append(big_boy_fit)


        error = error[count > 1000].reset_index(drop=True)

        print(f'y after, {y}, xs {x}, errors {error}')



        mu, sigma = 0, 1 # mean and standard deviation
        

        plt.clf()
        
        # iterate
        # save slope values
        slope_list = []
        for num in range(100):

            
            Y = [y[i]+ error[i] * np.random.normal(mu, sigma, 1)  for i in range(len(y))]
            
            
            if num == 0:
                print('y',y)
                print('error', error)
                print('big Y', Y)
            

            #scaler = StandardScaler()
            #scaler.fit(X)
            #X_standardized = scaler.transform(X)
            
            res = sm.OLS(Y, X).fit()#, missing = 'drop'
            
            

            
            #plt.scatter(x, Y, s=0.1, color=colors[color_count])
            try:
                slope_list.append(res.params[1])
            except:
                continue
                slope_list.append(999)
            
            

            st, data, ss2 = summary_table(res, alpha=0.05)
            fittedvalues = data[:,2]
            predict_mean_se  = data[:,3]
            predict_mean_ci_low, predict_mean_ci_upp = data[:,4:6].T
            predict_ci_low, predict_ci_upp = data[:,6:8].T

            #print(summary_table(res, alpha=0.05))
            

            

            plt.plot(x, fittedvalues, 'black', alpha=0.5)#, label='OLS')

        #plt.plot(x, predict_ci_low, 'b--')
        #plt.plot(x, predict_ci_upp, 'b--')
        #plt.plot(x, predict_mean_ci_low, 'g--')
        #plt.plot(x, predict_mean_ci_upp, 'g--')
        plt.scatter(x, y, color='black', label='data', zorder=100)
        plt.plot(x, big_boy_fit, color = 'black', zorder=100)

        plt.errorbar(x, y, yerr = error, linestyle='None', color='black', zorder=100)
        for (count, x, y) in zip(count, x, y):
            plt.annotate(str(count), xy = (x, y+0.07), xycoords='data', color = 'black')

        plt.xlabel('Mass bins')
        plt.ylabel('fmerg')
        plt.title('$z = $'+str(zcen))
        #plt.legend()
        try:
            plt.annotate(str(round(res_bb.params[1],2)), 
                xy=(0.01,0.95), xycoords='axes fraction', color='black')
        except IndexError:
            continue
        plt.annotate(str(round(np.mean(slope_list),2))+'+/-'+str(round(np.std(slope_list),2)), 
            xy=(0.01,0.9), xycoords='axes fraction', color='black')
        plt.show()


plt.clf()
color_list = ['#FFCDB2','#FFB4A2','#E5989B','#B5838D','#6D6875',
              'black','black','black']
color_list = [
              '#104F55','#32746D','#9EC5AB','#01200F','#EF2D56',
              '#EF6461','#6B2D5C',
              'black','black','black']
for i, zcen in enumerate(centers_z):
    try:
        if len(xs[i]) < 3:
            continue
    except:
        break
    '''
    print('i', i, 'zcen', zcen)
    print('xs', xs[i])
    print('ys', ys[i], ys[i].values)
    print(fit[i])
    '''
    try:
        plt.scatter(xs[i], ys[i].values, label = f'z = {round(zcen,2)}', color=color_list[i])
        plt.errorbar(xs[i], ys[i].values, yerr = errors[i], color=color_list[i], ls='None', capsize=2)
        plt.plot(xs[i], fit[i],  color=color_list[i], lw=5)
    except:
        break
    
plt.legend()
plt.xlabel('log stellar mass')
plt.ylabel(r'$f_{\mathrm{merg}}$')
plt.show()


xs = []
ys = []
errors = []
fit = []

plt.clf()
# Make the same plot but for redshift on the x axis:
color_count = 0
for masscen in centers_mass:

    print(masscen)
    print(str(round(bins_mass[color_count],3))+'$ < M < $'+str(round(bins_mass[color_count+1],3)))
    #color_count+=1
    #continue
    # Grab everything with a z value from the df
    df_select = df_fmerg[df_fmerg['mass'] == masscen].dropna().reset_index()
    print(df_select)
    if len(df_select)==0:
        color_count+=1
        continue
    # should already be sorted by mass
    count = df_select['count'].values
    print('total count', np.sum(count))
    try:
        zcen = df_select['z'].values
    except KeyError:
        zcen = df_select['z_x'].values


    
    

    # to do a linear regression, I'm going to need to define X and y
    #masscen_masked = np.ma.masked_where(count < 1000, masscen)
    x = zcen.reshape(-1,1)
    x = x[count > 1000]
    #x = np.ma.masked_where(count < 1000, x)
    try:
        X = sm.add_constant(x)
    except ValueError:
        continue
    y = df_select['fmerg']

    # mask y where count is less than 1000
    print(f'y before, {y}')
    y = y[count > 1000].reset_index(drop=True)
    #np.ma.masked_where(count < 1000, y)

    error = df_select['fmerg_std']
    
    xs.append(zcen[count > 1000])
    ys.append(y)
    errors.append(error[count > 1000])

    if np.all(error) == 0.0 or JK_anyway:
        res = sm.OLS(y, X, missing='drop').fit()
        try:
            slope = res.params[1]
        except IndexError:
            fit.append(0)
            continue
        st, data, ss2 = summary_table(res, alpha=0.05)
        fittedvalues = data[:,2]
        fit.append(fittedvalues)
        predict_mean_se  = data[:,3]
        predict_mean_ci_low, predict_mean_ci_upp = data[:,4:6].T
        predict_ci_low, predict_ci_upp = data[:,6:8].T

        #print(summary_table(res, alpha=0.05))
        
        plt.plot(x, fittedvalues, color='#3D3B8E')#, label='OLS')
        plt.scatter(x, y, color='#E072A4', label='data', zorder=100)

        plt.plot(x, predict_ci_low, color='#6883BA', lw=2)
        plt.plot(x, predict_ci_upp, color='#6883BA', lw=2)
        plt.plot(x, predict_mean_ci_low, color='#6883BA', lw=2)
        plt.plot(x, predict_mean_ci_upp, color='#6883BA', lw=2)

        slopes = []
        # What about bootstrapping, iteratively dropping each of the points and re-fitting the line?
        for i in range(len(y)):
            xcrop = np.delete(x,i)
            Xcrop = sm.add_constant(xcrop)
            
            #X_crop = X.crop(i).reset_index()
            ycrop = y.drop(i).reset_index(drop=True)

            

        
            res = sm.OLS(ycrop, Xcrop, missing='drop').fit()
            try:
                slope = res.params[1]
            except IndexError:
                continue
            st, data, ss2 = summary_table(res, alpha=0.05)
            fittedvalues = data[:,2]
            plt.plot(xcrop, fittedvalues, color='#B0E298', alpha=0.5)#, label='OLS')
            slopes.append(slope)

        
        plt.xlabel('Redshift bins')
        plt.ylabel('fmerg')
        plt.title('M = '+str(masscen))
        #plt.legend()
        plt.annotate(f'{round(slope,3)} JK {round(np.mean(slopes),3)} pm {round(np.std(slopes),3)}', 
            xy=(0.01,0.9), xycoords='axes fraction', color='#3D3B8E')
        plt.show()
    else:

        res_bb = sm.OLS(y, X).fit()#, missing = 'drop'
        try:
            _, data_bb, _ = summary_table(res_bb, alpha=0.05)
        except TypeError:
            fit.append(0)
            continue
        big_boy_fit = data_bb[:,2]
        fit.append(big_boy_fit)


        error = df_select['fmerg_std']
        error = error[count > 1000].reset_index(drop=True)

        print(f'y after, {y}, xs {x}, errors {error}')

        
        plt.clf()
        
        # iterate
        # save slope values
        slope_list = []
        for num in range(100):
            Y = [y[i] + error[i] * np.random.normal(mu, sigma, 1) for i in range(len(y))]

            #scaler = StandardScaler()
            #scaler.fit(X)
            #X_standardized = scaler.transform(X)


            res = sm.OLS(Y, X).fit()
            
            #plt.scatter(x, Y, s=0.1, color=colors[color_count])
            try:
                slope_list.append(res.params[1])
            except:
                continue
                slope_list.append(999)
            
            

            st, data, ss2 = summary_table(res, alpha=0.05)
            fittedvalues = data[:,2]
            predict_mean_se  = data[:,3]
            predict_mean_ci_low, predict_mean_ci_upp = data[:,4:6].T
            predict_ci_low, predict_ci_upp = data[:,6:8].T

            #print(summary_table(res, alpha=0.05))
            

            

            plt.plot(x, fittedvalues, 'black', alpha=0.5)#, label='OLS')
        #plt.plot(x, predict_ci_low, 'b--')
        #plt.plot(x, predict_ci_upp, 'b--')
        #plt.plot(x, predict_mean_ci_low, 'g--')
        #plt.plot(x, predict_mean_ci_upp, 'g--')
        plt.scatter(x, y, color=colors[color_count], label='data', zorder=100)
        plt.plot(x, big_boy_fit, color = 'black', zorder=100)

        plt.errorbar(x, y, yerr = error, linestyle='None', color='black', zorder=100)
        for (count, x, y) in zip(count, x, y):
            plt.annotate(str(count), xy = (x, y+0.07), xycoords='data', color = 'black')

        plt.xlabel('Redshift bins')
        plt.ylabel('fmerg')
        plt.title('$M = $'+str(masscen))
        #plt.legend()
        try:
            plt.annotate(str(round(res_bb.params[1],2)), 
                xy=(0.01,0.95), xycoords='axes fraction', color='black')
        except IndexError:
            continue
        plt.annotate(str(round(np.mean(slope_list),2))+'+/-'+str(round(np.std(slope_list),2)), 
            xy=(0.01,0.9), xycoords='axes fraction', color='black')
        plt.show()

    color_count+=1

plt.clf()
color_list = ['#FFE5E5',
              '#FFB3B3','#FF9999','#FF8080',
              '#FF4D4D','#FF1A1A',
              '#E60000','#CC0000',
              '#990000','#660000',
              '#1A0000',
              'black','black','black']

for i, masscen in enumerate(centers_mass):
    try:
        if len(xs[i]) < 3:
            continue
    except IndexError:
        break
    '''
    print('i', i, 'zcen', zcen)
    print('xs', xs[i])
    print('ys', ys[i], ys[i].values)
    print(fit[i])
    '''
    try:
        plt.scatter(xs[i], ys[i].values, label = f'M = {round(masscen,2)}', color=color_list[i])
        plt.errorbar(xs[i], ys[i].values, yerr = errors[i], color=color_list[i], ls='None', capsize=2)
        plt.plot(xs[i], fit[i],  color=color_list[i], lw=5)
    except:
        break
    
plt.legend()
plt.xlabel(r'$z$')
plt.ylabel(r'$f_{\mathrm{merg}}$')
plt.show()