# EMG-Controlled Robotic Hand

This project is currently in development and it's ment to control Arduino-based robotic hand by EMG muscle data using machine learning algorithm

![Live dashboard using Dash by plotly](https://i.imgur.com/0bKAc9m.png)

This is a student project, it's goint to have a basic machine learning algorithm to control a Arduino-Uno based robotic hand or any other device or it could be used as a controller. Arduino send voltage from non-invasive on-skin electrodes (EMG).
Repository contains arduino source code for passing raw EMG data to computer and python3 code for analyzing and sending control signals.

### What's done:
* Arduino code that sends voltage data
* Python module *emg_api.py* that provides API to connect, synchronise and read data in real-time from Arduino
* Server on Flask *emg_server.py* for real-time reading, processing and analyzing data from Arduino and sending processed data (e.g. Fourie transform) it to localhost:5000/emg/{channel} in *json* format. For now it's processing this data:
  * Fourie transform for frequency spectre analysis
  * Standart deviation calculation that will be used for ML as input
  * Just a raw voltage data
* Live web dashboard *emg_web_dashboard.py* made with [Dash by Plotly](https://plot.ly/products/dash/) that reads data from server and visualize it
![Changing number of channels showing](https://media.giphy.com/media/TH2ezXdGOONqkhkqFF/giphy.gif)
* Vue.js web dashboard prototype (made just for fun to see what possibilities are available)
![Vue.js web dashboard scratch](https://media.giphy.com/media/1ylcxnn1thUjvHeb5r/giphy.gif)

### What's going to be done:
* Implementation of TensorFlow for analyzing hand gestures
* Build web virtual hand to be controlled by EMG
* Redesign server side to get rid of http data sending to front-end
