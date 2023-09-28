![alt text](readme/personpath22.png)

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


![alt text](readme/personpath22_small.gif)
**We ask all researchers to re-download the videos / annotations, if your data copy was downloaded before 10/21/2022 (MM/DD/YYYY).**

[PersonPath22 Homepage](https://amazon-science.github.io/tracking-dataset/personpath22.html))


## Leaderboard
We encourage all researchers report their evaluation results on the [leaderboard](https://paperswithcode.com/sota/multi-object-tracking-on-personpath22) 
on paperswithcode.com.


## Requirements
The code should be run with python 3. We use the aws cli to help download the data, please first run
`python3 -m pip install -r requirements.txt` to install it.

The code also requires ffmpeg to process some videos, please install it for your respective system 
and make sure ffmpeg and ffprobe are available in the command line path. Use your package manager 
or find other download options here: https://ffmpeg.org/download.html

## Data 
Data can be downloaded using the download.py script in this folder. Simply run:
`python3 download.py`
It will automatically download the dataset videos and annotations and extract them under
REPO_ROOT/dataset/raw_data REPO_ROOT/dataset/annotations respectively.

There are a few videos from [external datasets](readme/external_dataset.md) that we don't have right to re-distribute, 
we also provide the following means to smoothly download and process them.  

## Annotation Format
Annotations are provided in the gluoncv motion dataset format:
https://github.com/dmlc/gluon-cv/tree/master/gluoncv/torch/data/gluoncv_motion_dataset

Annotations are provided with visible and amodal bounding boxes in anno_visible_2022.json and anno_amodal_2022.json
respectively.

## Public Detection
Please refer to [Public detection](readme/public_detection.md) for details

## Version
[Updated 10/21/2022] Bugs were fixed related to Pixabay and MEVA videos in the early downloading script. 

[Updated 09/28/2023] Official pre-trained detection results for "public detection" evaluation protocol.

[To Appear] Official script to convert gluoncv motion dataset format to MOTChallenge and MSCOCO dataset format.

[To Appear] The full FPS annotation. (The existing annotation only includes key frames which are sampled at 5FPS.)  


## License
This provided code is licensed under the Apache-2.0 License. 

The retrieved videos and their annotations are licensed under the CC-BY-NC-4.0 License.

