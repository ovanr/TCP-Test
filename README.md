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
The previous chapter mentions the directory where tests are made, as well as the naming convention. To create a new testcase we must create a new python file following the naming convention. For the purposes of this tutorial, let's say we make test15.py.
### Structuring the file
First we will have to import relevant classes and tools for making a testcase. These imports are the same for any testcase.
```python
from tcpTester.testCommand import (
    CommandType,
    ConnectParameters,
    ListenParameters,
    SendReceiveParameters,
    SendParameters,
    ReceiveParameters,
    TestCommand,
)
from tcpTester.config import TEST_SERVER_IP
from tcpTester.baseTestCase import BaseTestCase
```
Afterwards, it will be necessary to define the ports for the Test Server (TS) and the  System Under Test (SUT). 
* Our convention is to use port 6000 + testNumber-1 for the TS port, and 5000 + testNumber-1 for the SUT port. 
So, given that we made test15.py, and our testNumber is 15, we would get the following:
```python
PORT_TS = 6014
PORT_SUT = 5014
```
Then, we must create a class which defines our testcase. This class must be unique compared to the classes in the other test files under testCases. We use the naming convention Test{testNumber to string}. So in our case, TestFifteen.
* The class must inherit the BaseTestCase class.
* The class must define two properties, namely
    * Test name: describes what the test is about in a few words.
    * Test number: the textNumber we talked about earlier, so 15.
Thus, we end up with:
```python
class TestFifteen(BaseTestCase):
    @property
    def test_name(self) -> str:
        return "Testing testcase creation"

    @property
    def test_id(self) -> int:
        return 15
```
## 3. How to run the defined testcases
