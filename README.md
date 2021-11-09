# TCP-Test

A Black-box testing technique to test the base Linux TCP impementation

# Setup
This section will go over how to setup and run the testing environment, and how to create tests of your own. In order to start with the setup, please clone the repository.

## 0. Requirements and installation
1.  You will need a linux kernel. The currently tested kernel versions are 5.04 and 5.10, but it is expected that it will work with any kernel version.
1. In order to run this project, you need at least python version 3.8. The project has been tested with python versions 3.8 and 3.9.
1. Additionally, you must have pip installed.
1. Finally, you have to navigate to the github folder using the terminal and run the following command:
```
pip install -r requirements.txt
```
## 1. Where to find and store existing testcases
In order to find existing testcases, you must first checkout the auto_testing_develop branch. You can do that by the following git command:
```
git checkout auto_testing_develop
```
Afterwards you can find the testcases under the folder tcpTester/testCases. Each test case is represented by a python file, following the textX.py format, where X is the number of the test case.
## 2. How to write a testcase
## 3. How to run the defined testcases
