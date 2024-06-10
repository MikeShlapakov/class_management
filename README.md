# My Class Management Project
Classroom management, originating from the field of command and control. This project is essentially a system that will allow the user (admin) to control selected computers that are on the same local network.</br>
The admin can create a new classroom, to which they can add all the computers on which the client's application is installed.</br>
By using the app, the admin can view the screens of the connected users, connect to a remote computer, manage tasks on it, and control it ***(full control over the mouse and keyboard including blocking the input and output).***</br>
In the classroom, the users an use a chat, as well as sending task/assignment, share files, and e.c.</br>
</br>

Overall the project touches these aspects:
• multi-threading
• Interception of functions using Hooks
• Transferring data and images between computers using advanced techniques.

## installing and running
### installing
First, you have to install all the packages via: 
```pip m –python install –r req.txt```</br>
req.txt file contains the names of all the libraries that need to be downloaded.</br>
</br>
After downloading, check in main the address that the server is connects to. The address must be the address of the computer (if on LAN you can use 127.0.0.1).</br>
The client sould include the same address.</br>
</br>
### running
Run the SERVER (```python server.py```), then you can run the client (```python client.py```).</br>
You can Sign-in with a new client or log-in as an admin with ```user:admin pass:123```</br>
</br>

Have Fun!
