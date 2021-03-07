# bubble detector using YOLOv4
~~~
Note : It's not the final version code. I will the refine and update the code.
~~~

## Overview 
Models detection speech bubble in webtoons or cartoons. I have referenced and implemented [pytorch-YOLOv4](https://github.com/Tianxiaomo/pytorch-YOLOv4) to detect speech bubble. The key point for improving performance is data analysis. In the case of speech bubbles, there are various forms. Therefore, I define the form of speech bubbles and present the results of training by considering the distribution of data.

<br>

### Definition of Speech Bubble

<!--
#### Original Trainning Data
|유미의 세포들|와라! 편의점|연애 혁명|랜덤채팅의 그녀|원피스|총수|총합|
|------------|-----------|--------|--------------|------|---|----|
|160|320|198|349|182|201|1410|

+ **The distribution is a figure collected by speech bubbles based on cuts.**


#### Performance Problem

![image](https://user-images.githubusercontent.com/61634628/105812024-d0837d00-5ff0-11eb-9977-1ac2805bee71.png)
+ **Most training data take the shape of ellipses.** 
<br><br>

-->

#### Various speech bubble forms of real webtoons
![image](https://user-images.githubusercontent.com/61634628/105813702-94055080-5ff3-11eb-92e5-ddfb921cb6a8.png)

+ **In fact, there are various colors and various shapes of speech bubbles in webtoons.**

<br>

### New Definition 
**Key standard for Data Definition: Shape, Color, Form** 

`standard`
+ shape : Ellipse(tawon), Thorn(gasi), Sea_urchin(seonggye), Rectangle(sagak), Cloud(gurm)
+ Color : Black/white(bw), Colorful(color), Transparency(tran), Gradation
+ Form : Basic, Double Speech bubble, Multi-External, Scatter-type
+ example image ![image](https://user-images.githubusercontent.com/61634628/106093155-1700e500-6173-11eb-9a5e-8828c45271c4.png)
 
+ **In this project, two categories are applied, shape and color, and form and Gradation are classified as ect.**
<br>


### classes
**This class is not about detection, but about speech bubble data distribution.** 
 

![image](https://user-images.githubusercontent.com/61634628/106093057-ee78eb00-6172-11eb-9783-4e2a2f380644.png)

 <!--
|tawon|gasi|seonggye|sagak|gurm|
|-----|----|--------|-----|----|
|tawon_bw<br>tawon_color<br>tawon_transparency|gasi_bw<br>gasi_color<br>gasi_transparency|seonggye_bw<br>seonggye_color<br>seonggye_transparency|sagak_bw<br>sagak_color<br>sagak_transparency|gurm_bw<br>gurm_color<br>gurm_transparency|
-->
<br>

### Install dependencies

+ **Pytorch Version** 
    + Pytorch 1.4.0 for TensorRT 7.0 and higher
    + Pytorch 1.5.0 and 1.6.0 for TensorRT 7.1.2 and higher

+ **Install Dependencies Code**
    ~~~
    pip install onnxruntime numpy torch tensorboardX scikit_image tqdm easydict Pillow skimage opencv_python pycocotools
    ~~~
    or
    ~~~
    pip install -r requirements.txt
    ~~~
<br>

### Pretrained model 

|**Model**|**Link**|
|---------|--------|
|YOLOv4|[Link](https://drive.google.com/open?id=1fcbR0bWzYfIEdLJPzOsn4R5mlvR6IQyA)|
|YOLOv4-bubble|[Link](https://drive.google.com/drive/u/2/folders/1hYGU8hPY1VH8P0DkKDnAfV4AOtRjKYhC)|
<br>

### Train 

+ **1. Download weight** 

+ **2. Train** 
    ~~~
    python train.py -g gpu_id -classes number of classes  -dir 'data_dir' -pretrained 'pretrained_model.pth'
    ~~~
    or
    ~~~
    Train.sh 
    ~~~
    
+ **3. Config setting**       
    + cfg.py
        + class = 1 
        + learning_rate = 0.001
        + max_batches = 2000 (class * 2000)
        + steps = [1600, 1800], (max_batches * 0.8 , max_batches * 0.9)
        + train_dir = your dataset root 
            + root tree <br> ![image](https://user-images.githubusercontent.com/61634628/106384599-16847a80-640f-11eb-94a4-ee8ab75649f1.png) <br> The image folder contains .jpg or .png image files. The XML folder contains .XML files(label).
              
    + cfg/yolov4.cfg
        + class 1
        + filter 18 (4 + 1 + class) * 3 (line: 961, 1049, 1137)

**If you want to train custom dataset, use the information above.**

<br>    

### Demo    
 
+ **1. Download weight**        
+ **2. Demo**
    ~~~
    python demp.py -cfgfile cfgfile -weightfile pretrained_model.pth -imgfile image_dir 
    ~~~
    + defualt cfgfile is `./cfg/yolov4.cfg`

<br>

### Metric

+ **1. validation dataset**


|tawon_bw|tawon_color|tawon_Transparency|gasi_bw|gasi_color|gasi_Transparency|seonggye_bw|seonggye_color|seonggye_Transparency|sagak_bw|sagak_color|sagak_Transparency|gurm_bw|gurm_color|gurm_Transparency|total|
|----|----|-----|-----|-----|-----|-----|-----|-----|------|-----|-----|-----|-----|------|----|
|116|70|68|65|29|59|51|43|44|42|33|69|47|2|12|750|


+ The above distribution is based on speech bubbles, not cuts.
+ The distribution is not constant because there are a number of speech bubbles inside a single cut. In addition, for some classes, examples are difficult to find, resulting in an unbalanced distribution as shown above.
