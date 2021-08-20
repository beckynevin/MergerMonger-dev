import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import StratifiedKFold
from sklearn import preprocessing
from sklearn.preprocessing import LabelEncoder
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA
from sklearn.metrics import confusion_matrix

def plot_confusion_matrix(cm, target_names, title, cmap=plt.cm.Blues):
    sns.set_style("dark")
    plt.imshow(cm, interpolation='nearest', cmap=cmap)
    plt.colorbar()
    tick_marks = np.arange(len(target_names))
    target_names=['Nonmerger','Merger']
    plt.xticks(tick_marks, target_names)
    plt.yticks(tick_marks, target_names)
    plt.ylabel('True label', size=20)
    plt.xlabel('Predicted label', size=20)
    
    fmt = '.2f' 
    thresh = cm.max() / 2.
    for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
        plt.text(j, i, format(cm[i, j], fmt),
                 horizontalalignment="center",
                 color="white" if cm[i, j] > thresh else "black")
                 
def locate_max(a):
    smallest = max(a)
    return smallest, [index for index, element in enumerate(a)
              if smallest == element]

def testAndTrainIndices(test_fold, Nfolds, folds):

    print('finding test and train indices...')

    train_folds = np.delete(np.arange(Nfolds), test_fold)

    test_ind   = [i for i in range(len(folds)) if folds[i]==test_fold]
    train_ind  = [i for i in range(len(folds)) if folds[i] in train_folds]

    return test_ind, train_ind



def run_RFR(df_merg, features_list, run, verbose):
    # These are adjustable RFR parameters
    Nfolds = 10
    Ndat = 5000

    features = df_merg[features_list].values
    #,'nspax','re'
    Nfeatures = len(features[0])
    
    #dat['features']#.reshape(-1,1)
    labels = df_merg[['class label']].values
    folds = np.arange(len(labels))%Nfolds
    
    
    #Test on fold 0, train on the remaining folds:
    test_ind, train_ind = testAndTrainIndices(test_fold = 0, Nfolds = Nfolds, folds=folds)
    
    #divide features and labels into test and train sets:
    test_features = features[test_ind]
    test_labels   = labels[test_ind]
   
    train_features  = features[train_ind]
    train_labels    = labels[train_ind]

    print('training fold 0')
    #make a random forest model:
    model = RandomForestRegressor(max_depth=10, random_state=42)
    model.fit(train_features, train_labels)

    print('predicting...')
    # Predict on new data
    preds = model.predict(test_features)
    #print out the first few mass predictions to see if they make sense:
    if verbose=='yes':
        for h in range(10):
            print(test_labels[h], preds[h])


    # rank feature importance:
    importances = model.feature_importances_
    std = np.std([tree.feature_importances_ for tree in model.estimators_], axis=0)
    indices = np.argsort(importances)[::-1]

    if verbose=='yes':
        # Plot the feature importances of the forest
        plt.clf()
        plt.figure(figsize=(15,5))
        plt.title("RFR Feature importances for "+str(run))
        plt.bar(range(Nfeatures), importances[indices], yerr=std[indices], align="center", color='pink')
        plt.xticks(range(Nfeatures), indices)
        plt.xlim([-1, Nfeatures])
        plt.show()
        
        #plt.savefig('feature_importance_'+str(run)+'_rando.pdf')
        
        
        
        print('Run ', run)
        print('Importance in Order ~~~~')
    
    # find the index of the random one:
    random_idx = features_list.index('random')
    random_value = importances[random_idx]
    random_std = std[random_idx]
    if verbose=='yes':
        print('random idx', random_idx)
        print('random_value', random_value)
    unin_here = []
    important_here = []
    for j in range(len(indices)):
        #if importances[indices[j]] - std[indices[j]] > 0:
        print(indices[j], features_list[indices[j]])
        if importances[indices[j]] > random_value:# or importances[indices[j]] - std[indices[j]] > random_value - random_std:
            important_here.append(features_list[indices[j]])
        else:
            unin_here.append(features_list[indices[j]])
        
  
    return important_here, unin_here


def cross_term(row, t1, t2):
    return row[t1]*row[t2]


def group_consecutives(vals, step=1):
    """Return list of consecutive lists of numbers from vals (number list)."""
    run = []
    result = [run]
    expect = None
    for v in vals:
        if (v == expect) or (expect is None):
            run.append(v)
        else:
            run = [v]
            result.append(run)
        expect = v + step
    return result


# Calculates observability time AND computes the LD1 value for all of the simulated datapoints
def classify_sim(df, inputs_all, coef, inter, myr, myr_non):
    X = df[inputs_all].values
    y = df['class label'].values
    std_scale = preprocessing.StandardScaler().fit(X)
    X = std_scale.transform(X)


    enc = LabelEncoder()
    label_encoder = enc.fit(y)
    y = label_encoder.transform(y) + 1



    X_lda_1=[]
    X_lda_2=[]
    X_lda_all = []
    for j in range(len(X)):
        X_lda_all.append(np.sum(X[j]*coef)+inter)#list_inter[new_min_index][0]
        if y[j] ==1:
            X_lda_1.append(np.sum(X[j]*coef)+inter)#list_inter[new_min_index][0]
        else:
            X_lda_2.append(np.sum(X[j]*coef)+inter)#list_inter[new_min_index][0])
    #input_hist=X_lda_sklearn


    my_lists = {key:[] for key in myr}
    for j in range(len(df)):
        if df[['class label']].values[j]==1:
            my_lists[df[['Myr']].values[j][0]].append(np.sum(X[j]*coef)+inter)




    means=[]
    maxes=[]
    mins=[]
    std=[]
    myr_here=[]

    for j in range(len(myr)):

        if np.std(my_lists[myr[j]])==0 and myr[j]!=coalescence:# or np.std(my_lists[myr[j]])< 0.01*np.mean(my_lists[myr[j]]):
            continue
        means.append(np.mean(my_lists[myr[j]]))#was just my_lists
        maxes.append(np.max(my_lists[myr[j]]))
        mins.append(np.min(my_lists[myr[j]]))

        std.append(np.std(my_lists[myr[j]]))



        myr_here.append(myr[j])



    myr_detect_LDA_val=[]
    myr_detect_LDA=[]
    for o in range(len(means)):
        if means[o] > 0:#this means above the decision boundary
            myr_detect_LDA.append(o)
            myr_detect_LDA_val.append(myr[o])

    grouped=group_consecutives(myr_detect_LDA)

    interval=[]
    for o in range(len(grouped)):
        interval.append(myr_detect_LDA_val[myr_detect_LDA.index(grouped[o][-1])]-myr_detect_LDA_val[myr_detect_LDA.index(grouped[o][0])])
    LDA_time =np.sum(interval)
    return LDA_time, X_lda_all




def run_LDA(run, df, priors_list,input_singular, myr, myr_non,
                      breakpoint, verbose):
    
    
    
    
    
    
    #Okay so this next part actually needs to be adaptable to reproduce all possible cross-terms
    crossterms = []
    ct_1 = []
    ct_2 = []
    for j in range(len(input_singular)):
        for i in range(len(input_singular)):
            if j == i or i < j:
                continue
            #input_singular.append(input_singular[j]+'*'+input_singular[i])
            crossterms.append(input_singular[j]+'*'+input_singular[i])
            ct_1.append(input_singular[j])
            ct_2.append(input_singular[i])
    
    inputs = input_singular + crossterms
    
    # Now you have to construct a bunch of new rows to the df that include all of these cross-terms
    for j in range(len(crossterms)):
        
        df[crossterms[j]] = df.apply(cross_term, axis=1, args=(ct_1[j], ct_2[j]))
        
    
    
    OG_length=len(inputs)
    
    prev_input=[]
    prev_input_here=[]
    missclass=[]
    missclass_e=[]
    num_comps=[]
    list_coef=[]
    list_coef_std=[]
    list_covar=[]
    list_means=[]
    list_inter=[]
    list_inter_std=[]
    list_master=[]
    list_master_confusion=[]
    list_classes=[]
    kf_choose=[]
    list_std_scale=[]
    list_sklearn=[]
    list_mean_non=[]
    list_diagnostics=[]
    
    
    kf = StratifiedKFold(n_splits=5, random_state=True, shuffle=True)
    
    for o in range(len(inputs)):#len(inputs)-20):
    
        coef_mean=[]
        coef_std=[]
        inter_mean=[]
        inter_std=[]
        covar_mean=[]
        class_means_mean=[]
        coef_mean_std=[]
        accuracy=[]
        accuracy_e=[]
        inputs_this_step=[]
        confusion_master_this_step=[]
        master_this_step=[]
        classes_this_step=[]
        std_scale_this_step=[]
        sklearn_this_step=[]
        mean_non_this_step=[]
        diagnostics_this_step=[]
        kf_list=[]
        


        #Now inputs is changing and you need to go through and choose a variable
        for k in range(len(inputs)):#Search through every one
            
            prev_input.append(inputs[k])
            inputs_here=[]
            inputs_here.append(inputs[k])
            
            
            
            X_use = df[prev_input].values
            y_use = df['class label'].values
            

            std_scale = preprocessing.StandardScaler().fit(X_use)
            X = std_scale.transform(X_use)

            std_scale_this_step.append(std_scale)
            enc = LabelEncoder()
            label_encoder = enc.fit(y_use)
            y = label_encoder.transform(y_use)
            
            
            

            label_dict = {1: 'NonMerger', 2: 'Merger'}
            
            
    
            kf.get_n_splits(X, y)
            kf_list.append(kf.split(X,y))



            coef_list=[]
            inter_list=[]
            covar_list=[]
            means_list=[]
            classes_list=[]
            confusion_master=[]
            y_test_master=[]
            pred_master=[]
            single_prediction=[]
            mean_non_list=[]
            score=[]
            diagnostic_list = []
            count=0
            iterate = 0
            for train_index, test_index in kf.split(X, y):

                X_train, X_CV = X[train_index], X[test_index]
                y_train, y_CV = y[train_index], y[test_index]
                
                
                

                sklearn_lda = LDA( solver='svd',priors=priors_list,store_covariance=True)#store_covariance=False
                
                

                X_lda_sklearn = sklearn_lda.fit_transform(X_train, y_train)
                
                
                coef = sklearn_lda.coef_
                inter = sklearn_lda.intercept_
                covar = sklearn_lda.covariance_
                class_means = sklearn_lda.means_
                

                inter_list.append(inter)
                coef_list.append(coef)
                covar_list.append(covar)
                means_list.append(class_means)
                inter_list.append(inter)
                pred =sklearn_lda.predict(X_CV)
                diagnostic_list.append([test_index, y_CV, pred])
                
                
                classes_list.append(sklearn_lda.classes_)
                
                
                # was minimizing missclassifications:
                #single_prediction.append(confusion_matrix(pred,y_CV)[1][0]+confusion_matrix(pred,y_CV)[0][1])
                mat = confusion_matrix(pred,y_CV)
                
                confusion_master.append(mat)
                single_prediction.append(2*mat[1][1]/(2*mat[1][1]+mat[0][1]+mat[1][0]))
                my_lists_none = []
                my_lists_merg = []


                
            accuracy.append(np.mean(single_prediction))#/(master[0][0]+master[1][0]+master[0][1]+master[1][1]))
            accuracy_e.append(np.std(single_prediction))
            inputs_this_step.append(np.array(prev_input))
            
            confusion_master_this_step.append(np.array((np.mean(confusion_master,axis=0)/np.sum(np.mean(confusion_master,axis=0))).transpose()))
            master_this_step.append(np.array(np.mean(confusion_master, axis=0).transpose()))
            #print('appending with this', np.array(prev_input))
            
            classes_this_step.append(np.array(classes_list))
    
            diagnostics_this_step.append(np.array(diagnostic_list))
            
            coef_mean.append(np.mean(coef_list, axis=0))
            coef_std.append(np.std(coef_list, axis=0))
            
            covar_mean.append(np.mean(covar_list, axis=0))
            class_means_mean.append(np.mean(means_list, axis=0))
            
            
            
            inter_mean.append(np.mean(inter_list, axis=0))
            inter_std.append(np.std(inter_list, axis=0))
            
            #prev_input.remove(new_stuff)
            for m in range(len(inputs_here)):
                try:
                    prev_input.remove(inputs_here[m])
                except ValueError:
                    continue
            
        
        try:
            if accuracy_e[accuracy.index(max(accuracy))]<0.00001:
                STOP
                break
        except ValueError:
            continue
        #print('all of inputs', inputs_this_step)
        #print('selecting the best model for this step', (inputs_this_step[accuracy.index(min(accuracy))]))
        
        thing=(inputs_this_step[accuracy.index(max(accuracy))])
        
        
        prev_input_here.append(thing)
        
        for m in range(len(thing)):
            
            prev_input.append(thing[m])
            
            try:
                
                inputs.remove(thing[m])
            except ValueError:
                #print('~~~RUning into troubles')
                #print('inputs', inputs)
                #print('the thing to remove', thing[m])
                continue
        #print('the input now', inputs)
        #STOP
        prev_input=list(set(prev_input))
        #print('finding the max of this', accuracy)
        lookup = max(accuracy)
        missclass.append(lookup)
        
        
        
        #print('coef previous to selecting min', coef_mean)
        missclass_e.append(accuracy_e[accuracy.index(lookup)])
        
        
        
        
        
        kf_choose.append(kf_list[accuracy.index(lookup)])
        
        list_coef.append(coef_mean[accuracy.index(lookup)])
        #print('coef list', coef_mean[accuracy.index(min(accuracy))])
        list_coef_std.append(coef_std[accuracy.index(lookup)])
        
        list_covar.append(covar_mean[accuracy.index(lookup)])
        list_means.append(class_means_mean[accuracy.index(lookup)])
        
        list_inter.append(inter_mean[accuracy.index(lookup)])
        list_inter_std.append(inter_std[accuracy.index(lookup)])
        
        list_master.append(master_this_step[accuracy.index(lookup)])
        list_master_confusion.append(confusion_master_this_step[accuracy.index(lookup)])
        
        list_classes.append(classes_this_step[accuracy.index(lookup)])
        list_std_scale.append(std_scale_this_step[accuracy.index(lookup)])

        list_diagnostics.append(diagnostics_this_step[accuracy.index(lookup)])
            
        num_comps.append(len(prev_input))#
        
        
        if len(prev_input) > breakpoint:
            break
    
    
    min_A=max(missclass)
    
    min_comps=num_comps[missclass.index(max(missclass))]
    
    min_index=locate_max(missclass)[1][0]
    
    
    min_A=missclass[locate_max(missclass)[1][0]]
    min_A_e=missclass_e[locate_max(missclass)[1][0]]
    '''Now you need to use one standard error '''
    
    
    for m in range(len(missclass)):
        if (missclass[m]) > (min_A-min_A_e):
            
            new_min_index=m
            break
        else:
            new_min_index=min_index
    
    if verbose=='yes':
        plt.clf()
        plt.axvline(x = num_comps[new_min_index], color='k')
        plt.axvline(x = num_comps[min_index], color='k')
        plt.plot(num_comps, missclass, color='#97CC04')
        plt.scatter(num_comps, missclass, color='#97CC04')
        plt.errorbar(num_comps, missclass, yerr = missclass_e, color='#97CC04')
        plt.title('Selecting the number of components in LD1')
        plt.xlabel('Number of Components')
        plt.ylabel('F1')#Number of Misclassifications')
        plt.show()
    
    min_A=missclass[new_min_index]
    min_A_e=missclass_e[new_min_index]
    min_comps=num_comps[new_min_index]
    inputs_all=prev_input_here[new_min_index]#:new_min_index+1]
    
    diagnostics = list_diagnostics[new_min_index]
    
    
    
    splits=kf_choose[new_min_index]
    
    
    #if verbose=='yes':
    print(run,'&')
    
    # There has got to be a better way to write this that involves listing them in order of importance
    inds = abs(list_coef[new_min_index][0]).argsort()
    sortedinput = inputs_all[inds]
    
    #if verbose=='yes':
    print('sorted inputs', sortedinput)
    print('coeff', list_coef[new_min_index][0][inds])
    print('std', list_coef_std[new_min_index][0][inds])
    
    #print out the first five coeff
    for u in range(len(sortedinput)):
        print(round(list_coef[new_min_index][0][inds][-u],2),'$\pm$',round(list_coef_std[new_min_index][0][inds][-u],2),' ',sortedinput[-u],' &')

    print(round(float(list_inter[new_min_index][0]),2), '$\pm$', round(float(list_inter_std[new_min_index]),2),'//')
    
    covar = list_covar[new_min_index]
    means_all_classes = list_means[new_min_index]
    
    master=list_master[new_min_index]
    
    print('~~~Accuracy~~~')
    print((master[1][1]+master[0][0])/(master[0][0]+master[1][0]+master[0][1]+master[1][1]))
    print('~~~Precision~~~')
    print(master[1][1]/(master[0][1]+master[1][1]))#TP/(TP+FP)
    print('~~~Recall~~~')
    print(master[1][1]/(master[1][0]+master[1][1]))#TP/(TP+FN)
    print('~~~F1~~~')
    print((2*master[1][1])/(master[0][1]+master[1][0]+2*master[1][1]))#2TP/(2TP+FP+FN)
    
    A = (master[1][1]+master[0][0])/(master[0][0]+master[1][0]+master[0][1]+master[1][1])
    P = master[1][1]/(master[0][1]+master[1][1])
    R = master[1][1]/(master[1][0]+master[1][1])
    
    FPR = master[0][1]/(master[0][1] + master[0][0])
    
    print('TPR', R)
    print('FPR', FPR)
    
    # We have to figure out how many terms to include
    significant_term = []
    significant_coef = []
    significant_std = []
    for l in range(len(sortedinput)):
        if float(abs(list_coef[new_min_index][0][inds][l]) - 3*list_coef_std[new_min_index][0][inds][l]) > 0:
            #then it is still significant to 3. sigma
            significant_term.append(sortedinput[l])
            significant_coef.append(list_coef[new_min_index][0][inds][l])
            significant_std.append(list_coef_std[new_min_index][0][inds][l])
    # this next section is entirely for the interactive plot:
    if len(significant_term[::-1]) < 1:
        # We have to figure out how many terms to include
        significant_term = []
        significant_coef = []
        significant_std = []
        for l in range(len(sortedinput)):
            if float(abs(list_coef[new_min_index][0][inds][l]) - list_coef_std[new_min_index][0][inds][l]) > 0:
                #then it is still significant to 3. sigma
                significant_term.append(sortedinput[l])
                significant_coef.append(list_coef[new_min_index][0][inds][l])
                significant_std.append(list_coef_std[new_min_index][0][inds][l])
        # this next section is entirely for the interactive plot:
    
    selected_features = prev_input_here[new_min_index]
    # I want to create a 2D plot of the two most important terms
    
    
    obs_time, LDA_all = classify_sim(df, selected_features, list_coef[new_min_index], list_inter[new_min_index][0],
                               myr, myr_non)
    
    print('observability timescale', obs_time)
    
    sns.set_style("darkgrid")
    
    
    
    # Time to. graberoo the actual prediction
    std_mean=[float(x) for x in list_std_scale[new_min_index].mean_]
    std_std=[float(np.sqrt(x)) for x in list_std_scale[new_min_index].var_]
    
    
    
    
    return std_mean, std_std, selected_features, list_coef[new_min_index], list_inter[new_min_index],  A, P, R, LDA_all, myr, myr_non, covar, means_all_classes