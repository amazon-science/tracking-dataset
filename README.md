# Large scale Real-world Multi-Person Tracking

This repo contains code and tools to retrieve and work with the large scale multi person tracking dataset in the
following paper.

> [**Large Scale Real-world Multi-Person Tracking**](),            
> Bing Shuai, Alessandro Bergamo, Uta Buechler, Andrew Berneshawi, Alyssa Boden and Joseph Tighe        


    @inproceedings{shuai2022dataset,
      title={Large Scale Real-world Multi-Person Tracking},
      author={Shuai, Bing and Bergamo, Alessandro and Buechler, Uta and Berneshawi, Andrew and Boden, Alyssa and Tighe, Joseph},
      booktitle={ECCV},
      year={2022}
    }

A detailed dataset homepage would be available very soon, stay tuned for more details.


## Requirements
The code should be run with python 3. We use the aws cli to help download the data, please first run
`python3 -m pip install -r requirements.txt` to install it

## Data 
Data can be downloaded using the download.py script in this folder. Simply run:
`python3 download.py`
It will automatically download the dataset videos and annotations and extract them under
REPO_ROOT/dataset/raw_data REPO_ROOT/dataset/annotations respectively

There are a few videos from [extrenal datasets](readme/external_dataset.md) that we don't have right to re-distribute, 
we also provide the following means to smoothly download and process them.  

## Annotations
Annotations are provided in the gluoncv motion dataset format:
https://github.com/dmlc/gluon-cv/tree/master/gluoncv/torch/data/gluoncv_motion_dataset

Annotations are provided with visible and amodal bounding boxes in anno_visible_v3.1.json and anno_amodal_v3.1.json
respectively.

## Version
This repo would be maintained by AWS AI team, and stay tuned for more utility scripts 
that are necessary to use this dataset.

## License
This provided code is licensed under the Apache-2.0 License. 

The retrieved videos and their annotations are licensed under the CC-BY-NC-4.0 License.

