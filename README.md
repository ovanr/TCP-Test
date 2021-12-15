# TCP Testing using AltWalker

## Running

**Note that the `testServerMain.py` and the `sutMain.py` must run on different machines**

1. Install python dependencies: `pip install --user -r requirements.txt`

2. Edit `test_server.ini` and specify the interface (iface) of where the test server should listen to (wifi or ethernet), specify the IP of the host that will be running the SUT and the port for communicating with AltWalker (in the AltWalker code these would be the port for the TestServer socket)

3. Edit `sut.ini` and specify the Torxakis port (in the AltWalker code this would be the port for the SUT socket). Additionally specify the IP address of the host that will be running the test server

4. Edit the `altwalker.ini` file and specify the IP and ports of the Sut and Test Server.

5. Start the sut: `python3 sutMain.py sut.ini`

6. Start the test server: `sudo python3 testServerMain.py test_server.ini`

7. Start altwalker: `altwalker online tests -m models/Tcp.json" "weighted_random(edge_coverage)"`
You can change the exit condition and generator for AltWalker/Graphwalker as specified on their website: "https://github.com/GraphWalker/graphwalker-project/wiki/Generators-and-stop-conditions".

