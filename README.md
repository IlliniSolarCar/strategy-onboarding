![Screenshot of simulation in render mode](images/demo.png)

Welcome to strategy onboarding! One of the main projects is to create a driving plan for a simulated race based on Stage 1 of the [2022 American Solar Challenge](https://www.americansolarchallenge.org/the-competition/2022-american-solar-challenge/). It's totally fine if you can't code yet, you can try to make these race decisions in the GUI version with keyboard controls, and slowly work towards automating your manual decisions. Advanced programmers can use the headless version to quickly simulate many races to run optimization algorithms. This repository also contains some data from the 2022 race to [analyze](https://github.com/IlliniSolarCar/strategy-onboarding22/blob/main/analysis/analysis_fsgp2022_1.ipynb) as a separate project.

# How to get started:
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
* Try running `sim.py` 
  * Click on the file in the side bar to open, and then click the play button [ ▶️ ] in the upper right, or run in terminal: `python simulator/sim.py`
  * Click yes if prompted to install python extensions
  * After installing extensions, select the python intepreter to be '.venv' by clicking on Python version in the lower right corner of VS Code.
  * A window filled with graphs should pop up. Press [P] on your keyboard to play the simulation.


# Goal:
Running `sim.py` successfully will print out results containing the number of miles earned and the energy left. According to the American Solar Challenge (ASC) regulations, the team who earns the most miles wins. There are 4 stages to ASC 2022, so finishing a stage with extra energy left is desireable. The goal for this simulation of ASC 2022 Stage 1 is to earn as many miles as possible for Stage 1, and the tiebreaker will be the amount of energy left in the battery at the end.

This is what the [routebook](https://www.americansolarchallenge.org/ASC/wp-content/uploads/2022/06/ASC-2022-Route-Book.pdf) tells us:
![Timing of stage 1](images/stage1_times.png)
![Map of stage 1](images/stage1_map.png)

There are 2 base legs and 2 optional loops.

Independence -> Topeka (+loop) -> Grand Island (+loop)

Schedule:
* Cars are released from Independence at 9:00.
* Teams should arrive at Topeka between 11:15pm and 13:45. At Topeka, they must stop and charge for 45 minutes, then choose whether to do the Topeka Loop. If the car arrives later than 13:45, it doesn't have to wait 45 minutes and should continue on to Grand Island.
* If the team tries the loop, they must finish the loop by 14:00. After finishing the loop, they may leave Topeka if it's later than 13:45, or attempt another loop after waiting 15 minutes.
* Teams who don't try the loop may leave Topeka at 13:45.
* Teams stop driving where they are at 18:00. Cars charge until 20:00. The next day (7/10), cars charge from 7:00 to 9:00, then can start driving again towards Grand Island.
* Cars should arrive at Grand Island between 9:00 and 18:00 on 7/10. When they arrive, cars stop and charge for 45 minutes, then choose whether to do the Grand Island Loop. If a car doesn't arrive by 18:00, they are considered trailered and drop to last place :(
* If the team tries the loop, they must finish the loop by 18:00. After finishing the loop, they may attempt another loop after waiting 15 minutes.


# Common problems:
* pip install failed: You may be using an older version of this repository. Try running `git pull`.
* module not found: Didn't activate virtual environment, or virtual environment not installed in the correct place. Or python interpreter wasn't selected to be '.venv'.
* most random errors: Copy paste the error into Google and hope someone posted about the same problem somewhere :(

