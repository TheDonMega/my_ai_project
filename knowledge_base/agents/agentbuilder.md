To convert the information about building AI Agents with Vertex AI Agent Builder into a Markdown file, here is the formatted content:

```markdown
# Building AI Agents with Vertex AI Agent Builder

This document summarizes the process of building, grounding, and deploying AI Agents using Google Cloud's Vertex AI Agent Builder, based on the provided codelabs.

## 1. Before You Begin

Before you start, it's essential to have a basic understanding of Generative AI on Google Cloud and AI Agent Concepts. You will need a **working computer**, **reliable Wi-Fi**, and a **Google Cloud project with billing attached**. If you don't have a Google Cloud project, instructions are available for creation, and you can also check out the Google Cloud Free Tier Services.

## 2. Designing Your First AI Agent

Designing your AI agent requires establishing a clear vision by asking key questions:

*   **What problem will it solve?** (e.g., automating tasks, providing information, entertainment)
*   **What are its primary functions?** (e.g., executing/delegating tasks, generating text/media)
*   **What are its limitations?** (e.g., autonomy, knowledge boundaries)
*   **What personality or persona should it have?** (e.g., formal, humorous, helpful)
*   **What are the success metrics?** (How will effectiveness be measured?)

For a travel agent example, the codelab provides pre-answered questions:

*   **Problem to solve:** Planning trips, discovering destinations, planning itineraries, booking flights and accommodations.
*   **Primary functions:** Answering destination questions (e.g., visa requirements), planning itineraries, booking flights and accommodations.
*   **Limitations:** May not answer complicated queries by default, won't generate visual images, knowledge limited by the underlying model.
*   **Personality:** Knowledgeable, helpful, enthusiastic about travel, communicates clearly and concisely.
*   **Success metrics:** User satisfaction with recommendations (exploring, planning, booking).

## 3. Building an AI Agent with Vertex AI Agent Builder

Creating an AI Agent in Vertex AI Agent Builder involves several steps:

1.  **Activate API**: Go to Vertex AI Agent Builder and click "CONTINUE AND ACTIVATE THE API".
2.  **Create New App**: You'll be redirected to the App Creation page; click "CREATE A NEW APP".
3.  **Choose Agent Type**: Select "Conversational agent" and click "CREATE". This opens a new Dialogflow Conversational Agents tab. You might need to select your Google Cloud Project and enable the Dialogflow API. In the Dialogflow page, click "Create Agent" and choose "Build your own".
4.  **Configure Agent**:
    *   **Pick a Display Name** (e.g., Travel Buddy).
    *   **Select Location**: Choose "global (Global serving, data-at-rest in US)" as the Region.
    *   Keep other configurations **default**.
    *   Click "CREATE".
5.  **Define Playbook**:
    *   **Pick a Playbook Name** (e.g., Info Agent).
    *   **Add a Goal** (e.g., Help customers answer travel related queries).
    *   **Define an Instruction** (e.g., Greet users, then ask how you can help them).
    *   Press "Save".
6.  **Test Agent**:
    *   Click the "Toggle Simulator" icon.
    *   Select your created agent (e.g., *Info Agent*).
    *   Choose an underlying generative AI model (e.g., *gemini-1.5-flash*).
    *   Test by typing input in the "Enter User Input" text box.

Upon completion of these steps, you will have successfully created an AI Agent.

## 4. Attaching Datastores to the Agent

To make your agent more helpful, especially when it can't answer questions from its built-in knowledge, you can **provide additional information through Datastores**. Datastores act as an additional knowledge base.

Steps to attach a Datastore:

1.  **Create a Datastore Tool**:
    *   Click the "+ Data store" button at the bottom of the Agent Basics page.
    *   Fill in:
        *   **Tool name:** Alternative Location
        *   **Type:** Data store
        *   **Description:** Use this tool if user's request contains a location that doesn't exist
    *   Click "Save".
2.  **Create Actual Datastore**:
    *   Click "add data stores" and then "Create a data store".
    *   Choose "Cloud Storage" option.
    *   Click on "FILE" (important to prevent import failure) and type `ai-workshops/agents/data/wakanda.txt`.
    *   Click "CONTINUE".
    *   Name your datastore (e.g., Wakanda Alternative) and click "CREATE".
    *   **SELECT** the data source you just created and click "CREATE". The import progress can be seen by clicking on your datastore.
3.  **Configure Grounding (Optional but Recommended)**:
    *   In the Dialogflow tab, refresh to see the datastore under "Available data stores".
    *   To prevent hallucinations, set the **grounding configuration** for your data store to "Very Low," which applies tighter restrictions on the agent from making things up. Keep it default for now but explore different settings later.
    *   Select the added data store, click "confirm," then "save".
4.  **Include Datastore Tool in Agent Instructions**:
    *   Go back to your Agent Basics page, check the Data Store (e.g., Alternative Location) at the bottom of the playbook configuration.
    *   Click "Save" at the top of the page.
    *   Add the line: `- Use ${TOOL: Alternative Location} if the user's request contains a location that does not exist` to the agent's instructions.
    *   Click "save".

Now, the agent can recommend places using the provided information from the text file. For example, asking "What's the best way to reach Wakanda?" will now yield suggestions like Oribi Gorge or Iguazu Falls, derived from the `wakanda.txt` content.

## 5. Additional Activities - Make Your AI Agent Live

After developing and grounding your AI agent, you can embed it within your website for real-time interaction.

There are various ways to expose your agent, including exporting or directly publishing it.

### Publishing the Agent for Web Integration

1.  **Publish Agent**: In the top right corner of your Dialogflow tab, click "Overflow menu" and then "Publish agent".
2.  **Enable Unauthenticated API**: Keep configurations default and click "Enable unauthenticated API." **Note**: This is for demo purposes only and not recommended for production workloads; secure publishing options are available in documentation.
3.  **Copy Code Snippet**: A small CSS code snippet will appear; **copy this code snippet** as it will be integrated into a website.

### Integrating with a Sample Python Flask Web Application

You can use the Cloud Editor environment to create a website.

1.  **Open Cloud Editor**:
    *   Open Google Cloud Console.
    *   Click "Activate Cloud Shell".
    *   Click "Open Editor". Authorize Cloud Shell if prompted.
2.  **Use Gemini Code Assist**:
    *   Once Cloud Shell Editor is open, click "Gemini Code Assist" and log in to your Google Cloud Project. Enable API if prompted.
    *   Ask Gemini Code Assist to create a Flask app and integrate the AI agent code snippet using a prompt like:
        ```
        Here is my Travel buddy Vertex AI agent builder agent publish code snippet,
        <REPLACE IT WITH YOUR AI AGENT PUBLISH CODE SNIPPET>
        can you create a sample flask app to use it
        ```
        Gemini Code Assist can generate code in different programming languages.
3.  **Create and Run `app.py`**:
    *   Copy the sample Flask app code snippet provided by Gemini Code Assist (an example is given in the sources).
    *   Create a new file named `app.py` in your project directory and save the code.
    *   Open the terminal in Cloud Shell and navigate to the directory where `app.py` is saved.
    *   Run the command: `python app.py`.
    *   **Note**: Flask installation is not required as Cloud Shell has common utilities installed by default.
4.  **Preview Web Application**:
    *   The Flask app will run on port `5000`.
    *   Click the "Web Preview" icon in Cloud Shell, then "Change Port," input `5000`, and click "Change and Preview".
    *   A sample website will appear with the AI agent available; click it to start chatting.

You can further customize your website or add more grounding data to the AI agent.

### Deploying the AI Agent to Cloud Run

To host your AI agent on Google Cloud for wider access, you can deploy the sample Flask application to Cloud Run as a container.

1.  **Stop Flask App**: In the Cloud Shell Terminal, press `Ctrl + C` to kill the Flask app process.
2.  **Ask Gemini Code Assist for Deployment Help**: Click "Open Editor" again and ask Gemini Code Assist for help with containerizing and deploying the application to Cloud Run with a prompt like: `Can you help me deploy this sample flask app to cloud run service`.
3.  **Follow Deployment Steps**: Gemini Code Assist will provide instructions and commands. Key steps include:
    *   **Prerequisites**: Google Cloud account with billing, `gcloud` CLI (installed and initialized), Docker (installed), and project setup in `gcloud` CLI. (Note: Cloud Shell handles many of these pre-requisites).
    *   **Create `requirements.txt`**: List all Python packages your app needs (e.g., `Flask`).
    *   **Create `Dockerfile`**: Define how to build a Docker image for your application.
        ```dockerfile
        # Use an official Python runtime as a parent image
        FROM python:3.9-slim-buster

        # Set the working directory to /app
        WORKDIR /app

        # Copy the current directory contents into the container at /app
        COPY . /app

        # Install any needed packages specified in requirements.txt
        RUN pip install --no-cache-dir -r requirements.txt

        # Make port 5000 available to the world outside this container
        EXPOSE 5000

        # Define environment variable
        ENV NAME World

        # Run app.py when the container launches
        CMD ["python", ".py"]
        ```
    *   **Build the Docker Image**: Open your terminal, navigate to your project directory, and run: `gcloud builds submit –tag gcr.io/bgr-workshop-23rd/travel-buddy`.
    *   **Deploy to Cloud Run**: After the image is built and uploaded, deploy it with: `gcloud run deploy travel-buddy --image gcr.io/bgr-workshop-23rd/travel-buddy --region us-central1`.

Once these steps are completed, your application with the integrated AI agent will be live for end users.

## 6. Clean Up

To avoid incurring charges, you can delete the Google Cloud project used for this codelab:

1.  Go to the Google Cloud console, Manage resources page.
2.  Select the project you want to delete and click "Delete".
3.  Type the project ID in the dialog and click "Shut down".
4.  Alternatively, you can go to Cloud Run on the console, select the service you deployed, and delete it.
```