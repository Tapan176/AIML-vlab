# # Convolutional Neural Network

# # Installing Theano
# # pip install --upgrade --no-deps git+git://github.com/Theano/Theano.git

# # Installing Tensorflow
# # Install Tensorflow from the website: https://www.tensorflow.org/versions/r0.12/get_started/os_setup.html

# # Installing Keras
# # pip install --upgrade keras

# # Part 1 - Building the CNN

# # Importing the Keras libraries and packages
# from keras.models import Sequential
# from keras.layers import Convolution2D
# from keras.layers import MaxPooling2D
# from keras.layers import Flatten
# from keras.layers import Dense

# # Initialising the CNN
# classifier = Sequential()

# # Step 1 - Convolution
# classifier.add(Convolution2D(32, 3, 3, input_shape = (64, 64, 3), activation = 'relu'))

# # Step 2 - Pooling
# classifier.add(MaxPooling2D(pool_size = (2, 2)))

# # Adding a second convolutional layer
# classifier.add(Convolution2D(32, 3, 3, activation = 'relu'))
# classifier.add(MaxPooling2D(pool_size = (2, 2)))

# # Step 3 - Flattening
# classifier.add(Flatten())

# # Step 4 - Full connection
# classifier.add(Dense(units = 128, activation = 'relu'))
# classifier.add(Dense(units = 1, activation = 'sigmoid'))

# # Compiling the CNN
# classifier.compile(optimizer = 'adam', loss = 'binary_crossentropy', metrics = ['accuracy'])

# # Part 2 - Fitting the CNN to the images

# from keras.preprocessing.image import ImageDataGenerator

# train_datagen = ImageDataGenerator(rescale = 1./255,
#                                    shear_range = 0.2,
#                                    zoom_range = 0.2,
#                                    horizontal_flip = True)

# test_datagen = ImageDataGenerator(rescale = 1./255)

# training_set = train_datagen.flow_from_directory('dataset/training_set',
#                                                  target_size = (64, 64),
#                                                  batch_size = 32,
#                                                  class_mode = 'binary')

# test_set = test_datagen.flow_from_directory('dataset/test_set',
#                                             target_size = (64, 64),
#                                             batch_size = 32,
#                                             class_mode = 'binary')

# # classifier.fit_generator(training_set,
# #                          samples_per_epoch = 8000,
# #                          nb_epoch = 25,
# #                          validation_data = test_set,
# #                          nb_val_samples = 2000)

# classifier.fit_generator(training_set,
#                          steps_per_epoch = 8000 // 32,  # Since you have 8000 samples and a batch size of 32
#                          epochs = 25,  # 'nb_epoch' is replaced with 'epochs'
#                          validation_data = test_set,
#                          validation_steps = 2000 // 32)  # Similar adjustment for validation

# Convolutional Neural Network

# Importing the Keras libraries and packages
from keras.models import Sequential
from keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout
from keras.optimizers import Adam
from keras.callbacks import EarlyStopping

# Initialising the CNN
classifier = Sequential()

# Step 1 - Convolution
classifier.add(Conv2D(32, (3, 3), input_shape=(64, 64, 3), activation='relu'))

# Step 2 - Pooling
classifier.add(MaxPooling2D(pool_size=(2, 2)))

# Adding a second convolutional layer
classifier.add(Conv2D(64, (3, 3), activation='relu'))
classifier.add(MaxPooling2D(pool_size=(2, 2)))

# Step 3 - Flattening
classifier.add(Flatten())

# Step 4 - Full connection
classifier.add(Dense(units=128, activation='relu'))
classifier.add(Dropout(0.5))  # Adding dropout to reduce overfitting
classifier.add(Dense(units=1, activation='sigmoid'))

# Compiling the CNN
optimizer = Adam(learning_rate=0.0001)  # Adjusting learning rate for better convergence
classifier.compile(optimizer=optimizer, loss='binary_crossentropy', metrics=['accuracy'])

# Part 2 - Fitting the CNN to the images

from keras.preprocessing.image import ImageDataGenerator

train_datagen = ImageDataGenerator(rescale=1./255,
                                   shear_range=0.2,
                                   zoom_range=0.2,
                                   horizontal_flip=True)

test_datagen = ImageDataGenerator(rescale=1./255)

training_set = train_datagen.flow_from_directory('dataset/training_set',
                                                 target_size=(64, 64),
                                                 batch_size=32,
                                                 class_mode='binary')

test_set = test_datagen.flow_from_directory('dataset/test_set',
                                            target_size=(64, 64),
                                            batch_size=32,
                                            class_mode='binary')

# Implementing Early Stopping to prevent overfitting
early_stopping = EarlyStopping(monitor='val_loss', patience=3, restore_best_weights=True)

classifier.fit_generator(training_set,
                         steps_per_epoch=len(training_set),
                         epochs=25,
                         validation_data=test_set,
                         validation_steps=len(test_set),
                         callbacks=[early_stopping])

# Save the model
classifier.save("cnn.h5")

# from keras.models import load_model

# # Load the saved model
# loaded_model = load_model("your_model_name.h5")
