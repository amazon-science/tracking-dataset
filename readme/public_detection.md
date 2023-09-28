## Public detection
To standardize the "public detection" evaluation protocol, we provide a pre-trained person detection model.

It is a Fully Convolutional Object Detection (FCOS) model that is trained on CrowdHuman train and validation dataset. It achieves 81.39% AP @ IOU = 0.5 AND 45.56% AP @ IOU = 0.75. 

We encourage all researchers report their model's results with the provided detection results. The detection results can be downloaded with [MOTChallenge format](https://aws-cv-sci-motion-public.s3.us-west-2.amazonaws.com/PersonPath22/public_detection_fcos/mot_format.zip) and [GluonCV format](https://aws-cv-sci-motion-public.s3.us-west-2.amazonaws.com/PersonPath22/public_detection_fcos/amazon_format.zip).