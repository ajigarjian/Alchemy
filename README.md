# Alchemy

## 1. Create and activate your Virtual Env

1. First step is to create a virtual environment on your computer. Create a parent folder you'd like to house the project in.
2. Upon clicking into the folder, follow the guidance here to create a virtual environment: https://docs.python.org/3/library/venv.html
    - Essentially, run "python -m venv /path/to/new/virtual/environment" in the command line, where the path is the path on your computer into the root folder of your project (note: ensure Python version is at least 3.3 and below 6.6 - if Python2 already exists on comptuer, use "python3 in command instead of python)
3. Now you have a virtual environment named "venv" in your root folder. To activate the venv, navigate to the root folder with the venv folder via the command line, and run "source venv/bin/activate" on Mac or Unix, and "venv\Scripts\activate.bat" on Windows. Now you'll notice in your command line that you're in your virtual environment! Whenever you work on this project, make sure you are doing so with your venv activated.
4. Note - you can exit your venv at any time in the command line by typing "deactivate"

## 2. Download the existing project files

1. Click the green "<> Code" button in the upper right portion of this repository. Copy the HTTPS link under "clone" - https://github.com/ajigarjian/Alchemy.git
2. Run "git clone https://github.com/ajigarjian/Alchemy.git" in the root folder you'd like the project to be (make sure you're in your venv first!)
3. Now, your root folder should have the venv, as well as the recently downloaded files from the Github repository. Run 'pip install -r requirements.txt' to automatically download all the dependenices you'll need for the project (requirements.txt should be at the highest directory of the repo you downloaded).

## 3. Create .env file

1. In the AlchemyApp folder, create a file and name it ".env".
2. In the ".env" file, write the line OPENAI_API_KEY='xxx', where 'xxx' is the API key (text/email me for it, it is too sensitive to share online)

## 4. Run the code and git push/pull

1. Move into the AlchemyProject folder and run 'python manage.py runserver & python manage.py tailwind start'. The command has the tailwind addendum because we are using the tailwind css framework.
2. The code should now be running on your browser!Create a new branch to work on using the command "git checkout -b new-branch-name". Replace 'new-branch-name' with a descriptive name for your branch.
3. Make the changes you want to make to the files in the repository.
4. Stage your changes for commit using the command "git add ." or "git add file-name" to stage specific files.
5. Commit your changes using the command "git commit -m "Your commit message"".
6. Push your changes to the remote repository using the command "git push origin new-branch-name". Replace 'new-branch-name' with the name of the branch you created in step 6.
7. Finally, go to the GitHub repository in your browser and create a pull request to merge your changes into the main branch. Your changes should now be successfully merged into the main branch of the repository.
