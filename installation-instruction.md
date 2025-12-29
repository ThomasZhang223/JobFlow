# Installation Manual for this Project
## Frontend:
We are using the Next.js framework and will need to install different things in the following order.
1. Install node version manager (nvm).
    - Run the following bash command: ```curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash```
2. Install node by running the following command with nvm: ```nvm install```
3. Use the latest version of node by using this command: ```nvm use node```
4. To create a new Next.js app, run this command: ```npx create-next-app my-app```. Please note that you can replace "my-app" with whatever name you want it to be.
5. You will then see the system asking you what settings you prefer. Answer according to your preferences and needs for the project.
6. cd into your "my-app" folder.
7. Use the command ```npm run dev``` to run it! You will see a local host link that you can use. That's it!

Note: For our current state, do NOT do step 4-5 as we already have an existing folder for our app.

## Backend:
Before you begin, follow these steps.
1. Create virtual environment using the following command: ```python3 -m venv venv```
2. Activate the virtual environment: ```source venv/bin/activate```
3. Install dependencies: ```pip install -r requirements.txt```
**Scrapy**

We are using Scrapy to scrape websites. This is a guide on how to use this tool.


