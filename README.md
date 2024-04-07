This repository contains two Jupyter Notebook files for building Convolutional Neural Network (CNN) architectures for image classification tasks. The notebooks are divided into two parts: Part A and Part B.

# Part A: CNN Architecture from Scratch

In Part A, the architecture can be customized by adjusting the following parameters:

The architecture can be customized by adjusting parameters such as:

  - Number of Filters: 32, 64, 128
  - Activation Function: ReLU, GELU, SiLU, Mish
  - Filter Organization: Same, Double, Halve
  - Batch Normalization: Yes, No
  - Dropout Value: 0.2, 0.3
  - Learning Rate: 0.001, 0.0001
  - Number of Epochs: 5, 10
  - Number of Neurons in Dense Layer: 128, 256, 512, 1024
  - Batch Size: 32, 64
  - Data Augmentation: Yes, No

- Usage:

  - Pass the path of train dataset folder to :
  - Pass the path of test dataset folder to :




# Part B: Pre Trained CNN Model and Fine-Tuning

In Part B, the following parameters can be customized:

  - Number of filters: 32, 64, 128
  - Activation function: ReLU, GELU, SiLU, Mish
  - Filter organization: Same, Double, Halve
  - Batch normalization: Yes, No
  - Dropout value: 0.2, 0.3
  - Learning rate: 0.001, 0.0001
  - Number of epochs: 5, 10
  - Number of neurons in dense layer: 128, 256, 512, 1024
  - Batch size: 32, 64
  - Freezing option: All Except Last, Except First, Up To
  - Freeze index: 2, 3, 4
  - Data augmentation: Yes, No

- Usage:

  - Pass the path of train dataset folder to :
  - Pass the path of test dataset folder to :


- Note:
  
  - Each notebook provides detailed instructions and code comments to guide customization and execution.
  - It is recommended to have a GPU-enabled environment for faster training.
  - Ensure that the dataset folders are correctly structured and contain the necessary images for training and testing.
    

Feel free to explore and experiment with different parameter configurations to achieve optimal performance for your image classification tasks!


