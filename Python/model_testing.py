from os import path, listdir
from matplotlib import pyplot, cm, patches
from mpl_toolkits.mplot3d import Axes3D
from sklearn import model_selection
from sklearn.utils import shuffle
from calculation_functions import lymph_equation
from performance_evaluation import calc_MCC
from model_definitions import FunctionalDenseModel
from sim_loading import load_data, load_training_data
from real_loading import load_real_model_data
import numpy as np
import random, time
from sklearn.model_selection import KFold

def test_model(model, num_samples):
    #Load files in grid test dictionary and predict them with the trained model
    # grid_header = {'depth':0, 'x_dist':1, 'y_dist':2, 'distance':3, 'frequency':4, 'potential':5}
    grid_header = {'lymph_y':0, 'lymph_x':1, 'depth':2, 'x_dist':3, 'y_dist':4, 'distance':5, 'frequency':6, 'potential':7}
    folder_path = 'NewTest/'
    if not path.exists(folder_path):
        raise FileNotFoundError('Folder does not exist')

    # x_differences = []
    # y_differences = []

    print('Loading grid test data')
    for filename in listdir(folder_path):
        test_data = load_data(path.join(folder_path, filename), grid_header, 'test', num_samples)
        x_vals = [val[1][0] for val in test_data]
        y_vals = [val[1][1] for val in test_data]
        h_vals = model.predict([val[3] for val in test_data])
        h_vals = [val[0] for val in h_vals]
        g_vals = [val[2] for val in test_data]
        r_vals = [val[4] for val in test_data]

        r_vals_trunc = []
        for v in r_vals:
            if v < 0:
                r_vals_trunc.append(0)
            elif v > 1:
                r_vals_trunc.append(1)
            else:
                r_vals_trunc.append(v)
        
        dpi = 40
        size = 20
        pyplot.rcParams.update({'font.size': 40})
        
        lab = []
        for i, _ in enumerate(x_vals):
            lab.append(((x_vals[i],y_vals[i])))
    
        eli = patches.Ellipse((g_vals[0][0]-8,g_vals[0][1]), width = 20, height = 10)
        eli.set_linewidth(5)
        eli.set_fill(False)
        eli.set_facecolor(None)
        eli.set_edgecolor(color='forestgreen')

        fig = pyplot.figure()
        ax = fig.add_subplot()
        fig.suptitle(filename)
        ax.set_title("Average calculated conductivity(S \u00B7 m\u207B¹)")
        ax.set_xlabel('x (mm)', labelpad=10)
        ax.set_ylabel('y (mm)', labelpad=10)
        ax.set_aspect(1)
        surf = ax.tricontourf(x_vals,y_vals,r_vals, cmap='coolwarm')
        fig.colorbar(surf, shrink=0.5, aspect=5)
        ax.add_patch(eli)
        ax.legend(["Ground Truth"])
        pyplot.show()


        gnd_vals = []
        for val in test_data:
            gnd_vals.append(lymph_equation(val[2][0],val[2][1],1, val[1][0], val[1][1],1))
        
        bestMcc = -1
        bestThresh = 0
        print(filename, ": ")
        for val in np.arange(0.01,1,0.01):
            MCC = calc_MCC(gnd_vals, h_vals, val)
            if MCC > bestMcc:
                bestMcc = MCC
                bestThresh = val
        print("Best MCC", bestMcc)
        print("Best threshold", bestThresh)

        size = 20
        dpi = 40

        eli = patches.Ellipse((g_vals[0][0]-8,g_vals[0][1]),width = 10, height = 5)
        eli.set_linewidth(5)
        eli.set_fill(False)
        eli.set_facecolor(None)
        eli.set_edgecolor(color='limegreen')

        fig = pyplot.figure(figsize=(size*2,size), dpi=dpi)
        ax = pyplot.axes()

        fig.suptitle(filename)
        surf = ax.tricontourf(x_vals, y_vals, h_vals, cmap='coolwarm', antialiased=False, vmax=1., vmin=0.)
        ax.set_xlabel('x (mm)', labelpad=10)
        ax.set_ylabel('y (mm)', labelpad=10)
        ax.set_aspect(1)
        ax.set_title("Confidence")
        fig.colorbar(surf, shrink=0.5, aspect=5)  
        ax.add_patch(eli)
        ax.legend(["Ground Truth"])


    pyplot.show()

def test_model_real_data(model, test_folder_path):
    test_data = load_real_model_data(test_folder_path, 'Test')

    xs = []
    ys = []
    zs = []

    test_conductivities = [p.conductivities for p in test_data]
    time_taken = []
    for i, point in enumerate(test_data):
        xs.append(point.x)
        ys.append(point.y)
        tic = time.perf_counter()
        z = float(model.predict([test_conductivities[i]])[0])
        toc = time.perf_counter()
        time_taken.append(toc-tic)
        zs.append(z)

    print(time_taken)

    for x, y, z_val in zip(xs, ys, zs):
        print('%f;%f;%f' % (x, y, z_val))
    return
    

    size = 20
    dpi = 40
    fig = pyplot.figure()
    ax = pyplot.axes()

    surf = ax.tricontourf(xs, ys, zs, cmap='coolwarm', antialiased=False)
    fig.colorbar(surf, shrink=0.5, aspect=5)  
    #ax.add_patch(eli)
    ax.legend(["Ground Truth"])
    pyplot.show()

    gnd_vals = []
    for val in test_data:
        gnd_vals.append(val.ground_truth)
    
    bestMcc = -1
    bestThresh = 0
    for val in np.arange(0.01,1,0.01):
        MCC = calc_MCC(gnd_vals, zs, val)
        if MCC > bestMcc:
            bestMcc = MCC
            bestThresh = val
    print("Best MCC", bestMcc)
    print("Best threshold", bestThresh)

    return

def plot_conductivity_val(val, identifier):
    vals = []
    curr = []

    for v in val[1]:
        curr.append(v)
        if len(curr) == 5:
            vals.append(curr)
            curr=[]
    
    x_vals = [0, 1, 2, 3, 4]
    for freq in vals:
        pyplot.plot(x_vals, freq)
    
    pyplot.savefig('%d %s.png' % (identifier, str(val[0])))
    pyplot.cla()

    pass

def save_training_data(training_data):
    with open('data.txt', 'a+') as f:
        for gt, data in training_data:
            output = '%s|%s\n' % (str(gt), ';'.join([str(v) for v in data]))
            f.write(output)

def load_training_data_from_disk():
    training_data = []
    with open('data.txt', 'r+') as f:
        data = f.readlines()
        for line in data:
            split_line = line.split('|')
            gt = split_line[0] == 'True'
            data = [float(v) for v in split_line[1].split(';')]
            training_data.append((gt, data))

    return training_data

def test_model_type(model, num_samples, retrain_model, real_data = True):
    if not real_data:
        if retrain_model:
            headers = [{'lymph_y':0, 'lymph_x':1, 'depth':2, 'x_dist':3, 'y_dist':4, 'distance':5, 'frequency':6, 'potential':7}]
            paths = ['water_data_output']

            x_train, y_train = load_training_data(headers, paths, num_samples, augment=False, normalise_frequency=False)

            model.train_model(x_train, y_train)
        else:
            model.load()
            
        test_model(model, num_samples)

    else:
        if retrain_model:
            # Uncomment to load new data

            # folder_path = '/Tissue training data'
            # train_data = load_real_model_data(folder_path, "Train")


            # filtered_train_data = []
            # for gt, data in train_data:
            #     if len(data) != 75:
            #         print('Train data not long enough')
            #         continue
            #     if not all(v > 0 for v in data):
            #         print('Negative found in training data, discarding')
            #         continue

            #     filtered_train_data.append((gt, data))

            # save_training_data(filtered_train_data)
            filtered_train_data = load_training_data_from_disk()

            #print('%d Points removed' % (len(train_data) - len(filtered_train_data)))
            # for index, val in enumerate(filtered_train_data):
            #     plot_conductivity_val(val, index)

            
            random.shuffle(filtered_train_data)
            bins = {False: [], True: []}
            for gt, data in filtered_train_data:
                bins[gt].append((gt, data))

            true_count = len(bins[True])
            false_count = len(bins[False])

            print('%d True, %d False' % (true_count, false_count))

            # new_train = []

            # if true_count > false_count:
            #     for i, false_val in enumerate(bins[False]):
            #         new_train.append(false_val)
            #         new_train.append(bins[True][i])

            # else:            
            #     for i in range(len(bins[True]) * 2):
            #         new_train.append(bins[False][i])

            #     new_train.extend(bins[True])
            random.shuffle(filtered_train_data)    


            x_train = [val[1] for val in filtered_train_data]
            y_train = [val[0] for val in filtered_train_data]

            model.train_model(x_train, y_train)

        else:
            model.load()
        
        test_model_real_data(model, '/tissue test data') 


# K-Fold data test
def train_model():
    data = load_training_data_from_disk()

    random.shuffle(data)

    inputs = [v[1] for v in data]
    targets = [v[0] for v in data]

    kf = KFold(n_splits = 5, shuffle = True)

    inputs = np.array(inputs)
    targets = np.array(targets)

    all_scores = []

    for train, test in kf.split(inputs, targets):
        model = FunctionalDenseModel('models/tissuemodel/model', 75)

        history = model.model.fit(inputs[train], targets[train], batch_size=4, epochs=250, verbose = 1)

        scores = model.model.evaluate(inputs[test], targets[test], verbose = 0)
        all_scores.append(scores)        

    for i, (loss, acc) in enumerate(all_scores):
        print('Fold %d accuracy = %f, loss = %f' % (i+1, acc*100, loss))



if __name__ == "__main__":
    test_model_type(FunctionalDenseModel('models/tissuemodel/model', 75), 8, retrain_model=True)
    #test_model_type(SklearnMlp('models/simmodel/model'),8, retrain_model=True)
    #train_model()