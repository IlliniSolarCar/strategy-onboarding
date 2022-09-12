![Screenshot of simulation in render mode](demo.png)

Welcome to strategy onboarding! One of the main projects is to create a driving plan for a simulated race based on Stage 1 of the [2022 American Solar Challenge](https://www.americansolarchallenge.org/the-competition/2022-american-solar-challenge/). It's totally fine if you can't code yet, you can try to make these race decisions in the GUI version with keyboard controls, and slowly work towards automating your manual decisions. Advanced programmers can use the headless version to quickly simulate many races to run optimization algorithms. This repository also contains some data from the 2022 race to [analyze](https://github.com/IlliniSolarCar/strategy-onboarding22/blob/main/analysis/analysis_fsgp2022_1.ipynb) as a separate project.

## How to get started:
* Install [VS Code](https://code.visualstudio.com/)
* Install [Python3](https://www.python.org/downloads/)
* Install [Git](https://git-scm.com/downloads)
* In a terminal/commandline, change directory to where you want to store this project
* Run in terminal: `git clone https://github.com/IlliniSolarCar/strategy-onboarding22`
* Open the strategy-onboarding22 folder in VS code, and open a terminal in the strategy-onboarding22 folder
* Create a virtual environment by running in terminal: `python3 -m venv .venv`
  * Should create a folder named ".venv"
  * If there is a VS Code popup asking whether you want to enable/activate the virtual environment, click yes.
* On mac, run `source .venv/bin/activate`. On windows, run `.venv/Scripts/activate.bat`
* There should be "(.venv)" before all commands in the terminal.
  * If not, try restarting VS Code or the terminal.
* Run in terminal: `pip3 install -r requirements.txt`
  * This installs modules like numpy, scipy, matplotlib that we depend on
* Try running sim.py 
  * Click on the file in the side bar to open, and then click the play button [ ▶️ ] in the upper right, or run in terminal: `python simulator/sim.py`
  * Click yes if prompted to install python extensions
  * A window filled with graphs should pop up. Press [P] on your keyboard to play the simulation.


## Goal: 




## Common problems:
* module not found: didn't activate virutal environemtn
* 

