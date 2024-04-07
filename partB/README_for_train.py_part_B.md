
# Part B 

Implemented pretrained model is Resnet.

Following are the parameters for train.py :

--num_filters: Number of filters/kernels in each convolutional layer. Default: 128.

--activation: Activation function after each layer. Default: 'gelu'.

--filter_organization: Filter organization pattern. Default: 'double'.

--batch_normalization: Whether to apply batch normalization. Default: 'Yes'.

--dropout_value: Dropout rate to prevent overfitting. Default: 0.3.

--learning_rate: Learning rate for model training. Default: 0.0001.

--num_epochs: Number of epochs for training. Default: 10.

--dense_neurons: Number of neurons in the fully connected layer. Default: 1024.

--batch_size: Batch size for training data. Default: 32.

--data_augmentation: Whether to apply data augmentation. Default: 'Yes'.

--wandb_project: Project name used to track experiments in Weights & Biases dashboard. Default: 'DL_Assignment_2_CS23M046'.

--wandb_entity: Wandb Entity used to track experiments in the Weights & Biases dashboard. Default: 'cs23m046'.

--train_dataset: Path to training dataset. Default: None.

--test_dataset: Path to test dataset. Default: None.

--freeze_option: Freeze option. Default: 'all_except_last'.

--freeze_index: Freeze index. Default: 2.










                        
# Example Usage:

python train_partb.py --num_filters 128 --activation gelu --filter_organization double --batch_normalization Yes --dropout_value 0.3 --learning_rate 0.0001 --num_epochs 10 --dense_neurons 1024 --batch_size 32 --data_augmentation Yes --wandb_project DL_Assignment_2_CS23M046 --wandb_entity cs23m046 --train_dataset /path/to/training_dataset --test_dataset /path/to/test_dataset --freeze_option all_except_last --freeze_index 2




# Replace /path/to/training_dataset and /path/to/test_dataset with the actual paths to your training and test datasets, respectively.

                        
