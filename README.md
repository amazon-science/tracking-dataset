![alt text](readme/person_path_22.png)

# Large scale Real-world Multi-Person Tracking

This repo contains utility codes for the PersonPath22 dataset introduced in the
following ECCV 2022 paper.

> [**Large Scale Real-world Multi-Person Tracking**](https://www.amazon.science/publications/large-scale-real-world-multi-person-tracking),            
> Bing Shuai, Alessandro Bergamo, Uta Buechler, Andrew Berneshawi, Alyssa Boden and Joseph Tighe        


    @inproceedings{personpath22,
      title={Large Scale Real-world Multi-Person Tracking},
      author={Shuai, Bing and Bergamo, Alessandro and Buechler, Uta and Berneshawi, Andrew and Boden, Alyssa and Tighe, Joseph},
      booktitle={ECCV},
      year={2022},
      organization={Springer}
    }


![alt text](readme/person_path_22.gif)

## Leaderboard
We encourage all researchers report their evaluation results on the [leaderboard](https://paperswithcode.com/sota/multi-object-tracking-on-personpath22) 
on paperswithcode.com.


## Requirements
The code should be run with python 3. We use the aws cli to help download the data, please first run
`python3 -m pip install -r requirements.txt` to install it.

## Data 
Data can be downloaded using the download.py script in this folder. Simply run:
`python3 download.py`
It will automatically download the dataset videos and annotations and extract them under
REPO_ROOT/dataset/raw_data REPO_ROOT/dataset/annotations respectively.

There are a few videos from [extrenal datasets](readme/external_dataset.md) that we don't have right to re-distribute, 
we also provide the following means to smoothly download and process them.  

## Annotation Format
Annotations are provided in the gluoncv motion dataset format:
https://github.com/dmlc/gluon-cv/tree/master/gluoncv/torch/data/gluoncv_motion_dataset

Annotations are provided with visible and amodal bounding boxes in anno_visible_2022.json and anno_amodal_2022.json
respectively.


## Version
[Updated 10/21/2022] Bugs were fixed related to Pixabay and MEVA videos in the early downloading script. 
<span style="color: orange"> *We ask all researchers to re-download the videos / annotations 
if your data copy was downloaded before 10/21/2022 (MM/DD/YYYY).*
 </span> 

[TO Appear] Official script to convert gluoncv motion dataset format to MOTChallenge and MSCOCO dataset format.

[To Appear] Official pre-trained detection results for "public detection" evaluation protocol. 

[To Appear] The full FPS annotation. (The existing annotation only includes key frames which are sampled at 5FPS.)  


## License
This provided code is licensed under the Apache-2.0 License. 

The retrieved videos and their annotations are licensed under the CC-BY-NC-4.0 License.

