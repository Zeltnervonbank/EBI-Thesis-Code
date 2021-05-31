from os import path, mkdir
import tensorflow as tf
from matplotlib import pyplot
import pickle
from sklearn.neural_network import MLPRegressor

# General form for a model
class MlModel:
    def __init__(self, model_path):
        self.model_path = model_path
        dirpath = path.dirname(self.model_path)
        if not path.exists(dirpath):
            mkdir(dirpath)
        
        self.model = None
        pass
    
    def train(self, training_data):
        pass

    def predict(self, data):
        pass

    def persist(self):
        pass

    def load(self):
        pass

class FunctionalDenseModel(MlModel):
    def __init__(self, model_path, input_shape):
        super().__init__(model_path)

        physical_devices = tf.config.list_physical_devices('GPU') 
        tf.config.experimental.set_memory_growth(physical_devices[0], True)

        self.training_epochs = 250
        self.batch_size = 4

        inputs = tf.keras.Input(shape = input_shape, name='Data')
        x = tf.keras.layers.Dense(256)(inputs)

        #x = tf.keras.layers.Dropout(0.5)(x)
        #x = tf.keras.layers.Dense(75)(x)
        #x = tf.keras.layers.BatchNormalization()(x)
        #x = tf.keras.layers.Dense(128)(x)
        #x = tf.keras.layers.Dense(256)(x)
        #x = tf.keras.layers.Dense(32)(x)
        output = tf.keras.layers.Dense(1, activation='sigmoid')(x)

        self.model = tf.keras.Model(inputs, output, name='Direction_net')
        self.model.summary()

        lr_schedule = tf.keras.optimizers.schedules.ExponentialDecay(
            initial_learning_rate=0.001,
            decay_steps=100,
            decay_rate=0.96)

        opt = tf.keras.optimizers.RMSprop(learning_rate=lr_schedule)
        self.model.compile(optimizer=opt,
                loss='binary_crossentropy',
                metrics=['accuracy'])

    def train_model(self, data, ground_truth):
        quarter = int(len(data)/4)
        val_data = data[:quarter]
        val_truth = ground_truth[:quarter]
        train_data = data[quarter:]
        train_truth = ground_truth[quarter:]

        # kf = KFold(n_splits=4, shuffle=False, random_state=None)

        # for train_index, val_index in kf.split(data):
        #     data_train = []
        #     data_val = []
        #     y_train = []
        #     y_val = []
        #     for index in train_index:
        #         data_train.append(data[index])
        #         y_train.append(ground_truth[index])
        #     for index in val_index:
        #         data_val.append(data[index])
        #         y_val.append(ground_truth[index])

        print('Fitting on %d data points' % (len(train_data)))
        history = self.model.fit(
            train_data, 
            train_truth, 
            epochs=self.training_epochs, 
            batch_size=self.batch_size, 
            validation_data=(val_data, val_truth)
            )
        print('Fitting complete')

        self.persist()

        # plot loss during training
        pyplot.subplot(211)
        pyplot.title('Loss')
        pyplot.plot(history.history['loss'], label='train')
        pyplot.plot(history.history['val_loss'], label='test')
        pyplot.legend()
        # plot accuracy during training
        pyplot.subplot(212)
        pyplot.title('Accuracy')
        pyplot.plot(history.history['accuracy'], label='train')
        pyplot.plot(history.history['val_accuracy'], label='test')
        pyplot.legend()
        pyplot.show()

    def predict(self, data):
        vals = self.model.predict(data)
        return list(vals)

    def persist(self):
        self.model.save_weights(self.model_path)

    def load(self):
        self.model.load_weights(self.model_path)



class SklearnMlp(MlModel):
    def __init__(self, model_path):
        super().__init__(model_path)
        self.model = MLPRegressor(solver='adam', alpha=1e-5, hidden_layer_sizes=(50), random_state=None)        

    def train_model(self, data, ground_truth):
        print('Fitting on %d data points' % (len(data)))
        self.model.fit(data, ground_truth)
        print('Fitting complete')

        self.persist()

    def predict(self, data):
        vals = self.model.predict(data)
        return list(vals)

    def persist(self):
        with open(self.model_path, 'wb') as f:
            pickle.dump(self.model, f)

    def load(self):
        with open(self.model_path, 'rb') as f:
            self.model = pickle.load(f)


class SequentialDenseModel(MlModel):
    def __init__(self, model_path):
        super().__init__(model_path)

        physical_devices = tf.config.list_physical_devices('GPU') 
        tf.config.experimental.set_memory_growth(physical_devices[0], True)

        self.training_epochs = 2

        self.model = tf.keras.Sequential([
            tf.keras.layers.Dense(20, activation='relu'),
            tf.keras.layers.Dense(1)
        ])

        self.model.compile(optimizer='adam',
              loss='mse',
              metrics=['accuracy'])
        pass

    def train_model(self, data, ground_truth):
        print('Fitting on %d data points' % (len(data)))
        history = self.model.fit(data, ground_truth, epochs=self.training_epochs)
        print('Fitting complete')

        self.persist()

        # plot loss during training
        pyplot.subplot(211)
        pyplot.title('Loss')
        pyplot.plot(history.history['loss'], label='train')
        pyplot.plot(history.history['val_loss'], label='test')
        pyplot.legend()
        # plot accuracy during training
        pyplot.subplot(212)
        pyplot.title('Accuracy')
        pyplot.plot(history.history['accuracy'], label='train')
        pyplot.plot(history.history['val_accuracy'], label='test')
        pyplot.legend()
        pyplot.show()

    def predict(self, data):
        vals = self.model.predict(data)
        return list(vals)

    def persist(self):
        self.model.save_weights(self.model_path)

    def load(self):
        self.model.load_weights(self.model_path)