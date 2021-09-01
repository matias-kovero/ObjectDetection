# Object Detection - Splitgate

<!-- PROJECT LOGO -->
<p align="center">
  <a href="">
    <img src="https://avatars.githubusercontent.com/u/47692525" alt="Logo" width="90" height="90" style="border-radius: 50%;">
  </a>
  <h3 align="center">Object Detection for FPS games</h3>
  <p align="center">
  <a href="https://github.com/matias-kovero/ObjectDetection/issues">Report Bug</a>
  </p>
</p>

<!-- TABLE OF CONTENTS -->
<details open="open">
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About the Project</a>
      <ul>
        <li><a href="#disclaimer">Disclaimer</a></li>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#final-words">Final words</a></li>
  </ol>
</details>

<!-- ABOUT THE PROJECT -->
## About The Project
[<p align="center"><img width="350" src="./docs/debug.png"></p>](./docs/debug.png)

This project started as an experiment as  
> _is it possible to "cheat" in FPS games using object detection_.

I already know that object detection gives valuable information from images and is used in many sectors - from social media algorithms to basic quality control. I'v had an opporturnity to work with image recognition and on my spare time I have also created my own scrapers that classify images - for vaurious different cases. But that all is made on still images from different sources - where there isn't really any hurry on the inference results. 

I wanted to find out would it be feasible to inference a FPS game, and then use the inference results to our advantage. The biggest issue was: _will this be practical_ - as will it be fast enough. The inference would need to run on the same machine as the game and would it be hindered by the GPU.

As traditional video game hacking is made by reading process memory and different anti-cheats try to detect & block these reads. Object detection would take an totally different approach - no memory reading - thus would have the possibility to be undetected by anti-cheat. Another issue would be that how could we send input to the desired video game without triggering any flags. Main goal of this project is to showcase an POC, that indeed this is currently possible with relative affordable equipment.

### Disclaimer
I do not condem any hacking - it ruins the fun for you but also for other players. This project was created just to show that it is possible to "cheat" using object detection. Also this is my first bigger python project and totally first time using multiprocessing and threads - thus someone could benefit from optimizing the code. At the end I'm happy with the performance of the code, I managed to inference at ~28ms (~30 FPS) while the game was running at high settings +140 FPS.

### Built With
I won't go to details on how to create your own custom models as there are way better tutorials on how to do this. If you are going to create your own model, you should have atleast an intermediate understanding of Image Recognition - as creating an valid dataset and analyzing the model outcome could be challenging if you are totally new. 
That said [YOLOv5 Github](https://github.com/ultralytics/yolov5) is an good starting point.

Here is an list of programs / platforms I used for this project:
- [YOLOv5](https://github.com/ultralytics/yolov5) Object detection (custom model)
- [Google Colab](https://colab.research.google.com/) to train my model - they give free GPU (ex. my 300 epoch took only 3h)
- [CVAT](https://cvat.org/) to label my datasets
- [Roboflow](https://app.roboflow.com/) to enrich these datasets
- [Interception_py](https://github.com/cobrce/interception_py) for mouse hooking (more on why this later)

<!-- Getting started -->
## Getting started
This repo contains two pretrained modes that will detect enemies in Splitgate.  
`best.pt` is trained on +600 images for 300 epoch.  
`bestv2.pt` is then refined from that with +1500 images and an another 300 epochs.  

These models only work on Splitgate - if you want to test this out in different games, you will need to create your own models.

### Prerequisites
- Install [Interception Driver](https://github.com/oblitum/Interception)
- [YOLOv5 requirements](https://github.com/ultralytics/yolov5#quick-start-examples)

Interception driver is selected because it will hook to your mouse on OS level - has low latency and does not trigger virtual_mouse flag - anticheat softwares may look for that flag.  
If you aren't okay on installing that driver you will need to alter `inter.py` and use ex. [pyautogui](https://pyautogui.readthedocs.io/en/latest/) or [mouse](https://github.com/boppreh/mouse) - however latency might become an issue.  
If you are getting inference issues with YOLOv5 or it isn't finding any targets - try downgrading PyTorch CUDA version. Ex. I have CUDA +11.7, but needed to use PyTorch CUDA 10.2.

### Installation
When above steps are done you only need to clone the repo:
```sh
git clone https://github.com/matias-kovero/ObjectDetection.git
```

## Usage
I have stripped the smooth aim - as I see it would create harm to Splitgates community - I don't want to distirbute an plug and play repository. This was only ment for showing that this is currently possible - of course if you have the skillset - you could add your own aim functions - but this is up to you.
Currently the code has an really simple aim movement - that more likely will get you flagged - but still proves my point that you can _"hack"_ with this.  

### `main.py`
Main entrypoint - params found [here](https://github.com/matias-kovero/ObjectDetection/blob/0536b2752cedff554ddae14a8af8cedbb72e2559/main.py#L70). Example usage:
```sh
python .\main.py --source 480
```
You can change `--source` and `--img` for better performance (smaller img = faster inference, but accuracy suffers).  
If you have an beefy GPU and want better accuracy, try to set --img to 640 and whatever source.
### `gather.py`
If you are creating your own dataset, you might find this useful - as I used this to gather my images. It is currently set to take screenshot while mouse left is pressed, and after 10 sec cooldown, allows an new screenshot to be taken. Source code should be readable, so do what you want.
```sh
python .\gather.py
```

## Final words
I was suprised how "easily" you could inference and play the game with relative low budget GPU.
My 1660 Super managed to inference with about 28ms delay (~30FPS) and hooking it up with smoothing aim created an discusting aimbot.  
I really don't know how anti-cheats could detect this kind of cheating. Biggest issue is still how to send human like mouse movement to the game.
