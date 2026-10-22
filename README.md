# Project: SecureTTT
 ### Members: JT Nesbitt, Canon Shaw, Xander Argiro, Bo Stokes


**Project Description:**

This project is a Secure and insecure implementation of tic-tac-toe in order to show the differences 
between what an attacker can do to a "secure" network connection versus an "insecure" network connection.
To do this, a simple game of tic-tac-toe (TTT) with two players communicating across a server was created.
All network traffic flows through our attacker proxy (Our Man in the middle attacker), which for the sake 
of the testing, is a simulation of what ARP spoofing would essentially result in.

*AI USAGE STATMENT:* 
The authors would like to acknowledge the use of ChatGPT and Copilot,
a language model developed by OpenAI and Microsoft respectively, in the preparation of 
this assignment. These tools were used in the following way(s) in 
this assignment: brainstorming in our intial planning phase,
figuring out a plausable implementation for this project,
and assisting with implementation of TLS (And its certificates) and the network.
We did not roll our own crypto :D 
All concepts and code have been reviewed and are understood by the authors. 

- Understanding is derivered from: 
- https://realpython.com/python-sockets/
- https://www.geeksforgeeks.org/computer-networks/transport-layer-security-tls/
- As well as previous network classes
