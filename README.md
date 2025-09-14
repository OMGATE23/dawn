# dawn
Dawn is a fully open-source AI generated app builder that takes visual feedback of the generated app for great results. Make SVGs, Simple HTML/CSS/JS or React apps with Dawn. 


## v0
The v0 will have a simple application maker system. It will return the HTML, JS, CSS and SVGs, and display it on the FE.
We will expect the FE of the application to be shippable from day one.
<img width="1351" height="1042" alt="UIGPT_v0" src="https://github.com/user-attachments/assets/6ed36eed-0b0e-4e17-bba6-25bd2adf503a" />

## v1 
In this version we will handle the flow where the UI output is taken back from FE to BE. The output which is displayed will be used as a feedback to check wether the output is as desired solving the problem why AI isn't as good at coding like humans, as they do not have the ability to get visual feedback on their code and update it accordingly

<img width="1551" height="1324" alt="UIGPT_v1" src="https://github.com/user-attachments/assets/3259cc5c-23c2-4b6f-bfc4-daa7767c2c2c" />

## v1.1
In this version, we will support the making of a complete React App and handle the bundling of the application.
Here are the key internal features
1. The application code can be big. So we will have to chunk it into tasks
2. The code must be stored for each session
3. Bundling of the final output, along with build success verification, and rectification if failed, shall be present as the app will be incomplete without this

<img width="1551" height="1324" alt="UIGPT_v2" src="https://github.com/user-attachments/assets/2a854eda-c133-42bc-9410-93ef2516b0ab" />
